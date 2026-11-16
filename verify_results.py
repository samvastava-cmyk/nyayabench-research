#!/usr/bin/env python3
"""Recompute every headline figure in this repository from the released files.

No dependencies beyond the Python standard library, and no API calls: this script
only re-derives numbers from result files that are already in the repository.

    python3 verify_results.py

Each check prints the value it recomputed next to the value claimed in the paper
and the README, and the script exits non-zero if any of them disagree.
"""

import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PASS, FAIL = [], []


def check(name, got, want, tol=0.05, unit=""):
    ok = abs(got - want) <= tol
    (PASS if ok else FAIL).append(name)
    mark = "ok  " if ok else "FAIL"
    print(f"  [{mark}] {name:<52} recomputed {got:>8.3f}{unit}   claimed {want:>8.3f}{unit}")


def entropy(probs):
    return -sum(p * math.log2(p) for p in probs if p > 0)


def load_matrix(path, drop=("ERROR", "NONE")):
    """Return {(western_label, rf_code): count} over classified cases only."""
    m = json.loads(path.read_text(encoding="utf-8"))["matrix"]
    rows, cols, data = m["rows"], m["columns"], m["data"]
    joint = {}
    for i, western in enumerate(rows):
        for j, code in enumerate(cols):
            if code in drop:
                continue
            n = data[i][j]
            if n:
                joint[(western, code)] = joint.get((western, code), 0) + n
    return joint


# --------------------------------------------------------------------------
print(__doc__.splitlines()[0])
print()
print("1. VRS v10 typed accuracy on the held-out suite")
print("   source: nyayabench/results/v10_full_validation_report.json")

report = json.loads((ROOT / "nyayabench/results/v10_full_validation_report.json").read_text(encoding="utf-8"))
rows = report["results"]
correct = sum(1 for r in rows if r["correct"])
check("typed accuracy, 120 held-out cases (%)" , 100 * correct / len(rows), 95.83, 0.01, "%")
check("cases classified as expected", correct, 115, 0)
print(f"         scorer {report['scorer_version']}, judge {report['judge_model']}, run {report['date'][:10]}")

# What the figure does NOT measure: the suite has no sound arguments at all.
n_none = sum(1 for r in rows if r["expected"] == "NONE")
check("sound (NONE) cases in the held-out suite", n_none, 0, 0)

# Confidence is not usable as a filter: it is slightly higher when wrong.
cw = [r["confidence"] for r in rows if not r["correct"]]
cr = [r["confidence"] for r in rows if r["correct"]]
mean_wrong, mean_right = sum(cw) / len(cw), sum(cr) / len(cr)
print(f"         mean confidence when WRONG {mean_wrong:.3f} vs when RIGHT {mean_right:.3f}"
      f"  -> {'no threshold can separate errors' if mean_wrong >= mean_right - 0.02 else 'separable'}")

# --------------------------------------------------------------------------
print()
print("2. Cross-taxonomy information analysis, 2,372 LOGIC arguments")
print("   source: vyapti/results/crossmap_logic_2372.json   (scorer v8-v9, March 2026)")

joint = load_matrix(ROOT / "vyapti/results/crossmap_logic_2372.json")
N = sum(joint.values())
p_code, p_west = {}, {}
for (west, code), n in joint.items():
    p_code[code] = p_code.get(code, 0) + n
    p_west[west] = p_west.get(west, 0) + n

h_code = entropy([n / N for n in p_code.values()])
h_cond = sum(
    (nw / N) * entropy([n / nw for (w, c), n in joint.items() if w == west])
    for west, nw in p_west.items()
)
mutual = h_code - h_cond

check("classified cases", N, 2174, 0)
check("H(Nyaya label), bits", h_code, 2.356, 0.002)
check("information shared with the Western label, bits", mutual, 0.746, 0.002)
check("share NOT derivable from the Western label (%)", 100 * h_cond / h_code, 68.3, 0.05, "%")

# Cramer's V over the same contingency table.
chi2 = 0.0
for west, nw in p_west.items():
    for code, nc in p_code.items():
        expected = nw * nc / N
        if expected > 0:
            chi2 += (joint.get((west, code), 0) - expected) ** 2 / expected
k = min(len(p_west), len(p_code))
check("Cramer's V", math.sqrt(chi2 / (N * (k - 1))), 0.401, 0.002)

# --------------------------------------------------------------------------
print()
print("3. Scope boundary: the taxonomy describes defective reasons, not irrelevant ones")
print("   Fallacies of relevance have no hetvabhasa counterpart, so they land in RF-01,")
print("   the broadest category. Structural fallacies do not.")

rf01_base = 100 * p_code["RF-01"] / N
check("RF-01 share of all classified cases (%)", rf01_base, 49.2, 0.05, "%")
print()
print(f"   {'Western label':<26}{'n':>6}{'-> RF-01':>10}{'share':>9}   vs base rate {rf01_base:.1f}%")
table = []
for west, nw in p_west.items():
    if nw < 4:
        continue
    table.append((100 * joint.get((west, "RF-01"), 0) / nw, west, nw, joint.get((west, "RF-01"), 0)))
for share, west, nw, n01 in sorted(table, reverse=True):
    flag = "  <-- relevance" if any(k in west.lower() for k in ("populum", "hominem", "emotion")) else ""
    print(f"   {west:<26}{nw:>6}{n01:>10}{share:>8.1f}%{flag}")

ad_populum = next((s for s, w, _, _ in table if "populum" in w.lower()), None)
ad_hominem = next((s for s, w, _, _ in table if "hominem" in w.lower()), None)
dilemma = next((s for s, w, _, _ in table if "dilemma" in w.lower()), None)
if ad_populum is not None:
    check("ad populum -> RF-01 (%)", ad_populum, 93.7, 0.1, "%")
if ad_hominem is not None:
    check("ad hominem -> RF-01 (%)", ad_hominem, 67.9, 0.1, "%")
if dilemma is not None:
    check("false dilemma -> RF-01 (%), a structural fallacy", dilemma, 9.2, 0.1, "%")

# --------------------------------------------------------------------------
print()
print("4. File fingerprints (SHA-256, first 16 hex characters)")
for rel in ("taxonomy/hetvabhasa_v2.1.json", "taxonomy/hetvabhasa_v2.2.json",
            "nyayabench/scorer/llm_reasoning_judge.py",
            "nyayabench/scorer-test-suites/vyapti_unseen_v4.json",
            "vyapti/prompts/production/v10-rf07a-fix.txt"):
    path = ROOT / rel
    if path.exists():
        print(f"  {hashlib.sha256(path.read_bytes()).hexdigest()[:16]}  {rel}")

# --------------------------------------------------------------------------
print()
print(f"{len(PASS)} checks reproduced, {len(FAIL)} failed.")
if FAIL:
    print("Did not reproduce: " + ", ".join(FAIL))
    sys.exit(1)
print()
print("Every figure above was recomputed from a file in this repository.")
print("What these numbers do NOT show, and LIMITATIONS.md explains: the scorer is poor")
print("at telling sound arguments from flawed ones, and the typed-accuracy figure is")
print("agreement with the author's own labels on a suite the author wrote.")
