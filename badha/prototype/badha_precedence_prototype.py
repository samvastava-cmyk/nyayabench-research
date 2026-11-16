"""
Prototype: proof-carrying rule-precedence items (zero model calls).

Tests three things offline:
  T1  Can a closed-world generator produce conflict items whose answer is decided
      mechanically by a stated lexicographic policy, balanced by which principle decides?
  T2  Do surface shortcuts (position, single-cue heuristics) solve the items?
  T3  Does Sam's HWR engine (as shipped, v1.0 Professional) agree with the strict
      lexicographic oracle on the same items?

Usage: python3 precedence_proto.py <path-to-HWR-src-dir> <out-json>
"""
import sys, json, random, itertools, collections, datetime, importlib.util

HWR_SRC, OUT = sys.argv[1], sys.argv[2]
rng = random.Random(20261111)

COUNTRIES = ["IN", "SG", "AE", "JP", "AU", "DE", "FR", "NL", "US", "CA", "BR", "ZA"]
REGIONS = {"APAC": ["IN", "SG", "AE", "JP", "AU"], "EU": ["DE", "FR", "NL"],
           "AMER": ["US", "CA", "BR"]}
TIERS = {1: "Regulator", 2: "Payment scheme", 3: "Market-practice group", 4: "Bank policy"}
VALUES = ["DEBT", "CRED", "SHAR", "SLEV"]
CURRENCIES = ["EUR", "USD", "INR", "SGD"]


def region_of(c):
    for r, cs in REGIONS.items():
        if c in cs:
            return r
    return None


def scope_chain(country):
    """Nested family of scopes that all contain `country`: single < region < GLOBAL."""
    reg = region_of(country)
    chain = [("ONE", [country])]
    if reg:
        chain.append((reg, REGIONS[reg]))
    chain.append(("GLOBAL", list(COUNTRIES)))
    return chain


def random_scope(msg_country, want_applicable):
    if want_applicable:
        return rng.choice(scope_chain(msg_country))
    # a scope that does NOT contain the message country
    others = [c for c in COUNTRIES if c != msg_country]
    if rng.random() < 0.5:
        return ("ONE", [rng.choice(others)])
    regs = [r for r, cs in REGIONS.items() if msg_country not in cs]
    r = rng.choice(regs)
    return (r, REGIONS[r])


def make_rule(i, msg, applicable):
    tier = rng.choice([1, 2, 3, 4])
    scope_applies = True if applicable else rng.random() < 0.5
    scope = random_scope(msg["country"], scope_applies)
    # optional extra condition on currency
    if applicable:
        cond = rng.choice([None, ("currency", msg["currency"])])
    else:
        if scope_applies:  # must fail on the condition instead
            cond = ("currency", rng.choice([c for c in CURRENCIES if c != msg["currency"]]))
        else:
            cond = rng.choice([None, ("currency", rng.choice(CURRENCIES))])
    year = rng.choice([2022, 2023, 2024, 2025, 2026])
    month = rng.choice([1, 4, 7, 10])
    return {"id": f"R{i}", "tier": tier, "scope_name": scope[0], "scope": scope[1],
            "cond": cond, "date": f"{year}-{month:02d}-01", "value": rng.choice(VALUES)}


def applies(rule, msg):
    if msg["country"] not in rule["scope"]:
        return False
    if rule["cond"] and msg[rule["cond"][0]] != rule["cond"][1]:
        return False
    return True


def key(rule):
    # lexicographic: authority (lower tier number wins), narrower scope, later date
    return (rule["tier"], len(rule["scope"]), -int(rule["date"].replace("-", "")))


def oracle(rules, msg):
    """Returns (answer, decider, witness)."""
    app = [r for r in rules if applies(r, msg)]
    if not app:
        return ("NO_RULE", "none", {})
    best = min(key(r) for r in app)
    top = [r for r in app if key(r) == best]
    vals = sorted({r["value"] for r in top})
    winner = top[0]
    rivals = [r for r in app if r["value"] != winner["value"]]
    if len(vals) > 1:
        return ("ESCALATE", "tie", {"top": [r["id"] for r in top]})
    if not rivals:
        return (winner["value"], "agreement", {"top": [r["id"] for r in top]})
    # which principle separates the winner from its strongest conflicting rival?
    rival = min(rivals, key=key)
    kw, kr = key(winner), key(rival)
    decider = "authority" if kw[0] != kr[0] else "specificity" if kw[1] != kr[1] else "recency"
    return (winner["value"], decider, {"winner": winner["id"], "strongest_rival": rival["id"]})


def gen_item(k):
    msg = {"country": rng.choice(COUNTRIES), "currency": rng.choice(CURRENCIES),
           "amount": rng.choice([5000, 40000, 250000, 900000])}
    n_app = rng.randint(2, max(2, k - 1))
    flags = [True] * n_app + [False] * (k - n_app)
    rng.shuffle(flags)
    rules = [make_rule(i + 1, msg, f) for i, f in enumerate(flags)]
    return msg, rules


def find_twin(msg, rules, ans):
    """Minimal pair: change ONE message fact (country) so the mechanical answer changes."""
    cands = [c for c in COUNTRIES if c != msg["country"]]
    rng.shuffle(cands)
    for c in cands:
        m2 = dict(msg, country=c)
        a2, d2, w2 = oracle(rules, m2)
        if a2 not in (ans, "NO_RULE") and d2 != "agreement":
            return m2, a2, d2
    return None


def render(msg, rules):
    lines = [
        "POLICY. A rule applies only if its jurisdiction covers the debtor country and its condition holds.",
        "When applicable rules prescribe different values: (1) the higher authority prevails "
        "(Regulator > Payment scheme > Market-practice group > Bank policy); (2) at equal authority, "
        "the narrower jurisdiction prevails; (3) at equal authority and jurisdiction, the later "
        "effective date prevails; (4) if still tied, answer ESCALATE.",
        f"MESSAGE. pacs.008; debtor country {msg['country']}; currency {msg['currency']}; amount {msg['amount']}.",
        "RULES (listed in no particular order)."]
    for r in rules:
        sc = "all countries" if r["scope_name"] == "GLOBAL" else ", ".join(r["scope"])
        cond = f"; condition: {r['cond'][0]} is {r['cond'][1]}" if r["cond"] else ""
        lines.append(f"{r['id']} [{TIERS[r['tier']]}; jurisdiction: {sc}; effective {r['date']}{cond}] "
                     f"Charge bearer must be {r['value']}.")
    lines.append("QUESTION. Which charge-bearer value must be used (DEBT, CRED, SHAR, SLEV or ESCALATE)?")
    return "\n".join(lines)


# ---------------------------------------------------------------- T1 generate
PER_CELL = 25
cells = collections.defaultdict(list)
attempts = 0
KS = [3, 5, 8]
DECIDERS = ["authority", "specificity", "recency", "tie"]
while any(len(cells[(d, k)]) < PER_CELL for d in DECIDERS for k in KS) and attempts < 2_000_000:
    attempts += 1
    k = rng.choice(KS)
    msg, rules = gen_item(k)
    ans, dec, wit = oracle(rules, msg)
    if dec not in DECIDERS or len(cells[(dec, k)]) >= PER_CELL:
        continue
    tw = find_twin(msg, rules, ans)
    if not tw:
        continue
    cells[(dec, k)].append({"msg": msg, "rules": rules, "answer": ans, "decider": dec, "k": k,
                            "witness": wit, "twin_msg": tw[0], "twin_answer": tw[1],
                            "twin_decider": tw[2]})

pairs = [it for v in cells.values() for it in v]
items = []
for p in pairs:
    items.append((p["msg"], p["rules"], p["answer"], p["decider"], p["k"]))
    items.append((p["twin_msg"], p["rules"], p["twin_answer"], p["twin_decider"], p["k"]))

# round-trip: text differs between twins by exactly one token
def tokdiff(a, b):
    ta, tb = a.split(), b.split()
    return len(ta) == len(tb) and sum(x != y for x, y in zip(ta, tb))
one_token = sum(tokdiff(render(p["msg"], p["rules"]), render(p["twin_msg"], p["rules"])) == 1 for p in pairs)

# ---------------------------------------------------------------- T2 shortcut audit
def first(msg, rules): return rules[0]["value"]
def last(msg, rules): return rules[-1]["value"]
def top_authority_listed(msg, rules): return min(rules, key=lambda r: r["tier"])["value"]
def newest_listed(msg, rules): return max(rules, key=lambda r: r["date"])["value"]
def narrowest_listed(msg, rules): return min(rules, key=lambda r: len(r["scope"]))["value"]
def majority_listed(msg, rules):
    return collections.Counter(r["value"] for r in rules).most_common(1)[0][0]
def always_escalate(msg, rules): return "ESCALATE"
def authority_only_applicable(msg, rules):
    app = [r for r in rules if applies(r, msg)]
    return min(app, key=lambda r: r["tier"])["value"]
def full_policy_ignoring_applicability(msg, rules):
    best = min(key(r) for r in rules)
    top = [r for r in rules if key(r) == best]
    return top[0]["value"] if len({r["value"] for r in top}) == 1 else "ESCALATE"
def full_policy_never_escalate(msg, rules):
    app = [r for r in rules if applies(r, msg)]
    return min(app, key=key)["value"]

BASELINES = {
    "first-listed rule": first, "last-listed rule": last,
    "highest authority listed": top_authority_listed, "newest rule listed": newest_listed,
    "narrowest jurisdiction listed": narrowest_listed, "majority value listed": majority_listed,
    "always ESCALATE": always_escalate,
    "authority only (applicable rules)": authority_only_applicable,
    "full policy, ignoring applicability": full_policy_ignoring_applicability,
    "full policy, never escalates": full_policy_never_escalate,
}
audit = {}
for name, fn in BASELINES.items():
    hit = [fn(m, r) == a for (m, r, a, d, k) in items]
    pair_hit = [fn(p["msg"], p["rules"]) == p["answer"] and fn(p["twin_msg"], p["rules"]) == p["twin_answer"]
                for p in pairs]
    by_dec = {}
    for d in DECIDERS:
        sub = [h for h, it in zip(hit, items) if it[3] == d]
        by_dec[d] = round(100 * sum(sub) / max(1, len(sub)), 1)
    audit[name] = {"item_acc": round(100 * sum(hit) / len(hit), 1),
                   "pair_acc": round(100 * sum(pair_hit) / len(pair_hit), 1), "by_decider": by_dec}

# ---------------------------------------------------------------- T3 HWR as shipped
sys.path.insert(0, HWR_SRC)
import logging; logging.disable(logging.CRITICAL)
from precedence_engine import PrecedenceEngine
eng = PrecedenceEngine()
AXES = ["AUTHORITY_HIERARCHY", "JURISDICTIONAL_SPECIFICITY", "TEMPORAL_RECENCY"]

def to_hwr(rule):
    incl = [] if rule["scope_name"] == "GLOBAL" else rule["scope"]
    d = {"rule_metadata": {"rule_id": rule["id"]},
         "source": {"authority_rank": rule["tier"], "issuing_body": TIERS[rule["tier"]]},
         "applicability": {"jurisdiction_scope": {"inclusive": incl, "exclusive": []}},
         "lifecycle_management": {"effective_date": rule["date"] + "T00:00:00"},
         "created_date": rule["date"], "enforcement_type": "MANDATORY"}
    # HWR's own per-axis scoring functions fill the scores it would otherwise expect pre-declared
    scores = {a: float(eng.calculate_axis_score(a, d)) for a in AXES}
    d["precedence_resolution"] = {"precedence_axes_order": AXES, "axis_scores": scores,
                                  "tie_breaker_policy": "LEXICOGRAPHIC_RULE_ID"}
    return d

hwr_hit, hwr_by_dec, hwr_err = [], collections.defaultdict(list), 0
inversions = []
for (m, rules, a, d, k) in items:
    app = [r for r in rules if applies(r, m)]
    try:
        w, _ = eng.resolve_conflict([to_hwr(r) for r in app])
        wid = w["rule_metadata"]["rule_id"]
        val = next(r["value"] for r in app if r["id"] == wid)
    except Exception as e:
        hwr_err += 1; val = None
    ok = (val == a)
    hwr_hit.append(ok); hwr_by_dec[d].append(ok)
    if not ok and d == "authority" and len(inversions) < 3:
        win = next(r for r in app if r["id"] == wid)
        true = min(app, key=key)
        inversions.append({"hwr_winner": f"{TIERS[win['tier']]} / {win['scope_name']} / {win['date']}",
                           "policy_winner": f"{TIERS[true['tier']]} / {true['scope_name']} / {true['date']}"})

res = {
    "generated_pairs": len(pairs), "items": len(items), "sampling_attempts": attempts,
    "cells": {f"{d}|k={k}": len(cells[(d, k)]) for d in DECIDERS for k in KS},
    "twins_differ_by_exactly_one_token": f"{one_token}/{len(pairs)}",
    "answer_distribution": dict(collections.Counter(a for (_, _, a, _, _) in items)),
    "decider_distribution_all_items": dict(collections.Counter(d for (_, _, _, d, _) in items)),
    "shortcut_audit": audit,
    "hwr_as_shipped": {
        "errors": hwr_err,
        "item_acc": round(100 * sum(hwr_hit) / len(hwr_hit), 1),
        "by_decider": {d: round(100 * sum(v) / len(v), 1) for d, v in hwr_by_dec.items()},
        "example_authority_inversions": inversions},
    "example_item": render(pairs[0]["msg"], pairs[0]["rules"]),
    "example_answer": pairs[0]["answer"], "example_decider": pairs[0]["decider"],
    "example_twin_country": pairs[0]["twin_msg"]["country"], "example_twin_answer": pairs[0]["twin_answer"],
}
json.dump(res, open(OUT, "w"), indent=1)
json.dump(pairs, open(OUT.replace(".json", "_pairs.json"), "w"))
print(json.dumps({k: v for k, v in res.items() if k not in ("example_item",)}, indent=1))
print(res["example_item"])
