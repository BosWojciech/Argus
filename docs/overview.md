# Argus overview

Argus is a desktop generator of formally valid Polish test data. It produces
records with correct checksums (PESEL, identity card, NIP, REGON, IBAN, payment
card, VIN) so forms and validators can be exercised without using real
people's data. Names, surnames, addresses and bank branches are drawn from
Polish public registers, weighted by how common they really are (see
[data.md](data.md)). Records are generated locally; the app itself makes no
network requests.

## Running

```bash
make install   # create .venv with uv (uv-managed Python 3.13, ships with Tk)
make data      # rebuild db/argus.db from the latest open data (temporary ~150 MB download)
make run       # open the window
make test      # run the test suite
make clean     # remove .venv and caches
```

`uv run argus` and `uv run python -m argus` work as well.

On Windows the same targets are provided by `make.cmd` (no GNU make needed):
`make install` in Command Prompt, `.\make install` in PowerShell. It performs the
same checks and prints the same one-line messages. Close the app before running
`make data`: Windows locks the open database file, and the build stops with a
message asking you to close it.

Requirements: [uv](https://docs.astral.sh/uv/) and Python 3.13+ with Tk, either
uv's own build (`uv python install 3.13`, preferred) or a python.org installer
(links in the README). Before `install`, `run`, `data` and `test`, the Makefile
checks that uv exists, that a Python of at least `MIN_PYTHON` is available and
that it can import `tkinter`. If not, it stops with a single line, e.g.
`Python version is too old. Please install Python 3.13 from https://www.python.org/downloads/ or run: uv python install 3.13`.

Without `db/argus.db` (for example, deleted) the app still runs on
small built-in lists; the line under the title says which data is in use.

## The window

Five tabs, each showing one generated record on open:

| Tab | Fields | Options (**Konfiguruj**) |
| --- | --- | --- |
| Zbiorcze | person + address, NIP, REGON (9), card, IBAN, VIN, plates | none |
| Osobowe | Imię, Nazwisko, Imię i nazwisko, Data urodzin, Pesel, Dowód osobisty, address | age range, gender, age/date text |
| Firmowe | NIP, REGON, address | REGON 9 or 14 digits |
| Bankowe | Konto bankowe, Nazwa banku, Karta płatnicza, CVC, Data ważności, person + address | card brand: any / Visa / MasterCard |
| Auto | VIN, Tablice rejestracyjne, person + address | none |

- **Generuj** draws a new record using the current options.
- **Konfiguruj** shows or hides the options panel.
- Clicking any value copies it to the clipboard; the status line confirms it.

### Personal options

- Age range: 0-99 (default), 0-18, 19-24, 25-65, 65-99 (completed years).
- Gender: obojętnie (random), kobieta, mężczyzna. Name, surname form and the
  PESEL sex digit always agree with the chosen gender.
- Age or date text (wins over the age range when filled):
  - `40` - exact age in completed years,
  - `1984-06` - that month, random day (never later than today),
  - `1984-06-03` - that exact date.
  Picking an age range clears the text. The field accepts only digits and `-`,
  max 10 characters. Invalid input (unknown format, non-existent day such as
  `2001-02-29`, a future date, or a birth year before 1800, e.g. age `300`) shows an error in the
  status line and keeps the previous record.

See [formats.md](formats.md) for the exact rules of every value and
[architecture.md](architecture.md) for the code layout.
