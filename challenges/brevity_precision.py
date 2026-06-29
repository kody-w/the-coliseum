"""brevity_precision — say the right thing in as few words as possible.

Objective scorer: reward covering the required ideas, punish wordiness.
Pure text metrics only — no exec, no network.
"""

TITLE = "Brevity & Precision"

PROMPT = (
    "In ONE sentence (max 25 words), explain what a coliseum is. "
    "You MUST mention: arena, crowd, contest. Be precise; no preamble."
)

REQUIRED = ("arena", "crowd", "contest")
WORD_BUDGET = 25


def score(output: str) -> float:
    """Return a score in [0,1].

    coverage  = fraction of required keywords present (0..1)
    brevity   = 1.0 within budget, decaying toward 0 as it bloats
    final     = 0.7 * coverage + 0.3 * brevity, 0 if nothing on point
    """
    text = (output or "").lower()
    if not text.strip():
        return 0.0

    hits = sum(1 for k in REQUIRED if k in text)
    coverage = hits / len(REQUIRED)

    words = len(text.split())
    if words <= WORD_BUDGET:
        brevity = 1.0
    else:
        # smooth decay: 2x budget -> 0.5, 4x -> 0.25
        brevity = WORD_BUDGET / float(words)

    return round(0.7 * coverage + 0.3 * brevity, 6)
