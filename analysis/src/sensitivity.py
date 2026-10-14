import copy

from src.recommender import recommend

SCENARIOS = (
    ("per_record_cost", "low", 0.5),
    ("per_record_cost", "high", 1.5),
    ("effectiveness", "low", 0.8),
    ("effectiveness", "high", 1.2),
    ("probabilities", "low", 0.8),
    ("probabilities", "high", 1.2),
    ("incident_probability", "low", 0.5),
    ("incident_probability", "high", 1.5),
)


def scaled_bundle(bundle, factor, f):
    b = copy.deepcopy(bundle)
    if factor == "per_record_cost":
        b["config"]["per_record_cost_inr"]["value"] *= f
    elif factor == "incident_probability":
        b["config"]["annual_incident_prob"]["value"] = min(
            b["config"]["annual_incident_prob"]["value"] * f, 1.0
        )
    elif factor == "effectiveness":
        for c in b["controls"]:
            if c["effectiveness"] is not None:
                c["effectiveness"] = min(c["effectiveness"] * f, 1.0)
    return b


def run_scenario(profile, bundle, factor, f):
    b = bundle if factor == "probabilities" else scaled_bundle(bundle, factor, f)
    return recommend(profile, b, p_scale=f if factor == "probabilities" else 1.0)


def plan_of(r):
    return [x["control"] for x in r["plan"]]


def sensitivity(profile, bundle):
    base = recommend(profile, bundle)
    rows = []
    for factor, side, f in SCENARIOS:
        r = run_scenario(profile, bundle, factor, f)
        rows.append(
            {
                "factor": factor,
                "side": side,
                "multiplier": f,
                "loss_no_controls_inr": r["totals"]["loss_no_controls_inr"],
                "loss_after_plan_inr": r["totals"]["loss_after_plan_inr"],
                "plan": plan_of(r),
                "same_order": plan_of(r) == plan_of(base),
                "same_set": set(plan_of(r)) == set(plan_of(base)),
            }
        )
    return base, rows


def tornado(base, rows, key="loss_after_plan_inr"):
    b = base["totals"][key]
    out = {}
    for r in rows:
        out.setdefault(r["factor"], {"factor": r["factor"], "base": b})[r["side"]] = r[key]
    for v in out.values():
        v["swing"] = abs(v.get("high", b) - v.get("low", b))
    return sorted(out.values(), key=swing_of, reverse=True)


def swing_of(v):
    return v["swing"]


def stable_controls(base, rows):
    keep = set(plan_of(base))
    for r in rows:
        keep &= set(r["plan"])
    return [k for k in plan_of(base) if k in keep]
