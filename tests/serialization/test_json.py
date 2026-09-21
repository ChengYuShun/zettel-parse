"""Tests for the JSON renderer."""

from __future__ import annotations

import json

from zettel_parser.serialization import to_data, to_json
from zettel_parser.structure_pass import parse


def test_json_round_trips_through_json_loads() -> None:
    ast = parse("#+title: Doc\ntext /em/\n")
    assert json.loads(to_json(ast)) == to_data(ast)


def test_type_is_the_first_key() -> None:
    text = to_json(parse("text\n"))
    assert text.startswith('{\n  "type": "Zettel",')


def test_non_ascii_is_preserved_verbatim() -> None:
    text = to_json(parse("#+title: café\n"))
    assert "café" in text
    assert "\\u" not in text


def test_compact_form_has_no_newlines() -> None:
    text = to_json(parse("text\n"), indent=None)
    assert "\n" not in text
    assert json.loads(text)["type"] == "Zettel"


def test_sorted_keys_starts_with_body() -> None:
    text = to_json(parse("text\n"), sort_keys=True)
    assert text.startswith('{\n  "body":')


def test_output_is_deterministic() -> None:
    ast = parse("- one\n- two\n")
    assert to_json(ast) == to_json(ast)
