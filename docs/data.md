# Data sources and the data build

`db/argus.db` (about 18 MB) is committed, so the app works right after
`make install`. To refresh it with the latest published data run:

```bash
make data
```

This runs `scripts/build_data.py`, which downloads the sources (~150 MB) into a
temporary directory, builds a new database next to the old one, swaps it in
only when complete, and deletes the downloads. Parsing takes about 10 seconds
after the downloads finish. The script uses only the standard library, plus
`truststore` (a dev dependency) so HTTPS works behind proxies that rely on the
system certificate store.

Set `ARGUS_DB` to make the app use a database stored elsewhere.

## Sources

| Data | Source | Filter |
| --- | --- | --- |
| First names by sex, with counts | dane.gov.pl dataset 1667, "lista imion ... w rejestrze PESEL ... imię pierwsze" (newest resource picked via the API) | count ≥ 100, Polish/Latin letters only |
| Surnames by sex, with counts | dane.gov.pl dataset 568, "Nazwiska żeńskie / męskie" (newest resource) | count ≥ 100, Polish/Latin letters only |
| Addresses | National register of boundaries (PRG), nationwide address-point CSV: `opendata.geoportal.gov.pl/prg/adresy/adruni/POLSKA.zip` (~130 MB zip, ~8.6 M rows) | points with a street and a postal code; streets with ≥ 3 points |
| Bank branches | National Bank of Poland list of settlement numbers (`ewib.nbp.pl`, `plewibnra.txt`, CP852, tab-separated) | valid check digit; central bank itself skipped |

The address CSV has columns `teryt;miejscowosc;ulica;numer;adruni`. The postal
code is the first `|`-separated field of `adruni` (`59424` → `59-424`).

Street names are normalised: a leading `ulica`/`ul.` becomes `ul.`,
`aleja`/`al.` becomes `al.`, `plac`/`pl.` → `pl.`, `osiedle`/`os.` → `os.`;
`Rynek ...` and a bare `Osiedle`/`Plac`/`Aleja` stay as they are; any other name
gets `ul.`. Whitespace is collapsed.

Current build: about 1,550 female and 2,000 male first names, 37,000 surnames
per sex, 255,000 street/postal-code pairs and 3,100 bank branches of 580 banks.

## Database layout

```sql
meta        (key, value)                                      -- source titles, build date
first_names (female, name, cum)
surnames    (female, name, cum)
addresses   (postal_code, city, street, max_number, cum)
banks       (settlement, name, cum)
```

`cum` is the running total of the weights (occurrences, address points, or 1
per bank branch). A weighted draw picks `r` in `[0, total)` and reads the first
row with `cum > r`, which is a single lookup on the `(..., cum)` index. Totals are
cached per query.

## How the app uses it

`argus.data` opens the file read-only on import. `first_name`, `surname`,
`address` and `bank_branch` read from it; if the file is missing they fall
back to the lists in `argus.fallback`. `data.use_database(path_or_None)`
switches source (used by tests). Draws take the same `rng` as everything else,
so a seeded `random.Random` gives repeatable records for a given database.

## Not included (yet)

- Places without street names (many villages) are skipped, since the record
  has a single "Ulica" field.
- Names are not matched to birth year (a 2020 birth is as likely to be
  "Krystyna" as a 1950 one). The names-given-to-children dataset (dane.gov.pl
  219) could add this.
- VIN manufacturer prefixes and plate prefixes are still short hand-picked
  tables in `data.py`.
