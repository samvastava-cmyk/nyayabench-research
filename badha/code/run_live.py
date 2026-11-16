import json, sys, os, hashlib, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import badha_probe as B
mode, out = sys.argv[1], sys.argv[2]
K = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "secrets", "keys.json")))
MODELS = [{"provider": "openai", "model": "gpt-6.1-sol", "key": K["openai"]},
          {"provider": "openai", "model": "gpt-4.1", "key": K["openai"]},
          {"provider": "anthropic", "model": "claude-opus-5-5", "key": K["anthropic"]},
          {"provider": "deepseek", "model": "deepseek-v4-pro", "key": K["deepseek"]}]
items = B.build_items(n_nontie=1, n_tie=2) if mode == "trial" else B.build_items()
os.makedirs(out, exist_ok=True)
json.dump(items, open(os.path.join(out, "items.json"), "w"))
with open(os.path.join(out, "prompts.jsonl"), "w") as f:
    for it in items:
        for arm in B.ARMS:
            f.write(json.dumps({"item": it["id"], "arm": arm, "arm_name": B.ARM_NAMES[arm], "system": B.SYSTEM,
                                "prompt": B.render(it, arm), "gold": B.gold(it, arm), "lure_value": it["lure_value"],
                                "k": it["k"], "decider": it["decider"]}) + "\n")
code = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "badha_probe.py"), "rb").read()
json.dump({"run": mode, "started_utc": datetime.datetime.utcnow().isoformat() + "Z", "seed": B.SEED,
           "models": [{"provider": m["provider"], "model": m["model"]} for m in MODELS],
           "n_items": len(items), "arms": B.ARM_NAMES, "thresholds_fixed_before_run": B.TH, "max_tokens": 4000,
           "temperature": "0 where the API accepts it", "code_sha256": hashlib.sha256(code).hexdigest()},
          open(os.path.join(out, "manifest.json"), "w"), indent=1)
path = B.run(MODELS, items, out_dir=out, workers=int(sys.argv[3]) if len(sys.argv) > 3 else 8, max_calls=6000, max_tokens=4000)
B.analyse(path, out_dir=out)
