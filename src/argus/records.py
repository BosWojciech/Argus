"""Record builders for the five generator tabs.

Each builder returns an ordered ``dict`` of Polish label -> value, ready to be
shown in the UI. Options mirror the controls on each tab.
"""

import random
import re
from datetime import date, timedelta

from argus import data, identifiers as ids

AGE_RANGES = {
    "0-99": (0, 99),
    "0-18": (0, 18),
    "19-24": (19, 24),
    "25-65": (25, 65),
    "65-99": (65, 99),
}
AGE_HINT = "Wpisz wiek lub datę (rrrr-mm, rrrr-mm-dd)"


def _years_before(day: date, years: int) -> date:
    """Same calendar day ``years`` earlier; 29 Feb falls back to 28 Feb."""
    try:
        return day.replace(year=day.year - years)
    except ValueError:
        return day.replace(year=day.year - years, day=28)


def birth_from_age_range(lo: int, hi: int, today: date, rng=random) -> date:
    """Random birth date for someone whose completed age is in ``[lo, hi]``."""
    earliest = _years_before(today, hi + 1) + timedelta(days=1)
    latest = _years_before(today, lo)
    return date.fromordinal(rng.randint(earliest.toordinal(), latest.toordinal()))


def parse_age_input(text: str, today: date, rng=random) -> date | None:
    """Turn the free-text age field into a birth date.

    Accepts an age in completed years (``40``), a month (``1984-06``, random
    day) or a full date (``1984-06-03``). Empty text returns ``None`` so the
    age range applies. Anything else raises ``ValueError`` with a user message.
    """
    text = text.strip()
    if not text:
        return None
    try:
        if re.fullmatch(r"\d{1,3}", text):
            age = int(text)
            birth = birth_from_age_range(age, age, today, rng)
        elif m := re.fullmatch(r"(\d{4})-(\d{2})", text):
            year, month = int(m[1]), int(m[2])
            first = date(year, month, 1)
            last = (first.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            if first <= today < last:
                last = today
            birth = date(year, month, rng.randint(1, last.day))
        elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            birth = date.fromisoformat(text)
        else:
            raise ValueError
    except ValueError:
        raise ValueError(f"Niepoprawna wartość: {text!r}. {AGE_HINT}") from None
    if birth > today:
        raise ValueError("Data urodzenia nie może być z przyszłości.")
    if birth.year < 1800:
        raise ValueError("PESEL obsługuje tylko lata 1800-2299.")
    return birth


def _address(rng) -> dict:
    """Postal code, city and street with house number."""
    postal, city, street = data.address(rng)
    return {"Kod pocztowy": postal, "Miasto": city, "Ulica": street}


def person(gender: str = "any", age_range: str = "0-99", age_text: str = "",
           today: date | None = None, rng=random) -> dict:
    """Personal record. A non-empty ``age_text`` overrides ``age_range``."""
    today = today or date.today()
    female = rng.random() < 0.5 if gender == "any" else gender == "female"
    birth = parse_age_input(age_text, today, rng) or birth_from_age_range(*AGE_RANGES[age_range], today, rng)
    first = data.first_name(female, rng)
    last = data.surname(female, rng)
    return {
        "Imię": first,
        "Nazwisko": last,
        "Imię i nazwisko": f"{first} {last}",
        "Data urodzin": birth.isoformat(),
        "Pesel": ids.make_pesel(birth, female, rng),
        "Dowód osobisty": ids.make_id_card(rng),
        **_address(rng),
    }


def company(regon_length: int = 9, rng=random) -> dict:
    """Company record: NIP, REGON of ``regon_length`` digits (9 or 14) and an address."""
    return {
        "NIP": ids.make_nip(rng),
        "REGON": ids.make_regon(regon_length, rng),
        **_address(rng),
    }


def bank(card_brand: str = "any", today: date | None = None, rng=random) -> dict:
    """Bank account and card are independent draws, followed by a person."""
    today = today or date.today()
    iban, bank_name = ids.make_iban(rng=rng)
    return {
        "Konto bankowe": iban,
        "Nazwa banku": bank_name,
        "Karta płatnicza": ids.make_card(card_brand, rng),
        "CVC": ids.make_cvc(rng),
        "Data ważności": ids.make_expiry(today, rng),
        **person(today=today, rng=rng),
    }


def vehicle(today: date | None = None, rng=random) -> dict:
    """Vehicle record: VIN and registration plate, followed by a person."""
    return {
        "VIN": ids.make_vin(rng),
        "Tablice rejestracyjne": ids.make_plate(rng),
        **person(today=today, rng=rng),
    }


def combined(today: date | None = None, rng=random) -> dict:
    """Everything at once, with a short bank section (no bank name/CVC/expiry)."""
    return {
        **person(today=today, rng=rng),
        "NIP": ids.make_nip(rng),
        "REGON": ids.make_regon(9, rng),
        "Karta płatnicza": ids.make_card("any", rng),
        "Konto bankowe": ids.make_iban(rng=rng)[0],
        "VIN": ids.make_vin(rng),
        "Tablice rejestracyjne": ids.make_plate(rng),
    }
