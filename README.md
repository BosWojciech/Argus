# Argus

Generator danych testowych - a desktop app that generates formally valid Polish
test data (PESEL, dowód osobisty, NIP, REGON, IBAN, payment cards, VIN, plates).
Names, addresses and banks come from Polish public registers, weighted by real frequency.

Requires [uv](https://docs.astral.sh/uv/) and Python 3.13 or newer with Tk
(see [Installing Python](#installing-python)).

```bash
make install
make run
```

If uv or a suitable Python is missing, `make` stops with a one-line message
saying what to install.

Works on macOS, Linux and Windows. On Windows, `make.cmd` provides the same
commands without needing GNU make: type `make install` / `make run` in Command
Prompt, or `.\make install` / `.\make run` in PowerShell.

The data ships with the repository in `db/argus.db`. To update it with the
latest published data, run:

```bash
make data
```

It downloads the sources, builds a fresh `db/argus.db` and removes the
downloaded files afterwards.

## Installing Python

The simplest way is to let uv install it:

```bash
uv python install 3.13
```

Or download the official installer for Python 3.13.16 from python.org
([release page](https://www.python.org/downloads/release/python-31316/)):

| Platform | Download |
| --- | --- |
| macOS 11+ (Intel and Apple Silicon) | [python-3.13.16-macos11.pkg](https://www.python.org/ftp/python/3.13.16/python-3.13.16-macos11.pkg) |
| Windows 64-bit | [python-3.13.16-amd64.exe](https://www.python.org/ftp/python/3.13.16/python-3.13.16-amd64.exe) |
| Windows ARM64 | [python-3.13.16-arm64.exe](https://www.python.org/ftp/python/3.13.16/python-3.13.16-arm64.exe) |
| Linux / source | [Python-3.13.16.tar.xz](https://www.python.org/ftp/python/3.13.16/Python-3.13.16.tar.xz) |

The macOS and Windows installers include Tk. On Windows keep the
"tcl/tk and IDLE" option selected. python.org has no Linux installer: use
`uv python install 3.13`, or your distribution's Python 3.13 together with its
Tk package. Homebrew's Python does not include Tk.

Docs: [overview](docs/overview.md) · [formats](docs/formats.md) · [data](docs/data.md) · [architecture](docs/architecture.md)
