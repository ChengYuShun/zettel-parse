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

# A resolved high-priority span: ``(start, end, match, kind)`` where ``kind``
# is either ``"latex"`` or ``"link"``.  High-priority spans (inline LaTeX and
# links) take precedence over emphasis markers and are never re-read as
# emphasis.
_HighPrioritySpan = tuple[int, int, re.Match[str], str]

# The emphasis markers that can be parsed, in priority order.  Each entry is
# ``(pattern, recursive, constructor)``: ``recursive`` is True when the marker's
# content may itself contain inline markup (bold, italic, underline and
# strike-through) and False when the content is literal (verbatim and code).
# The order matters: if two markers match at the same position, the first spec
# in this sequence wins.
_EmphasisSpec = tuple[
    re.Pattern[str],
    bool,
    Callable[[re.Match[str]], InlinePart],
]

_EMPHASIS_SPECS: tuple[_EmphasisSpec, ...] = (
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
)


def _get_high_priority_spans(text: str) -> list[_HighPrioritySpan]:
    """Find the non-overlapping inline LaTeX and link spans, left to right.

    Matches of both kinds are collected from every pattern and then reduced to
    a set in which the leftmost match wins: any later match that overlaps an
    already accepted one is discarded.
    """
    spans: list[_HighPrioritySpan] = []
    for pattern, kind in ((INLINE_LATEX, "latex"), (INLINE_LINK, "link")):
        for match in pattern.finditer(text):
            spans.append((match.start(), match.end(), match, kind))

    # Sort by start position; for equal starts, prefer the longer match.
    spans.sort(key=lambda item: (item[0], -item[1]))

    # Accept a match only when it starts at or after the end of the previous
    # one, which guarantees the retained spans never overlap.
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
    """Return whether an emphasis span improperly overlaps a high-priority span.

    Only two arrangements are allowed: the spans are disjoint, or a recursive
    emphasis marker (bold, italic, underline, strike-through) completely
    contains a high-priority span.  Every other overlap -- a partial crossing,
    or a non-recursive marker containing a span -- is a conflict.
    """
    for hp_start, hp_end, _, _ in hp_spans:
        if end <= hp_start or start >= hp_end:
            continue  # The spans are disjoint.
        if recursive and start <= hp_start and end >= hp_end:
            continue  # A recursive marker may fully contain the span.
        return True
    return False


def _next_high_priority_span(
    hp_spans: list[_HighPrioritySpan],
    pos: int,
) -> _HighPrioritySpan | None:
    """Return the first high-priority span starting at or after ``pos``."""
    for span in hp_spans:
        if span[0] >= pos:
            return span
    return None


def _find_best_emphasis(
    text: str,
    pos: int,
    hp_spans: list[_HighPrioritySpan],
) -> tuple[re.Match[str], Callable[[re.Match[str]], InlinePart]] | None:
    """Return the earliest non-conflicting emphasis match at or after ``pos``.

    Every emphasis pattern is searched from ``pos``; a match that overlaps a
    high-priority span is skipped by resuming the search one character past its
    start.  The leftmost match over all patterns wins, with ties broken by the
    order of :data:`_EMPHASIS_SPECS`.
    """
    best_match: re.Match[str] | None = None
    best_ctor: Callable[[re.Match[str]], InlinePart] | None = None

    for pattern, recursive, ctor in _EMPHASIS_SPECS:
        search_pos = pos
        while search_pos < len(text):
            match = pattern.search(text, search_pos)
            if match is None:
                break
            start, end = match.start(), match.end()
            if not _conflicts_with_hp(start, end, hp_spans, recursive):
                if best_match is None or start < best_match.start():
                    best_match = match
                    best_ctor = ctor
                break
            # This candidate is unusable; look for the next one.
            search_pos = start + 1

    if best_match is None or best_ctor is None:
        return None
    return best_match, best_ctor


def _build_high_priority_element(span: _HighPrioritySpan) -> InlinePart:
    """Build the AST element represented by a high-priority span."""
    _, _, match, kind = span
    if kind == "latex":
        return InlineLatex(content=match.group("content"))

    # A link's description is inline content in its own right, so it is parsed
    # recursively (a missing description stays None).
    description = match.group("description")
    desc_elements = parse_inline(description) if description is not None else None
    return Link(target=match.group("target"), description=desc_elements)


def _merge_adjacent_strings(elements: list[InlinePart]) -> list[InlinePart]:
    """Concatenate neighbouring plain strings and drop empty ones."""
    merged: list[InlinePart] = []
    for element in elements:
        if not isinstance(element, str):
            merged.append(element)
        elif element:
            if merged and isinstance(merged[-1], str):
                merged[-1] += element
            else:
                merged.append(element)
    return merged


def parse_inline(text: str) -> list[InlinePart]:
    """Parse a string into a list of inline elements and unannotated strings.

    Inline LaTeX expressions and links have higher precedence over emphasis
    markers.  Recursive elements (bold, italic, underline, strike-through, and
    link descriptions) have their inner text parsed recursively.
    """

    # Resolve inline LaTeX and links up front so that emphasis markers cannot
    # claim text that belongs to them.
    hp_spans = _get_high_priority_spans(text)
    result: list[InlinePart] = []
    pos = 0

    # Walk the text left to right, repeatedly emitting whichever comes first:
    # the next high-priority span or the next emphasis match.
    while pos < len(text):
        next_hp = _next_high_priority_span(hp_spans, pos)
        emphasis = _find_best_emphasis(text, pos, hp_spans)

        # Nothing else matches, so the rest of the text is plain.
        if next_hp is None and emphasis is None:
            result.append(text[pos:])
            break

        emphasis_start = emphasis[0].start() if emphasis is not None else None
        # A tie is won by the high-priority span.
        if next_hp is not None and (
            emphasis_start is None or next_hp[0] <= emphasis_start
        ):
            hp_start, hp_end, _, _ = next_hp
            # Emit any plain text between the cursor and the span.
            if hp_start > pos:
                result.append(text[pos:hp_start])
            result.append(_build_high_priority_element(next_hp))
            pos = hp_end
        else:
            assert emphasis is not None
            match, ctor = emphasis
            match_start, match_end = match.start(), match.end()
            # Emit any plain text between the cursor and the match.
            if match_start > pos:
                result.append(text[pos:match_start])
            result.append(ctor(match))
            pos = match_end

    return _merge_adjacent_strings(result)


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
