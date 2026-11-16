#!/usr/bin/env python3
"""Scan a tree for credential-shaped strings.

Run before every push. Wired into CI and into the pre-commit hook.

Context: two live API keys reached the Phase 1 repository — an Emergent key in
``README.md`` and a Google key captured inside logged 429 URLs in a benchmark
results JSON. Neither was noticed for months. This script is the standing
answer to that.

Usage
-----
    python scripts/secret_scan.py .
    python scripts/secret_scan.py . --fail-on-finding
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("OpenAI key", re.compile(r"sk-(?!ant-|emergent-)[A-Za-z0-9_\-]{20,}")),
    ("OpenAI project key", re.compile(r"sk-proj-[A-Za-z0-9_\-]{20,}")),
    ("Anthropic key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("Google API key", re.compile(r"AIza[0-9A-Za-z_\-]{35}")),
    ("Emergent key", re.compile(r"sk-emergent-[A-Za-z0-9_\-]{6,}")),
    ("DeepSeek key", re.compile(r"\bsk-[0-9a-f]{32}\b")),
    ("HuggingFace token", re.compile(r"hf_[A-Za-z0-9]{30,}")),
    ("GitHub token", re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}")),
    ("AWS access key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("Slack token", re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}")),
    ("Mongo URI with credentials", re.compile(r"mongodb(?:\+srv)?://[^\s:\"']+:[^\s@\"']+@")),
    ("Private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("Bearer literal", re.compile(r"Bearer\s+[A-Za-z0-9_\-\.]{25,}")),
]

PLACEHOLDER = re.compile(r"(YOUR[_ ]|xxx|XXX|<[^>]+>|example|placeholder|REDACT|\bdummy\b|\.\.\.)", re.I)

SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", ".pytest_cache",
             ".ruff_cache", "build", "dist", ".mypy_cache"}
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz", ".tar", ".whl",
            ".so", ".dylib", ".woff", ".woff2", ".ico"}
# This file necessarily contains the patterns it looks for.
SELF = os.path.basename(__file__)


def scan(root: str) -> list[dict]:
    findings = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn == SELF or os.path.splitext(fn)[1].lower() in SKIP_EXT:
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path, encoding="utf-8", errors="ignore") as f:
                    for lineno, line in enumerate(f, 1):
                        for name, pat in PATTERNS:
                            for m in pat.finditer(line):
                                tok = m.group(0)
                                if PLACEHOLDER.search(tok):
                                    continue
                                findings.append({
                                    "file": os.path.relpath(path, root),
                                    "line": lineno,
                                    "type": name,
                                    "masked": tok[:10] + "…" + tok[-4:],
                                })
            except OSError:
                continue
    return findings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Scan a tree for credential-shaped strings.")
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--fail-on-finding", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    findings = scan(args.root)

    if args.json:
        print(json.dumps(findings, indent=2))
    elif not findings:
        print(f"clean — no credential-shaped strings under {args.root}")
    else:
        print(f"{len(findings)} potential credential(s) found:\n", file=sys.stderr)
        for f in findings:
            print(f"  {f['file']}:{f['line']}  {f['type']}  {f['masked']}", file=sys.stderr)
        print("\nRevoke each key at the provider before doing anything else. "
              "Removing it from the working tree does not remove it from git history.",
              file=sys.stderr)

    return 1 if (findings and args.fail_on_finding) else 0


if __name__ == "__main__":
    raise SystemExit(main())
