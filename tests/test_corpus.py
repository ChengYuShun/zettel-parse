"""File-based tests over the editable corpus in ``tests/corpus``.

Every ``*.org`` file in that directory is discovered automatically.  Each one
is checked with an exact source round-trip through the first pass and a
structure snapshot of the full AST.  Add or edit corpus files freely, then
refresh the snapshots with ``pytest --snapshot-update``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from syrupy.assertion import SnapshotAssertion
from syrupy.extensions.amber import AmberSnapshotExtension

from zettel_parser.first_pass import parse_first_pass
from zettel_parser.serialization import to_org, to_text, to_xml
from zettel_parser.structure_pass import parse

etree = pytest.importorskip("lxml.etree")

SCHEMA_PATH = Path(__file__).parents[1] / "docs" / "zettel.xsd"

CORPUS_DIR = Path(__file__).parent / "corpus"
ORG_FILES = sorted(CORPUS_DIR.glob("*.org"))

if not ORG_FILES:
    pytest.skip("no corpus files yet", allow_module_level=True)


@pytest.fixture(scope="module")
def xml_schema() -> object:
    """The compiled schema shared by the schema tests below."""
    return etree.XMLSchema(etree.parse(str(SCHEMA_PATH)))


class RawTextSnapshotExtension(AmberSnapshotExtension):
    """Store strings verbatim so snapshots read as the AST outline itself."""

    def serialize(self, data: Any, **kwargs: Any) -> str:
        if isinstance(data, str):
            return data
        return super().serialize(data, **kwargs)


@pytest.fixture
def ast_snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """A snapshot that writes raw text instead of a quoted representation."""
    return snapshot.use_extension(RawTextSnapshotExtension)


def _roundtrip_first_pass(source: str) -> str:
    """Reconstruct the source text (lossless) from the first-pass elements."""
    return "".join(str(element) for element in parse_first_pass(source))


def _roundtrip_parse(source: str) -> str:
    """Reconstruct the source text (lossy) from `parse`."""
    return to_org(parse(source))


@pytest.mark.parametrize("org_file", ORG_FILES, ids=lambda path: path.stem)
def test_first_pass_roundtrips(org_file: Path) -> None:
    """The first pass must reproduce the source text exactly."""
    source = org_file.read_text(encoding="utf-8")
    assert _roundtrip_first_pass(source) == source


@pytest.mark.parametrize("org_file", ORG_FILES, ids=lambda path: path.stem)
def test_structure_snapshot(
    org_file: Path, ast_snapshot: SnapshotAssertion
) -> None:
    """Parsing sample files must give the same result the committed snapshot."""
    source = org_file.read_text(encoding="utf-8")
    assert ast_snapshot == to_text(parse(source))


@pytest.mark.parametrize("org_file", ORG_FILES, ids=lambda path: path.stem)
def test_reparse_is_stable(org_file: Path) -> None:
    """Reparsing the file must give the same result."""
    source = org_file.read_text(encoding="utf-8")
    assert _roundtrip_parse(source) == _roundtrip_parse(_roundtrip_parse(source))


@pytest.mark.parametrize("org_file", ORG_FILES, ids=lambda path: path.stem)
def test_xml_matches_schema(org_file: Path, xml_schema: object) -> None:
    """Every corpus document must serialize to schema-valid XML."""
    source = org_file.read_text(encoding="utf-8")
    document = etree.fromstring(to_xml(parse(source)).encode("utf-8"))
    xml_schema.assertValid(document)
