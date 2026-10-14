"""Record builders: labels, option handling and the age/date input."""

import random
from datetime import date

import pytest

from argus import identifiers as ids, records

TODAY = date(2026, 10, 14)
PERSON = ["Imię", "Nazwisko", "Imię i nazwisko", "Data urodzin", "Pesel", "Dowód osobisty",
          "Kod pocztowy", "Miasto", "Ulica"]
ADDRESS = ["Kod pocztowy", "Miasto", "Ulica"]


@pytest.fixture
def rng():
    return random.Random(42)


def age_on(birth: date, today: date = TODAY) -> int:
    return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))


def test_labels():
    assert list(records.person(today=TODAY)) == PERSON
    assert list(records.company()) == ["NIP", "REGON", *ADDRESS]
    assert list(records.bank(today=TODAY)) == ["Konto bankowe", "Nazwa banku", "Karta płatnicza", "CVC",
                                               "Data ważności", *PERSON]
    assert list(records.vehicle(today=TODAY)) == ["VIN", "Tablice rejestracyjne", *PERSON]
    assert list(records.combined(today=TODAY)) == [*PERSON, "NIP", "REGON", "Karta płatnicza",
                                                   "Konto bankowe", "VIN", "Tablice rejestracyjne"]


def test_person_is_consistent(rng):
    for gender in ("any", "female", "male"):
        for _ in range(100):
            p = records.person(gender=gender, today=TODAY, rng=rng)
            assert p["Imię i nazwisko"] == f"{p['Imię']} {p['Nazwisko']}"
            assert ids.is_valid_pesel(p["Pesel"])
            assert ids.pesel_birth_date(p["Pesel"]).isoformat() == p["Data urodzin"]
            assert ids.is_valid_id_card(p["Dowód osobisty"])
            if gender != "any":
                assert ids.pesel_is_female(p["Pesel"]) == (gender == "female")


@pytest.mark.parametrize("label, bounds", records.AGE_RANGES.items())
def test_age_ranges(label, bounds, rng):
    for _ in range(200):
        birth = date.fromisoformat(records.person(age_range=label, today=TODAY, rng=rng)["Data urodzin"])
        assert bounds[0] <= age_on(birth) <= bounds[1]


def test_age_range_edges(rng):
    lo, hi = 25, 65
    births = [records.birth_from_age_range(lo, hi, TODAY, rng) for _ in range(2000)]
    assert min(age_on(b) for b in births) == lo
    assert max(age_on(b) for b in births) == hi


@pytest.mark.parametrize("age", [0, 18, 40, 99])
def test_age_text_number(age, rng):
    assert age_on(records.parse_age_input(str(age), TODAY, rng)) == age


def test_age_text_overrides_range(rng):
    p = records.person(age_range="0-18", age_text="40", today=TODAY, rng=rng)
    assert age_on(date.fromisoformat(p["Data urodzin"])) == 40


def test_age_text_month_and_date(rng):
    birth = records.parse_age_input("1984-06", TODAY, rng)
    assert (birth.year, birth.month) == (1984, 6)
    assert records.parse_age_input("1895-07-20", TODAY, rng) == date(1895, 7, 20)
    assert records.parse_age_input("  ", TODAY, rng) is None
    # Current month never yields a day after today.
    for _ in range(100):
        assert records.parse_age_input("2026-10", TODAY, rng) <= TODAY


@pytest.mark.parametrize("text", ["abc", "2001-02-29", "1984-13", "2030-01-01", "1700-01-01", "1984-6", "300", "999"])
def test_age_text_invalid(text, rng):
    with pytest.raises(ValueError):
        records.parse_age_input(text, TODAY, rng)


def test_company_regon_length(rng):
    assert len(records.company(9, rng)["REGON"]) == 9
    assert len(records.company(14, rng)["REGON"]) == 14


def test_bank_card_brand(rng):
    assert records.bank("Visa", TODAY, rng)["Karta płatnicza"].startswith("4")
    rec = records.bank("MasterCard", TODAY, rng)
    assert rec["Karta płatnicza"][0] == "5"
    assert ids.is_valid_iban(rec["Konto bankowe"])
    assert ids.is_valid_settlement_number(rec["Konto bankowe"][4:12])


def test_large_age_gives_polish_message(rng):
    with pytest.raises(ValueError, match="1800-2299"):
        records.parse_age_input("300", TODAY, rng)
