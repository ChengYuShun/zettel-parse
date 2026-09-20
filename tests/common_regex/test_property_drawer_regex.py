"""Tests for property drawer regular expressions in common_regex."""

from __future__ import annotations

import unittest

from zettel_parser.common_regex import (
    DRAWER_BEGIN,
    DRAWER_END,
    NODE_PROPERTY,
)


class TestRegexes(unittest.TestCase):
    """Tests verifying property drawer regex patterns in common_regex.py."""

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


if __name__ == "__main__":
    unittest.main()
