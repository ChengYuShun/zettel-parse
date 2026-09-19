"""Block element produced by the first parsing pass."""

from __future__ import annotations

from dataclasses import dataclass, field


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
