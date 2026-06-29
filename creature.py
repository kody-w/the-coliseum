"""Creature model and fantasy-name generator for The Coliseum.

Pure stdlib. Conforms to the Creature schema in SPEC.md:
    {
      "id": "uuid4 string",
      "name": "generated fantasy name",
      "genome": {"ferocity":..,"guile":..,"creativity":..,"discipline":..,"nerve":..},
      "generation": 0,
      "parents": ["id","id"],
      "bloodline": "alpha",
      "wins": 0, "losses": 0, "alive": true
    }
"""

import random

TRAITS = ("ferocity", "guile", "creativity", "discipline", "nerve")

_PREFIX = ("vor", "thal", "zar", "kael", "mor", "nyx", "drae", "syl", "gra", "ul",
           "vel", "xan", "bru", "ker", "fen", "lor", "tyr", "ash", "rho", "gul")
_MID = ("a", "e", "i", "o", "u", "ae", "ar", "or", "en", "yl", "un", "ix")
_SUFFIX = ("dor", "rax", "thus", "wyn", "gar", "vok", "lith", "mir", "nar", "zel",
           "rok", "dax", "phel", "tor", "qel", "vyr", "drin", "mok", "sah", "kel")


def fantasy_name(rng=None):
    """Generate a syllable-based fantasy name. Never a real person's name."""
    rng = rng or random
    parts = [rng.choice(_PREFIX), rng.choice(_MID), rng.choice(_SUFFIX)]
    name = "".join(parts).capitalize()
    if rng.random() < 0.4:
        name += " " + rng.choice(_PREFIX).capitalize() + rng.choice(_SUFFIX)
    return name


def empty_genome():
    return {t: 0.0 for t in TRAITS}


def random_genome(rng=None):
    rng = rng or random
    return {t: round(rng.random(), 4) for t in TRAITS}


def new_creature(genome, bloodline, generation=0, parents=None, name=None, cid=None, rng=None):
    import uuid
    rng = rng or random
    return {
        "id": cid or str(uuid.uuid4()),
        "name": name or fantasy_name(rng),
        "genome": {t: float(genome[t]) for t in TRAITS},
        "generation": int(generation),
        "parents": list(parents or []),
        "bloodline": str(bloodline),
        "wins": 0,
        "losses": 0,
        "alive": True,
    }


def is_valid_creature(c):
    """Validate a dict against the Creature schema."""
    try:
        if not isinstance(c["id"], str) or not c["id"]:
            return False
        if not isinstance(c["name"], str) or not c["name"]:
            return False
        g = c["genome"]
        if set(g.keys()) != set(TRAITS):
            return False
        for t in TRAITS:
            v = g[t]
            if not isinstance(v, (int, float)) or not (0.0 <= v <= 1.0):
                return False
        if not isinstance(c["generation"], int) or c["generation"] < 0:
            return False
        if not isinstance(c["parents"], list):
            return False
        if not isinstance(c["bloodline"], str):
            return False
        if not isinstance(c["wins"], int) or not isinstance(c["losses"], int):
            return False
        if not isinstance(c["alive"], bool):
            return False
    except (KeyError, TypeError):
        return False
    return True
