"""Coliseum challenges.

Each module exports:
- PROMPT: str           the task posed to a creature
- score(output) -> float  higher is better, objective where possible
Optional: TITLE: str

Challenges are pure functions of the creature's text output. They MUST be safe:
no exec/eval of model output, no private network calls, no file/system access.
"""
