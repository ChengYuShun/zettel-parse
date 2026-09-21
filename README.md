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

## Serialization

The parsed AST can be rendered into several formats:

```python
from zettel_parser import parse, serialize

ast = parse("#+title: Doc\n\nHello *world*\n")

serialize(ast, "json")   # JSON tree
serialize(ast, "xml")    # XML document
serialize(ast, "text")   # compact outline used by the snapshots
serialize(ast, "org")    # best-effort Org-mode reconstruction
```

Each format also has a dedicated function (`to_json`, `to_xml`, `to_text`,
`to_org`), and `to_data` returns the canonical JSON-compatible representation
that every renderer consumes. Custom formats can be added with
`register_serializer`.

Serialization is output-only: the `"org"` format is a best-effort
reconstruction and is not guaranteed to round-trip, since some source
information (e.g. original headline lines and list indentation) is not kept in
the AST.

## Command line

The same formats are available from the command line. The document is read
from a file, or from standard input when the file is omitted or `-`:

```bash
python -m zettel_parser -f json document.org
zettel-parser -f org document.org < document.org
```

Options: `-f/--format` (one of `json`, `xml`, `text`, `org`; default `json`),
`-o/--output` (write to a file instead of standard output), and `--version`.

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

## AI usage

The development of this program is heavily assisted by AI.
