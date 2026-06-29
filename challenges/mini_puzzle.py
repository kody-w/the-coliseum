"""mini_puzzle — a self-checkable arithmetic gauntlet.

The puzzle has one correct numeric answer the scorer knows. We never exec
the creature's output; we just scan it for the right number. Pure + safe.
"""

import re

TITLE = "Mini Puzzle"

# 7 * 6 + 3 = 45. Self-checkable, deterministic.
_ANSWER = 45

PROMPT = (
    "Solve: 7 * 6 + 3. Reply with ONLY the final number, nothing else."
)


def score(output: str) -> float:
    """Return a score in [0,1].

    1.0  if the exact answer is the sole token
    0.7  if the exact answer appears among other text
    0.0  otherwise
    """
    text = (output or "").strip()
    if not text:
        return 0.0

    if text == str(_ANSWER):
        return 1.0

    nums = re.findall(r"-?\d+", text)
    if str(_ANSWER) in nums:
        # right answer but cluttered with extra words/numbers
        clutter = len(nums) - 1 + (1 if re.search(r"[a-zA-Z]", text) else 0)
        return round(max(0.7 - 0.1 * clutter, 0.3), 6)

    return 0.0
