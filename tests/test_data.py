"""Data layer: weighted draws from the database and the fallback lists."""

import collections
import random
import re

from argus import data, identifiers as ids

STREET = re.compile(r"((ul|al|pl|os)\. )?\S.* \d+")


def test_mode_and_note(data_source):
    assert data.has_database() is (data_source == "database")
    assert ("make data" in data.source_note()) is (data_source == "fallback")


def test_names(data_source):
    rng = random.Random(1)
    for female in (True, False):
        for _ in range(200):
            first, last = data.first_name(female, rng), data.surname(female, rng)
            assert first and first[0].isupper() and first == first.strip()
            assert last and last[0].isupper()


def test_female_surname_forms(data_source):
    rng = random.Random(2)
    female = [data.surname(True, rng) for _ in range(300)]
    assert not any(s.endswith("ski") for s in female)
    assert any(s.endswith("ska") for s in female)


def test_addresses(data_source):
    rng = random.Random(3)
    for _ in range(300):
        postal, city, street = data.address(rng)
        assert re.fullmatch(r"\d{2}-\d{3}", postal)
        assert city
        assert STREET.fullmatch(street), street


def test_bank_branches(data_source):
    rng = random.Random(4)
    for _ in range(300):
        branch, name = data.bank_branch(rng)
        assert ids.is_valid_settlement_number(branch) and name


def test_same_seed_same_draws(data_source):
    def draw(seed):
        rng = random.Random(seed)
        return [data.first_name(True, rng), data.surname(False, rng), data.address(rng), data.bank_branch(rng)]
    assert draw(7) == draw(7)


def test_database_draws_follow_frequency(data_source):
    if data_source != "database":
        return
    rng = random.Random(5)
    counts = collections.Counter(data.first_name(True, rng) for _ in range(3000))
    top10 = [n for (n,) in data._db.execute(
        "SELECT name FROM first_names WHERE female = 1 ORDER BY cum LIMIT 10")]
    # The ten most frequent names hold roughly a third of the population;
    # a uniform draw over ~1500 names would give well under 2%.
    assert sum(counts[n] for n in top10) / 3000 > 0.2
