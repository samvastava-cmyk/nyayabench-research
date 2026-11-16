"""Experiment harness: smoke test, crash-safe execution, resume, metrics.

Every rule encoded here was bought with a lost Phase 1 run.

1. **Smoke test before every run.** Three known cases. If the judge is
   unreachable or the profile is wrong, abort in seconds rather than
   discovering it after 3,000 calls.
2. **Append-and-flush after every case.** The August runs were lost twice.
   Results are written as JSON Lines, flushed per case, and a re-run of the
   same output file resumes from the case IDs already present.
3. **Never truncate.** Full response text, finish reason, token counts and
   latency go to disk. Three-hundred-character previews cost the Phase 1
   human-verification study.
"""

from __future__ import annotations

import asyncio
import json
import os
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

from .pipeline import VyaptiPipeline
from .schemas import CaseResult, RFCode

# Three arguments with unambiguous, hand-checked labels drawn from the
# classical sources, not from any released suite.
SMOKE_CASES: tuple[tuple[str, RFCode], ...] = (
    (
        "The mountain has fire, because it is knowable.",
        RFCode.RF_01,  # knowability holds of the kitchen and the lake alike
    ),
    (
        "Sound is eternal, because it is audible.",
        RFCode.RF_02,  # audibility belongs to sound and nothing else
    ),
    (
        "All humans are mortal. Socrates is a human. Therefore Socrates is mortal.",
        RFCode.NONE,  # a sound argument must be recognisable as one
    ),
)


class SmokeTestFailure(RuntimeError):
    """The judge is not answering usefully. Abort before spending the budget."""


async def smoke_test(pipeline: VyaptiPipeline, strict_labels: bool = False) -> list[CaseResult]:
    """Verify the judge is reachable and returning parseable verdicts.

    ``strict_labels=False`` by default: the gate is *liveness and contract*,
    not accuracy. A reference profile that answers RF-07a instead of RF-01 is
    working; a profile that errors, or that answers NONE to all three, is not.
    """
    results = [await pipeline.classify(t, case_id=f"SMOKE-{i}", suite="smoke", gold_label=g)
               for i, (t, g) in enumerate(SMOKE_CASES, 1)]

    errors = [r for r in results if r.status == "error"]
    if errors:
        detail = "; ".join(f"{r.case_id}: {r.error_type}: {r.error_detail}" for r in errors)
        raise SmokeTestFailure(f"smoke test failed — judge not usable. {detail}")

    labels = {r.final_label for r in results}
    if labels == {RFCode.NONE}:
        raise SmokeTestFailure(
            "smoke test returned NONE for all three cases including two known failures — "
            "the profile is almost certainly not being applied."
        )
    if strict_labels:
        wrong = [r for r in results if r.final_label != r.gold_label]
        if wrong:
            raise SmokeTestFailure(
                "strict smoke test: "
                + "; ".join(f"{r.case_id} expected {r.gold_label} got {r.final_label}" for r in wrong)
            )
    return results


def load_suite(path: str | Path, limit: int | None = None) -> list[dict[str, Any]]:
    """Read a JSONL suite."""
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
            if limit and len(rows) >= limit:
                break
    return rows


def _completed_ids(path: str | Path) -> set[str]:
    p = Path(path)
    if not p.exists():
        return set()
    done = set()
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue  # a torn final line from a crash; it will be redone
            if rec.get("status") == "ok":
                done.add(rec["case_id"])
    return done


@dataclass
class ArmSummary:
    arm: str
    repeat: int
    n_total: int = 0
    n_ok: int = 0
    n_error: int = 0
    label_counts: Counter = field(default_factory=Counter)
    errors: Counter = field(default_factory=Counter)

    def as_dict(self) -> dict[str, Any]:
        return {
            "arm": self.arm,
            "repeat": self.repeat,
            "n_total": self.n_total,
            "n_ok": self.n_ok,
            "n_error": self.n_error,
            "label_counts": dict(self.label_counts),
            "errors": dict(self.errors),
        }


async def run_arm(
    pipeline: VyaptiPipeline,
    suite_path: str | Path,
    output_path: str | Path,
    *,
    run_id: str,
    arm: str,
    repeat: int = 1,
    limit: int | None = None,
    resume: bool = True,
    run_smoke: bool = True,
    progress_every: int = 25,
) -> ArmSummary:
    """Execute one experimental arm, crash-safe and resumable."""
    if run_smoke:
        await smoke_test(pipeline)

    rows = load_suite(suite_path, limit=limit)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    done = _completed_ids(out) if resume else set()
    todo = [r for r in rows if r["id"] not in done]

    summary = ArmSummary(arm=arm, repeat=repeat, n_total=len(rows))
    summary.n_ok = len(done)

    lock = asyncio.Lock()
    fh = open(out, "a", encoding="utf-8")

    async def one(row: dict[str, Any]) -> None:
        gold = row.get("label")
        result = await pipeline.classify(
            row["text"],
            case_id=row["id"],
            suite=row.get("suite", Path(suite_path).stem),
            gold_label=RFCode(gold) if gold else None,
            run_id=run_id,
            arm=arm,
            repeat=repeat,
        )
        async with lock:
            fh.write(result.model_dump_json() + "\n")
            fh.flush()
            os.fsync(fh.fileno())
            if result.status == "ok":
                summary.n_ok += 1
                summary.label_counts[result.final_label.value if result.final_label else "?"] += 1
            else:
                summary.n_error += 1
                summary.errors[result.error_type or "unknown"] += 1
            processed = summary.n_ok + summary.n_error
            if progress_every and processed % progress_every == 0:
                print(f"  [{arm} r{repeat}] {processed}/{len(rows)}  errors={summary.n_error}", flush=True)

    try:
        await asyncio.gather(*(one(r) for r in todo))
    finally:
        fh.close()

    return summary


# --------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------


def binary_metrics(results: Iterable[CaseResult | dict[str, Any]]) -> dict[str, float]:
    """Flag-vs-sound metrics — the numbers Phase 2's gate is written against.

    Positive class = "this argument has a structural failure" (any RF code).
    Specificity is reported explicitly because it is the defect: the Phase 1
    classifier reaches 97–100% recall at 33–37% specificity, which is a
    screening instrument, not a gate.
    """
    tp = fp = tn = fn = 0
    for r in results:
        d = r if isinstance(r, dict) else r.model_dump()
        if d.get("status") != "ok":
            continue
        gold, pred = d.get("gold_label"), d.get("final_label")
        if gold is None or pred is None:
            continue
        gold_pos, pred_pos = gold != "NONE", pred != "NONE"
        if gold_pos and pred_pos:
            tp += 1
        elif not gold_pos and pred_pos:
            fp += 1
        elif not gold_pos and not pred_pos:
            tn += 1
        else:
            fn += 1

    def _safe(a: int, b: int) -> float:
        return round(100 * a / b, 2) if b else 0.0

    precision = _safe(tp, tp + fp)
    recall = _safe(tp, tp + fn)
    f1 = round(2 * precision * recall / (precision + recall), 2) if (precision + recall) else 0.0
    return {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision": precision,
        "recall": recall,
        "specificity": _safe(tn, tn + fp),
        "f1": f1,
        "accuracy": _safe(tp + tn, tp + fp + tn + fn),
    }


def typed_accuracy(results: Iterable[CaseResult | dict[str, Any]]) -> dict[str, Any]:
    """Exact-label accuracy over cases where a failure was correctly flagged."""
    correct = total = 0
    per_cat: dict[str, list[int]] = {}
    for r in results:
        d = r if isinstance(r, dict) else r.model_dump()
        if d.get("status") != "ok":
            continue
        gold, pred = d.get("gold_label"), d.get("final_label")
        if not gold or gold == "NONE" or pred is None:
            continue
        total += 1
        hit = int(gold == pred)
        correct += hit
        per_cat.setdefault(gold, [0, 0])
        per_cat[gold][0] += hit
        per_cat[gold][1] += 1
    return {
        "typed_accuracy": round(100 * correct / total, 2) if total else 0.0,
        "correct": correct,
        "total": total,
        "per_category": {
            k: {"correct": v[0], "total": v[1], "accuracy": round(100 * v[0] / v[1], 2)}
            for k, v in sorted(per_cat.items())
        },
    }


def label_share(results: Iterable[CaseResult | dict[str, Any]]) -> dict[str, float]:
    """Share of predictions per label. RF-01's share is the Experiment 2 target."""
    c: Counter = Counter()
    for r in results:
        d = r if isinstance(r, dict) else r.model_dump()
        if d.get("status") == "ok" and d.get("final_label"):
            c[d["final_label"]] += 1
    n = sum(c.values())
    return {k: round(100 * v / n, 2) for k, v in sorted(c.items())} if n else {}


def confidence_split(results: Iterable[CaseResult | dict[str, Any]]) -> dict[str, Any]:
    """Mean judge confidence on false positives vs true negatives.

    Phase 1 measured 0.906 on false positives against 0.946 on correct
    negatives — the classifier is confidently wrong, which is why confidence
    thresholding does not fix specificity. Re-measure this every arm.
    """
    fp_conf, tn_conf = [], []
    for r in results:
        d = r if isinstance(r, dict) else r.model_dump()
        if d.get("status") != "ok" or not d.get("judge_verdict"):
            continue
        gold, pred = d.get("gold_label"), d.get("final_label")
        conf = (d.get("judge_verdict") or {}).get("confidence")
        if gold != "NONE" or pred is None or conf is None:
            continue
        (fp_conf if pred != "NONE" else tn_conf).append(conf)

    def _mean(xs: Sequence[float]) -> float | None:
        return round(sum(xs) / len(xs), 4) if xs else None

    return {
        "mean_confidence_false_positive": _mean(fp_conf),
        "n_false_positive": len(fp_conf),
        "mean_confidence_true_negative": _mean(tn_conf),
        "n_true_negative": len(tn_conf),
    }


def summarise(path: str | Path) -> dict[str, Any]:
    """Full metric block for one results file."""
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    return {
        "file": str(path),
        "n_records": len(rows),
        "n_errors": sum(1 for r in rows if r.get("status") != "ok"),
        "binary": binary_metrics(rows),
        "typed": typed_accuracy(rows),
        "label_share": label_share(rows),
        "confidence": confidence_split(rows),
    }
