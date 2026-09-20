"""Tests for the inline pass parser."""

from __future__ import annotations

from zettel_parser.inline_pass import (
    Bold,
    Code,
    InlineLatex,
    Italic,
    Link,
    StrikeThrough,
    Underline,
    Verbatim,
    parse_inline,
)


def test_empty_string() -> None:
    assert parse_inline("") == []


def test_plain_unannotated_text() -> None:
    text = "Just a plain sentence with no markup.\n"
    assert parse_inline(text) == [text]


def test_unmatched_or_invalid_delimiters_remain_plain_text() -> None:
    cases = [
        "5 * 4 = 20",
        "= a=",
        "a=b=",
        "~ a~",
        "a~b~",
        "/ a/",
        "a/b/",
        "_ a_",
        "my_variable_name",
        "+ a+",
        "a+b+",
        "single * asterisk",
        "[[unclosed target",
        r"\(unclosed latex",
    ]
    for case in cases:
        assert parse_inline(case) == [case]


def test_precedence_latex_over_emphasis() -> None:
    # User example: /a \(b/ \) has inline LaTeX expression but no italic
    text = r"/a \(b/ \)"
    result = parse_inline(text)
    assert result == ["/a ", InlineLatex(content="b/ ")]
    assert str(result[1]) == r"\(b/ \)"

    # Bold marker crossing into LaTeX is rejected
    text2 = r"*a \(b* \)"
    assert parse_inline(text2) == ["*a ", InlineLatex(content="b* ")]

    # LaTeX starts inside and ends outside emphasis
    text3 = r"\(a /b\) c/"
    assert parse_inline(text3) == [InlineLatex(content="a /b"), " c/"]


def test_precedence_links_over_emphasis() -> None:
    # Italic crossing into link description
    text = "/a [[target][b/]]"
    result = parse_inline(text)
    assert result == ["/a ", Link(target="target", description=["b/"])]

    # Star in link description does not match with following star
    text2 = "[[target][desc*]] *after*"
    result2 = parse_inline(text2)
    assert result2 == [
        Link(target="target", description=["desc*"]),
        " ",
        Bold(elements=["after"]),
    ]


def test_emphasis_enclosing_latex_and_links() -> None:
    # Bold enclosing LaTeX
    text = r"*bold \(x\) bold*"
    result = parse_inline(text)
    assert result == [
        Bold(elements=["bold ", InlineLatex(content="x"), " bold"])
    ]
    assert str(result[0]) == text

    # Bold enclosing Link
    text2 = "*bold [[url][desc]] bold*"
    result2 = parse_inline(text2)
    assert result2 == [
        Bold(elements=["bold ", Link(target="url", description=["desc"]), " bold"])
    ]
    assert str(result2[0]) == text2


def test_latex_preserves_whitespace() -> None:
    result = parse_inline(r"\( a\)")
    assert result == [InlineLatex(content=" a")]
    assert isinstance(result[0], InlineLatex)
    assert result[0].content == " a"
    assert str(result[0]) == r"\( a\)"

    result2 = parse_inline(r"\(  \alpha + \beta  \)")
    assert result2 == [InlineLatex(content=r"  \alpha + \beta  ")]


def test_link_preserves_whitespace() -> None:
    # Target only with spaces
    result = parse_inline("[[ a ]]")
    assert result == [Link(target=" a ", description=None)]
    assert isinstance(result[0], Link)
    assert result[0].target == " a "
    assert result[0].description is None
    assert str(result[0]) == "[[ a ]]"

    # Target and description with spaces
    result2 = parse_inline("[[ a ][ b ]]")
    assert result2 == [Link(target=" a ", description=[" b "])]
    assert isinstance(result2[0], Link)
    assert result2[0].target == " a "
    assert result2[0].description == [" b "]
    assert str(result2[0]) == "[[ a ][ b ]]"


def test_multiline_support() -> None:
    # Italic, bold, underline, strike-through allow newlines
    assert parse_inline("/a\nb/") == [Italic(elements=["a\nb"])]
    assert parse_inline("*a\nb*") == [Bold(elements=["a\nb"])]
    assert parse_inline("_a\nb_") == [Underline(elements=["a\nb"])]
    assert parse_inline("+a\nb+") == [StrikeThrough(elements=["a\nb"])]

    # Inline LaTeX allows newlines
    assert parse_inline("\\(a\nb\\)") == [InlineLatex(content="a\nb")]

    # Link description allows newlines
    assert parse_inline("[[target][a\nb]]") == [
        Link(target="target", description=["a\nb"])
    ]

    # Verbatim and Code do NOT allow newlines
    assert parse_inline("=a\nb=") == ["=a\nb="]
    assert parse_inline("~a\nb~") == ["~a\nb~"]

    # Link target does NOT allow newlines
    assert parse_inline("[[a\nb]]") == ["[[a\nb]]"]


def test_verbatim_and_code_are_literal() -> None:
    text = "=foo *not bold* and /not italic/="
    result = parse_inline(text)
    assert result == [Verbatim(text="foo *not bold* and /not italic/")]
    assert str(result[0]) == text

    text2 = "~bar /not italic/ and _not underline_~"
    result2 = parse_inline(text2)
    assert result2 == [Code(text="bar /not italic/ and _not underline_")]
    assert str(result2[0]) == text2

    # Links and LaTeX take precedence over verbatim
    assert parse_inline(r"=\(x\)=") == ["=", InlineLatex(content="x"), "="]
    assert parse_inline("=[[target]]=") == ["=", Link(target="target"), "="]


def test_nested_emphasis() -> None:
    text = "hello *bold /italic/ bold* world"
    result = parse_inline(text)
    assert result == [
        "hello ",
        Bold(elements=["bold ", Italic(elements=["italic"]), " bold"]),
        " world",
    ]
    assert "".join(str(element) for element in result) == text


def test_nested_in_link_description() -> None:
    text = r"[[https://example.com][visit *bold* and \(x\)]]"
    result = parse_inline(text)
    assert result == [
        Link(
            target="https://example.com",
            description=[
                "visit ",
                Bold(elements=["bold"]),
                " and ",
                InlineLatex(content="x"),
            ],
        )
    ]
    assert str(result[0]) == text


def test_all_elements_roundtrip() -> None:
    elements = [
        InlineLatex(content=" x "),
        Link(target="url", description=["desc"]),
        Link(target="url_only"),
        Verbatim(text="verb"),
        Code(text="code"),
        Bold(elements=["b"]),
        Italic(elements=["i"]),
        Underline(elements=["u"]),
        StrikeThrough(elements=["s"]),
    ]
    expected_strs = [
        r"\( x \)",
        "[[url][desc]]",
        "[[url_only]]",
        "=verb=",
        "~code~",
        "*b*",
        "/i/",
        "_u_",
        "+s+",
    ]
    for el, exp in zip(elements, expected_strs, strict=True):
        assert str(el) == exp
