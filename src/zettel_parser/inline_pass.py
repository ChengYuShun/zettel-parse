"""Inline pass parser for Org-mode variant.

This module provides AST elements and parsing functions for inline markup,
including inline LaTeX expressions, links, verbatim, code, italic, bold,
underlined, and strike-through text.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field

from zettel_parser.common_regex import (
    INLINE_BOLD,
    INLINE_CODE,
    INLINE_ITALIC,
    INLINE_LATEX,
    INLINE_LINK,
    INLINE_STRIKETHROUGH,
    INLINE_UNDERLINE,
    INLINE_VERBATIM,
)


@dataclass
class InlineLatex:
    """An inline LaTeX expression surrounded by \\( and \\).

    Attributes:
        content: The verbatim content between delimiters, preserving whitespace.
    """

    content: str = ""

    def __str__(self) -> str:
        """Return the verbatim representation with delimiters."""
        return f"\\({self.content}\\)"


@dataclass
class Link:
    """An Org-mode link [[TARGET][DESCRIPTION]] or [[TARGET]].

    Attributes:
        target: The verbatim target string, preserving whitespace.
        description: Parsed description elements, or None if no description.
    """

    target: str
    description: list[InlinePart] | None = None

    def __str__(self) -> str:
        """Return the verbatim representation of the link."""
        if self.description is None:
            return f"[[{self.target}]]"
        desc_str = "".join(str(element) for element in self.description)
        return f"[[{self.target}][{desc_str}]]"


@dataclass
class Verbatim:
    """Verbatim text surrounded by =...=.

    Attributes:
        text: The verbatim string content.
    """

    text: str = ""

    def __str__(self) -> str:
        """Return the verbatim representation with delimiters."""
        return f"={self.text}="


@dataclass
class Code:
    """Code text surrounded by ~...~.

    Attributes:
        text: The code string content.
    """

    text: str = ""

    def __str__(self) -> str:
        """Return the code representation with delimiters."""
        return f"~{self.text}~"


@dataclass
class Bold:
    """Bold text surrounded by *...*.

    Attributes:
        elements: The parsed inner inline elements.
    """

    elements: list[InlinePart] = field(default_factory=list)

    def __str__(self) -> str:
        """Return the bold representation with delimiters."""
        inner = "".join(str(element) for element in self.elements)
        return f"*{inner}*"


@dataclass
class Italic:
    """Italic text surrounded by /.../.

    Attributes:
        elements: The parsed inner inline elements.
    """

    elements: list[InlinePart] = field(default_factory=list)

    def __str__(self) -> str:
        """Return the italic representation with delimiters."""
        inner = "".join(str(element) for element in self.elements)
        return f"/{inner}/"


@dataclass
class Underline:
    """Underlined text surrounded by _..._.

    Attributes:
        elements: The parsed inner inline elements.
    """

    elements: list[InlinePart] = field(default_factory=list)

    def __str__(self) -> str:
        """Return the underlined representation with delimiters."""
        inner = "".join(str(element) for element in self.elements)
        return f"_{inner}_"


@dataclass
class StrikeThrough:
    """Strike-through text surrounded by +...+.

    Attributes:
        elements: The parsed inner inline elements.
    """

    elements: list[InlinePart] = field(default_factory=list)

    def __str__(self) -> str:
        """Return the strike-through representation with delimiters."""
        inner = "".join(str(element) for element in self.elements)
        return f"+{inner}+"


InlinePart = (
    str
    | InlineLatex
    | Link
    | Verbatim
    | Code
    | Bold
    | Italic
    | Underline
    | StrikeThrough
)

_HighPrioritySpan = tuple[int, int, re.Match[str], str]


def _get_high_priority_spans(text: str) -> list[_HighPrioritySpan]:
    """Find non-overlapping inline LaTeX and link spans ordered by position."""
    spans: list[_HighPrioritySpan] = []
    for pattern, kind in [(INLINE_LATEX, "latex"), (INLINE_LINK, "link")]:
        for match in pattern.finditer(text):
            spans.append((match.start(), match.end(), match, kind))
    spans.sort(key=lambda item: (item[0], -item[1]))

    non_overlapping: list[_HighPrioritySpan] = []
    last_end = 0
    for start, end, match, kind in spans:
        if start >= last_end:
            non_overlapping.append((start, end, match, kind))
            last_end = end
    return non_overlapping


def _conflicts_with_hp(
    start: int,
    end: int,
    hp_spans: list[_HighPrioritySpan],
    recursive: bool,
) -> bool:
    """Determine whether an emphasis span improperly overlaps with high-priority spans.

    An emphasis match is invalid if its delimiters fall inside a high-priority
    span or if it partially overlaps one.  Recursive emphasis markers (bold,
    italic, underline, strike-through) are allowed to completely enclose
    high-priority spans.
    """
    for hp_start, hp_end, _, _ in hp_spans:
        if end <= hp_start or start >= hp_end:
            continue
        if hp_start < start < hp_end or hp_start < end < hp_end:
            return True
        if start < hp_start and hp_start < end <= hp_end:
            return True
        if hp_start <= start < hp_end and end > hp_end:
            return True
        if start <= hp_start and end >= hp_end:
            if not recursive:
                return True
            continue
        return True
    return False


def parse_inline(text: str) -> list[InlinePart]:
    """Parse a string into a list of inline elements and unannotated strings.

    Inline LaTeX expressions and links have higher precedence over emphasis
    markers.  Recursive elements (bold, italic, underline, strike-through, and
    link descriptions) have their inner text parsed recursively.
    """
    if not text:
        return []

    hp_spans = _get_high_priority_spans(text)
    result: list[InlinePart] = []
    pos = 0

    emphasis_specs: list[
        tuple[
            re.Pattern[str],
            bool,
            Callable[[re.Match[str]], InlinePart],
        ]
    ] = [
        (INLINE_VERBATIM, False, lambda m: Verbatim(text=m.group("content"))),
        (INLINE_CODE, False, lambda m: Code(text=m.group("content"))),
        (INLINE_BOLD, True, lambda m: Bold(elements=parse_inline(m.group("content")))),
        (
            INLINE_ITALIC,
            True,
            lambda m: Italic(elements=parse_inline(m.group("content"))),
        ),
        (
            INLINE_UNDERLINE,
            True,
            lambda m: Underline(elements=parse_inline(m.group("content"))),
        ),
        (
            INLINE_STRIKETHROUGH,
            True,
            lambda m: StrikeThrough(elements=parse_inline(m.group("content"))),
        ),
    ]

    while pos < len(text):
        next_hp: _HighPrioritySpan | None = None
        for span in hp_spans:
            if span[0] >= pos:
                next_hp = span
                break

        best_emph: re.Match[str] | None = None
        best_emph_ctor: Callable[[re.Match[str]], InlinePart] | None = None
        for pattern, recursive, ctor in emphasis_specs:
            search_pos = pos
            while search_pos < len(text):
                match = pattern.search(text, search_pos)
                if match is None:
                    break
                match_start, match_end = match.start(), match.end()
                if not _conflicts_with_hp(
                    match_start, match_end, hp_spans, recursive
                ):
                    if best_emph is None or match_start < best_emph.start():
                        best_emph = match
                        best_emph_ctor = ctor
                    break
                search_pos = match_start + 1

        if next_hp is None and best_emph is None:
            result.append(text[pos:])
            break

        if next_hp is not None and (
            best_emph is None or next_hp[0] <= best_emph.start()
        ):
            hp_start, hp_end, hp_match, hp_kind = next_hp
            if hp_start > pos:
                result.append(text[pos:hp_start])
            if hp_kind == "latex":
                result.append(InlineLatex(content=hp_match.group("content")))
            else:
                target = hp_match.group("target")
                description = hp_match.group("description")
                desc_elements = (
                    parse_inline(description) if description is not None else None
                )
                result.append(Link(target=target, description=desc_elements))
            pos = hp_end
        else:
            assert best_emph is not None
            assert best_emph_ctor is not None
            match_start, match_end = best_emph.start(), best_emph.end()
            if match_start > pos:
                result.append(text[pos:match_start])
            result.append(best_emph_ctor(best_emph))
            pos = match_end

    # Merge adjacent plain text runs and omit empty strings.
    merged: list[InlinePart] = []
    for element in result:
        if isinstance(element, str):
            if not element:
                continue
            if merged and isinstance(merged[-1], str):
                merged[-1] += element
            else:
                merged.append(element)
        else:
            merged.append(element)
    return merged


__all__ = [
    "Bold",
    "Code",
    "InlineLatex",
    "InlinePart",
    "Italic",
    "Link",
    "StrikeThrough",
    "Underline",
    "Verbatim",
    "parse_inline",
]
