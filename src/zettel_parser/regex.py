"""Reusable regular expressions for Org-mode syntax parsing."""

from __future__ import annotations

import re

PROPERTY_DRAWER_BEGIN_PATTERN: str = r"^[ \t]*:PROPERTIES:[ \t]*\r?$"
PROPERTY_DRAWER_END_PATTERN: str = r"^[ \t]*:END:[ \t]*\r?$"
NODE_PROPERTY_PATTERN: str = (
    r"^[ \t]*:(?!(?:END|PROPERTIES)\s*:)(?P<name>\S+?)(?P<append>\+)?:(?:[ \t]+(?P<value>.*?))?[ \t]*\r?$"
)

DRAWER_BEGIN_PATTERN: str = r"^[ \t]*:(?P<name>[a-zA-Z0-9_\-]+):[ \t]*\r?$"
DRAWER_END_PATTERN: str = r"^[ \t]*:END:[ \t]*\r?$"

INDENTATION_PATTERN: str = r"^[ \t]*"

PROPERTY_DRAWER_BEGIN: re.Pattern[str] = re.compile(
    PROPERTY_DRAWER_BEGIN_PATTERN, re.IGNORECASE)
PROPERTY_DRAWER_END: re.Pattern[str] = re.compile(PROPERTY_DRAWER_END_PATTERN,
                                                  re.IGNORECASE)
NODE_PROPERTY: re.Pattern[str] = re.compile(NODE_PROPERTY_PATTERN,
                                            re.IGNORECASE)

DRAWER_BEGIN: re.Pattern[str] = re.compile(DRAWER_BEGIN_PATTERN, re.IGNORECASE)
DRAWER_END: re.Pattern[str] = re.compile(DRAWER_END_PATTERN, re.IGNORECASE)

INDENTATION: re.Pattern[str] = re.compile(INDENTATION_PATTERN)

__all__ = [
    "DRAWER_BEGIN",
    "DRAWER_BEGIN_PATTERN",
    "DRAWER_END",
    "DRAWER_END_PATTERN",
    "INDENTATION",
    "INDENTATION_PATTERN",
    "NODE_PROPERTY",
    "NODE_PROPERTY_PATTERN",
    "PROPERTY_DRAWER_BEGIN",
    "PROPERTY_DRAWER_BEGIN_PATTERN",
    "PROPERTY_DRAWER_END",
    "PROPERTY_DRAWER_END_PATTERN",
]
