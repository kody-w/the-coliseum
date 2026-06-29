import json
import os
import random

import genome
from creature import TRAITS, fantasy_name, is_valid_creature, new_creature, random_genome


def test_fantasy_name_no_pii():
    rng = random.Random(0)
    names = {fantasy_name(rng) for _ in range(50)}
    assert all(n and isinstance(n, str) for n in names)
    assert "/" not in "".join(names) and "@" not in "".join(names)


def test_spawn_seed_writes_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cs = genome.spawn_seed(5, "alpha")
    assert len(cs) == 5
    for c in cs:
        assert is_valid_creature(c)
        assert c["generation"] == 0
        assert c["parents"] == []
        assert c["bloodline"] == "alpha"
        assert c["wins"] == 0 and c["losses"] == 0 and c["alive"] is True
        assert os.path.exists(os.path.join("creatures", c["id"] + ".json"))
    idx = json.load(open(os.path.join("creatures", "index.json")))
    assert len(idx) == 5
    assert all(f.endswith(".json") for f in idx)


def test_random_genome_bounds():
    rng = random.Random(1)
    for _ in range(100):
        g = random_genome(rng)
        assert set(g) == set(TRAITS)
        assert all(0.0 <= g[t] <= 1.0 for t in TRAITS)


def test_breed_bounds_and_structure():
    rng = random.Random(2)
    a = new_creature(random_genome(rng), "alpha", generation=2, rng=rng)
    b = new_creature(random_genome(rng), "alpha", generation=5, rng=rng)
    child = genome.breed(a, b, rng=rng)
    assert is_valid_creature(child)
    assert child["generation"] == 6
    assert child["parents"] == [a["id"], b["id"]]
    assert child["id"] not in (a["id"], b["id"])
    assert child["bloodline"] == "alpha"
    for t in TRAITS:
        assert 0.0 <= child["genome"][t] <= 1.0


def test_persona_is_string():
    rng = random.Random(3)
    c = new_creature(random_genome(rng), "alpha", rng=rng)
    p = genome.genome_to_persona(c)
    assert isinstance(p, str) and c["name"] in p


def test_schema_conformance(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cs = genome.spawn_seed(3, "beta")
    for c in cs:
        on_disk = json.load(open(os.path.join("creatures", c["id"] + ".json")))
        assert is_valid_creature(on_disk)
        assert set(on_disk["genome"]) == set(TRAITS)
