# zettel-parser

A Python library for parsing a custom variant of Org-mode.

## Installation

```bash
pip install .
```

For development:

```bash
pip install -e ".[dev]"
```

## Running Tests & Checks

```bash
pytest
ruff check .
mypy src
```

## File-based tests

Real documents live in `tests/corpus/*.org` and can be edited freely. Each file
is discovered automatically and checked by:

- an exact source round-trip through the first pass, which needs no expected
  data; and
- a structure snapshot stored under `tests/__snapshots__/`.

After editing a file, run `pytest`. If the parsed structure changed, refresh
the snapshots with [syrupy](https://github.com/syrupy-project/syrupy) and
review the diff:

```bash
pytest --snapshot-update
```
