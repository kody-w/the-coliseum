"""keyword_quest — name the cardinal virtues of a gladiator.

Objective scorer: fraction of the expected safe keywords present, with a
small bonus for not padding. Pure text metrics only — no exec, no network.
"""

TITLE = "Keyword Quest"

EXPECTED = ("courage", "skill", "honor", "discipline", "endurance")

PROMPT = (
    "List the five cardinal virtues of a gladiator. "
    "Use single words, comma-separated: courage, skill, honor, discipline, endurance."
)


def score(output: str) -> float:
    """Return a score in [0,1] = recall of expected keywords, lightly
    penalized if the answer is much longer than the keyword list itself."""
    text = (output or "").lower()
    if not text.strip():
        return 0.0

    found = sum(1 for k in EXPECTED if k in text)
    recall = found / len(EXPECTED)

    words = len(text.split())
    # ideal is ~5 words; allow generous slack before penalizing.
    bloat = max(0, words - 2 * len(EXPECTED))
    penalty = min(0.3, bloat * 0.01)

    return round(max(0.0, recall - penalty), 6)
