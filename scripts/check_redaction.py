from __future__ import annotations

import argparse
import re
from pathlib import Path


FORBIDDEN_LITERAL_TERMS = [
    "Advan" + "tage",
    "But" + "ler",
    "Out" + "look",
    "G" + "mail",
    "Tele" + "gram",
    "/Us" + "ers/",
    "fro" + "bertomaya",
    "cl" + "awd",
]

PATTERNS = {
    "email_address": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "phone_number": re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})\b"),
    "ipv4_address": re.compile(r"\b(?:10|127|172\.(?:1[6-9]|2\d|3[01])|192\.168|\d{1,3})\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
    "mac_address": re.compile(r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b"),
    "coordinate_pair": re.compile(r"\b-?\d{1,2}\.\d{4,}\s*,\s*-?\d{1,3}\.\d{4,}\b"),
}

SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
TEXT_SUFFIXES = {
    ".csv",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".gitignore",
}


def iter_files(root: Path):
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and (path.suffix in TEXT_SUFFIXES or path.name == ".gitignore"):
            yield path


def check_file(path: Path, root: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    relative = path.relative_to(root)
    findings: list[str] = []

    for term in FORBIDDEN_LITERAL_TERMS:
        if term in text:
            findings.append(f"{relative}: forbidden literal {term!r}")

    for name, pattern in PATTERNS.items():
        for match in pattern.finditer(text):
            findings.append(f"{relative}: {name} pattern {match.group(0)!r}")

    return findings


def run(root: Path) -> list[str]:
    findings: list[str] = []
    for path in iter_files(root):
        findings.extend(check_file(path, root))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan the public demo repo for obvious private identifiers.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)

    findings = run(args.root)
    if findings:
        print("REDACTION CHECK FAILED")
        for finding in findings:
            print(f"- {finding}")
        return 1

    print("REDACTION CHECK PASSED: no forbidden literals or obvious private identifier patterns found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
