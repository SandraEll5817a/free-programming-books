#!/usr/bin/env python3
"""
fpb-lint.py - Linter for free-programming-books markdown files.

Checks for common formatting issues such as:
  - Duplicate links
  - Incorrect link formatting
  - Alphabetical ordering within sections
  - Trailing whitespace
  - Missing or malformed section headers

Usage:
    python scripts/fpb-lint.py [file ...]
"""

import re
import sys
from pathlib import Path

# Regex patterns
LINK_PATTERN = re.compile(r'\* \[(.+?)\]\((.+?)\)(.*)')
SECTION_HEADER_PATTERN = re.compile(r'^#{1,4} .+')
TRAILING_WHITESPACE_PATTERN = re.compile(r'[ \t]+$')


def check_trailing_whitespace(lines: list[str], filename: str) -> list[str]:
    """Check for trailing whitespace on each line."""
    errors = []
    for i, line in enumerate(lines, start=1):
        if TRAILING_WHITESPACE_PATTERN.search(line.rstrip('\n')):
            errors.append(f"{filename}:{i}: trailing whitespace found")
    return errors


def check_duplicate_links(lines: list[str], filename: str) -> list[str]:
    """Check for duplicate URLs within the file."""
    errors = []
    seen_urls: dict[str, int] = {}
    for i, line in enumerate(lines, start=1):
        match = LINK_PATTERN.match(line.strip())
        if match:
            url = match.group(2)
            if url in seen_urls:
                errors.append(
                    f"{filename}:{i}: duplicate URL '{url}' "
                    f"(first seen at line {seen_urls[url]})"
                )
            else:
                seen_urls[url] = i
    return errors


def check_link_format(lines: list[str], filename: str) -> list[str]:
    """Check that links follow the expected markdown format."""
    errors = []
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        # Lines that look like list items but don't match the expected pattern
        if stripped.startswith('* ') and '[' in stripped:
            if not LINK_PATTERN.match(stripped):
                errors.append(
                    f"{filename}:{i}: malformed link entry: {stripped!r}"
                )
    return errors


def check_alphabetical_order(lines: list[str], filename: str) -> list[str]:
    """Check that entries within a section are in alphabetical order.

    Note: comparison is case-insensitive, which handles mixed-case titles
    like '(e)Book' or 'iOS' more gracefully.
    """
    errors = []
    section_entries: list[tuple[int, str]] = []

    def flush_section(entries: list[tuple[int, str]]) -> list[str]:
        section_errors = []
        titles = [title.lower() for _, title in entries]
        for idx in range(1, len(titles)):
            if titles[idx] < titles[idx - 1]:
                lineno, title = entries[idx]
                prev_title = entries[idx - 1][1]
                section_errors.append(
                    f"{filename}:{lineno}: '{title}' should come before "
                    f"'{prev_title}' (alphabetical order)"
                )
        return section_errors

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if SECTION_HEADER_PATTERN.match(stripped):
            if sect