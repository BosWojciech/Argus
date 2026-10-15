"""Access to the data used to draw names, addresses and banks.

Draws come from ``db/argus.db`` (built by ``make data`` from the PESEL name
registry, the national address register and the central bank's list of bank
branches) and are weighted by real frequency. When the database is missing,
the small lists in ``argus.fallback`` are used instead.
"""

import os
import random
import sqlite3
import sys
from pathlib import Path

from argus import fallback

# Repository-level db/ directory (or the bundle dir inside Argus.exe); ARGUS_DB points elsewhere when set.
_ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
DB_PATH = Path(os.environ.get("ARGUS_DB") or _ROOT / "db" / "argus.db")

_db: sqlite3.Connection | None = None
_totals: dict[tuple, int] = {}


def use_database(path: Path | None = DB_PATH) -> bool:
    """Open ``path`` read-only (``None`` or a missing file selects the fallback lists).

    Returns whether a database is now in use.
    """
    global _db
    if _db is not None:
        _db.close()
    _db = None
    _totals.clear()
    if path is not None and Path(path).is_file():
        _db = sqlite3.connect(f"{Path(path).resolve().as_uri()}?mode=ro", uri=True)
    return _db is not None


def has_database() -> bool:
    """True when draws come from the generated database."""
    return _db is not None


def source_note() -> str:
    """Short description of where the data comes from, for the UI."""
    if _db is None:
        return "Dane: wbudowane listy (uruchom make data, by pobrać pełne dane)"
    meta = dict(_db.execute("SELECT key, value FROM meta"))
    return f"Dane: rejestr PESEL, PRG, NBP (zbudowano {meta.get('built', '?')})"


def _pick(rng, table: str, columns: str, where: str = "1", params: tuple = ()) -> tuple:
    """Weighted random row: draw below the total weight, take the first row whose running total exceeds it."""
    key = (table, where, params)
    if key not in _totals:
        _totals[key] = _db.execute(f"SELECT max(cum) FROM {table} WHERE {where}", params).fetchone()[0]
    target = rng.randrange(_totals[key])
    return _db.execute(f"SELECT {columns} FROM {table} WHERE {where} AND cum > ? ORDER BY cum LIMIT 1",
                       (*params, target)).fetchone()


def first_name(female: bool, rng=random) -> str:
    """Given name, as common as it is in the population."""
    if _db is None:
        return rng.choice(fallback.FIRST_NAMES_FEMALE if female else fallback.FIRST_NAMES_MALE)
    return _pick(rng, "first_names", "name", "female = ?", (int(female),))[0]


def surname(female: bool, rng=random) -> str:
    """Surname in the form matching the sex (``Kowalski`` / ``Kowalska``)."""
    if _db is None:
        name = rng.choice(fallback.SURNAMES)
        return fallback.feminine_surname(name) if female else name
    return _pick(rng, "surnames", "name", "female = ?", (int(female),))[0]


def address(rng=random) -> tuple[str, str, str]:
    """``(postal_code, city, "street number")``.

    From the database these belong together: a real street in a real place with
    its postal code; the house number is drawn up to the highest one on that
    street. The fallback lists draw the three parts independently.
    """
    if _db is None:
        postal = f"{rng.randint(0, 99):02d}-{rng.randint(0, 999):03d}"
        street = f"ul. {rng.choice(fallback.STREETS)}"
        return postal, rng.choice(fallback.CITIES), f"{street} {rng.randint(1, 199)}"
    postal, city, street, max_number = _pick(rng, "addresses", "postal_code, city, street, max_number")
    return postal, city, f"{street} {rng.randint(1, max_number)}"


def bank_branch(rng=random) -> tuple[str, str]:
    """``(8-digit settlement number, bank name)`` of a bank branch."""
    if _db is None:
        from argus.identifiers import settlement_number  # deferred: identifiers imports this module
        code = rng.choice(list(fallback.BANKS))
        return settlement_number(code, rng), fallback.BANKS[code]
    return _pick(rng, "banks", "settlement, name")


# World manufacturer identifiers of common makes.
VIN_WMI = [
    "WVW", "WAU", "WBA", "WDD", "WF0", "VF1", "VF3", "VF7", "ZFA", "TMB",
    "TMA", "YV1", "YS3", "SAL", "JTD", "JMZ", "KMH", "KNA", "SUP", "1C4",
]

# Two-letter vehicle registration district prefixes.
PLATE_PREFIXES = [
    "WA", "WB", "WD", "WE", "WH", "WI", "WJ", "WK", "WN", "WT", "WU", "WX",
    "WY", "KR", "KK", "KN", "KT", "PO", "PL", "PK", "PZ", "GD", "GA", "GS",
    "DW", "DB", "DJ", "DL", "EL", "ER", "SK", "SC", "SG", "SO", "ST", "ZS",
    "ZK", "CB", "CT", "LU", "LC", "LZ", "BI", "BL", "BS", "RZ", "RK", "TK",
    "NO", "NE", "OP", "FZ", "FG",
]


use_database()
