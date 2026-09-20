"""Tests for inline regular expressions in common_regex."""

from __future__ import annotations

import re

from zettel_parser.common_regex import (
    INLINE_BOLD,
    INLINE_CODE,
    INLINE_ITALIC,
    INLINE_LATEX,
    INLINE_LINK,
    INLINE_STRIKETHROUGH,
    INLINE_UNDERLINE,
    INLINE_VERBATIM,
    POST_EMPHASIS,
    PRE_EMPHASIS,
)


def test_pre_emphasis_regex() -> None:
    # PRE_EMPHASIS is zero-width, so it is probed by attaching a literal.
    pattern = re.compile(PRE_EMPHASIS + "x")
    assert pattern.search("x") is not None  # Beginning of line.
    for prefix in [" ", "\t", "-", "(", "'", '"', "{", "["]:
        assert pattern.search(f"{prefix}x") is not None, prefix
    for prefix in ["a", ".", ")", "}"]:
        assert pattern.search(f"{prefix}x") is None, prefix


def test_post_emphasis_regex() -> None:
    # POST_EMPHASIS is zero-width, so it is probed by attaching a literal.
    pattern = re.compile("x" + POST_EMPHASIS)
    assert pattern.search("x") is not None  # End of line.
    for suffix in [
        " ",
        "\t",
        "-",
        ".",
        ",",
        ";",
        ":",
        "!",
        "?",
        "'",
        '"',
        ")",
        "}",
        "\\",
        "[",
        "]",
    ]:
        assert pattern.search(f"x{suffix}") is not None, suffix
    for suffix in ["a", "(", "{", "="]:
        assert pattern.search(f"x{suffix}") is None, suffix


def test_emphasis_rejected_by_invalid_pre_character() -> None:
    # A preceding character outside PRE_EMPHASIS must block every emphasis.
    emphases = [
        (INLINE_VERBATIM, "="),
        (INLINE_CODE, "~"),
        (INLINE_ITALIC, "/"),
        (INLINE_BOLD, "*"),
        (INLINE_UNDERLINE, "_"),
        (INLINE_STRIKETHROUGH, "+"),
    ]
    for pattern, mark in emphases:
        for prefix in ["a", ".", ")", "}", "\\"]:
            text = f"{prefix}{mark}x{mark}"
            assert pattern.search(text) is None, text


def test_emphasis_rejected_by_invalid_post_character() -> None:
    # A following character outside POST_EMPHASIS must block every emphasis.
    emphases = [
        (INLINE_VERBATIM, "="),
        (INLINE_CODE, "~"),
        (INLINE_ITALIC, "/"),
        (INLINE_BOLD, "*"),
        (INLINE_UNDERLINE, "_"),
        (INLINE_STRIKETHROUGH, "+"),
    ]
    for pattern, mark in emphases:
        for suffix in ["a", "(", "{"]:
            text = f"{mark}x{mark}{suffix}"
            assert pattern.search(text) is None, text


def test_inline_latex_regex() -> None:
    match = INLINE_LATEX.search(r"\(a\)")
    assert match is not None
    assert match.group("content") == "a"

    # Spacing must not be stripped
    match = INLINE_LATEX.search(r"\( a\)")
    assert match is not None
    assert match.group("content") == " a"

    # Multiline is allowed
    match = INLINE_LATEX.search(r"\(a" + "\n" + r"b\)")
    assert match is not None
    assert match.group("content") == "a\nb"

    # Blank line is not allowed
    assert INLINE_LATEX.search(r"\(a" + "\n\n" + r"b\)") is None


def test_inline_link_regex() -> None:
    # Target only
    match = INLINE_LINK.search("[[target]]")
    assert match is not None
    assert match.group("target") == "target"
    assert match.group("description") is None

    # Spaces in target must not be stripped
    match = INLINE_LINK.search("[[ target ]]")
    assert match is not None
    assert match.group("target") == " target "
    assert match.group("description") is None

    # Target and description
    match = INLINE_LINK.search("[[target][description]]")
    assert match is not None
    assert match.group("target") == "target"
    assert match.group("description") == "description"

    # Spaces in target and description must not be stripped
    match = INLINE_LINK.search("[[ target ][ description ]]")
    assert match is not None
    assert match.group("target") == " target "
    assert match.group("description") == " description "

    # Newlines allowed in description
    match = INLINE_LINK.search("[[target][desc\nwith\nnewline]]")
    assert match is not None
    assert match.group("target") == "target"
    assert match.group("description") == "desc\nwith\nnewline"

    # Newline not allowed in target
    assert INLINE_LINK.search("[[tar\nget]]") is None


def test_inline_verbatim_regex() -> None:
    match = INLINE_VERBATIM.search("=a=")
    assert match is not None
    assert match.group("content") == "a"

    match = INLINE_VERBATIM.search("a =b=")
    assert match is not None
    assert match.group("content") == "b"

    # Preceding character must satisfy pre-boundary
    assert INLINE_VERBATIM.search("a=b=") is None

    # Following opening marker cannot be whitespace
    assert INLINE_VERBATIM.search("= a=") is None

    # Preceding closing marker cannot be whitespace
    assert INLINE_VERBATIM.search("=a =") is None

    # Verbatim cannot span newlines
    assert INLINE_VERBATIM.search("=a\nb=") is None


def test_inline_code_regex() -> None:
    match = INLINE_CODE.search("~a~")
    assert match is not None
    assert match.group("content") == "a"

    match = INLINE_CODE.search("a ~b~")
    assert match is not None
    assert match.group("content") == "b"

    assert INLINE_CODE.search("a~b~") is None
    assert INLINE_CODE.search("~ a~") is None
    assert INLINE_CODE.search("~a ~") is None
    assert INLINE_CODE.search("~a\nb~") is None


def test_inline_italic_regex() -> None:
    match = INLINE_ITALIC.search("/a/")
    assert match is not None
    assert match.group("content") == "a"

    match = INLINE_ITALIC.search("a /b/")
    assert match is not None
    assert match.group("content") == "b"

    assert INLINE_ITALIC.search("a/b/") is None
    assert INLINE_ITALIC.search("/ a/") is None
    assert INLINE_ITALIC.search("/a /") is None

    # Italic allows newlines
    match = INLINE_ITALIC.search("/a\nb/")
    assert match is not None
    assert match.group("content") == "a\nb"

    # Blank lines not allowed
    assert INLINE_ITALIC.search("/a\n\nb/") is None


def test_inline_bold_regex() -> None:
    match = INLINE_BOLD.search("*a*")
    assert match is not None
    assert match.group("content") == "a"

    match = INLINE_BOLD.search("a *b*")
    assert match is not None
    assert match.group("content") == "b"

    assert INLINE_BOLD.search("a*b*") is None
    assert INLINE_BOLD.search("* a*") is None
    assert INLINE_BOLD.search("*a *") is None

    # Bold allows newlines
    match = INLINE_BOLD.search("*a\nb*")
    assert match is not None
    assert match.group("content") == "a\nb"
    assert INLINE_BOLD.search("*a\n\nb*") is None


def test_inline_underline_regex() -> None:
    match = INLINE_UNDERLINE.search("_a_")
    assert match is not None
    assert match.group("content") == "a"

    match = INLINE_UNDERLINE.search("a _b_")
    assert match is not None
    assert match.group("content") == "b"

    # Snake_case variable protection
    assert INLINE_UNDERLINE.search("my_variable_name") is None
    assert INLINE_UNDERLINE.search("_ a_") is None
    assert INLINE_UNDERLINE.search("_a _") is None

    # Underline allows newlines
    match = INLINE_UNDERLINE.search("_a\nb_")
    assert match is not None
    assert match.group("content") == "a\nb"


def test_inline_strikethrough_regex() -> None:
    match = INLINE_STRIKETHROUGH.search("+a+")
    assert match is not None
    assert match.group("content") == "a"

    match = INLINE_STRIKETHROUGH.search("a +b+")
    assert match is not None
    assert match.group("content") == "b"

    assert INLINE_STRIKETHROUGH.search("a+b+") is None
    assert INLINE_STRIKETHROUGH.search("+ a+") is None
    assert INLINE_STRIKETHROUGH.search("+a +") is None

    # Strike-through allows newlines
    match = INLINE_STRIKETHROUGH.search("+a\nb+")
    assert match is not None
    assert match.group("content") == "a\nb"


def test_punctuation_boundaries() -> None:
    # Opening preceded by (, closing followed by )
    match = INLINE_BOLD.search("(*a*)")
    assert match is not None
    assert match.group("content") == "a"

    # Closing followed by punctuation
    for punct in [
        ".",
        ",",
        ";",
        ":",
        "!",
        "?",
        "'",
        '"',
        "-",
        "]",
        "}",
        "[",
        "\\",
    ]:
        match = INLINE_ITALIC.search(f"/a/{punct}")
        assert match is not None, f"Failed for /a/{punct}"
        assert match.group("content") == "a"

    # Opening preceded by punctuation
    for punct in ["-", "(", "{", "[", "'", '"']:
        match = INLINE_ITALIC.search(f"{punct}/a/")
        assert match is not None, f"Failed for {punct}/a/"
        assert match.group("content") == "a"
