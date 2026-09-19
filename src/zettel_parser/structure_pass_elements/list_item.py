"""List item element produced by the structure pass."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from zettel_parser.common_regex import BLANK_LINE
from zettel_parser.cursor import Cursor
from zettel_parser.first_pass import ListItemFirstPassParser
from zettel_parser.first_pass_elements import ListItem as FirstPassListItem
from zettel_parser.structure_pass_elements.flat_text import FlatText

if TYPE_CHECKING:
    from zettel_parser.first_pass_elements import FirstPassElement


def _content_line(item: FirstPassListItem) -> str:
    """Return the item's own text with its bullet and a following space removed.

    If the bullet is not followed by whitespace (e.g. a bare bullet at the end
    of the line), no text can be recovered, so an empty line is returned
    instead, preserving the line ending when one is present.
    """
    rest = item.raw_line[len(item.bullet):]
    if rest[:1] in (" "):
        return rest[1:]
    return "\n" if item.raw_line.endswith("\n") else ""


def _remove_indent(line: str, required_prefix: str) -> str:
    """Remove up to ``width`` leading spaces from ``line``.

    Unlike ``lstrip``, this preserves any spaces beyond ``width``.
    """
    if line.startswith(required_prefix):
        return line[len(required_prefix):]
    else:
        return "\n" if line.endswith("\n") else ""


@dataclass
class ListItem:
    """A top-level list item with its indented continuation lines.

    Continuation lines must be indented by at least the width of the bullet
    plus the following space; that much indentation is stripped when the lines
    are collected, preserving any spaces beyond it.  Blank lines are kept only
    when followed by an indented line, and are de-indented the same way.

    Attributes:
        bullet: The list marker taken from the first pass.
        value: The item text following the marker on the first line.
        lines: The item's own text (bullet removed) followed by its
            de-indented continuation lines.
        body: The continuation lines parsed as flat text, if any.
        raw_lines: Verbatim source lines, for reconstructing the original.
    """

    bullet: str
    value: str
    lines: list[str] = field(default_factory=list)
    body: FlatText | None = field(default=None, compare=False)
    raw_lines: list[str] = field(default_factory=list, compare=False)

    @property
    def indent(self) -> int:
        """The minimal number of spaces required for a continuation line."""
        return len(self.bullet) + 1

    @classmethod
    def try_parse(cls, cursor: Cursor[FirstPassElement]) -> ListItem | None:
        """Consume a leading list item from ``cursor``.

        Parsing starts only if the cursor is at a first-pass list item.
        Subsequent plain lines are attached while they are indented by at
        least ``indent`` spaces.  Blank line runs are attached only when they
        are followed by such an indented line; otherwise parsing stops at the
        start of the blank run.  The collected lines are then re-parsed with
        the restricted :class:`ListItemFirstPassParser` and grouped into a
        :class:`FlatText` body.  If no list item starts at the cursor, it is
        left untouched and None is returned.

        Args:
            cursor: The cursor to consume elements from.

        Returns:
            A ListItem instance, or None if no list item starts here.
        """
        source = cursor.current
        if not isinstance(source, FirstPassListItem):
            return None

        cursor.advance()
        required = " " * (len(source.bullet) + 1)

        lines: list[str] = [_content_line(source)]
        raw_lines: list[str] = [source.raw_line]

        while True:
            element = cursor.peek()

            if isinstance(element, str) and BLANK_LINE.match(element):
                offset = 0
                while True:
                    probe = cursor.peek(offset)
                    if not (isinstance(probe, str)
                            and BLANK_LINE.match(probe)):
                        break
                    offset += 1
                following = cursor.peek(offset)
                if not (isinstance(following, str)
                        and not BLANK_LINE.match(following)
                        and following.startswith(required)):
                    break

                for _ in range(offset):
                    blank = cursor.peek()
                    if not isinstance(blank, str):
                        break
                    lines.append(_remove_indent(blank, required))
                    raw_lines.append(blank)
                    cursor.advance()
                continue

            if isinstance(element, str) and element.startswith(required):
                lines.append(element[len(required):])
                raw_lines.append(element)
                cursor.advance()
                continue

            break

        parsed = ListItemFirstPassParser().parse(lines)
        body = FlatText.try_parse(Cursor(parsed))

        return cls(
            bullet=source.bullet,
            value=source.value,
            lines=lines,
            body=body,
            raw_lines=raw_lines,
        )

    def __str__(self) -> str:
        """Return the verbatim representation of the list item."""
        return "".join(self.raw_lines)


__all__ = ["ListItem"]
