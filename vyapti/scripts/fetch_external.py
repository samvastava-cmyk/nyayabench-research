"""Fill in LOGIC and MAFALDA texts locally. Neither dataset states a licence, so this
repository ships row references only. Run once after cloning:  python scripts/fetch_external.py"""
import csv, hashlib, io, json, re, sys, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
LOGIC = "https://raw.githubusercontent.com/causalNLP/logical-fallacy/2a3d09708122c0994279df034d867b80950700ea/data/edu_all.csv"
MAFALDA = "https://raw.githubusercontent.com/ChadiHelwe/MAFALDA/0df434477b914a20f55c0592ba05a53fe924c65b/datasets/gold_standard_dataset.jsonl"
def get(u): return urllib.request.urlopen(u, timeout=60).read().decode("utf-8")
def key(t): return re.sub(r"[^a-z0-9]", "", t.lower())
def h16(t): return hashlib.sha256(key(t).encode()).hexdigest()[:16]
csv.field_size_limit(10**8)
logic = list(csv.DictReader(io.StringIO(get(LOGIC))))
gold = [json.loads(l) for l in get(MAFALDA).splitlines() if l.strip()]
bad = 0
files = list((ROOT / "data/crossmap").glob("*.jsonl")) + [ROOT / "data/external/mafalda_200.jsonl", ROOT / "data/suites/unseen_v5_balanced.jsonl"]
for f in files:
    rows = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    for r in rows:
        if r.get("text") is not None: continue
        t = logic[r["logic_row"]]["source_article"] if "logic_row" in r else gold[r["mafalda_gold_row"]]["text"]
        if h16(t) != r["text_key_sha256_16"]: bad += 1; continue
        r["text"] = t
    f.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
print(f"done: {bad} rows did not verify" if bad else "done: all rows verified")
sys.exit(1 if bad else 0)
