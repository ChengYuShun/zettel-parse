"""File tags element produced by the first parsing pass."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FileTags:
    """A file tags keyword (#+filetags: :tag1:tag2: ...).

    Attributes:
        tags: The tags in order. Tags are case-sensitive and may contain
            spaces.
        raw_line: Verbatim source line comprising this keyword.
    """

    tags: list[str]
    raw_line: str = field(default="", compare=False)

    def __str__(self) -> str:
        """Return the verbatim representation of the file tags line."""
        return self.raw_line
