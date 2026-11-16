#!/usr/bin/env python3
"""Experiment 1 — the NONE ablation ladder.

The question Phase 2 exists to answer:

    Does specificity clear 65% with recall holding at or above 93%?

Design: 5 arms × 200 cases × 3 independent repeats = 3,000 calls (~$30).
Each arm differs only in how many sound-argument (NONE) exemplars the prompt
profile carries. The August pilot moved specificity 30.8% → 38.5% with 8
exemplars but had 7 discordant pairs and p = 0.13; this design is powered.

    A0   2 exemplars   3.0% of budget   (the v10 baseline)
    A1   8             11%
    A2  16             20%
    A3  24             27%
    A4  32             33%   — matches the 32.5% real-world prevalence

Arms are read from ``$VYAPTI_PROMPT_DIR`` as ``<arm>.txt``. The profiles are
not distributed; see prompts/README.md.

    python scripts/experiment1_ladder.py --suite data/suites/mafalda_200.jsonl \\
        --arms A0 A1 A2 A3 A4 --repeats 3 --out runs/exp1
"""

from __future__ import annotations

import argparse
import asyncio
import json
import uuid
from pathlib import Path

from dotenv import load_dotenv

from vyapti import ChatClient, VyaptiPipeline, load_profile, load_taxonomy
from vyapti.runner import SmokeTestFailure, run_arm, summarise


async def ladder(args: argparse.Namespace) -> int:
    load_dotenv()
    taxonomy = load_taxonomy()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    run_id = args.run_id or uuid.uuid4().hex[:12]

    index: dict[str, dict] = {}
    for arm in args.arms:
        try:
            profile = load_profile(arm, taxonomy)
        except FileNotFoundError as e:
            print(f"\n[{arm}] {e}")
            print("Set VYAPTI_PROMPT_DIR to the directory holding the arm profiles.")
            return 1

        for repeat in range(1, args.repeats + 1):
            client = ChatClient(
                provider=args.provider,
                model=args.model,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
                concurrency=args.concurrency,
            )
            pipeline = VyaptiPipeline(client, profile, taxonomy,
                                      use_arbitration=not args.no_arbitration)
            path = out_dir / f"{arm}_r{repeat}.jsonl"
            print(f"\n=== {arm} repeat {repeat} — {profile.line_count} prompt lines, "
                  f"sha {profile.sha256[:12]} ===")
            try:
                summary = await run_arm(
                    pipeline,
                    suite_path=args.suite,
                    output_path=path,
                    run_id=run_id,
                    arm=arm,
                    repeat=repeat,
                    limit=args.limit,
                )
            except SmokeTestFailure as e:
                print(f"ABORTED before spending budget: {e}")
                return 1

            metrics = summarise(path)
            index[f"{arm}_r{repeat}"] = {
                "arm": arm,
                "repeat": repeat,
                "prompt_sha256": profile.sha256,
                "file": str(path),
                "summary": summary.as_dict(),
                "metrics": metrics,
            }
            b = metrics["binary"]
            print(f"  precision {b['precision']}  recall {b['recall']}  "
                  f"specificity {b['specificity']}  F1 {b['f1']}")
            # Save after every arm. The August runs were lost twice.
            (out_dir / "index.json").write_text(json.dumps(index, indent=2, default=str))

    print("\n=== ladder complete ===")
    print(f"{'arm':6} {'rep':>4} {'prec':>7} {'recall':>7} {'spec':>7} {'F1':>7}  gate")
    for key, v in index.items():
        b = v["metrics"]["binary"]
        gate = "PASS" if (b["specificity"] >= 65.0 and b["recall"] >= 93.0) else "—"
        print(f"{v['arm']:6} {v['repeat']:4} {b['precision']:7.2f} {b['recall']:7.2f} "
              f"{b['specificity']:7.2f} {b['f1']:7.2f}  {gate}")
    print(f"\nindex written to {out_dir / 'index.json'}")
    print("Gate: specificity >= 65% with recall >= 93%.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", required=True)
    ap.add_argument("--arms", nargs="+", default=["A0", "A1", "A2", "A3", "A4"])
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--out", default="runs/exp1")
    ap.add_argument("--provider", default="openai")
    ap.add_argument("--model", default="gpt-4.1")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--max-tokens", type=int, default=1000)
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--no-arbitration", action="store_true")
    return asyncio.run(ladder(ap.parse_args(argv)))


if __name__ == "__main__":
    raise SystemExit(main())
