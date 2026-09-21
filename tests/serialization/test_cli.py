"""Tests for the command-line interface."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

from zettel_parser.cli import build_parser, main
from zettel_parser.serialization import to_org
from zettel_parser.structure_pass import parse

CORPUS = Path(__file__).parents[1] / "corpus" / "standard.org"


def test_format_choices_come_from_the_registry() -> None:
    parser = build_parser()
    action = next(
        action
        for action in parser._actions
        if action.dest == "format"
    )
    assert set(action.choices or []) == {"json", "xml", "text", "org"}


def test_json_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(CORPUS), "-f", "json"]) == 0
    out = capsys.readouterr().out
    assert json.loads(out)["type"] == "Zettel"


def test_default_format_is_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(CORPUS)]) == 0
    assert json.loads(capsys.readouterr().out)["type"] == "Zettel"


def test_org_matches_library(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(CORPUS), "-f", "org"]) == 0
    expected = to_org(parse(CORPUS.read_text(encoding="utf-8")))
    assert capsys.readouterr().out == expected


def test_reads_stdin(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO("#+title: Doc\n"))
    assert main(["-f", "text"]) == 0
    assert capsys.readouterr().out.startswith("Zettel title='Doc'")


def test_writes_output_file(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    output = tmp_path / "out.json"
    assert main([str(CORPUS), "-o", str(output)]) == 0
    assert capsys.readouterr().out == ""
    assert json.loads(output.read_text(encoding="utf-8"))["type"] == "Zettel"


def test_missing_file_returns_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main([str(CORPUS.parent / "nope.org")]) == 1
    assert "error" in capsys.readouterr().err


def test_unknown_format_exits() -> None:
    with pytest.raises(SystemExit):
        main([str(CORPUS), "-f", "yaml"])
