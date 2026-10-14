"""Checksum rules and generators for individual identifiers."""

import random
from datetime import date

import pytest

from argus import identifiers as ids

RUNS = 300


@pytest.fixture
def rng():
    return random.Random(1234)


# Publicly known valid examples confirm the validators themselves.
@pytest.mark.parametrize("check, value", [
    (ids.is_valid_pesel, "44051401458"),
    (ids.is_valid_id_card, "ABA300000"),
    (ids.is_valid_nip, "1234563218"),
    (ids.is_valid_regon, "123456785"),
    (ids.is_valid_iban, "PL61109010140000071219812874"),
    (ids.is_valid_luhn, "4111111111111111"),
    (ids.is_valid_vin, "1M8GDM9AXKP042788"),
])
def test_known_valid(check, value):
    assert check(value)


@pytest.mark.parametrize("check, value", [
    (ids.is_valid_pesel, "44051401459"),
    (ids.is_valid_id_card, "ABA300001"),
    (ids.is_valid_nip, "1234563219"),
    (ids.is_valid_regon, "123456786"),
    (ids.is_valid_iban, "PL62109010140000071219812874"),
    (ids.is_valid_luhn, "4111111111111112"),
    (ids.is_valid_vin, "1M8GDM9A1KP042788"),
])
def test_known_invalid(check, value):
    assert not check(value)


@pytest.mark.parametrize("birth, prefix", [
    (date(1895, 7, 20), "958720"),
    (date(1928, 6, 17), "280617"),
    (date(2021, 1, 6), "212106"),
    (date(2105, 12, 31), "055231"),
    (date(2299, 1, 1), "996101"),
])
def test_pesel_century_encoding(birth, prefix, rng):
    pesel = ids.make_pesel(birth, female=True, rng=rng)
    assert pesel.startswith(prefix)
    assert ids.pesel_birth_date(pesel) == birth
    assert ids.is_valid_pesel(pesel)


def test_pesel_sex_digit(rng):
    for _ in range(RUNS):
        assert ids.pesel_is_female(ids.make_pesel(date(1990, 1, 1), True, rng))
        assert not ids.pesel_is_female(ids.make_pesel(date(1990, 1, 1), False, rng))


def test_pesel_rejects_unencodable_year(rng):
    with pytest.raises(ValueError):
        ids.make_pesel(date(1799, 1, 1), True, rng)


def test_generated_values_are_valid(rng):
    for _ in range(RUNS):
        assert ids.is_valid_id_card(ids.make_id_card(rng))
        assert ids.is_valid_nip(ids.make_nip(rng))
        assert ids.is_valid_regon(ids.make_regon(9, rng))
        assert ids.is_valid_iban(ids.make_iban(rng=rng)[0])
        assert ids.is_valid_luhn(ids.make_card("any", rng))
        assert ids.is_valid_vin(ids.make_vin(rng))


def test_regon14_keeps_valid_base(rng):
    for _ in range(RUNS):
        regon = ids.make_regon(14, rng)
        assert len(regon) == 14 and ids.is_valid_regon(regon)
        assert ids.is_valid_regon(regon[:9])


def test_iban_layout_and_bank(rng):
    for _ in range(RUNS):
        iban, name = ids.make_iban(rng)
        assert iban.startswith("PL") and len(iban) == 28 and name
        assert ids.is_valid_settlement_number(iban[4:12])


@pytest.mark.parametrize("number, valid", [("10205385", True), ("10205386", False), ("1020538", False)])
def test_settlement_number(number, valid):
    assert ids.is_valid_settlement_number(number) is valid


def test_card_brands(rng):
    for _ in range(RUNS):
        assert ids.make_card("Visa", rng).startswith("4")
        assert 51 <= int(ids.make_card("MasterCard", rng)[:2]) <= 55
        assert len(ids.make_card("any", rng)) == 16


def test_expiry_in_future(rng):
    today = date(2026, 10, 14)
    for _ in range(RUNS):
        mm, yy = map(int, ids.make_expiry(today, rng).split("/"))
        assert 1 <= mm <= 12
        assert (2000 + yy, mm) > (today.year, today.month)


def test_plate_format(rng):
    import re
    for _ in range(RUNS):
        assert re.fullmatch(r"[A-Z]{2} \d{5}", ids.make_plate(rng))


# Non-ASCII digits/letters pass str.isdigit()/isalpha() but must be rejected, not raise.
@pytest.mark.parametrize("check, value", [
    (ids.is_valid_pesel, "4405140145²"),
    (ids.is_valid_nip, "123456321²"),
    (ids.is_valid_regon, "12345678²"),
    (ids.is_valid_iban, "PL6110901014000007121981287²"),
    (ids.is_valid_luhn, "411111111111111²"),
    (ids.is_valid_id_card, "ĄBA300000"),
    (ids.is_valid_id_card, "ABA30000²"),
    (ids.is_valid_pesel, "٤٤٠٥١٤٠١٤٥٨"),  # Arabic-Indic digits
])
def test_non_ascii_input_is_rejected(check, value):
    assert check(value) is False
