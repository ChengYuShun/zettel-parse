"""Inline pass parser for Org-mode variant.

This module provides AST elements and parsing functions for inline markup,
including inline LaTeX expressions, links, verbatim, code, italic, bold,
underlined, and strike-through text.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import ClassVar

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


class Emphasis(ABC):
    """Common base for the six emphasis markers.

    A subclass records the regex that matches it (:attr:`pattern`) and whether
    its content may itself contain inline markup (:attr:`recursive`), and
    implements :meth:`from_str` to build an element from the captured content.
    """

    recursive: ClassVar[bool] = False
    pattern: ClassVar[re.Pattern[str]]

    @classmethod
    @abstractmethod
    def from_str(cls, content: str) -> InlinePart:
        """Build an element from the content captured between the delimiters."""
        raise NotImplementedError


@dataclass
class Verbatim(Emphasis):
    """Verbatim text surrounded by =...=.

    Attributes:
        text: The verbatim string content.
    """

    text: str = ""
    recursive: ClassVar[bool] = False
    pattern: ClassVar[re.Pattern[str]] = INLINE_VERBATIM

    @classmethod
    def from_str(cls, content: str) -> Verbatim:
        """Build verbatim text; its content is literal, so no parsing occurs."""
        return cls(text=content)

    def __str__(self) -> str:
        """Return the verbatim representation with delimiters."""
        return f"={self.text}="


@dataclass
class Code(Emphasis):
    """Code text surrounded by ~...~.

    Attributes:
        text: The code string content.
    """

    text: str = ""
    recursive: ClassVar[bool] = False
    pattern: ClassVar[re.Pattern[str]] = INLINE_CODE

    @classmethod
    def from_str(cls, content: str) -> Code:
        """Build code text; its content is literal, so no parsing occurs."""
        return cls(text=content)

    def __str__(self) -> str:
        """Return the code representation with delimiters."""
        return f"~{self.text}~"


@dataclass
class Bold(Emphasis):
    """Bold text surrounded by *...*.

    Attributes:
        elements: The parsed inner inline elements.
    """

    elements: list[InlinePart] = field(default_factory=list)
    recursive: ClassVar[bool] = True
    pattern: ClassVar[re.Pattern[str]] = INLINE_BOLD

    @classmethod
    def from_str(cls, content: str) -> Bold:
        """Build bold text, parsing the content for nested inline markup."""
        return cls(elements=parse_inline(content))

    def __str__(self) -> str:
        """Return the bold representation with delimiters."""
        inner = "".join(str(element) for element in self.elements)
        return f"*{inner}*"


@dataclass
class Italic(Emphasis):
    """Italic text surrounded by /.../.

    Attributes:
        elements: The parsed inner inline elements.
    """

    elements: list[InlinePart] = field(default_factory=list)
    recursive: ClassVar[bool] = True
    pattern: ClassVar[re.Pattern[str]] = INLINE_ITALIC

    @classmethod
    def from_str(cls, content: str) -> Italic:
        """Build italic text, parsing the content for nested inline markup."""
        return cls(elements=parse_inline(content))

    def __str__(self) -> str:
        """Return the italic representation with delimiters."""
        inner = "".join(str(element) for element in self.elements)
        return f"/{inner}/"


@dataclass
class Underline(Emphasis):
    """Underlined text surrounded by _..._.

    Attributes:
        elements: The parsed inner inline elements.
    """

    elements: list[InlinePart] = field(default_factory=list)
    recursive: ClassVar[bool] = True
    pattern: ClassVar[re.Pattern[str]] = INLINE_UNDERLINE

    @classmethod
    def from_str(cls, content: str) -> Underline:
        """Build underlined text, parsing the content for nested inline markup."""
        return cls(elements=parse_inline(content))

    def __str__(self) -> str:
        """Return the underlined representation with delimiters."""
        inner = "".join(str(element) for element in self.elements)
        return f"_{inner}_"


@dataclass
class StrikeThrough(Emphasis):
    """Strike-through text surrounded by +...+.

    Attributes:
        elements: The parsed inner inline elements.
    """

    elements: list[InlinePart] = field(default_factory=list)
    recursive: ClassVar[bool] = True
    pattern: ClassVar[re.Pattern[str]] = INLINE_STRIKETHROUGH

    @classmethod
    def from_str(cls, content: str) -> StrikeThrough:
        """Build strike-through text, parsing the content for nested markup."""
        return cls(elements=parse_inline(content))

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


def _first_emphasis_valid_match(
    text: str,
    pos: int,
    emphasis_cls: type[Emphasis],
    hp_spans: list[_HighPrioritySpan],
) -> re.Match[str] | None:
    """Return the first match of ``emphasis_cls`` that does not conflict.

    The marker's pattern is searched from ``pos``; a candidate that overlaps a
    high-priority span is skipped by resuming the search one character past its
    start, until a usable match is found or the text is exhausted.
    """
    search_pos = pos
    while search_pos < len(text):
        match = emphasis_cls.pattern.search(text, search_pos)
        if match is None:
            return None
        if not _conflicts_with_hp(
            match.start(), match.end(), hp_spans, emphasis_cls.recursive
        ):
            return match
        search_pos = match.start() + 1
    return None


def _find_best_emphasis(
    text: str,
    pos: int,
    hp_spans: list[_HighPrioritySpan],
) -> tuple[re.Match[str], type[Emphasis]] | None:
    """Return the earliest non-conflicting emphasis match at or after ``pos``.

    The first valid match of every marker is considered and the leftmost one is
    returned, so ties are broken by the order in which the markers are tried
    below.
    """
    best: tuple[re.Match[str], type[Emphasis]] | None = None

    # The markers in priority order: if two match at the same position the
    # first one wins.
    for emphasis_cls in (Verbatim, Code, Bold, Italic, Underline, StrikeThrough):
        match = _first_emphasis_valid_match(text, pos, emphasis_cls, hp_spans)
        if match is not None and (best is None or match.start() < best[0].start()):
            best = (match, emphasis_cls)
    return best


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
            match, emphasis_cls = emphasis
            match_start, match_end = match.start(), match.end()
            # Emit any plain text between the cursor and the match.
            if match_start > pos:
                result.append(text[pos:match_start])
            result.append(emphasis_cls.from_str(match.group("content")))
            pos = match_end

    return _merge_adjacent_strings(result)


__all__ = [
    "Bold",
    "Code",
    "Emphasis",
    "InlineLatex",
    "InlinePart",
    "Italic",
    "Link",
    "StrikeThrough",
    "Underline",
    "Verbatim",
    "parse_inline",
]
