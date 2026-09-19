"""LaTeX block elements produced by the first parsing pass."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from zettel_parser.common_regex import LATEX_DELIMITERS


class LatexBlockType(Enum):
    """The recognized flavors of block-level LaTeX expression."""

    BRACKET = "bracket"
    EQUATION = "equation"
    TIKZCD = "tikzcd"


LATEX_BLOCK_TYPE_BY_DELIMITER: dict[str, LatexBlockType] = {
    r"\[": LatexBlockType.BRACKET,
    r"\begin{equation*}": LatexBlockType.EQUATION,
    r"\begin{tikzcd}": LatexBlockType.TIKZCD,
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

    @property
    def end_delimiter(self) -> str:
        """Return the closing delimiter paired with this opening delimiter."""
        return LATEX_DELIMITERS[self.delimiter]

    def __str__(self) -> str:
        """Return the complete verbatim expression."""
        return self.text
