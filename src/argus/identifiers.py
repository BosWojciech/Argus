"""Generators and validators for Polish identifiers and financial numbers.

Every ``make_*`` function returns a value that passes the matching ``is_valid_*``
check. Functions take an optional ``rng`` (anything with the ``random`` module
API) so tests can seed them.
"""

import random
import string
from datetime import date

from argus import data

DIGITS = string.digits
# VIN alphabet: letters I, O and Q are not allowed.
VIN_CHARS = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789"
VIN_YEAR_CHARS = "ABCDEFGHJKLMNPRSTVWXY123456789"
VIN_WEIGHTS = (8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2)
VIN_VALUES = {**{d: int(d) for d in DIGITS}, **dict(zip("ABCDEFGH", range(1, 9))),
              **dict(zip("JKLMN", range(1, 6))), "P": 7, "R": 9,
              **dict(zip("STUVWXYZ", range(2, 10)))}

PESEL_WEIGHTS = (1, 3, 7, 9, 1, 3, 7, 9, 1, 3)
# Century is encoded by adding an offset to the month.
PESEL_MONTH_OFFSET = {18: 80, 19: 0, 20: 20, 21: 40, 22: 60}
ID_CARD_WEIGHTS = (7, 3, 1, 9, 7, 3, 1, 7, 3)
NIP_WEIGHTS = (6, 5, 7, 2, 3, 4, 5, 6, 7)
REGON9_WEIGHTS = (8, 9, 2, 3, 4, 5, 6, 7)
REGON14_WEIGHTS = (2, 4, 8, 5, 0, 9, 7, 3, 6, 1, 2, 4, 8)
SETTLEMENT_WEIGHTS = (3, 9, 7, 1, 3, 9, 7)

CARD_PREFIXES = {
    "Visa": ["4"],
    "MasterCard": ["51", "52", "53", "54", "55"],
}
# "Any" also covers Maestro-style 56-58 prefixes.
CARD_PREFIXES["any"] = CARD_PREFIXES["Visa"] + CARD_PREFIXES["MasterCard"] + ["56", "57", "58"]


def _is_digits(text: str) -> bool:
    """ASCII digits only; ``str.isdigit`` alone accepts e.g. superscripts that ``int`` rejects."""
    return text.isascii() and text.isdigit()


def _digits(rng, n: int) -> str:
    """``n`` random digits as a string."""
    return "".join(rng.choice(DIGITS) for _ in range(n))


def _weighted(digits: str, weights) -> int:
    """Sum of digit * weight over the shorter of the two sequences."""
    return sum(int(d) * w for d, w in zip(digits, weights))


# --- PESEL -------------------------------------------------------------------

def pesel_check_digit(first10: str) -> int:
    """Return the PESEL check digit for the first ten digits."""
    return (10 - _weighted(first10, PESEL_WEIGHTS) % 10) % 10


def make_pesel(birth: date, female: bool, rng=random) -> str:
    """Build a PESEL for ``birth`` (years 1800-2299) with the sex digit set."""
    offset = PESEL_MONTH_OFFSET.get(birth.year // 100)
    if offset is None:
        raise ValueError(f"PESEL cannot encode year {birth.year}")
    sex = rng.choice("02468" if female else "13579")
    head = f"{birth.year % 100:02d}{birth.month + offset:02d}{birth.day:02d}{_digits(rng, 3)}{sex}"
    return head + str(pesel_check_digit(head))


def pesel_birth_date(pesel: str) -> date:
    """Decode the birth date stored in a PESEL."""
    yy, mm, dd = int(pesel[:2]), int(pesel[2:4]), int(pesel[4:6])
    for century, offset in PESEL_MONTH_OFFSET.items():
        if 1 <= mm - offset <= 12:
            return date(century * 100 + yy, mm - offset, dd)
    raise ValueError(f"Bad PESEL month field: {mm}")


def pesel_is_female(pesel: str) -> bool:
    """Sex digit (10th) is even for women."""
    return int(pesel[9]) % 2 == 0


def is_valid_pesel(pesel: str) -> bool:
    """True for an 11-digit PESEL with a real birth date and a matching check digit."""
    if len(pesel) != 11 or not _is_digits(pesel):
        return False
    try:
        pesel_birth_date(pesel)
    except ValueError:
        return False
    return pesel_check_digit(pesel[:10]) == int(pesel[10])


# --- Identity card -------------------------------------------------------------

def _id_value(ch: str) -> int:
    """Digit value, or ``A=10 ... Z=35`` for letters."""
    return int(ch) if ch.isdigit() else ord(ch) - ord("A") + 10


def make_id_card(rng=random) -> str:
    """Three-letter series, check digit, five digits (e.g. ``ABA300000``)."""
    series = "".join(rng.choice(string.ascii_uppercase) for _ in range(3))
    tail = _digits(rng, 5)
    partial = series + "0" + tail  # check position weighs 9, contributes 0 here
    check = sum(_id_value(c) * w for c, w in zip(partial, ID_CARD_WEIGHTS)) % 10
    return f"{series}{check}{tail}"


def is_valid_id_card(number: str) -> bool:
    """True for three A-Z letters and six digits whose weighted sum ends in 0."""
    if len(number) != 9 or not (number.isascii() and number[:3].isalpha() and number[:3].isupper()
                                and _is_digits(number[3:])):
        return False
    return sum(_id_value(c) * w for c, w in zip(number, ID_CARD_WEIGHTS)) % 10 == 0


# --- NIP / REGON ---------------------------------------------------------------

def make_nip(rng=random) -> str:
    """Ten-digit tax id. Bodies whose checksum would be 10 are redrawn."""
    while True:
        body = str(rng.randint(1, 9)) + _digits(rng, 8)
        check = _weighted(body, NIP_WEIGHTS) % 11
        if check != 10:
            return body + str(check)


def is_valid_nip(nip: str) -> bool:
    """True for a 10-digit NIP whose mod-11 checksum equals the last digit."""
    if len(nip) != 10 or not _is_digits(nip):
        return False
    check = _weighted(nip, NIP_WEIGHTS) % 11
    return check != 10 and check == int(nip[9])


def _regon_check(body: str, weights) -> int:
    """REGON check digit for ``body`` with the given weights."""
    return _weighted(body, weights) % 11 % 10  # remainder 10 becomes 0


def make_regon(length: int = 9, rng=random) -> str:
    """9-digit REGON, or 14-digit (valid 9-digit base plus local-unit suffix)."""
    body = _digits(rng, 8)
    regon9 = body + str(_regon_check(body, REGON9_WEIGHTS))
    if length == 9:
        return regon9
    if length != 14:
        raise ValueError("REGON length must be 9 or 14")
    body = regon9 + _digits(rng, 4)
    return body + str(_regon_check(body, REGON14_WEIGHTS))


def is_valid_regon(regon: str) -> bool:
    """True for a 9- or 14-digit REGON; a 14-digit one must also have a valid 9-digit base."""
    if not _is_digits(regon) or len(regon) not in (9, 14):
        return False
    if _regon_check(regon[:8], REGON9_WEIGHTS) != int(regon[8]):
        return False
    return len(regon) == 9 or _regon_check(regon[:13], REGON14_WEIGHTS) == int(regon[13])


# --- Bank account (IBAN) -------------------------------------------------------

def settlement_number(bank_code: str, rng=random) -> str:
    """8-digit bank settlement number: 3-digit bank, 4-digit branch, check digit."""
    head = bank_code + _digits(rng, 4)
    return head + str((10 - _weighted(head, SETTLEMENT_WEIGHTS) % 10) % 10)


def _iban_number(text: str) -> int:
    """Replace each character by its base-36 value and read the result as one integer."""
    return int("".join(str(int(c, 36)) for c in text))


def is_valid_settlement_number(number: str) -> bool:
    """True for 8 digits whose last one is the weighted check digit of the first seven."""
    return (len(number) == 8 and _is_digits(number)
            and (10 - _weighted(number, SETTLEMENT_WEIGHTS) % 10) % 10 == int(number[7]))


def make_iban(rng=random) -> tuple[str, str]:
    """Return ``(iban, bank_name)`` for a Polish account at a real bank branch, passing mod 97."""
    branch, bank_name = data.bank_branch(rng)
    bban = branch + _digits(rng, 16)
    check = 98 - _iban_number(bban + "PL00") % 97
    return f"PL{check:02d}{bban}", bank_name


def is_valid_iban(iban: str) -> bool:
    """True for a Polish IBAN (``PL`` + 26 digits) passing the mod-97 check."""
    if len(iban) != 28 or not iban.startswith("PL") or not _is_digits(iban[2:]):
        return False
    return _iban_number(iban[4:] + iban[:4]) % 97 == 1


# --- Payment card --------------------------------------------------------------

def luhn_check_digit(payload: str) -> int:
    """Check digit that makes ``payload + digit`` pass Luhn."""
    total = 0
    for i, d in enumerate(reversed(payload)):
        n = int(d) * (2 if i % 2 == 0 else 1)
        total += n - 9 if n > 9 else n
    return (10 - total % 10) % 10


def is_valid_luhn(number: str) -> bool:
    """True for a digit string of length 2+ passing the Luhn check."""
    return _is_digits(number) and len(number) > 1 and luhn_check_digit(number[:-1]) == int(number[-1])


def make_card(brand: str = "any", rng=random) -> str:
    """16-digit card number for ``brand`` ("any", "Visa" or "MasterCard")."""
    prefix = rng.choice(CARD_PREFIXES[brand])
    payload = prefix + _digits(rng, 15 - len(prefix))
    return payload + str(luhn_check_digit(payload))


def make_cvc(rng=random) -> str:
    """Three random digits."""
    return _digits(rng, 3)


def make_expiry(today: date, rng=random) -> str:
    """``MM/YY`` between next month and eight years ahead."""
    months_ahead = rng.randint(1, 8 * 12)
    total = today.year * 12 + today.month - 1 + months_ahead
    return f"{total % 12 + 1:02d}/{total // 12 % 100:02d}"


# --- Vehicle -------------------------------------------------------------------

def vin_check_char(vin: str) -> str:
    """ISO 3779 check character for a 17-char VIN (position 9 is ignored)."""
    rem = sum(VIN_VALUES[c] * w for c, w in zip(vin, VIN_WEIGHTS)) % 11
    return "X" if rem == 10 else str(rem)


def make_vin(rng=random) -> str:
    """WMI + 5 descriptor chars + check + model year + plant + 6-digit serial."""
    wmi = rng.choice(data.VIN_WMI)
    vds = "".join(rng.choice(VIN_CHARS) for _ in range(5))
    rest = rng.choice(VIN_YEAR_CHARS) + rng.choice(VIN_CHARS) + _digits(rng, 6)
    draft = wmi + vds + "0" + rest
    return wmi + vds + vin_check_char(draft) + rest


def is_valid_vin(vin: str) -> bool:
    """True for 17 allowed characters with a correct ISO 3779 check character."""
    if len(vin) != 17 or any(c not in VIN_CHARS for c in vin):
        return False
    return vin_check_char(vin) == vin[8]


def make_plate(rng=random) -> str:
    """Two-letter district prefix, a space, five digits (e.g. ``PO 12345``)."""
    return f"{rng.choice(data.PLATE_PREFIXES)} {_digits(rng, 5)}"
