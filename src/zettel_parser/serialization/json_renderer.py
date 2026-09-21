"""JSON renderer for the canonical AST representation."""

from __future__ import annotations

import json

from zettel_parser.serialization.ir import to_data


def to_json(
    node: object,
    *,
    indent: int | None = 2,
    sort_keys: bool = False,
) -> str:
    """Render an AST node as JSON.

    Args:
        node: The AST node to render.
        indent: The indentation passed to :func:`json.dumps`; ``None`` selects
            the compact form.
        sort_keys: Whether to emit mapping keys in sorted order instead of the
            canonical field order.

    Returns:
        The JSON text, without a trailing newline.
    """
    return json.dumps(
        to_data(node),
        ensure_ascii=False,
        indent=indent,
        sort_keys=sort_keys,
    )


__all__ = ["to_json"]
