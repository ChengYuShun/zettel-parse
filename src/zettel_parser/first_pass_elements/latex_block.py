"""LaTeX block elements produced by the first parsing pass."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from zettel_parser.common_regex import (
    LATEX_BLOCK_BEGIN,
    LATEX_BLOCK_DELIMITERS,
    LATEX_BLOCK_END,
    LATEX_DELIMITERS,
)
from zettel_parser.cursor import Cursor


class LatexBlockType(Enum):
    """The recognized flavors of block-level LaTeX expression."""

    BRACKET = "bracket"
    EQUATION = "equation"
    TIKZCD = "tikzcd"


LATEX_BLOCK_TYPE_BY_DELIMITER: dict[str, LatexBlockType] = {
    opening: LatexBlockType[name]
    for opening, _, name in LATEX_BLOCK_DELIMITERS
}


@dataclass
class LatexBlock:
    """A block-level LaTeX expression.

    Attributes:
        type: The flavor of the expression.
        delimiter: The opening delimiter, one of ``LATEX_DELIMITERS`` keys
            (e.g. ``\\[`` or ``\\begin{tikzcd}``).
        text: The complete verbatim expression, including both delimiters and
            every newline in between.
    """

    type: LatexBlockType
    delimiter: str
    text: str

    @classmethod
    def try_parse(cls, cursor: Cursor[str]) -> LatexBlock | None:
        """Consume a leading unindented LaTeX block from ``cursor``.

        A LaTeX block runs from an opening delimiter to its matching closing
        delimiter.  If no matching closing delimiter is found, the cursor is
        left untouched and None is returned.

        Args:
            cursor: The cursor to consume lines from.

        Returns:
            A LatexBlock instance, or None if no LaTeX block starts here.
        """
        begin = cursor.peek()
        if not isinstance(begin, str):
            return None
        match = LATEX_BLOCK_BEGIN.match(begin)
        if match is None:
            return None

        delimiter = match.group("delimiter")
        block_type = LATEX_BLOCK_TYPE_BY_DELIMITER[delimiter]
        end_delimiter = LATEX_DELIMITERS[delimiter]
        lines = [begin]

        offset = 1
        while (candidate := cursor.peek(offset)) is not None:
            if not isinstance(candidate, str):
                return None
            end = LATEX_BLOCK_END.match(candidate)
            if end is not None and end.group("delimiter") == end_delimiter:
                lines.append(candidate)
                cursor.advance(offset + 1)
                return cls(
                    type=block_type,
                    delimiter=delimiter,
                    text="".join(lines),
                )
            lines.append(candidate)
            offset += 1

        return None

    @property
    def end_delimiter(self) -> str:
        """Return the closing delimiter paired with this opening delimiter."""
        return LATEX_DELIMITERS[self.delimiter]

    def __str__(self) -> str:
        """Return the complete verbatim expression."""
        return self.text


__all__ = ["LatexBlock", "LatexBlockType"]
