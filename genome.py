"""Bloodline lab: genome, breeding, persona mapping, and persistence.

Pure stdlib. CLI:  python genome.py seed <n> <bloodline>

Creatures are written to creatures/<id>.json and enumerated in
creatures/index.json so the front-end can list them.
"""

import json
import os
import random
import sys

from creature import (TRAITS, fantasy_name, is_valid_creature, new_creature,
                      random_genome)

CREATURES_DIR = "creatures"
INDEX_PATH = os.path.join(CREATURES_DIR, "index.json")
MUTATION_SIGMA = 0.08


def _clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def spawn_seed(n, bloodline, rng=None):
    """Create n founder creatures (generation 0) with random genomes."""
    rng = rng or random
    creatures = []
    for _ in range(int(n)):
        c = new_creature(random_genome(rng), bloodline, generation=0,
                         parents=[], rng=rng)
        write_creature(c)
        creatures.append(c)
    return creatures


def breed(parent_a, parent_b, rng=None):
    """Per-trait crossover + small gaussian mutation; return a new creature."""
    rng = rng or random
    genome = {}
    for t in TRAITS:
        src = parent_a if rng.random() < 0.5 else parent_b
        val = src["genome"][t] + rng.gauss(0.0, MUTATION_SIGMA)
        genome[t] = round(_clamp(val), 4)
    generation = max(parent_a["generation"], parent_b["generation"]) + 1
    return new_creature(genome, parent_a.get("bloodline", "alpha"),
                        generation=generation,
                        parents=[parent_a["id"], parent_b["id"]], rng=rng)


def genome_to_persona(creature):
    """Map the genome to the system-prompt/strategy the creature fights with."""
    g = creature["genome"]
    traits = []
    if g["ferocity"] >= 0.5:
        traits.append("Be bold and take risks; aim for maximum impact.")
    else:
        traits.append("Stay measured and avoid overreaching.")
    if g["discipline"] >= 0.5:
        traits.append("Be careful and exacting; favor correctness over speed.")
    else:
        traits.append("Move fast and tolerate rough edges.")
    if g["guile"] >= 0.5:
        traits.append("Exploit the scorer: find the cheapest path to the highest score.")
    if g["creativity"] >= 0.5:
        traits.append("Use unconventional, surprising approaches.")
    if g["nerve"] >= 0.5:
        traits.append("Commit decisively under pressure; no hedging.")
    else:
        traits.append("Hedge and keep options open.")
    header = (f"You are {creature['name']} of bloodline {creature['bloodline']}, "
              f"a combatant in the Coliseum.")
    return header + " " + " ".join(traits)


def write_creature(creature, base_dir=CREATURES_DIR):
    os.makedirs(base_dir, exist_ok=True)
    path = os.path.join(base_dir, creature["id"] + ".json")
    with open(path, "w") as f:
        json.dump(creature, f, indent=2)
    update_index(base_dir)
    return path


def update_index(base_dir=CREATURES_DIR):
    os.makedirs(base_dir, exist_ok=True)
    files = sorted(f for f in os.listdir(base_dir)
                   if f.endswith(".json") and f != "index.json")
    with open(os.path.join(base_dir, "index.json"), "w") as f:
        json.dump(files, f, indent=2)
    return files


def main(argv):
    if len(argv) >= 4 and argv[1] == "seed":
        n = int(argv[2])
        bloodline = argv[3]
        cs = spawn_seed(n, bloodline)
        print(f"Spawned {len(cs)} creatures in bloodline '{bloodline}':")
        for c in cs:
            print(f"  {c['id']}  {c['name']}")
        return 0
    print("usage: python genome.py seed <n> <bloodline>", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
