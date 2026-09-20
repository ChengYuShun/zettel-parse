"""Tests for list regular expressions in common_regex."""

from __future__ import annotations

from zettel_parser.common_regex import LIST_ITEM


def test_list_item_regex_unordered() -> None:
    for bullet in ("-", "+"):
        match = LIST_ITEM.match(f"{bullet} item\n")
        assert match is not None
        assert match.group("bullet") == bullet
        assert match.group("value") == "item"


def test_list_item_regex_ordered() -> None:
    for bullet in ("1.", "1)", "10.", "42)"):
        match = LIST_ITEM.match(f"{bullet} item\n")
        assert match is not None
        assert match.group("bullet") == bullet
        assert match.group("value") == "item"


def test_list_item_regex_allows_leading_spaces() -> None:
    for indent in ("", " ", "   ", "\t"):
        match = LIST_ITEM.match(f"{indent}- item\n")
        assert match is not None
        assert match.group("indent") == indent
        assert match.group("bullet") == "-"
        assert match.group("value") == "item"


def test_list_item_regex_allows_leading_spaces_with_bullet_alone() -> None:
    match = LIST_ITEM.match("  1.\n")
    assert match is not None
    assert match.group("indent") == "  "
    assert match.group("bullet") == "1."
    assert match.group("value") is None


def test_list_item_regex_allows_star_bullet() -> None:
    for indent in ("", " ", "  ", "\t", " \t "):
        match = LIST_ITEM.match(f"{indent}* item\n")
        assert match is not None
        assert match.group("indent") == indent
        assert match.group("bullet") == "*"
        assert match.group("value") == "item"

    match = LIST_ITEM.match("*\n")
    assert match is not None
    assert match.group("indent") == ""
    assert match.group("bullet") == "*"
    assert match.group("value") is None

    match = LIST_ITEM.match("  *\n")
    assert match is not None
    assert match.group("indent") == "  "
    assert match.group("bullet") == "*"
    assert match.group("value") is None


def test_list_item_regex_bullet_may_end_line() -> None:
    for bullet in ("-", "+", "1.", "1)"):
        match = LIST_ITEM.match(f"{bullet}\n")
        assert match is not None
        assert match.group("bullet") == bullet
        assert match.group("value") is None

        match = LIST_ITEM.match(bullet)
        assert match is not None
        assert match.group("bullet") == bullet
        assert match.group("value") is None


def test_list_item_regex_bullet_may_end_crlf_line() -> None:
    match = LIST_ITEM.match("-\r\n")
    assert match is not None
    assert match.group("bullet") == "-"
    assert match.group("value") is None


def test_list_item_regex_requires_space_or_line_end() -> None:
    for bullet in ("*", "-", "+", "1.", "1)"):
        assert LIST_ITEM.match(f"{bullet}item\n") is None


def test_list_item_regex_rejects() -> None:
    assert LIST_ITEM.match("a. letter\n") is None
    assert LIST_ITEM.match("A) letter\n") is None
    assert LIST_ITEM.match("z) letter\n") is None
    assert LIST_ITEM.match("ab. two letters\n") is None
    assert LIST_ITEM.match("#+title: x\n") is None


def test_list_item_regex_rejects_tab_after_bullet() -> None:
    for bullet in ("*", "-", "+", "1.", "1)"):
        assert LIST_ITEM.match(f"{bullet}\titem\n") is None
        assert LIST_ITEM.match(f"{bullet}\t\n") is None
        assert LIST_ITEM.match(f"{bullet}\t") is None


def test_list_item_regex_allows_trailing_tab_after_value() -> None:
    match = LIST_ITEM.match("- item\t\n")
    assert match is not None
    assert match.group("bullet") == "-"
    assert match.group("value") == "item"


def test_list_item_regex_removes_only_one_separating_space() -> None:
    match = LIST_ITEM.match("-   item\n")
    assert match is not None
    assert match.group("value") == "  item"

    match = LIST_ITEM.match("-   \n")
    assert match is not None
    assert match.group("value") == ""
