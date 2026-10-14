"""Data build script: parsing helpers and a full offline build from tiny sample files."""

import importlib.util
import io
import random
import zipfile
from pathlib import Path

import pytest

from argus import data, identifiers as ids

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "build_data.py"
spec = importlib.util.spec_from_file_location("build_data", SCRIPT)
build_data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_data)


@pytest.fixture(params=["only"])
def data_source(request):
    """Override the global fixture: these tests do not depend on the data mode."""
    yield request.param


@pytest.mark.parametrize("raw, expected", [
    ("ulica  Różana", "ul. Różana"),
    ("ul.  Wałowa", "ul. Wałowa"),
    ("Aleja  Czereśniowa", "al. Czereśniowa"),
    ("Al.  Wojska Polskiego", "al. Wojska Polskiego"),
    ("Plac Wolności", "pl. Wolności"),
    ("osiedle Czaplinieckie", "os. Czaplinieckie"),
    ("Osiedle", "Osiedle"),
    ("Rynek", "Rynek"),
    ("Rynek Główny", "Rynek Główny"),
    ("gen. Stefana Grota-Roweckiego", "ul. gen. Stefana Grota-Roweckiego"),
    ("Długa", "ul. Długa"),
    ("", ""),
])
def test_normalize_street(raw, expected):
    assert build_data.normalize_street(raw) == expected


@pytest.mark.parametrize("raw, expected", [("108A", 108), ("4", 4), ("12/3", 12), ("bn", 0)])
def test_house_number(raw, expected):
    assert build_data.house_number(raw) == expected


def test_short_bank_name():
    assert build_data.short_bank_name("mBank Spółka Akcyjna") == "mBank S.A."
    assert build_data.short_bank_name("BANK POLSKIEJ SPÓŁDZIELCZOŚCI SPÓŁKA AKCYJNA") == "Bank Polskiej Spółdzielczości S.A."


def test_with_cum():
    assert list(build_data.with_cum([("a", 3), ("b", 2)], 1)) == [("a", 3), ("b", 5)]


def write_samples(tmp: Path) -> dict:
    """Minimal source files in the same formats as the real downloads."""
    (tmp / "names_f.csv").write_text("IMIĘ_PIERWSZE,PŁEĆ,LICZBA_WYSTĄPIEŃ\nANNA,KOBIETA,900\nZOFIA,KOBIETA,100\n"
                                     "RZADKA,KOBIETA,5\nМАРІЯ,KOBIETA,500\n", encoding="utf-8-sig")
    (tmp / "names_m.csv").write_text("IMIĘ_PIERWSZE,PŁEĆ,LICZBA_WYSTĄPIEŃ\nPIOTR,MĘŻCZYZNA,700\n", encoding="utf-8-sig")
    (tmp / "surnames_f.csv").write_text("Nawisko aktualne,Liczba\nKOWALSKA,300\nNOWAK-ZIELIŃSKA,150\n",
                                        encoding="utf-8-sig")
    (tmp / "surnames_m.csv").write_text("Nawisko aktualne,Liczba\nKOWALSKI,300\n", encoding="utf-8-sig")
    rows = ["teryt;miejscowosc;ulica;numer;adruni"]
    rows += [f"1465011;Warszawa;ulica  Długa;{n};00238|146501|0918123|0918123|03869|1|2|{n}|" for n in ("1", "5", "12A")]
    rows += ["0205032;Pomocne;;32;59424|020503|0365693|0365693|00000|1|2|32|"]  # no street: skipped
    rows += ["0205032;Rzadka;Polna;1;59424|020503|0365693|0365693|00000|1|2|1|"]  # too few points: skipped
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("POLSKA.csv", "﻿" + "\n".join(rows) + "\n")
    (tmp / "addresses.zip").write_bytes(buf.getvalue())
    banks = ["114\tmBank Spółka Akcyjna\t\t114\t11402004\tOddział", "101\tNarodowy Bank Polski\t\t101\t10100000\tCentrala",
             "114\tmBank Spółka Akcyjna\t\t114\t11402005\tZła cyfra kontrolna"]
    (tmp / "banks.txt").write_bytes("\r\n".join(banks).encode("cp852"))
    return {p.stem: p for p in tmp.iterdir()}


def test_offline_build(tmp_path, monkeypatch):
    files = write_samples(tmp_path)
    names = build_data.read_counts(files["names_f"], 100)
    assert names == [("Anna", 900), ("Zofia", 100)]  # rare and non-Latin entries dropped

    addresses = build_data.read_addresses(files["addresses"])
    assert addresses == [("00-238", "Warszawa", "ul. Długa", 12, 3)]
    assert build_data.read_banks(files["banks"]) == [("11402004", "mBank S.A.")]

    db_path = tmp_path / "argus.db"
    monkeypatch.setattr(build_data, "DB_PATH", db_path)
    build_data.write_db(
        {True: names, False: build_data.read_counts(files["names_m"], 100)},
        {True: build_data.read_counts(files["surnames_f"], 100), False: build_data.read_counts(files["surnames_m"], 100)},
        addresses, build_data.read_banks(files["banks"]), {"built": "2026-01-01"})

    try:
        assert data.use_database(db_path)
        rng = random.Random(0)
        assert {data.first_name(True, rng) for _ in range(200)} == {"Anna", "Zofia"}
        assert data.surname(False, rng) == "Kowalski"
        assert {data.surname(True, rng) for _ in range(100)} == {"Kowalska", "Nowak-Zielińska"}
        postal, city, street = data.address(rng)
        assert (postal, city) == ("00-238", "Warszawa") and street.startswith("ul. Długa ")
        branch, name = data.bank_branch(rng)
        assert ids.is_valid_settlement_number(branch) and name == "mBank S.A."
        assert "2026-01-01" in data.source_note()
    finally:
        data.use_database()


def test_locked_database_gives_clear_message(tmp_path, monkeypatch):
    """On Windows an open database cannot be replaced; the build must say so and clean up."""
    db_path = tmp_path / "db" / "argus.db"
    monkeypatch.setattr(build_data, "DB_PATH", db_path)
    monkeypatch.setattr(build_data, "ROOT", tmp_path)

    def locked(self, target):
        raise PermissionError("file in use")

    monkeypatch.setattr(Path, "replace", locked)
    with pytest.raises(SystemExit, match="close Argus"):
        build_data.write_db({True: [], False: []}, {True: [], False: []}, [], [], {})
    assert not db_path.with_suffix(".tmp").exists()
