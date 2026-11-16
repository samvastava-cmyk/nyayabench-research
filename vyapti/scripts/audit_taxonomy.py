#!/usr/bin/env python3
"""Report the taxonomy's own source-verification status.

The distinguishing claim of this project is that the taxonomy is textually
grounded and says so where it isn't. This script prints exactly which
categories are verbatim-attested in a primary source and which are our
extensions, so nobody has to take the README's word for it.

    python scripts/audit_taxonomy.py
    python scripts/audit_taxonomy.py --json
"""

from __future__ import annotations

import argparse
import json

from vyapti import load_taxonomy


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--taxonomy", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    tax = load_taxonomy(args.taxonomy)
    problems = tax.validate()

    if args.json:
        print(json.dumps({
            "version": tax.version,
            "n_categories": len(tax),
            "verified": [c.id for c in tax.verified()],
            "inferred": [c.id for c in tax.inferred()],
            "problems": problems,
            "primary_sources": [s["id"] for s in tax.primary_sources],
        }, indent=2))
        return 1 if problems else 0

    print(f"Hetvābhāsa taxonomy v{tax.version} — {len(tax)} categories\n")
    print(f"{'ID':8} {'BASIS':10} {'SOURCE':32} CATEGORY")
    print("-" * 100)
    for c in tax:
        basis = "VERIFIED" if c.is_verified else "INFERRED"
        print(f"{c.id:8} {basis:10} {c.source_text[:30]:32} {c.english[:44]}")

    v, i = len(tax.verified()), len(tax.inferred())
    print(f"\n{v} verbatim-attested, {i} inferred extension(s).")
    print("Inferred: " + ", ".join(c.id for c in tax.inferred()))
    print("\nPrimary sources:")
    for s in tax.primary_sources:
        print(f"  {s['id']:5} {s['full_name']} — {s.get('author', '?')}, {s.get('century', '?')}")

    if problems:
        print(f"\n{len(problems)} structural problem(s):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\nStructural self-check: clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
