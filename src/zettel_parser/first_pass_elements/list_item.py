"""List item element produced by the first parsing pass."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from zettel_parser.common_regex import CHECKBOX, LIST_ITEM
from zettel_parser.cursor import Cursor


class CheckboxState(Enum):
    """The recognized states of a checklist checkbox."""

    UNCHECKED = "unchecked"
    CHECKED = "checked"
    PARTIAL = "partial"


CHECKBOX_STATE_BY_MARK: dict[str, CheckboxState] = {
    " ": CheckboxState.UNCHECKED,
    "X": CheckboxState.CHECKED,
    "-": CheckboxState.PARTIAL,
}


def parse_checkbox(text: str) -> tuple[CheckboxState | None, str]:
    """Split a leading checklist marker off ``text``.

    A marker is ``[ ]`` (unchecked), ``[X]`` (checked), or ``[-]``
    (partial), and is only recognized when followed by a space or the
    end of the text.  When present, the marker and exactly one following space
    (if any) are removed.

    Args:
        text: The item text to inspect.

    Returns:
        A ``(state, remainder)`` pair.  ``state`` is the matching
        :class:`CheckboxState`, or None when no marker is present, in which
        case ``remainder`` is ``text`` unchanged.
    """
    match = CHECKBOX.match(text)
    if match is None:
        return None, text
    state = CHECKBOX_STATE_BY_MARK[match.group("mark")]
    remainder = text[match.end():]
    if remainder.startswith(" "):
        remainder = remainder[1:]
    return state, remainder


@dataclass
class ListItem:
    """A plain list item line, ordered or unordered.

    Attributes:
        bullet: The list marker (``-``, ``+``, ``1.``, or ``1)`` with an
            arbitrary number).
        value: The item text following the marker, with any checklist marker
            removed.
        checked: The checklist state, or None when the item has no checkbox.
        raw_line: Verbatim source line comprising this list item.
    """

    bullet: str
    value: str
    checked: CheckboxState | None = None
    raw_line: str = field(default="", compare=False)

    @property
    def ordered(self) -> bool:
        """Return True if this is an ordered list item."""
        return self.bullet not in ("-", "+")

    @classmethod
    def try_parse(cls, cursor: Cursor[str]) -> ListItem | None:
        """Consume a leading, unindented list item from ``cursor``.

        Indented list items are left for the structure pass and therefore
        return None here.

        Args:
            cursor: The cursor to consume a line from.

        Returns:
            A ListItem instance, or None if the line is not a list item.
        """
        line = cursor.current
        if not isinstance(line, str):
            return None
        match = LIST_ITEM.match(line)
        if match is None or match.group("indent"):
            return None
        cursor.advance()
        checked, value = parse_checkbox(match.group("value") or "")
        return cls(
            bullet=match.group("bullet"),
            value=value,
            checked=checked,
            raw_line=line,
        )

    def __str__(self) -> str:
        """Return the verbatim representation of the list item."""
        return self.raw_line
