"""Build ``db/argus.db`` from Polish open-data sources.

Sources (downloaded into a temporary directory that is removed afterwards,
so every run uses the latest published data):

- first names and surnames with occurrence counts from the PESEL registry
  (dane.gov.pl, datasets 1667 and 568; the newest resource is picked automatically),
- address points from the national register of boundaries (PRG, nationwide CSV),
- bank settlement numbers from the National Bank of Poland.

Every table has a ``cum`` column holding the running total of weights, so the
app can draw a weighted random row with one indexed query.

Usage: ``python scripts/build_data.py`` (or ``make data``).
Standard library only, plus ``truststore`` when installed so downloads use the
operating system's certificate store (needed behind TLS-inspecting proxies).
"""

import collections
import csv
import io
import json
import re
import sqlite3
import sys
import tempfile
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "db" / "argus.db"

API = "https://api.dane.gov.pl/1.4"
NAMES_DATASET = 1667
SURNAMES_DATASET = 568
ADDRESSES_URL = "https://opendata.geoportal.gov.pl/prg/adresy/adruni/POLSKA.zip"
BANKS_URL = "https://ewib.nbp.pl/plewibnra?dokNazwa=plewibnra.txt"

# Rare entries are mostly typos and one-off foreign names.
MIN_NAME_COUNT = 100
MIN_SURNAME_COUNT = 100
MIN_ADDRESSES_PER_STREET = 3
MAX_HOUSE_NUMBER = 300
POLISH_WORD = re.compile(r"[A-ZĄĆĘŁŃÓŚŹŻ][A-ZĄĆĘŁŃÓŚŹŻ' -]*")

# Leading street-type words in the address register -> display prefix.
STREET_TYPES = {
    "ulica": "ul.", "ul.": "ul.",
    "aleja": "al.", "al.": "al.", "aleje": "al.",
    "plac": "pl.", "pl.": "pl.",
    "osiedle": "os.", "os.": "os.",
}
# Names used on their own, without a prefix ("Rynek 5", "Osiedle 12").
BARE_STREETS = {"rynek", "osiedle", "plac", "aleja"}

SETTLEMENT_WEIGHTS = (3, 9, 7, 1, 3, 9, 7)


def fetch(url: str, folder: Path, name: str) -> Path:
    """Download ``url`` to ``folder / name``."""
    path = folder / name
    print(f"  download {name} <- {url}")
    request = urllib.request.Request(url, headers={"User-Agent": "argus-data-builder"})
    with urllib.request.urlopen(request, timeout=600) as response, open(path, "wb") as out:
        while chunk := response.read(1 << 20):
            out.write(chunk)
    return path


def latest_resource(dataset: int, title_pattern: str) -> tuple[str, str]:
    """Return ``(csv_url, title)`` of the newest resource whose title matches."""
    url = f"{API}/datasets/{dataset}/resources?per_page=100&sort=-created"
    with urllib.request.urlopen(url, timeout=60) as response:
        resources = json.load(response)["data"]
    for item in resources:
        attrs = item["attributes"]
        if re.search(title_pattern, attrs["title"], re.IGNORECASE) and attrs.get("csv_download_url"):
            return attrs["csv_download_url"], attrs["title"]
    raise RuntimeError(f"No resource matching {title_pattern!r} in dataset {dataset}")


def read_counts(path: Path, minimum: int) -> list[tuple[str, int]]:
    """``(Title-cased name, count)`` pairs from a name/count CSV, most common first."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))[1:]
    out = []
    for row in rows:
        name, count = row[0].strip(), int(row[-1])
        if count >= minimum and POLISH_WORD.fullmatch(name):
            out.append((name.title(), count))
    return sorted(out, key=lambda r: -r[1])


def normalize_street(raw: str) -> str:
    """``"ulica  Różana"`` -> ``"ul. Różana"``; streets without a type get ``ul.``."""
    words = raw.split()
    if not words:
        return ""
    head = words[0].lower()
    if len(words) == 1 and head in BARE_STREETS:
        return words[0].capitalize()
    if head == "rynek":
        return " ".join(words)
    if head in STREET_TYPES:
        return " ".join([STREET_TYPES[head], *words[1:]])
    return " ".join(["ul.", *words])


def house_number(raw: str) -> int:
    """Numeric part of a house number (``"108A"`` -> 108), 0 when there is none."""
    m = re.match(r"\d+", raw)
    return int(m[0]) if m else 0


def read_addresses(path: Path) -> list[tuple[str, str, str, int, int]]:
    """``(postal_code, city, street, max_number, weight)`` per street and postal code.

    Weight is the number of address points, so busy streets in big cities are
    drawn more often. Address points without a street (small villages) are skipped.
    """
    stats: dict[tuple[str, str, str], list[int]] = collections.defaultdict(lambda: [0, 0])
    with zipfile.ZipFile(path) as archive:
        member = next(n for n in archive.namelist() if n.lower().endswith(".csv"))
        with io.TextIOWrapper(archive.open(member), encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f, delimiter=";")
            header = next(reader)
            col = {name: i for i, name in enumerate(header)}
            for row in reader:
                street = normalize_street(row[col["ulica"]])
                postal = row[col["adruni"]].split("|", 1)[0]
                if not street or not re.fullmatch(r"\d{5}", postal):
                    continue
                entry = stats[(f"{postal[:2]}-{postal[2:]}", row[col["miejscowosc"]], street)]
                entry[0] += 1
                entry[1] = max(entry[1], min(house_number(row[col["numer"]]), MAX_HOUSE_NUMBER))
    return [(p, c, s, max(n, 1), w) for (p, c, s), (w, n) in stats.items() if w >= MIN_ADDRESSES_PER_STREET]


def short_bank_name(name: str) -> str:
    """Shorten legal forms and fix all-caps names."""
    if name.isupper():
        name = name.title()
    return re.sub(r"\s+", " ", re.sub(r"Spółka Akcyjna", "S.A.", name, flags=re.IGNORECASE)).strip()


def read_banks(path: Path) -> list[tuple[str, str]]:
    """``(settlement_number, bank_name)`` for every branch with a valid check digit.

    The central bank (code 101) is skipped; it does not keep personal accounts.
    """
    out = []
    for line in path.read_text(encoding="cp852").splitlines():
        cols = [c.strip() for c in line.split("\t")]
        if len(cols) < 5 or not re.fullmatch(r"\d{8}", cols[4]) or cols[0] == "101":
            continue
        number = cols[4]
        check = (10 - sum(int(d) * w for d, w in zip(number, SETTLEMENT_WEIGHTS)) % 10) % 10
        if check == int(number[7]):
            out.append((number, short_bank_name(cols[1])))
    return out


def with_cum(rows, weight_index: int):
    """Replace the weight column with a running total."""
    total = 0
    for row in rows:
        total += row[weight_index]
        yield (*row[:weight_index], total, *row[weight_index + 1:])


def write_db(names, surnames, addresses, banks, sources: dict) -> None:
    """Create a fresh database file, replacing the old one only when complete."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = DB_PATH.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)
    db = sqlite3.connect(tmp)
    db.executescript("""
        CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE first_names (female INTEGER, name TEXT, cum INTEGER);
        CREATE TABLE surnames (female INTEGER, name TEXT, cum INTEGER);
        CREATE TABLE addresses (postal_code TEXT, city TEXT, street TEXT, max_number INTEGER, cum INTEGER);
        CREATE TABLE banks (settlement TEXT, name TEXT, cum INTEGER);
    """)
    for table, groups in (("first_names", names), ("surnames", surnames)):
        for female, rows in groups.items():
            db.executemany(f"INSERT INTO {table} VALUES (?, ?, ?)",
                           ((int(female), n, cum) for n, cum in with_cum(rows, 1)))
    db.executemany("INSERT INTO addresses VALUES (?, ?, ?, ?, ?)", with_cum(addresses, 4))
    db.executemany("INSERT INTO banks VALUES (?, ?, ?)", ((s, n, i) for i, (s, n) in enumerate(banks, 1)))
    db.executemany("INSERT INTO meta VALUES (?, ?)", sources.items())
    db.executescript("""
        CREATE INDEX first_names_pick ON first_names (female, cum);
        CREATE INDEX surnames_pick ON surnames (female, cum);
        CREATE INDEX addresses_pick ON addresses (cum);
        CREATE INDEX banks_pick ON banks (cum);
    """)
    db.commit()
    db.execute("VACUUM")
    db.close()
    try:
        tmp.replace(DB_PATH)
    except PermissionError:  # Windows keeps the file locked while the app has it open
        tmp.unlink(missing_ok=True)
        raise SystemExit(f"Cannot replace {DB_PATH.relative_to(ROOT)}: close Argus and run make data again.")


def main() -> int:
    sources = {"built": date.today().isoformat(),
               "addresses": "PRG address points (opendata.geoportal.gov.pl)",
               "banks": "NBP bank settlement numbers (ewib.nbp.pl)"}
    with tempfile.TemporaryDirectory(prefix="argus-data-") as tmp:
        folder = Path(tmp)
        print("Fetching sources")
        files = {}
        for key, dataset, pattern in (
            ("names_f", NAMES_DATASET, r"imion żeńskich .* imię pierwsze"),
            ("names_m", NAMES_DATASET, r"imion męskich .* imię pierwsze"),
            ("surnames_f", SURNAMES_DATASET, r"^Nazwiska żeńskie"),
            ("surnames_m", SURNAMES_DATASET, r"^Nazwiska męskie"),
        ):
            url, sources[key] = latest_resource(dataset, pattern)
            files[key] = fetch(url, folder, f"{key}.csv")
        files["addresses"] = fetch(ADDRESSES_URL, folder, "addresses.zip")
        files["banks"] = fetch(BANKS_URL, folder, "banks.txt")

        print("Parsing")
        names = {female: read_counts(files[f"names_{s}"], MIN_NAME_COUNT) for female, s in ((True, "f"), (False, "m"))}
        surnames = {female: read_counts(files[f"surnames_{s}"], MIN_SURNAME_COUNT)
                    for female, s in ((True, "f"), (False, "m"))}
        addresses = read_addresses(files["addresses"])
        banks = read_banks(files["banks"])

    write_db(names, surnames, addresses, banks, sources)
    print(f"Wrote {DB_PATH.relative_to(ROOT)} ({DB_PATH.stat().st_size / 1e6:.1f} MB): "
          f"{len(names[True])}+{len(names[False])} first names, "
          f"{len(surnames[True])}+{len(surnames[False])} surnames, "
          f"{len(addresses)} streets, {len(banks)} bank branches. Downloads removed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
