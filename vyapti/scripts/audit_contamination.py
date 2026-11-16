#!/usr/bin/env python3
"""Audit a suite for verbatim overlap with a reference corpus.

Standing Phase 2 rule: no new test set is reported on until it has been run
through this. The reference corpus is normally the prompt profile in use —
which for the production profile lives outside this repository, so point
``--reference`` at it.

    # is the v4 suite contaminated with the reference prompt?
    python scripts/audit_contamination.py data/suites/unseen_v4.jsonl \\
        --reference-profile reference

    # against an external prompt file
    python scripts/audit_contamination.py data/suites/unseen_v4.jsonl \\
        --reference /path/to/production.txt

    # how much do the released suites leak into each other?
    python scripts/audit_contamination.py --cross-suite
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

from vyapti.contamination import audit_suite, cross_suite_overlap
from vyapti.judge import load_profile

ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("suite", nargs="?", help="path to a JSONL suite")
    ap.add_argument("--reference", help="text file to treat as the reference corpus")
    ap.add_argument("--reference-profile", help="prompt profile name to use as reference")
    ap.add_argument("-n", type=int, default=6, help="n-gram size (default 6)")
    ap.add_argument("--threshold", type=float, default=50.0,
                    help="%% of a case's n-grams present in the reference before flagging")
    ap.add_argument("--cross-suite", action="store_true",
                    help="pairwise overlap between all released suites")
    ap.add_argument("--self-check", action="store_true",
                    help="audit every suite against the reference profile")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if args.cross_suite:
        paths = sorted(glob.glob(str(ROOT / "data" / "suites" / "*.jsonl")))
        out = cross_suite_overlap(paths, n=args.n)
        if args.json:
            print(json.dumps(out, indent=2))
        else:
            print(f"pairwise {args.n}-gram overlap between released suites\n")
            for pair, v in sorted(out.items(), key=lambda x: -x[1]["jaccard"])[:25]:
                print(f"  {v['jaccard']:.4f}  {v['shared_ngrams']:6}  {pair}")
        return 0

    def reference_texts() -> list[str]:
        if args.reference:
            return [Path(args.reference).read_text(encoding="utf-8")]
        name = args.reference_profile or "reference"
        return [load_profile(name).template]

    if args.self_check:
        refs = reference_texts()
        rows = []
        for p in sorted(glob.glob(str(ROOT / "data" / "suites" / "*.jsonl"))):
            r = audit_suite(p, refs, n=args.n, flag_threshold=args.threshold)
            rows.append(r)
        if args.json:
            print(json.dumps([{k: v for k, v in r.items() if k != "per_case"} for r in rows], indent=2))
        else:
            print(f"{'suite':24} {'cases':>6} {'flagged':>8} {'mean%':>7} {'max%':>7}")
            for r in rows:
                print(f"{Path(r['suite']).stem:24} {r['n_cases']:6} "
                      f"{r['n_flagged']:8} {r['mean_overlap_pct']:7.2f} {r['max_overlap_pct']:7.2f}")
        return 0

    if not args.suite:
        ap.error("give a suite path, or use --cross-suite / --self-check")

    report = audit_suite(args.suite, reference_texts(), n=args.n, flag_threshold=args.threshold)
    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    print(f"suite:            {report['suite']}")
    print(f"n-gram size:      {report['n_gram_size']}")
    print(f"flag threshold:   {report['flag_threshold_pct']}% of a case's n-grams")
    print(f"cases:            {report['n_cases']}")
    print(f"flagged:          {report['n_flagged']} ({report['flagged_pct']}%)")
    print(f"mean overlap:     {report['mean_overlap_pct']}%")
    print(f"max overlap:      {report['max_overlap_pct']}%")
    if report["flagged_ids"]:
        print("\nflagged ids:", ", ".join(report["flagged_ids"][:40]))
        print("\nReport the contamination-free figure alongside the raw one.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
