import itertools
import math

import numpy as np
import pandas as pd

from src.nbutil import slug

CATEGORIES = ("hacking", "malware", "social", "error", "misuse", "physical")
SIZES = ("small", "medium", "large", "unknown")
ALL = "all"


def split_tokens(s):
    return [t for t in str(s or "").split(";") if t]


def coverage_shares(df, controls, cats=CATEGORIES):
    out = {}
    for c in controls:
        ts = split_tokens(c["mitigates"])
        row = {}
        for k in cats:
            sub = df[df[f"action_{k}"] == 1]
            if ALL in ts:
                row[k] = 1.0
            elif len(sub) == 0:
                row[k] = 0.0
            else:
                cols = [t for t in ts if t in sub.columns]
                row[k] = float(sub[cols].max(axis=1).mean()) if cols else 0.0
        out[c["control"]] = row
    return out


def encode_profile(profile, order, sectors):
    s = profile.get("sector")
    z = profile.get("size", "unknown")
    a = set(profile.get("assets", []))
    v = {}
    for f in order:
        if f.startswith("sector_"):
            v[f] = 1.0 if s in sectors and f == f"sector_{slug(s)}" else 0.0
        elif f.startswith("size_"):
            v[f] = 1.0 if f == f"size_{z}" else 0.0
        elif f.startswith("asset_"):
            v[f] = 1.0 if f in a else 0.0
        else:
            v[f] = 0.0
    return v


def logit_trace(m, x, n=5):
    cs = {f: m["coefficients"][f] * x[f] for f in m["coefficients"]}
    z = m["intercept"] + sum(cs.values())
    tc = sorted(((f, c) for f, c in cs.items() if c != 0), key=abs_second, reverse=True)[:n]
    return z, 1 / (1 + math.exp(-z)), [{"feature": f, "contribution": c} for f, c in tc]


def abs_second(t):
    return abs(t[1])


def impact_records(imp, x, cat):
    y = imp["intercept"]
    for f, b in imp["coefficients"].items():
        if f.startswith("action_"):
            y += b * (1.0 if f == f"action_{cat}" else 0.0)
        else:
            y += b * x.get(f, 0.0)
    return y, max(10**y - 1, 0.0)


def combined_factor(chosen, cat, controls):
    f = 1.0
    for k in chosen:
        f *= 1 - controls[k]["effectiveness"] * controls[k]["coverage"].get(cat, 0.0)
    return f


def expected_loss(base, chosen, controls):
    return sum(v * combined_factor(chosen, c, controls) for c, v in base.items())


def greedy(base, controls, start, budget):
    s, spent, steps = list(start), 0.0, []
    while True:
        cur = expected_loss(base, s, controls)
        cand = []
        for k, c in controls.items():
            if k in s or c["cost"] > budget - spent:
                continue
            red = cur - expected_loss(base, [*s, k], controls)
            ratio = math.inf if c["cost"] == 0 else red / c["cost"]
            cand.append({"control": k, "reduction": red, "cost": c["cost"], "ratio": ratio})
        cand = [q for q in cand if q["reduction"] > 0]
        if not cand:
            return s, spent, steps
        free = [q for q in cand if q["cost"] == 0]
        pick = max(free, key=reduction_of) if free else max(cand, key=ratio_of)
        s.append(pick["control"])
        spent += pick["cost"]
        steps.append(
            {"candidates": cand, "pick": pick["control"], "loss_after": expected_loss(base, s, controls)}
        )


def reduction_of(q):
    return q["reduction"]


def ratio_of(q):
    return q["ratio"]


def exhaustive(base, controls, start, budget):
    free = [k for k in controls if k not in start]
    best, bs = expected_loss(base, start, controls), list(start)
    for r in range(1, len(free) + 1):
        for comb in itertools.combinations(free, r):
            if sum(controls[k]["cost"] for k in comb) > budget:
                continue
            v = expected_loss(base, [*start, *comb], controls)
            if v < best - 1e-9:
                best, bs = v, [*start, *comb]
    return bs, best


def persona_trace(personas, x):
    v = np.array([x[f] for f in personas["feature_order"]])
    d = [float(((np.array(c) - v) ** 2).sum()) for c in personas["centroids"]]
    i = int(np.argmin(d))
    return {
        "distances": [{"persona": personas["names"][j], "distance": d[j]} for j in range(len(d))],
        "chosen": personas["names"][i],
        "index": i,
    }


def scorable(bundle):
    out, skipped = {}, []
    for c in bundle["controls"]:
        if c["effectiveness"] is None or c["annual_cost_inr"] is None:
            miss = [
                n
                for n, v in (("effectiveness", c["effectiveness"]), ("cost", c["annual_cost_inr"]))
                if v is None
            ]
            skipped.append({"control": c["control"], "reason": f"{' and '.join(miss)} MISSING"})
            continue
        out[c["control"]] = {
            "effectiveness": c["effectiveness"],
            "cost": c["annual_cost_inr"],
            "coverage": c["coverage"],
        }
    return out, skipped


def recommend(profile, bundle, p_scale=1.0):
    att, imp, cfg = bundle["attack"], bundle["impact"], bundle["config"]
    x = encode_profile(profile, att["feature_order"], att["sectors"])
    pi = cfg["annual_incident_prob"]["value"]
    cpr = cfg["per_record_cost_inr"]["value"]
    cats, base = [], {}
    for c in CATEGORIES:
        z, p, top = logit_trace(att["models"][c], x)
        p = min(p * p_scale, 1.0)
        y, rec = impact_records(imp, x, c)
        ic = rec * cpr
        lc = pi * p * ic
        base[c] = lc
        cats.append(
            {
                "category": c,
                "intercept": att["models"][c]["intercept"],
                "top_contributions": top,
                "z": z,
                "p_c": p,
                "log_records": y,
                "records": rec,
                "impact_inr": ic,
                "expected_loss_inr": lc,
            }
        )
    ctl, skipped = scorable(bundle)
    start = [k for k in profile.get("controls", []) if k in ctl]
    budget = float(profile.get("budget_inr", 0))
    plan, spent, steps = greedy(base, ctl, start, budget)
    l0 = expected_loss(base, [], ctl)
    l1 = expected_loss(base, plan, ctl)
    lin = expected_loss(base, start, ctl)
    return {
        "estimate": True,
        "profile": profile,
        "features": [{"name": f, "value": x[f]} for f in att["feature_order"]],
        "categories": cats,
        "persona": persona_trace(bundle["personas"], x),
        "plan": [{"control": k, "cost": ctl[k]["cost"], "already_in_place": k in start} for k in plan],
        "not_scored": skipped,
        "greedy_steps": steps,
        "totals": {
            "loss_no_controls_inr": l0,
            "loss_with_current_controls_inr": lin,
            "loss_after_plan_inr": l1,
            "spent_inr": spent,
            "budget_inr": budget,
            "residual_risk_pct": 100 * l1 / l0 if l0 else 0.0,
        },
        "inputs": {
            k: {"value": v["value"], "fallback_level": v.get("fallback_level", "")} for k, v in cfg.items()
        },
    }


def hit(top, actual_flags, controls_tokens):
    for k in top:
        ts = controls_tokens[k]
        if ALL in ts or any(actual_flags.get(t, 0) == 1 for t in ts):
            return True
    return False


def hit_rate(rows):
    r = pd.Series(rows, dtype=float)
    return float(r.mean()) if len(r) else float("nan")
