"""Reusable regular expressions for Org-mode syntax parsing."""

from __future__ import annotations

import re

DRAWER_BEGIN_PATTERN: str = r"^[ \t]*:(?P<name>[a-zA-Z0-9_\-]+):[ \t]*\r?$"
DRAWER_END_PATTERN: str = r"^[ \t]*:END:[ \t]*\r?$"
NODE_PROPERTY_PATTERN: str = (
    r"^[ \t]*:(?!(?:END|PROPERTIES)\s*:)(?P<name>\S+?)(?P<append>\+)?:"
    r"(?:[ \t]+(?P<value>.*?))?[ \t]*\r?$"
)

BLOCK_BEGIN_PATTERN: str = (
    r"^(?P<indent>[ \t]*)#\+begin_(?P<name>[a-zA-Z0-9_\-]+)"
    r"(?:[ \t]+(?P<args>.*?))?[ \t]*\r?$"
)
BLOCK_END_PATTERN: str = (
    r"^(?P<indent>[ \t]*)#\+end_(?P<name>[a-zA-Z0-9_\-]+)[ \t]*\r?$"
)

LATEX_DELIMITERS: dict[str, str] = {
    r"\[": r"\]",
    r"\begin{equation*}": r"\end{equation*}",
    r"\begin{tikzcd}": r"\end{tikzcd}",
}

_LATEX_BEGIN_ALTERNATION: str = "|".join(
    re.escape(delimiter) for delimiter in LATEX_DELIMITERS
)
_LATEX_END_ALTERNATION: str = "|".join(
    re.escape(delimiter) for delimiter in LATEX_DELIMITERS.values()
)
LATEX_BLOCK_BEGIN_PATTERN: str = (
    rf"^(?P<indent>[ \t]*)(?P<delimiter>{_LATEX_BEGIN_ALTERNATION})"
    rf"[ \t]*(?P<content>.*?)[ \t]*\r?$"
)
LATEX_BLOCK_END_PATTERN: str = (
    rf"^(?P<indent>[ \t]*)(?P<delimiter>{_LATEX_END_ALTERNATION})[ \t]*\r?$"
)

TITLE_PATTERN: str = r"^#\+title:[ \t]*(?P<value>.*?)[ \t]*\r?$"

FILETAGS_PATTERN: str = (
    r"^#\+filetags:[ \t]+(?P<tags>:(?:[^:]+:)+)[ \t]*\r?$"
)

HEADLINE_PATTERN: str = r"^(?P<stars>\*+)[ \t]+(?P<title>.*?)[ \t]*\r?$"

LIST_ITEM_PATTERN: str = (
    r"^(?P<indent>[ \t]*)"
    r"(?P<bullet>\*|[-+]|\d+[.)])"
    r"(?: (?P<value>.*?)[ \t]*)?\r?$"
)

CHECKBOX_PATTERN: str = r"^\[(?P<mark>[ X])\](?= |$)"

INDENTATION_PATTERN: str = r"^[ \t]*"

BLANK_LINE_PATTERN: str = r"^[ \t]*\r?$"

DRAWER_BEGIN: re.Pattern[str] = re.compile(DRAWER_BEGIN_PATTERN, re.IGNORECASE)
DRAWER_END: re.Pattern[str] = re.compile(DRAWER_END_PATTERN, re.IGNORECASE)
NODE_PROPERTY: re.Pattern[str] = re.compile(NODE_PROPERTY_PATTERN,
                                            re.IGNORECASE)

BLOCK_BEGIN: re.Pattern[str] = re.compile(BLOCK_BEGIN_PATTERN, re.IGNORECASE)
BLOCK_END: re.Pattern[str] = re.compile(BLOCK_END_PATTERN, re.IGNORECASE)

LATEX_BLOCK_BEGIN: re.Pattern[str] = re.compile(LATEX_BLOCK_BEGIN_PATTERN)
LATEX_BLOCK_END: re.Pattern[str] = re.compile(LATEX_BLOCK_END_PATTERN)

TITLE: re.Pattern[str] = re.compile(TITLE_PATTERN, re.IGNORECASE)
FILETAGS: re.Pattern[str] = re.compile(FILETAGS_PATTERN, re.IGNORECASE)
HEADLINE: re.Pattern[str] = re.compile(HEADLINE_PATTERN)
LIST_ITEM: re.Pattern[str] = re.compile(LIST_ITEM_PATTERN)
CHECKBOX: re.Pattern[str] = re.compile(CHECKBOX_PATTERN)

INDENTATION: re.Pattern[str] = re.compile(INDENTATION_PATTERN)

BLANK_LINE: re.Pattern[str] = re.compile(BLANK_LINE_PATTERN)

__all__ = [
    "BLANK_LINE",
    "BLANK_LINE_PATTERN",
    "BLOCK_BEGIN",
    "BLOCK_BEGIN_PATTERN",
    "BLOCK_END",
    "BLOCK_END_PATTERN",
    "CHECKBOX",
    "CHECKBOX_PATTERN",
    "DRAWER_BEGIN",
    "DRAWER_BEGIN_PATTERN",
    "DRAWER_END",
    "DRAWER_END_PATTERN",
    "FILETAGS",
    "FILETAGS_PATTERN",
    "HEADLINE",
    "HEADLINE_PATTERN",
    "INDENTATION",
    "INDENTATION_PATTERN",
    "LATEX_BLOCK_BEGIN",
    "LATEX_BLOCK_BEGIN_PATTERN",
    "LATEX_BLOCK_END",
    "LATEX_BLOCK_END_PATTERN",
    "LATEX_DELIMITERS",
    "LIST_ITEM",
    "LIST_ITEM_PATTERN",
    "NODE_PROPERTY",
    "NODE_PROPERTY_PATTERN",
    "TITLE",
    "TITLE_PATTERN",
]
