"""Headline element produced by the first parsing pass."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Headline:
    """An Org-mode headline (one or more leading stars and a title).

    Attributes:
        level: The outline level, i.e. the number of leading stars.
        title: The headline text after the stars.
        raw_line: Verbatim source line comprising this headline.
    """

    level: int
    title: str
    raw_line: str = field(default="", compare=False)

    def __str__(self) -> str:
        """Return the verbatim representation of the headline."""
        return self.raw_line
