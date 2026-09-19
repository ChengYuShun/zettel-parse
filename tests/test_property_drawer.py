"""Tests for property drawer parsing in toplevel.py and regexes in regex.py."""

from __future__ import annotations

import io
import unittest

from zettel_parser.regex import (
    DRAWER_BEGIN,
    DRAWER_END,
    NODE_PROPERTY,
    PROPERTY_DRAWER_BEGIN,
    PROPERTY_DRAWER_END,
)
from zettel_parser.toplevel import (
    NodeProperty,
    PropertyDrawer,
    TopLevelParser,
    parse,
    parse_toplevel,
)


class TestRegexes(unittest.TestCase):
    """Tests verifying regex patterns in regex.py."""

    def test_property_drawer_begin(self) -> None:
        self.assertTrue(PROPERTY_DRAWER_BEGIN.match(":PROPERTIES:"))
        self.assertTrue(PROPERTY_DRAWER_BEGIN.match(":properties:"))
        self.assertTrue(PROPERTY_DRAWER_BEGIN.match("  :PROPERTIES:  "))
        self.assertTrue(PROPERTY_DRAWER_BEGIN.match("\t:PROPERTIES:\n"))
        self.assertTrue(PROPERTY_DRAWER_BEGIN.match("  :PROPERTIES:\r\n"))

        self.assertIsNone(PROPERTY_DRAWER_BEGIN.match(":PROPERTIES: extra"))
        self.assertIsNone(PROPERTY_DRAWER_BEGIN.match("* :PROPERTIES:"))
        self.assertIsNone(PROPERTY_DRAWER_BEGIN.match("something :PROPERTIES:"))

    def test_property_drawer_end(self) -> None:
        self.assertTrue(PROPERTY_DRAWER_END.match(":END:"))
        self.assertTrue(PROPERTY_DRAWER_END.match(":end:"))
        self.assertTrue(PROPERTY_DRAWER_END.match("  :END:  "))
        self.assertTrue(PROPERTY_DRAWER_END.match(":END:\n"))
        self.assertTrue(PROPERTY_DRAWER_END.match(":END:\r\n"))

        self.assertIsNone(PROPERTY_DRAWER_END.match(":END: extra"))
        self.assertIsNone(PROPERTY_DRAWER_END.match("* :END:"))

    def test_node_property_matching(self) -> None:
        m1 = NODE_PROPERTY.match(":CUSTOM_ID: my-custom-id\n")
        self.assertIsNotNone(m1)
        assert m1 is not None
        self.assertEqual(m1.group("name"), "CUSTOM_ID")
        self.assertIsNone(m1.group("append"))
        self.assertEqual(m1.group("value"), "my-custom-id")

        m2 = NODE_PROPERTY.match("  :header-args+: :session py\r\n")
        self.assertIsNotNone(m2)
        assert m2 is not None
        self.assertEqual(m2.group("name"), "header-args")
        self.assertEqual(m2.group("append"), "+")
        self.assertEqual(m2.group("value"), ":session py")

        m3 = NODE_PROPERTY.match(":EMPTY:\n")
        self.assertIsNotNone(m3)
        assert m3 is not None
        self.assertEqual(m3.group("name"), "EMPTY")
        self.assertIsNone(m3.group("value"))

        m4 = NODE_PROPERTY.match(":URL: https://example.com:8080/path\n")
        self.assertIsNotNone(m4)
        assert m4 is not None
        self.assertEqual(m4.group("name"), "URL")
        self.assertEqual(m4.group("value"), "https://example.com:8080/path")

        # :END: and :PROPERTIES: must not match as property names
        self.assertIsNone(NODE_PROPERTY.match(":END:\n"))
        self.assertIsNone(NODE_PROPERTY.match(":PROPERTIES:\n"))

    def test_drawer_patterns(self) -> None:
        m = DRAWER_BEGIN.match("  :LOGBOOK:\n")
        self.assertIsNotNone(m)
        assert m is not None
        self.assertEqual(m.group("name"), "LOGBOOK")
        self.assertTrue(DRAWER_END.match("  :END:\n"))


class TestPropertyDrawerParsing(unittest.TestCase):
    """Tests for parsing property drawers from input streams."""

    def test_basic_property_drawer(self) -> None:
        doc = (
            "#+TITLE: Sample\n"
            ":PROPERTIES:\n"
            ":CUSTOM_ID: sec-1\n"
            ":ID: 12345\n"
            ":END:\n"
            "* Heading\n"
        )
        elements = parse(doc)
        self.assertEqual(len(elements), 3)
        self.assertEqual(elements[0], "#+TITLE: Sample\n")
        self.assertEqual(elements[2], "* Heading\n")

        drawer = elements[1]
        self.assertIsInstance(drawer, PropertyDrawer)
        assert isinstance(drawer, PropertyDrawer)

        self.assertEqual(drawer["CUSTOM_ID"], "sec-1")
        self.assertEqual(drawer["ID"], "12345")
        self.assertEqual(drawer.properties, {"CUSTOM_ID": "sec-1", "ID": "12345"})
        self.assertEqual(len(drawer), 2)
        self.assertEqual(len(drawer.node_properties), 2)
        self.assertEqual(drawer.indent, "")

    def test_case_insensitivity(self) -> None:
        doc = (
            ":properties:\n"
            ":Custom_Id: my-id\n"
            ":end:\n"
        )
        elements = parse(doc)
        self.assertEqual(len(elements), 1)
        drawer = elements[0]
        self.assertIsInstance(drawer, PropertyDrawer)
        assert isinstance(drawer, PropertyDrawer)

        self.assertEqual(drawer["CUSTOM_ID"], "my-id")
        self.assertEqual(drawer["custom_id"], "my-id")
        self.assertEqual(drawer["Custom_Id"], "my-id")
        self.assertEqual(drawer.get("CUSTOM_ID"), "my-id")
        self.assertTrue("CUSTOM_ID" in drawer)
        self.assertTrue("custom_id" in drawer)
        self.assertFalse("NONEXISTENT" in drawer)

    def test_indented_property_drawer(self) -> None:
        doc = (
            "* Heading\n"
            "  :PROPERTIES:\n"
            "  :ID: abc-999\n"
            "  :END:\n"
            "Body\n"
        )
        elements = parse(doc)
        self.assertEqual(len(elements), 3)
        drawer = elements[1]
        self.assertIsInstance(drawer, PropertyDrawer)
        assert isinstance(drawer, PropertyDrawer)
        self.assertEqual(drawer.indent, "  ")
        self.assertEqual(drawer["ID"], "abc-999")
        self.assertEqual(
            drawer.raw_lines,
            ["  :PROPERTIES:\n", "  :ID: abc-999\n", "  :END:\n"],
        )

    def test_append_property_syntax(self) -> None:
        doc = (
            ":PROPERTIES:\n"
            ":header-args: :results output\n"
            ":header-args+: :session py\n"
            ":header-args+: :tangle yes\n"
            ":END:\n"
        )
        elements = parse(doc)
        self.assertEqual(len(elements), 1)
        drawer = elements[0]
        self.assertIsInstance(drawer, PropertyDrawer)
        assert isinstance(drawer, PropertyDrawer)
        self.assertEqual(
            drawer["header-args"],
            ":results output :session py :tangle yes",
        )
        self.assertEqual(len(drawer.node_properties), 3)
        self.assertTrue(drawer.node_properties[1].append)
        self.assertTrue(drawer.node_properties[2].append)

    def test_initial_append_syntax(self) -> None:
        doc = (
            ":PROPERTIES:\n"
            ":header-args+: :session first\n"
            ":END:\n"
        )
        elements = parse(doc)
        drawer = elements[0]
        assert isinstance(drawer, PropertyDrawer)
        self.assertEqual(drawer["header-args"], ":session first")

    def test_empty_property_drawer(self) -> None:
        doc = ":PROPERTIES:\n:END:\n"
        elements = parse(doc)
        self.assertEqual(len(elements), 1)
        drawer = elements[0]
        self.assertIsInstance(drawer, PropertyDrawer)
        assert isinstance(drawer, PropertyDrawer)
        self.assertEqual(len(drawer), 0)
        self.assertEqual(drawer.properties, {})
        self.assertEqual(drawer.node_properties, [])

    def test_empty_property_value(self) -> None:
        doc = (
            ":PROPERTIES:\n"
            ":EMPTY_VAL:\n"
            ":SPACED_VAL:   \n"
            ":END:\n"
        )
        elements = parse(doc)
        drawer = elements[0]
        assert isinstance(drawer, PropertyDrawer)
        self.assertEqual(drawer["EMPTY_VAL"], "")
        self.assertEqual(drawer["SPACED_VAL"], "")

    def test_duplicate_properties_overwrite_and_get_all(self) -> None:
        doc = (
            ":PROPERTIES:\n"
            ":TAG: first\n"
            ":TAG: second\n"
            ":END:\n"
        )
        elements = parse(doc)
        drawer = elements[0]
        assert isinstance(drawer, PropertyDrawer)
        self.assertEqual(drawer["TAG"], "second")
        self.assertEqual(drawer.get_all("TAG"), ["first", "second"])

    def test_unclosed_property_drawer_stays_lines(self) -> None:
        lines = [
            ":PROPERTIES:\n",
            ":ID: 123\n",
            "* Heading\n",
        ]
        elements = parse(lines)
        self.assertEqual(elements, lines)

    def test_property_drawer_with_blank_line_stays_lines(self) -> None:
        lines = [
            ":PROPERTIES:\n",
            "\n",
            ":ID: 123\n",
            ":END:\n",
        ]
        elements = parse(lines)
        self.assertEqual(elements, lines)

    def test_property_drawer_with_invalid_text_stays_lines(self) -> None:
        lines = [
            ":PROPERTIES:\n",
            "This is not a property line.\n",
            ":END:\n",
        ]
        elements = parse(lines)
        self.assertEqual(elements, lines)

    def test_multiple_property_drawers(self) -> None:
        doc = (
            ":PROPERTIES:\n"
            ":ROOT_ID: 0\n"
            ":END:\n"
            "* Sub 1\n"
            ":PROPERTIES:\n"
            ":SUB_ID: 1\n"
            ":END:\n"
        )
        elements = parse(doc)
        self.assertEqual(len(elements), 3)
        self.assertIsInstance(elements[0], PropertyDrawer)
        self.assertEqual(elements[1], "* Sub 1\n")
        self.assertIsInstance(elements[2], PropertyDrawer)
        assert isinstance(elements[0], PropertyDrawer)
        assert isinstance(elements[2], PropertyDrawer)
        self.assertEqual(elements[0]["ROOT_ID"], "0")
        self.assertEqual(elements[2]["SUB_ID"], "1")

    def test_input_variations(self) -> None:
        # bytes
        raw_bytes = b":PROPERTIES:\n:ID: b1\n:END:\n"
        res_bytes = parse(raw_bytes)
        self.assertIsInstance(res_bytes[0], PropertyDrawer)
        assert isinstance(res_bytes[0], PropertyDrawer)
        self.assertEqual(res_bytes[0]["ID"], "b1")

        # list of bytes
        byte_lines = [b":PROPERTIES:\n", b":ID: b2\n", b":END:\n"]
        res_byte_lines = parse(byte_lines)
        self.assertIsInstance(res_byte_lines[0], PropertyDrawer)
        assert isinstance(res_byte_lines[0], PropertyDrawer)
        self.assertEqual(res_byte_lines[0]["ID"], "b2")

        # StringIO
        res_sio = parse(io.StringIO(":PROPERTIES:\n:ID: sio\n:END:\n"))
        self.assertIsInstance(res_sio[0], PropertyDrawer)
        assert isinstance(res_sio[0], PropertyDrawer)
        self.assertEqual(res_sio[0]["ID"], "sio")

        # Windows CRLF
        res_crlf = parse(":PROPERTIES:\r\n:ID: crlf\r\n:END:\r\n")
        self.assertIsInstance(res_crlf[0], PropertyDrawer)
        assert isinstance(res_crlf[0], PropertyDrawer)
        self.assertEqual(res_crlf[0]["ID"], "crlf")

    def test_mapping_methods(self) -> None:
        drawer = PropertyDrawer(
            properties={"A": "1", "B": "2"},
            raw_lines=[":PROPERTIES:\n", ":A: 1\n", ":B: 2\n", ":END:\n"],
        )
        self.assertEqual(list(drawer), ["A", "B"])
        self.assertEqual(list(drawer.keys()), ["A", "B"])
        self.assertEqual(list(drawer.values()), ["1", "2"])
        self.assertEqual(list(drawer.items()), [("A", "1"), ("B", "2")])
        self.assertEqual(len(drawer), 2)
        self.assertEqual(drawer.get("a"), "1")
        self.assertEqual(drawer.get("missing", "def"), "def")
        self.assertEqual(str(drawer), ":PROPERTIES:\n:A: 1\n:B: 2\n:END:\n")

        with self.assertRaises(KeyError):
            _ = drawer["NONEXISTENT"]


if __name__ == "__main__":
    unittest.main()
