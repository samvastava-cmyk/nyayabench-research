"""N-gram contamination auditing.

Any accuracy figure reported on a suite that shares verbatim spans with the
prompt is inflated by an unknown amount. The ICON paper concedes 8.3% verbatim
contamination between the v4 held-out suite and the calibrated prompt, and
reports a contamination-free figure alongside the raw one. This module is how
that number is produced, so anyone can recompute it.

Rule for Phase 2: no new suite is reported on until it has been audited here.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

_TOKEN = re.compile(r"[a-z0-9']+")


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall((text or "").lower())


def ngrams(tokens: list[str], n: int) -> set[tuple[str, ...]]:
    if len(tokens) < n:
        return set()
    return {tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def overlap_report(
    candidate: str,
    reference_ngrams: set[tuple[str, ...]],
    n: int = 6,
) -> dict[str, Any]:
    """How much of ``candidate`` already appears in the reference corpus."""
    toks = tokenize(candidate)
    cand = ngrams(toks, n)
    if not cand:
        return {"n": n, "candidate_ngrams": 0, "shared": 0, "overlap_pct": 0.0, "examples": []}
    shared = cand & reference_ngrams
    return {
        "n": n,
        "candidate_ngrams": len(cand),
        "shared": len(shared),
        "overlap_pct": round(100 * len(shared) / len(cand), 2),
        "examples": [" ".join(g) for g in list(shared)[:5]],
    }


def build_reference(texts: Iterable[str], n: int = 6) -> set[tuple[str, ...]]:
    ref: set[tuple[str, ...]] = set()
    for t in texts:
        ref |= ngrams(tokenize(t), n)
    return ref


def audit_suite(
    suite_path: str | Path,
    reference_texts: Iterable[str],
    n: int = 6,
    flag_threshold: float = 50.0,
) -> dict[str, Any]:
    """Audit a JSONL suite against a reference corpus (e.g. the prompt).

    ``flag_threshold`` is the share of a case's n-grams that must appear in
    the reference before the case is called contaminated. 50% is strict; the
    paper's 8.3% figure used verbatim whole-case matching, which is stricter
    still. Report which you used.
    """
    ref = build_reference(reference_texts, n)
    rows = [json.loads(l) for l in open(suite_path, encoding="utf-8") if l.strip()]

    per_case, flagged = [], []
    for r in rows:
        rep = overlap_report(r.get("text", ""), ref, n)
        rep["id"] = r.get("id")
        per_case.append(rep)
        if rep["overlap_pct"] >= flag_threshold:
            flagged.append(r.get("id"))

    scored = [c["overlap_pct"] for c in per_case if c["candidate_ngrams"]]
    return {
        "suite": str(suite_path),
        "n_gram_size": n,
        "flag_threshold_pct": flag_threshold,
        "n_cases": len(rows),
        "n_flagged": len(flagged),
        "flagged_pct": round(100 * len(flagged) / len(rows), 2) if rows else 0.0,
        "mean_overlap_pct": round(sum(scored) / len(scored), 2) if scored else 0.0,
        "max_overlap_pct": round(max(scored), 2) if scored else 0.0,
        "flagged_ids": flagged,
        "per_case": per_case,
    }


def cross_suite_overlap(paths: list[str | Path], n: int = 6) -> dict[str, Any]:
    """Pairwise n-gram overlap between suites — do they leak into each other?"""
    corpora: dict[str, set[tuple[str, ...]]] = {}
    for p in paths:
        rows = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
        corpora[Path(p).stem] = build_reference(r.get("text", "") for r in rows)

    out: dict[str, Any] = {}
    names = list(corpora)
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            inter = corpora[a] & corpora[b]
            union = corpora[a] | corpora[b]
            out[f"{a} vs {b}"] = {
                "shared_ngrams": len(inter),
                "jaccard": round(len(inter) / len(union), 4) if union else 0.0,
            }
    return out
