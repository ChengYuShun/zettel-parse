"""Tests for the XML renderer."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from zettel_parser.serialization import to_xml
from zettel_parser.structure_pass import parse
from zettel_parser.structure_pass_elements import Zettel


def _root(xml: str) -> ET.Element:
    return ET.fromstring(xml)


def test_declaration_and_root_element() -> None:
    xml = to_xml(parse("#+title: Doc\n"))
    assert xml.startswith('<?xml version="1.0" encoding="utf-8"?>\n')
    root = _root(xml)
    assert root.tag == "zettel"
    assert root.attrib == {"title": "Doc", "level": "0"}


def test_scalar_attributes_use_kebab_case() -> None:
    root = _root(to_xml(parse("- item\n")))
    list_element = root.find(".//list")
    assert list_element is not None
    assert list_element.attrib == {"bullet-type": "-"}


def test_latex_block_is_all_attributes() -> None:
    root = _root(to_xml(parse("\\[\nx\n\\]\n")))
    block = root.find(".//latex-block")
    assert block is not None
    assert block.attrib["latex-type"] == "bracket"
    assert block.attrib["delimiter"] == "\\["
    assert block.attrib["text"] == "\\[\nx\n\\]\n"
    assert block.text is None


def test_scalar_collections_become_repeated_elements() -> None:
    root = _root(to_xml(Zettel(filetags=["a", "b"])))
    tags = [element.attrib["value"] for element in root.findall("filetag")]
    assert tags == ["a", "b"]


def test_inline_content_is_mixed() -> None:
    xml = to_xml(parse("a /b/ c\n"))
    root = _root(xml)
    paragraph = root.find(".//paragraph-text")
    assert paragraph is not None
    assert paragraph.text == "a "
    italic = paragraph.find("italic")
    assert italic is not None
    assert italic.text == "b"
    assert italic.tail == " c\n"


def test_attributes_are_escaped() -> None:
    xml = to_xml(Zettel(title='a <b> & "c"'))
    root = _root(xml)
    assert root.attrib["title"] == 'a <b> & "c"'


def test_inline_text_is_escaped() -> None:
    xml = to_xml(parse("a < b & c\n"))
    assert "a &lt; b &amp; c" in xml
    assert _root(xml) is not None


def test_multi_line_strings_become_escaped_attributes() -> None:
    xml = to_xml(parse("\\[\na < b & c\n\\]\n"))
    assert "&#10;" in xml
    block = _root(xml).find(".//latex-block")
    assert block is not None
    assert block.attrib["text"] == "\\[\na < b & c\n\\]\n"


def test_blank_lines_are_not_mixed() -> None:
    root = _root(to_xml(parse("\n")))
    blank = root.find(".//blank-lines")
    assert blank is not None
    line = blank.find("line")
    assert line is not None
    assert line.attrib["value"] == "\n"
    assert line.text is None


def test_empty_elements_are_self_closing() -> None:
    xml = to_xml(Zettel())
    assert xml.endswith('<zettel title="" level="0"/>\n')
