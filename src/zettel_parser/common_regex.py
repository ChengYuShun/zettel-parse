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
    r"^#\+begin_(?P<name>[a-zA-Z0-9_\-]+)"
    r"(?:[ \t]+(?P<args>.*?))?[ \t]*\r?$"
)
BLOCK_END_PATTERN: str = (
    r"^#\+end_(?P<name>[a-zA-Z0-9_\-]+)[ \t]*\r?$"
)

# Each entry is an ``(opening, closing, LatexBlockType member name)`` triple.
LATEX_BLOCK_DELIMITERS: tuple[tuple[str, str, str], ...] = (
    (r"\[", r"\]", "BRACKET"),
    (r"\begin{equation*}", r"\end{equation*}", "EQUATION"),
    (r"\begin{tikzcd}", r"\end{tikzcd}", "TIKZCD"),
    (r"\begin{align*}", r"\end{align*}", "ALIGN"),
)

_LATEX_BEGIN_ALTERNATION: str = "|".join(
    re.escape(opening) for opening, _, _ in LATEX_BLOCK_DELIMITERS
)
_LATEX_END_ALTERNATION: str = "|".join(
    re.escape(closing) for _, closing, _ in LATEX_BLOCK_DELIMITERS
)
LATEX_BLOCK_BEGIN_PATTERN: str = (
    rf"^(?P<delimiter>{_LATEX_BEGIN_ALTERNATION})(?P<content>.*?)\r?$"
)
LATEX_BLOCK_END_PATTERN: str = (
    rf"^(?P<delimiter>{_LATEX_END_ALTERNATION})[ \t]*\r?$"
)

TITLE_PATTERN: str = r"^#\+title:[ \t]*(?P<value>.*?)[ \t]*\r?$"

FILETAGS_PATTERN: str = (
    r"^#\+filetags:[ \t]+(?P<tags>:(?:[^:]+:)+)[ \t]*\r?$"
)

HEADLINE_PATTERN: str = r"^(?P<stars>\*+)[ \t]+(?P<title>.*?)[ \t]*\r?$"

LIST_ITEM_PATTERN: str = (
    r"^(?P<bullet>\*|[-+]|\d+[.)])"
    r"(?: (?P<value>.*?))?\r?$"
)

CHECKBOX_PATTERN: str = r"^\[(?P<mark>[- X])\](?= |$)"

INDENTATION_PATTERN: str = r"^[ \t]*"

BLANK_LINE_PATTERN: str = r"^[ \t]*\r?$"

# Emphasis boundary assertions.  The sets of accepted characters are taken
# from the Emacs Lisp function `org-element--parse-generic-emphasis`, with some
# modification.  Both assertions are zero-width, so they are never captured as
# part of the emphasis content.
#
# PRE_EMPHASIS matches the start of a line, a whitespace character, or one of
# "-", "(", "'", '"', "{", and "[".
# POST_EMPHASIS matches the end of a line, a whitespace character, or one of
# "-", ".", ",", ";", ":", "!", "?", "'", '"', ")", "}", "\", "[", and "]".
PRE_EMPHASIS: str = r"(?:(?<=^)|(?<=[\s\-({[\x27\x22]))"
POST_EMPHASIS: str = r"(?=$|[\s\-.,:!?;\x27\x22)}\]\\[])"

INLINE_LATEX_PATTERN: str = (
    r"\\\((?P<content>(?:(?!\n[ \t]*\n)[\s\S])*?)\\\)"
)

INLINE_LINK_PATTERN: str = (
    r"\[\[(?P<target>[^\]\r\n]+?)"
    r"(?:\]\[(?P<description>(?:(?!\n[ \t]*\n|\]\])[\s\S])*?))?\]\]"
)

INLINE_VERBATIM_PATTERN: str = (
    rf"{PRE_EMPHASIS}="
    r"(?P<content>[^\s\r\n]|[^\s\r\n][^\r\n]*?[^\s\r\n])"
    rf"={POST_EMPHASIS}"
)

INLINE_CODE_PATTERN: str = (
    rf"{PRE_EMPHASIS}~"
    r"(?P<content>[^\s\r\n]|[^\s\r\n][^\r\n]*?[^\s\r\n])"
    rf"~{POST_EMPHASIS}"
)

INLINE_ITALIC_PATTERN: str = (
    rf"{PRE_EMPHASIS}/"
    r"(?P<content>[^\s]|[^\s](?:(?!\n[ \t]*\n)[\s\S])*?[^\s])"
    rf"/{POST_EMPHASIS}"
)

INLINE_BOLD_PATTERN: str = (
    rf"{PRE_EMPHASIS}\*"
    r"(?P<content>[^\s]|[^\s](?:(?!\n[ \t]*\n)[\s\S])*?[^\s])"
    rf"\*{POST_EMPHASIS}"
)

INLINE_UNDERLINE_PATTERN: str = (
    rf"{PRE_EMPHASIS}_"
    r"(?P<content>[^\s]|[^\s](?:(?!\n[ \t]*\n)[\s\S])*?[^\s])"
    rf"_{POST_EMPHASIS}"
)

INLINE_STRIKETHROUGH_PATTERN: str = (
    rf"{PRE_EMPHASIS}\+"
    r"(?P<content>[^\s]|[^\s](?:(?!\n[ \t]*\n)[\s\S])*?[^\s])"
    rf"\+{POST_EMPHASIS}"
)

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

INLINE_LATEX: re.Pattern[str] = re.compile(INLINE_LATEX_PATTERN)
INLINE_LINK: re.Pattern[str] = re.compile(INLINE_LINK_PATTERN)
INLINE_VERBATIM: re.Pattern[str] = re.compile(INLINE_VERBATIM_PATTERN)
INLINE_CODE: re.Pattern[str] = re.compile(INLINE_CODE_PATTERN)
INLINE_ITALIC: re.Pattern[str] = re.compile(INLINE_ITALIC_PATTERN)
INLINE_BOLD: re.Pattern[str] = re.compile(INLINE_BOLD_PATTERN)
INLINE_UNDERLINE: re.Pattern[str] = re.compile(INLINE_UNDERLINE_PATTERN)
INLINE_STRIKETHROUGH: re.Pattern[str] = re.compile(INLINE_STRIKETHROUGH_PATTERN)

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
    "INLINE_BOLD",
    "INLINE_BOLD_PATTERN",
    "INLINE_CODE",
    "INLINE_CODE_PATTERN",
    "INLINE_ITALIC",
    "INLINE_ITALIC_PATTERN",
    "INLINE_LATEX",
    "INLINE_LATEX_PATTERN",
    "INLINE_LINK",
    "INLINE_LINK_PATTERN",
    "INLINE_STRIKETHROUGH",
    "INLINE_STRIKETHROUGH_PATTERN",
    "INLINE_UNDERLINE",
    "INLINE_UNDERLINE_PATTERN",
    "INLINE_VERBATIM",
    "INLINE_VERBATIM_PATTERN",
    "LATEX_BLOCK_BEGIN",
    "LATEX_BLOCK_BEGIN_PATTERN",
    "LATEX_BLOCK_DELIMITERS",
    "LATEX_BLOCK_END",
    "LATEX_BLOCK_END_PATTERN",
    "LIST_ITEM",
    "LIST_ITEM_PATTERN",
    "NODE_PROPERTY",
    "NODE_PROPERTY_PATTERN",
    "POST_EMPHASIS",
    "PRE_EMPHASIS",
    "TITLE",
    "TITLE_PATTERN",
]
