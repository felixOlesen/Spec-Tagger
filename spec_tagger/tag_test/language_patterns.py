"""language_patterns.py:
Based on the crawled file extension, a specific regex pattern is used to identify function signatures.
When traversing lines, patterns for skipping lines are also identified (comments and decorators)

A key distinction also needs to be made between programming languages that have unique function names (e.g. python, rust, java)
versus languages that test using description-based signatures like with the JEST test framework.
"""

import re
from dataclasses import dataclass
from pathlib import Path

FRAMEWORKS = {
    "python.pytest": {
        "extensions": {".py"},
        "func": re.compile(r"^\s*(?:async\s+)?def\s+(test\w*)"),
        "class_pattern": re.compile(r"^\s*class\s+(\w+)"),
        "skip_prefixes": ("#", "@"),
        "block_style": None,
        "address_mode": "name",
        "test_format": "{file}::{line}",
        "detection": {
            "command_signals": [re.compile(r"\bpytest\b"), re.compile(r"-m\s+pytest\b")]
        },
    },
    "ruby.minitest": {
        "extensions": {".rb"},
        "func": re.compile(r"^\s*def\s+(test_\w*[?!]?)"),
        "skip_prefixes": ("#",),
        "block_style": None,
        "address_mode": "name",
        "test_format": "{file} -n /^{name}$/",
        "detection": {
            "command_signals": [
                re.compile(r"\bruby\b.*-Itest\b"),
                re.compile(r"\bminitest\b"),
            ]
        },
    },
    "ruby.rspec": {
        "extensions": {".rb"},
        "func": None,
        "skip_prefixes": ("#",),
        "block_style": "do_end",
        "describe": re.compile(r'^\s*(?:RSpec\.)?describe\s+["\']?(.+?)["\']?\s+do\b'),
        "example": re.compile(r'^\s*(?:it|specify)\s+["\'](.+?)["\']\s+do\b'),
        "address_mode": "file_line",
        "test_format": "{file}:{line}",
        "detection": {"command_signals": [re.compile(r"\brspec\b")]},
    },
    "js.jest": {
        "extensions": {".js", ".ts", ".jsx", ".tsx"},
        "func": None,
        "skip_prefixes": ("//",),
        "block_style": None,
        "describe": re.compile(r'^\s*describe\s*\(\s*["\'`](.+?)["\'`]'),
        "example": re.compile(r'^\s*(?:it|test)\s*\(\s*["\'`](.+?)["\'`]'),
        "address_mode": "name_pattern",
        "test_format": '{file} -t "{name}"',
        "detection": {"command_signals": [re.compile(r"\bjest\b")]},
    },
}


def framework_support_check(framework_name: str) -> bool:
    if framework_name in FRAMEWORKS:
        return True
    else:
        return False


def detect_framework(test_command: str) -> tuple[str | None, list[str]]:
    matches = []
    for fw, info in FRAMEWORKS.items():
        for p in info.get("detection", {}).get("command_signals", ()):
            if re.search(p, test_command):
                matches.append(fw)

    if not matches:
        return None, []

    return matches[0], matches
