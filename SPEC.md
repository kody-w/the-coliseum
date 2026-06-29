# The Coliseum — Data Contract (v1)

Every component builds against these shapes. Keep them stable so parts integrate.

## Creature — `creatures/<id>.json`
```json
{
  "id": "uuid4 string",
  "name": "generated fantasy name (NEVER a real person)",
  "genome": {"ferocity":0.0, "guile":0.0, "creativity":0.0, "discipline":0.0, "nerve":0.0},
  "generation": 0,
  "parents": ["id","id"],
  "bloodline": "alpha",
  "wins": 0, "losses": 0, "alive": true
}
```
genome values are floats in [0,1].

## Challenge — `challenges/<name>.py`
Each module exports:
- `PROMPT: str` — the task posed to a creature
- `def score(output: str) -> float` — higher is better; objective where possible
Optional: `TITLE: str`. No private network calls.

## Match — appended to `arena/feed.jsonl` (one JSON object per line)
```json
{"ts": 0.0, "challenge":"name", "a":"id", "b":"id", "score_a":0.0, "score_b":0.0, "winner":"id|draw"}
```

## genome -> strategy
`genome_to_persona(creature) -> str` returns the system-prompt a creature fights with.
High ferocity=bold/risky; discipline=careful/correct; guile=exploits the scorer;
creativity=unconventional; nerve=commits under pressure.

## Components & how they connect
- `genome.py` / `creature.py`  — bloodline lab (genome, breeding, genome_to_persona)
- `arena.py` + `challenges/`    — match engine; calls the LOCAL brainstem at `http://127.0.0.1:7071/chat`
- `index.html`                  — Coliseum Floor; reads `creatures/` + `arena/feed.jsonl`, auto-refresh

## HARD RULES (enforced)
- **NO PII ANYWHERE**: no real names, emails, usernames, home paths (`/Users/...`), hostnames, IPs, MACs, tokens, or machine identifiers — in code, comments, commits, tests, or data. Fantasy/generic only. Relative paths only.
- Secrets via env, never committed.
