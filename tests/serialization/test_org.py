"""Tests for the Org-mode renderer."""

from __future__ import annotations

from pathlib import Path

import pytest

from zettel_parser.first_pass_elements import (
    Block,
    CheckboxState,
    NodeProperty,
    PropertyDrawer,
)
from zettel_parser.serialization import to_org
from zettel_parser.structure_pass import parse
from zettel_parser.structure_pass_elements import Headline, ListItem, Zettel

CORPUS_DIR = Path(__file__).parents[1] / "corpus"
ORG_FILES = sorted(CORPUS_DIR.glob("*.org"))


@pytest.mark.parametrize("org_file", ORG_FILES, ids=lambda path: path.stem)
def test_org_output_reparses_to_same_ast(org_file: Path) -> None:
    source = org_file.read_text(encoding="utf-8")
    assert parse(to_org(parse(source))) == parse(source)


def test_zettel_preamble_is_rebuilt() -> None:
    node = Zettel(title="Doc", filetags=":a:b:")
    assert to_org(node) == "#+title: Doc\n#+filetags: :a:b:\n"


def test_headline_stars_are_rebuilt() -> None:
    assert to_org(Headline(title="A", level=3)) == "*** A\n"


def test_list_item_is_rebuilt_with_checkbox() -> None:
    item = ListItem(
        bullet="-",
        value="task",
        checked=CheckboxState.UNCHECKED,
        lines=["task\n"],
    )
    assert to_org(item) == "- [ ] task\n"


def test_property_drawer_is_rebuilt() -> None:
    drawer = PropertyDrawer(
        node_properties=[NodeProperty(name="ID", value="1")]
    )
    assert to_org(drawer) == ":PROPERTIES:\n:ID: 1\n:END:\n"


def test_block_is_rebuilt_without_raw_lines() -> None:
    block = Block(name="src", arguments="python")
    assert to_org(block) == "#+begin_src python\n#+end_src\n"


def test_block_uses_verbatim_lines_when_available() -> None:
    block = Block(
        name="src",
        arguments="python",
        raw_lines=["#+begin_src python\n", "x = 1\n", "#+end_src\n"],
    )
    assert to_org(block) == "#+begin_src python\nx = 1\n#+end_src\n"


def test_unknown_object_raises_type_error() -> None:
    with pytest.raises(TypeError):
        to_org(object())
