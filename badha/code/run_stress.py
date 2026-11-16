import json, sys, os, hashlib, datetime
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import badha_stress as T
out, scale, seed = sys.argv[1], float(sys.argv[2]), int(sys.argv[3])
arms = sys.argv[4].split(",") if len(sys.argv) > 4 else None
K = json.load(open(os.path.join(here, "..", "secrets", "keys.json")))
MODELS = [{"provider": "openai", "model": "gpt-6.1-sol", "key": K["openai"]},
          {"provider": "anthropic", "model": "claude-opus-5-5", "key": K["anthropic"]},
          {"provider": "deepseek", "model": "deepseek-v4-pro", "key": K["deepseek"]}]
items = T.build_all(seed=seed, scale=scale)
if arms:
    items = {a: (v if a in arms else []) for a, v in items.items()}
os.makedirs(out, exist_ok=True)
json.dump(items, open(os.path.join(out, "items.json"), "w"))
json.dump({"started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "seed": seed, "scale": scale, "arms": arms or "all",
           "models": [m["model"] for m in MODELS], "n_items": {a: len(v) for a, v in items.items()},
           "decision_rules_fixed_before_run": T.PREREG, "system_prompt": T.SYSTEM, "agent_system_prompt": T.AGENT_SYSTEM, "agent_task": T.AGENT_TASK,
           "code_sha256": hashlib.sha256(open(os.path.join(here, "badha_stress.py"), "rb").read()).hexdigest()},
          open(os.path.join(out, "manifest.json"), "w"), indent=1)
path = T.run(MODELS, items, out, workers=int(sys.argv[5]) if len(sys.argv) > 5 else 9)
T.analyse(path, out)
