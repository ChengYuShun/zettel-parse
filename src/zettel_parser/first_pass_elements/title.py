"""Title element produced by the first parsing pass."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Title:
    """A document title keyword (#+title: ...).

    Attributes:
        value: The title text following the keyword.
        raw_line: Verbatim source line comprising this title.
    """

    value: str
    raw_line: str = field(default="", compare=False)

    def __str__(self) -> str:
        """Return the verbatim representation of the title line."""
        return self.raw_line
