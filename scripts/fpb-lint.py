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
    """Check that entries within a section are in alphabetical order."""
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
            if section_entries:
                errors.extend(flush_section(section_entries))
            section_entries = []
        else:
            match = LINK_PATTERN.match(stripped)
            if match:
                title = match.group(1)
                section_entries.append((i, title))

    if section_entries:
        errors.extend(flush_section(section_entries))

    return errors


def lint_file(filepath: str) -> list[str]:
    """Run all lint checks on a single file and return a list of error messages."""
    path = Path(filepath)
    if not path.exists():
        return [f"ERROR: File not found: {filepath}"]
    if path.suffix.lower() != '.md':
        return [f"SKIP: Not a markdown file: {filepath}"]

    lines = path.read_text(encoding='utf-8').splitlines(keepends=True)
    errors: list[str] = []

    errors.extend(check_trailing_whitespace(lines, filepath))
    errors.extend(check_duplicate_links(lines, filepath))
    errors.extend(check_link_format(lines, filepath))
    errors.extend(check_alphabetical_order(lines, filepath))

    return errors


def main() -> int:
    """Entry point. Returns exit code 0 if no errors, 1 otherwise."""
    files = sys.argv[1:]
    if not files:
        print("Usage: fpb-lint.py <file.md> [file.md ...]")
        return 1

    all_errors: list[str] = []
    for f in files:
        all_errors.extend(lint_file(f))

    if all_errors:
        for error in all_errors:
            print(error)
        print(f"\n{len(all_errors)} issue(s) found.")
        return 1

    print("No issues found.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
