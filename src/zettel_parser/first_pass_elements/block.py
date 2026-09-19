"""Block element produced by the first parsing pass."""

from __future__ import annotations

from dataclasses import dataclass, field

from zettel_parser.common_regex import BLOCK_BEGIN, BLOCK_END
from zettel_parser.cursor import Cursor


@dataclass
class Block:
    """An Org-mode block (#+begin_NAME ... #+end_NAME).

    Attributes:
        name: The block name, normalized to lower case (e.g. ``src``).
        arguments: The text following the block name on the begin line.
        raw_lines: Verbatim source lines comprising this block.
    """

    name: str
    arguments: str = ""
    raw_lines: list[str] = field(default_factory=list, compare=False)

    @classmethod
    def try_parse(cls, cursor: Cursor[str]) -> Block | None:
        """Consume a leading unindented block from ``cursor``.

        A block runs from a ``#+begin_NAME`` line to the matching
        ``#+end_NAME`` line (case-insensitively).  If no matching end is
        found, the cursor is left untouched and None is returned.

        Args:
            cursor: The cursor to consume lines from.

        Returns:
            A Block instance, or None if no block starts here.
        """
        begin = cursor.peek()
        if not isinstance(begin, str):
            return None
        match = BLOCK_BEGIN.match(begin)
        if match is None or match.group("indent"):
            return None

        name = match.group("name").lower()
        arguments = match.group("args") or ""
        lines = [begin]

        offset = 1
        while (candidate := cursor.peek(offset)) is not None:
            if not isinstance(candidate, str):
                return None
            end = BLOCK_END.match(candidate)
            if (
                end is not None
                and not end.group("indent")
                and end.group("name").lower() == name
            ):
                lines.append(candidate)
                cursor.advance(offset + 1)
                return cls(name=name, arguments=arguments, raw_lines=lines)
            lines.append(candidate)
            offset += 1

        return None

    @property
    def body(self) -> str:
        """Return the text between the begin and end lines."""
        return "".join(self.raw_lines[1:-1])

    @property
    def body_lines(self) -> list[str]:
        """Return the lines between the begin and end lines."""
        return list(self.raw_lines[1:-1])

    def __str__(self) -> str:
        """Return the verbatim representation of the block."""
        return "".join(self.raw_lines)


__all__ = ["Block"]
