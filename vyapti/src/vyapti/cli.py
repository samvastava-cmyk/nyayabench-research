"""Command-line entry points: ``vyapti-smoke`` and ``vyapti-run``."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv

from .client import ChatClient
from .judge import load_profile
from .pipeline import VyaptiPipeline
from .runner import SmokeTestFailure, run_arm, smoke_test, summarise
from .taxonomy import load_taxonomy


def _build_pipeline(args: argparse.Namespace) -> VyaptiPipeline:
    load_dotenv()
    taxonomy = load_taxonomy(args.taxonomy) if args.taxonomy else load_taxonomy()
    profile = load_profile(args.profile, taxonomy)
    client = ChatClient(
        provider=args.provider,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        concurrency=args.concurrency,
    )
    return VyaptiPipeline(
        client=client,
        profile=profile,
        taxonomy=taxonomy,
        use_arbitration=not args.no_arbitration,
    )


def _common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--provider", default="openai", help="openai | anthropic | google | deepseek")
    p.add_argument("--model", default="gpt-4.1")
    p.add_argument("--temperature", type=float, default=0.0,
                   help="always sent explicitly, for every provider")
    p.add_argument("--max-tokens", type=int, default=1000)
    p.add_argument("--concurrency", type=int, default=8)
    p.add_argument("--profile", default="reference",
                   help="prompt profile; only 'reference' ships with this repo")
    p.add_argument("--taxonomy", default=None)
    p.add_argument("--no-arbitration", action="store_true",
                   help="measure the judge unaided by stage 3")


def smoke_main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="vyapti-smoke", description="Verify the judge is usable.")
    _common(p)
    p.add_argument("--strict", action="store_true", help="also require correct labels")
    args = p.parse_args(argv)

    pipeline = _build_pipeline(args)
    print(f"fingerprint: {pipeline.fingerprint}")
    print(f"profile:     {pipeline.profile.name} ({pipeline.profile.line_count} lines, "
          f"sha256 {pipeline.profile.sha256[:12]})")
    print(f"taxonomy:    v{pipeline.taxonomy.version}, {len(pipeline.taxonomy)} categories")
    try:
        results = asyncio.run(smoke_test(pipeline, strict_labels=args.strict))
    except SmokeTestFailure as e:
        print(f"\nSMOKE TEST FAILED\n{e}", file=sys.stderr)
        return 1
    print()
    for r in results:
        mark = "ok " if r.final_label == r.gold_label else "  ~"
        print(f"  {mark} {r.case_id}: expected {r.gold_label.value:6} got "
              f"{r.final_label.value if r.final_label else '?':6} "
              f"conf={r.judge_verdict.confidence if r.judge_verdict else '-'} "
              f"({r.latency_ms:.0f} ms)")
    print("\nSMOKE TEST PASSED — judge reachable, contract honoured.")
    return 0


def run_main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="vyapti-run", description="Run one experimental arm.")
    _common(p)
    p.add_argument("suite", help="path to a JSONL suite, e.g. data/suites/unseen_v4.jsonl")
    p.add_argument("-o", "--output", required=True, help="JSONL results path (append/resume)")
    p.add_argument("--arm", default="A0")
    p.add_argument("--repeat", type=int, default=1)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--run-id", default=None)
    p.add_argument("--no-resume", action="store_true")
    p.add_argument("--skip-smoke", action="store_true",
                   help="not recommended; the smoke test costs 3 calls")
    args = p.parse_args(argv)

    pipeline = _build_pipeline(args)
    run_id = args.run_id or uuid.uuid4().hex[:12]
    print(f"run_id={run_id} arm={args.arm} repeat={args.repeat} "
          f"fingerprint={pipeline.fingerprint}")

    try:
        summary = asyncio.run(
            run_arm(
                pipeline,
                suite_path=args.suite,
                output_path=args.output,
                run_id=run_id,
                arm=args.arm,
                repeat=args.repeat,
                limit=args.limit,
                resume=not args.no_resume,
                run_smoke=not args.skip_smoke,
            )
        )
    except SmokeTestFailure as e:
        print(f"\nABORTED — {e}", file=sys.stderr)
        return 1

    print("\n--- arm summary ---")
    print(json.dumps(summary.as_dict(), indent=2))
    if Path(args.output).exists():
        print("\n--- metrics ---")
        print(json.dumps(summarise(args.output), indent=2, default=str)[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(run_main())
