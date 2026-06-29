#!/usr/bin/env python3
"""The Coliseum — arena engine.

Loads creatures, poses challenges to them via the LOCAL brainstem, scores the
outputs, records matches, then culls the weak and breeds the strong into the
next generation.

Run:
    python arena.py seed --count 8        # forge a starting population
    python arena.py run --generations 5   # fight, cull, breed

Contract lives in SPEC.md. NO PII anywhere — fantasy/generic only, relative
paths only. Model output is NEVER executed; the brainstem host is local only.
"""

import argparse
import glob
import importlib
import json
import os
import random
import time
import urllib.error
import urllib.request
import uuid

# Paths are relative to this file so the engine works from any cwd.
ROOT = os.path.dirname(os.path.abspath(__file__))
CREATURES_DIR = os.path.join(ROOT, "creatures")
ARENA_DIR = os.path.join(ROOT, "arena")
FEED_PATH = os.path.join(ARENA_DIR, "feed.jsonl")

# Local brainstem only. Overridable via env, but defaults to loopback.
BRAINSTEM_URL = os.environ.get("BRAINSTEM_URL", "http://127.0.0.1:7071/chat")
BRAINSTEM_TIMEOUT = float(os.environ.get("BRAINSTEM_TIMEOUT", "30"))

TRAITS = ("ferocity", "guile", "creativity", "discipline", "nerve")

# --- genome lab integration -------------------------------------------------
# genome.py is built by the bloodline-lab component. Import it when present;
# otherwise fall back to a spec-faithful local implementation so the arena is
# self-sufficient and merge-safe.
try:
    from genome import genome_to_persona, breed  # type: ignore
except Exception:  # pragma: no cover - exercised when genome.py is absent
    def genome_to_persona(creature):
        g = creature.get("genome", {})

        def lv(t):
            return g.get(t, 0.0)
        bits = []
        bits.append("bold and risky" if lv("ferocity") > 0.5 else "measured")
        bits.append("careful and correct" if lv("discipline") > 0.5 else "loose")
        if lv("guile") > 0.5:
            bits.append("works the scorer to maximize points")
        if lv("creativity") > 0.5:
            bits.append("unconventional")
        bits.append("commits under pressure" if lv("nerve") > 0.5 else "cautious")
        return (
            "You are a coliseum creature. Fight to win the challenge. "
            "Be " + ", ".join(bits) + ". Answer the task directly."
        )

    def breed(a, b):
        ga, gb = a.get("genome", {}), b.get("genome", {})
        child = {}
        for t in TRAITS:
            base = ga.get(t, 0.0) if random.random() < 0.5 else gb.get(t, 0.0)
            base += random.uniform(-0.08, 0.08)  # mutation
            child[t] = round(min(1.0, max(0.0, base)), 4)
        return {
            "genome": child,
            "parents": [a.get("id"), b.get("id")],
            "bloodline": a.get("bloodline", "alpha"),
        }


# --- creature io ------------------------------------------------------------

def _ensure_dirs():
    os.makedirs(CREATURES_DIR, exist_ok=True)
    os.makedirs(ARENA_DIR, exist_ok=True)


def creature_path(cid):
    return os.path.join(CREATURES_DIR, f"{cid}.json")


def load_creatures():
    """Load every creature. Honors creatures/index.json if present."""
    _ensure_dirs()
    paths = []
    index = os.path.join(CREATURES_DIR, "index.json")
    if os.path.exists(index):
        with open(index) as f:
            ids = json.load(f)
        for entry in ids:
            entry = str(entry)
            p = entry if entry.endswith(".json") else f"{entry}.json"
            paths.append(os.path.join(CREATURES_DIR, os.path.basename(p)))
    else:
        for p in sorted(glob.glob(os.path.join(CREATURES_DIR, "*.json"))):
            if os.path.basename(p) != "index.json":
                paths.append(p)
    out = []
    for p in paths:
        if not os.path.exists(p):
            continue
        with open(p) as f:
            c = json.load(f)
        c["_path"] = p
        out.append(c)
    return out


def save_creature(c):
    data = {k: v for k, v in c.items() if not k.startswith("_")}
    path = c.get("_path") or creature_path(c["id"])
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def make_creature(generation=0, parents=None, bloodline="alpha", genome=None):
    cid = str(uuid.uuid4())
    if genome is None:
        genome = {t: round(random.random(), 4) for t in TRAITS}
    name = random.choice(_FALLBACK_NAMES) + "-" + cid[:4]
    return {
        "id": cid,
        "name": name,
        "genome": genome,
        "generation": generation,
        "parents": parents or [],
        "bloodline": bloodline,
        "wins": 0,
        "losses": 0,
        "alive": True,
    }


_FALLBACK_NAMES = [
    "Ashfang", "Brakka", "Cindra", "Dornel", "Emberlyn", "Fyrgar", "Grimsel",
    "Halveth", "Ironmaw", "Jorund", "Kessra", "Lurok", "Mordwen", "Nyxara",
    "Othrik", "Pyralis", "Quenvar", "Rhaegor", "Sablewing", "Thornak",
]


# --- brainstem --------------------------------------------------------------

def query_brainstem(user_input):
    """POST {"user_input": ...} to the local brainstem; return response text.

    Network/parse failures yield "" so a match is still recorded (low score).
    """
    body = json.dumps({"user_input": user_input}).encode("utf-8")
    req = urllib.request.Request(
        BRAINSTEM_URL, data=body, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=BRAINSTEM_TIMEOUT) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        return str(payload.get("response", ""))
    except (urllib.error.URLError, ValueError, OSError):
        return ""


# --- matches ----------------------------------------------------------------

def _challenge_name(challenge):
    return getattr(challenge, "NAME", challenge.__name__.split(".")[-1])


def _fight(creature, challenge):
    persona = genome_to_persona(creature)
    user_input = persona + "\n\n" + challenge.PROMPT
    output = query_brainstem(user_input)
    return float(challenge.score(output))


def run_match(a, b, challenge):
    """Pit a vs b at a challenge, append a feed line, return the result dict."""
    score_a = _fight(a, challenge)
    score_b = _fight(b, challenge)
    if score_a > score_b:
        winner = a["id"]
    elif score_b > score_a:
        winner = b["id"]
    else:
        winner = "draw"
    record = {
        "ts": time.time(),
        "challenge": _challenge_name(challenge),
        "a": a["id"],
        "b": b["id"],
        "score_a": score_a,
        "score_b": score_b,
        "winner": winner,
    }
    _ensure_dirs()
    with open(FEED_PATH, "a") as f:
        f.write(json.dumps(record) + "\n")
    return record


# --- generation -------------------------------------------------------------

def run_generation(challenges):
    """Round-robin living creatures across challenges, tally, cull, breed."""
    creatures = [c for c in load_creatures() if c.get("alive", True)]
    by_id = {c["id"]: c for c in creatures}
    if len(creatures) < 2:
        print("Not enough living creatures to run a generation (need >= 2).")
        return creatures

    for i in range(len(creatures)):
        for j in range(i + 1, len(creatures)):
            a, b = creatures[i], creatures[j]
            for ch in challenges:
                r = run_match(a, b, ch)
                if r["winner"] == a["id"]:
                    a["wins"] += 1
                    b["losses"] += 1
                elif r["winner"] == b["id"]:
                    b["wins"] += 1
                    a["losses"] += 1

    def winrate(c):
        total = c["wins"] + c["losses"]
        return c["wins"] / total if total else 0.0

    ranked = sorted(creatures, key=winrate, reverse=True)
    cull_n = len(ranked) // 3
    survivors = ranked[: len(ranked) - cull_n] if cull_n else ranked[:]
    for c in ranked[len(ranked) - cull_n:]:
        c["alive"] = False

    next_gen = (max(c["generation"] for c in creatures) + 1) if creatures else 1
    pairs = max(1, len(survivors) // 2)
    for k in range(pairs):
        pa, pb = survivors[2 * k % len(survivors)], survivors[(2 * k + 1) % len(survivors)]
        spawn = breed(pa, pb)
        genome = spawn.get("genome", spawn)
        child = make_creature(
            generation=next_gen,
            parents=spawn.get("parents", [pa["id"], pb["id"]]),
            bloodline=spawn.get("bloodline", pa.get("bloodline", "alpha")),
            genome=genome,
        )
        save_creature(child)

    for c in creatures:
        save_creature(c)

    living = sum(1 for c in load_creatures() if c.get("alive", True))
    print(f"gen done: {len(creatures)} fought, {cull_n} culled, {pairs} bred, {living} alive")
    return creatures


# --- challenge discovery ----------------------------------------------------

def load_challenges():
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, "challenges", "*.py"))):
        base = os.path.basename(p)
        if base.startswith("_"):
            continue
        mod = importlib.import_module(f"challenges.{base[:-3]}")
        if hasattr(mod, "PROMPT") and hasattr(mod, "score"):
            out.append(mod)
    return out


def seed(count):
    _ensure_dirs()
    for _ in range(count):
        save_creature(make_creature())
    print(f"seeded {count} creatures")


def main():
    ap = argparse.ArgumentParser(description="The Coliseum arena engine")
    sub = ap.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("run", help="run N generations")
    pr.add_argument("--generations", type=int, default=1)
    ps = sub.add_parser("seed", help="create starting creatures")
    ps.add_argument("--count", type=int, default=8)
    args = ap.parse_args()

    if args.cmd == "seed":
        seed(args.count)
    elif args.cmd == "run":
        challenges = load_challenges()
        if not challenges:
            print("no challenges found in challenges/")
            return
        for g in range(args.generations):
            print(f"== generation {g + 1}/{args.generations} ==")
            run_generation(challenges)


if __name__ == "__main__":
    main()
