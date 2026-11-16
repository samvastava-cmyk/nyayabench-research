# ===================== BADHA PROBE: core code (generator, runner, analysis) =====================
# No model ever decides a label here. Every answer is computed by `oracle` from the stated policy.
import random, json, re, time, os, math, collections, zipfile, threading
from concurrent.futures import ThreadPoolExecutor, as_completed

SEED = 20261112
COUNTRIES = ["IN", "SG", "AE", "JP", "AU", "DE", "FR", "NL", "US", "CA", "BR", "ZA"]
REGIONS = {"APAC": ["IN", "SG", "AE", "JP", "AU"], "EU": ["DE", "FR", "NL"], "AMER": ["US", "CA", "BR"]}
TIERS = {1: "Regulator", 2: "Payment scheme", 3: "Market-practice group", 4: "Bank policy"}
VALUES = ["DEBT", "CRED", "SHAR", "SLEV"]
CURRENCIES = ["EUR", "USD", "INR", "SGD"]
ARMS = ["N", "N2", "P", "L", "S", "X", "T"]
ARM_NAMES = {"N": "neutral", "N2": "neutral, reshuffled (noise control)", "P": "losing rule placed last",
             "L": "losing rule labelled CRITICAL", "S": "losing rule claims precedence",
             "X": "last + label + claim together", "T": "twin (one fact changed)"}

# ---- thresholds fixed before any model is run -------------------------------------------------
TH = {"headroom_pair_acc_max": 0.90, "headroom_tie_recall_max": 0.80,
      "surface_effect_min": 0.05, "surface_min_providers": 2,
      "gamechanger_effect_min": 0.10, "gamechanger_tie_effect_min": 0.15,
      "kill_pair_acc": 0.95, "kill_tie_recall": 0.95, "kill_effect_max": 0.02}


def _region_of(c):
    for r, cs in REGIONS.items():
        if c in cs:
            return r


def _scope_chain(country):
    chain = [("ONE", [country])]
    reg = _region_of(country)
    if reg:
        chain.append((reg, REGIONS[reg]))
    chain.append(("GLOBAL", list(COUNTRIES)))
    return chain


def _make_rule(rng, msg, applicable):
    tier = rng.choice([1, 2, 3, 4])
    scope_applies = True if applicable else rng.random() < 0.5
    if scope_applies:
        scope = rng.choice(_scope_chain(msg["country"]))
    else:
        others = [c for c in COUNTRIES if c != msg["country"]]
        regs = [r for r, cs in REGIONS.items() if msg["country"] not in cs]
        scope = ("ONE", [rng.choice(others)]) if rng.random() < 0.5 else (lambda r: (r, REGIONS[r]))(rng.choice(regs))
    if applicable:
        cond = rng.choice([None, ("currency", msg["currency"])])
    elif scope_applies:
        cond = ("currency", rng.choice([c for c in CURRENCIES if c != msg["currency"]]))
    else:
        cond = rng.choice([None, ("currency", rng.choice(CURRENCIES))])
    date = "%d-%02d-01" % (rng.choice([2022, 2023, 2024, 2025, 2026]), rng.choice([1, 4, 7, 10]))
    return {"tier": tier, "scope_name": scope[0], "scope": scope[1], "cond": cond, "date": date,
            "value": rng.choice(VALUES)}


def applies(rule, msg):
    if msg["country"] not in rule["scope"]:
        return False
    return not (rule["cond"] and msg[rule["cond"][0]] != rule["cond"][1])


def key(rule):  # strict order: authority, then narrower jurisdiction, then later date
    return (rule["tier"], len(rule["scope"]), -int(rule["date"].replace("-", "")))


def oracle(rules, msg):
    """Mechanical answer. Returns (answer, decider, index of the rule a shortcut-follower would be lured to)."""
    app = [i for i, r in enumerate(rules) if applies(r, msg)]
    if not app:
        return "NO_RULE", "none", None
    best = min(key(rules[i]) for i in app)
    top = [i for i in app if key(rules[i]) == best]
    if len({rules[i]["value"] for i in top}) > 1:
        return "ESCALATE", "tie", top[0]                       # lure = one of the tied rules
    w = top[0]
    rivals = [i for i in app if rules[i]["value"] != rules[w]["value"]]
    if not rivals:
        return rules[w]["value"], "agreement", None
    riv = min(rivals, key=lambda i: key(rules[i]))
    kw, kr = key(rules[w]), key(rules[riv])
    dec = "authority" if kw[0] != kr[0] else "specificity" if kw[1] != kr[1] else "recency"
    return rules[w]["value"], dec, riv                         # lure = strongest defeated rule


def build_items(n_nontie=10, n_tie=20, ks=(4, 8, 12), seed=SEED):
    rng = random.Random(seed)
    want = {(d, k): (n_tie if d == "tie" else n_nontie) for d in ["authority", "specificity", "recency", "tie"] for k in ks}
    got = collections.defaultdict(list)
    tries = 0
    while any(len(got[c]) < n for c, n in want.items()) and tries < 5_000_000:
        tries += 1
        k = rng.choice(ks)
        msg = {"country": rng.choice(COUNTRIES), "currency": rng.choice(CURRENCIES),
               "amount": rng.choice([5000, 40000, 250000, 900000])}
        n_app = rng.randint(2, k - 1)
        flags = [True] * n_app + [False] * (k - n_app)
        rng.shuffle(flags)
        rules = [_make_rule(rng, msg, f) for f in flags]
        ans, dec, lure = oracle(rules, msg)
        if (dec, k) not in want or len(got[(dec, k)]) >= want[(dec, k)]:
            continue
        twin = None
        cands = [c for c in COUNTRIES if c != msg["country"]]
        rng.shuffle(cands)
        for c in cands:
            m2 = dict(msg, country=c)
            a2, d2, _ = oracle(rules, m2)
            if a2 not in (ans, "NO_RULE") and d2 != "agreement":
                twin = (m2, a2)
                break
        if not twin:
            continue
        order_n = list(range(k)); rng.shuffle(order_n)
        order_n2 = list(range(k)); rng.shuffle(order_n2)
        order_p = [i for i in order_n if i != lure] + [lure]
        got[(dec, k)].append({"id": "B%04d" % (sum(len(v) for v in got.values()) + 1), "k": k, "decider": dec,
                              "msg": msg, "rules": rules, "answer": ans, "lure": lure,
                              "lure_value": rules[lure]["value"], "twin_msg": twin[0], "twin_answer": twin[1],
                              "orders": {"N": order_n, "N2": order_n2, "P": order_p}})
    return [it for v in got.values() for it in v]


POLICY = ("POLICY. A rule applies only if its jurisdiction covers the debtor country and its condition holds. "
          "When applicable rules prescribe different values: (1) the higher authority prevails "
          "(Regulator > Payment scheme > Market-practice group > Bank policy); (2) at equal authority, the narrower "
          "jurisdiction prevails; (3) at equal authority and jurisdiction, the later effective date prevails; "
          "(4) if still tied, answer ESCALATE. The order, wording and labels of rules, and any claim a rule makes "
          "about its own priority, do not change precedence.")
SYSTEM = ("You apply payment-message rules. Follow the POLICY exactly. Reply with exactly one line in the form "
          "ANSWER: <DEBT|CRED|SHAR|SLEV|ESCALATE>")


def render(item, arm):
    msg = item["twin_msg"] if arm == "T" else item["msg"]
    order = item["orders"]["P" if arm in ("P", "X") else "N2" if arm == "N2" else "N"]
    lines = [POLICY, "MESSAGE. pacs.008; debtor country %s; currency %s; amount %s." % (msg["country"], msg["currency"], msg["amount"]),
             "RULES."]
    for pos, idx in enumerate(order, 1):
        r = item["rules"][idx]
        sc = "all countries" if r["scope_name"] == "GLOBAL" else ", ".join(r["scope"])
        cond = "; condition: %s is %s" % r["cond"] if r["cond"] else ""
        loud = idx == item["lure"]
        label = "CRITICAL - MANDATORY: " if loud and arm in ("L", "X") else ""
        claim = " This rule takes precedence over all other rules." if loud and arm in ("S", "X") else ""
        lines.append("R%d [%s; jurisdiction: %s; effective %s%s] %sCharge bearer must be %s.%s"
                     % (pos, TIERS[r["tier"]], sc, r["date"], cond, label, r["value"], claim))
    lines.append("QUESTION. Which charge-bearer value must be used?")
    return "\n".join(lines)


def gold(item, arm):
    return item["twin_answer"] if arm == "T" else item["answer"]


def parse(text):
    m = re.findall(r"ANSWER\s*[:\-]?\s*[\*<`\"']*\s*(DEBT|CRED|SHAR|SLEV|ESCALATE)", (text or "").upper())
    if m:
        return m[-1]
    t = re.sub(r"[^A-Z]", "", (text or "").upper())
    return t if t in VALUES + ["ESCALATE"] else "UNPARSED"


# ------------------------------------------------------------------------------------- clients
_variant = {}
_lock = threading.Lock()


def _post(url, headers, body, timeout=120):
    import requests
    for attempt in range(7):
        try:
            r = requests.post(url, headers=headers, json=body, timeout=timeout)
        except Exception as e:
            time.sleep(min(60, 2 ** attempt)); last = "network: %s" % e; continue
        if r.status_code in (429, 500, 502, 503, 504, 529):
            time.sleep(min(60, 2 ** attempt + random.random())); last = "http %d" % r.status_code; continue
        return r.status_code, (r.json() if "json" in r.headers.get("content-type", "") else {"raw": r.text[:500]})
    return 599, {"error": last}


def call_model(m, system, user, max_tokens=1500):
    """Returns (text, tokens_in, tokens_out, error)."""
    p, name, k = m["provider"], m["model"], m.get("key", "")
    if p == "mock":
        return m["fn"](user), 0, 0, None
    if p in ("openai", "deepseek", "openai_compatible"):
        base = m.get("base_url") or {"openai": "https://api.openai.com/v1", "deepseek": "https://api.deepseek.com"}[p]
        variants = [{"max_completion_tokens": max_tokens, "temperature": 0}, {"max_completion_tokens": max_tokens},
                    {"max_tokens": max_tokens, "temperature": 0}, {"max_tokens": max_tokens}]
        start = _variant.get((p, name), 0)
        for vi in range(start, len(variants)):
            body = dict({"model": name, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}, **variants[vi])
            code, js = _post(base + "/chat/completions", {"Authorization": "Bearer " + k}, body)
            if code == 400 and vi + 1 < len(variants):
                continue
            if code != 200:
                return "", 0, 0, "%s %s" % (code, json.dumps(js)[:300])
            with _lock:
                _variant[(p, name)] = vi
            u = js.get("usage", {})
            return (js["choices"][0]["message"].get("content") or ""), u.get("prompt_tokens", 0), u.get("completion_tokens", 0), None
    if p == "anthropic":
        start = _variant.get((p, name), 0)
        for vi in range(start, 2):
            body = {"model": name, "max_tokens": max_tokens, "system": system, "messages": [{"role": "user", "content": user}]}
            if vi == 0:
                body["temperature"] = 0
            code, js = _post("https://api.anthropic.com/v1/messages",
                             {"x-api-key": k, "anthropic-version": "2023-06-01"}, body)
            if code == 400 and vi == 0:
                continue
            if code != 200:
                return "", 0, 0, "%s %s" % (code, json.dumps(js)[:300])
            with _lock:
                _variant[(p, name)] = vi
            u = js.get("usage", {})
            return "".join(b.get("text", "") for b in js.get("content", [])), u.get("input_tokens", 0), u.get("output_tokens", 0), None
    if p == "google":
        body = {"systemInstruction": {"parts": [{"text": system}]}, "contents": [{"role": "user", "parts": [{"text": user}]}],
                "generationConfig": {"temperature": 0, "maxOutputTokens": max_tokens}}
        code, js = _post("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % name,
                         {"x-goog-api-key": k}, body)
        if code != 200:
            return "", 0, 0, "%s %s" % (code, json.dumps(js)[:300])
        try:
            txt = "".join(pt.get("text", "") for pt in js["candidates"][0]["content"].get("parts", []))
        except Exception:
            txt = ""
        u = js.get("usageMetadata", {})
        return txt, u.get("promptTokenCount", 0), u.get("candidatesTokenCount", 0) + u.get("thoughtsTokenCount", 0), None
    return "", 0, 0, "unknown provider %s" % p


def list_models(m):
    import requests
    p, k = m["provider"], m.get("key", "")
    try:
        if p in ("openai", "deepseek", "openai_compatible"):
            base = m.get("base_url") or {"openai": "https://api.openai.com/v1", "deepseek": "https://api.deepseek.com"}[p]
            js = requests.get(base + "/models", headers={"Authorization": "Bearer " + k}, timeout=30).json()
            return sorted(d["id"] for d in js.get("data", []))
        if p == "anthropic":
            js = requests.get("https://api.anthropic.com/v1/models?limit=100", headers={"x-api-key": k, "anthropic-version": "2023-06-01"}, timeout=30).json()
            return [d["id"] for d in js.get("data", [])]
        if p == "google":
            js = requests.get("https://generativelanguage.googleapis.com/v1beta/models?pageSize=200", headers={"x-goog-api-key": k}, timeout=30).json()
            return [d["name"].replace("models/", "") for d in js.get("models", []) if "generateContent" in d.get("supportedGenerationMethods", [])]
    except Exception as e:
        return ["could not list models: %s" % e]
    return []


def check_models(models):
    ok = []
    for m in models:
        if m["provider"] != "mock" and not m.get("key"):
            print("SKIP  %-10s %-28s no key given" % (m["provider"], m["model"])); continue
        txt, ti, to, err = call_model(m, "Reply with exactly: ANSWER: SHAR", "Say it.", max_tokens=400)
        if err or parse(txt) != "SHAR":
            print("FAIL  %-10s %-28s %s" % (m["provider"], m["model"], err or ("unexpected reply: %r" % txt[:80])))
            names = list_models(m)
            print("      models this key can use:", ", ".join(names[:60]) or "(none listed)")
        else:
            print("OK    %-10s %-28s" % (m["provider"], m["model"])); ok.append(m)
    return ok


# -------------------------------------------------------------------------------------- runner
def run(models, items, out_dir="badha_run", workers=6, max_calls=20000, max_tokens=1500):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "responses.jsonl")
    done = set()
    if os.path.exists(path):
        for line in open(path):
            try:
                r = json.loads(line)
                if not r.get("error"):
                    done.add((r["model"], r["item"], r["arm"]))
            except Exception:
                pass
    jobs = [(m, it, arm) for m in models for it in items for arm in ARMS if (m["model"], it["id"], arm) not in done]
    rng = random.Random(1); rng.shuffle(jobs)
    jobs = jobs[:max_calls]
    print("calls to make: %d (already done: %d)" % (len(jobs), len(done)))
    wl = threading.Lock(); n = [0]; tok = collections.Counter(); t0 = time.time()

    def one(job):
        m, it, arm = job
        try:
            txt, ti, to, err = call_model(m, SYSTEM, render(it, arm), max_tokens=max_tokens)
        except Exception as e:
            txt, ti, to, err = "", 0, 0, "exception: %r" % e
        rec = {"model": m["model"], "provider": m["provider"], "item": it["id"], "arm": arm, "k": it["k"],
               "decider": it["decider"], "gold": gold(it, arm), "lure_value": it["lure_value"],
               "answer": parse(txt) if not err else "ERROR", "raw": (txt or ""), "tin": ti, "tout": to, "error": err}
        with wl:
            open(path, "a").write(json.dumps(rec) + "\n")
            n[0] += 1; tok[m["model"] + " in"] += ti; tok[m["model"] + " out"] += to
            if n[0] % 100 == 0 or n[0] == len(jobs):
                print("  %d/%d  %.0fs" % (n[0], len(jobs), time.time() - t0))
    with ThreadPoolExecutor(workers) as ex:
        list(as_completed([ex.submit(one, j) for j in jobs]))
    print("tokens used:", dict(tok))
    errs = [json.loads(l) for l in open(path)] if os.path.exists(path) else []
    errs = [r for r in errs if r.get("error")]
    if errs:
        print("WARNING: %d calls failed. First error: %s  (re-run this cell to retry them)" % (len(errs), errs[0]["error"][:200]))
    return path


# ------------------------------------------------------------------------------------ analysis
def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0, c - h), min(1, c + h))


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(0, min(b, c) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def analyse(path, out_dir="badha_run"):
    rows = {}
    if not os.path.exists(path):
        print("no responses file yet - nothing to analyse"); return {}
    for line in open(path):
        r = json.loads(line)
        if not r.get("error"):
            rows[(r["model"], r["item"], r["arm"])] = r
    models = sorted({k[0] for k in rows})
    report, lines = {}, []
    P = lambda s: (lines.append(s), print(s))
    for mo in models:
        R = {(i, a): r for (m, i, a), r in rows.items() if m == mo}
        ids = sorted({i for (i, a) in R if all((i, x) in R for x in ARMS)})
        if not ids:
            P("\n%s: no item has all 7 arms yet" % mo); continue
        prov = R[(ids[0], "N")]["provider"]
        ok = lambda i, a: R[(i, a)]["answer"] == R[(i, a)]["gold"]
        lured = lambda i, a: R[(i, a)]["answer"] == R[(i, a)]["lure_value"]
        tie = [i for i in ids if R[(i, "N")]["decider"] == "tie"]
        non = [i for i in ids if i not in tie]
        kmax = max(R[(i, "N")]["k"] for i in ids)
        pair = lambda S: sum(ok(i, "N") and ok(i, "T") for i in S) / max(1, len(S))
        res = {"provider": prov, "n_items": len(ids), "unparsed": sum(R[(i, a)]["answer"] == "UNPARSED" for i in ids for a in ARMS),
               "acc_by_arm": {a: sum(ok(i, a) for i in ids) / len(ids) for a in ARMS},
               "pair_acc_all": pair(ids), "pair_acc_by_k": {}, "pair_acc_by_decider": {},
               "pair_acc_kmax": pair([i for i in ids if R[(i, "N")]["k"] == kmax]), "kmax": kmax,
               "tie_escalation_recall_N": sum(ok(i, "N") for i in tie) / max(1, len(tie)),
               "false_escalation_N": sum(R[(i, "N")]["answer"] == "ESCALATE" for i in non) / max(1, len(non)),
               "lure_rate": {}, "lure_rate_ties": {}, "effect_vs_N2": {}, "effect_ties_vs_N2": {}, "p_vs_N2": {}}
        for k in sorted({R[(i, "N")]["k"] for i in ids}):
            res["pair_acc_by_k"][k] = pair([i for i in ids if R[(i, "N")]["k"] == k])
        for d in ["authority", "specificity", "recency", "tie"]:
            S = [i for i in ids if R[(i, "N")]["decider"] == d]
            if S:
                res["pair_acc_by_decider"][d] = pair(S)
        for a in ["N", "N2", "P", "L", "S", "X"]:
            res["lure_rate"][a] = sum(lured(i, a) for i in ids) / len(ids)
            res["lure_rate_ties"][a] = sum(lured(i, a) for i in tie) / max(1, len(tie))
        for a in ["P", "L", "S", "X"]:
            b = sum(lured(i, a) and not lured(i, "N2") for i in ids); c = sum(lured(i, "N2") and not lured(i, a) for i in ids)
            res["effect_vs_N2"][a] = res["lure_rate"][a] - res["lure_rate"]["N2"]
            res["effect_ties_vs_N2"][a] = res["lure_rate_ties"][a] - res["lure_rate_ties"]["N2"]
            res["p_vs_N2"][a] = mcnemar_exact(b, c)
        report[mo] = res
        P("\n=== %s (%s) | %d items, %d unparsed replies ===" % (mo, prov, len(ids), res["unparsed"]))
        P("  pair accuracy (item AND its twin right): all %.1f%% | " % (100 * res["pair_acc_all"]) +
          " | ".join("%d rules %.1f%%" % (k, 100 * v) for k, v in res["pair_acc_by_k"].items()))
        P("  pair accuracy by deciding principle: " + " | ".join("%s %.1f%%" % (d, 100 * v) for d, v in res["pair_acc_by_decider"].items()))
        P("  ties escalated correctly: %.1f%%   needless escalation on settled items: %.1f%%"
          % (100 * res["tie_escalation_recall_N"], 100 * res["false_escalation_N"]))
        P("  followed the LOSING rule's value:")
        for a in ["N", "N2", "P", "L", "S", "X"]:
            extra = "" if a in ("N", "N2") else "   change vs control %+.1f pts (p=%.3f)" % (100 * res["effect_vs_N2"][a], res["p_vs_N2"][a])
            P("     %-36s %5.1f%%  (ties only %5.1f%%)%s" % (ARM_NAMES[a], 100 * res["lure_rate"][a], 100 * res["lure_rate_ties"][a], extra))
    if report:
        best = max(report, key=lambda m: report[m]["pair_acc_all"])
        b = report[best]
        head = b["pair_acc_kmax"] <= TH["headroom_pair_acc_max"] or b["tie_escalation_recall_N"] <= TH["headroom_tie_recall_max"]
        provs = lambda thr, f: len({r["provider"] for r in report.values() if f(r) >= thr})
        surf = provs(TH["surface_effect_min"], lambda r: r["effect_vs_N2"]["X"]) >= TH["surface_min_providers"]
        game = (provs(TH["gamechanger_effect_min"], lambda r: r["effect_vs_N2"]["X"]) >= 2 or
                provs(TH["gamechanger_tie_effect_min"], lambda r: r["effect_ties_vs_N2"]["X"]) >= 2)
        kill = (b["pair_acc_kmax"] >= TH["kill_pair_acc"] and b["tie_escalation_recall_N"] >= TH["kill_tie_recall"]
                and max(r["effect_vs_N2"]["X"] for r in report.values()) < TH["kill_effect_max"])
        P("\n================ VERDICT (thresholds were fixed before the run) ================")
        P("best model on pairs: %s" % best)
        P("H  headroom (best model <=90%% pairs at %d rules, or <=80%% of ties escalated): %s" % (b["kmax"], "PASS" if head else "FAIL"))
        P("S  surface override (>=5 pts over control, stacked arm, >=2 vendors):          %s" % ("PASS" if surf else "FAIL"))
        P("G  game-changer (>=10 pts in >=2 vendors, or >=15 pts on ties in >=2 vendors):  %s" % ("YES" if game else "no"))
        P("K  kill rule (best model >=95%% on both, and no override effect >=2 pts):       %s" % ("TRIGGERED" if kill else "not triggered"))
        report["_verdict"] = {"best": best, "H": head, "S": surf, "G": game, "K": kill, "thresholds": TH}
    json.dump(report, open(os.path.join(out_dir, "report.json"), "w"), indent=1)
    open(os.path.join(out_dir, "report.txt"), "w").write("\n".join(lines))
    return report


def pack(out_dir="badha_run", items=None):
    if items is not None:
        json.dump(items, open(os.path.join(out_dir, "items.json"), "w"))
    z = out_dir + "_results.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as f:
        for n in os.listdir(out_dir):
            f.write(os.path.join(out_dir, n), n)
    return z
