"""Command-line interface for parsing and serializing Org-mode documents."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from zettel_parser import __version__
from zettel_parser.serialization import SERIALIZERS, serialize
from zettel_parser.structure_pass import parse

PROG = "zettel-parser"


def _read_source(path: str | None) -> str:
    """Read the document from ``path``, or from standard input when absent."""
    if path is None or path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Parse a custom Org-mode document and serialize its AST.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default=None,
        help="document to read; omit or use '-' to read standard input",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=sorted(SERIALIZERS),
        default="json",
        help="output format (default: %(default)s)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="write to this file instead of standard output",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command-line interface.

    Args:
        argv: The argument list, defaulting to ``sys.argv[1:]``.

    Returns:
        The process exit code.
    """
    args = build_parser().parse_args(argv)
    try:
        source = _read_source(args.file)
    except OSError as error:
        print(f"{PROG}: error: {error}", file=sys.stderr)
        return 1

    result = serialize(parse(source), args.format)
    if not result.endswith("\n"):
        result = f"{result}\n"

    if args.output is None:
        sys.stdout.write(result)
    else:
        Path(args.output).write_text(result, encoding="utf-8")
    return 0


__all__ = ["PROG", "build_parser", "main"]
