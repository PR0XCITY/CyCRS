# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
# ---

# %% [markdown]
# # 06 Recommendation engine
# Expected loss per attack category, a budget-constrained greedy control plan, and an offline coverage check.

# %%
import json
import shutil
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def find_root():
    c = Path(globals().get("__file__", Path.cwd() / "x")).resolve().parent
    for p in (c, *c.parents):
        if (p / "src" / "cards.py").exists():
            return p
        if (p / "analysis" / "src" / "cards.py").exists():
            return p / "analysis"
    raise FileNotFoundError("analysis root not found")


A = find_root()
sys.path.insert(0, str(A))

from src.cards import write_card
from src.classify import PROFILE_ASSETS
from src.export_web import WEB, build_bundle, export_all
from src.log import get_logger, log_event
from src.nbutil import MODELS, OUT, load_clean, save_fig, var, write_json
from src.recommender import (
    CATEGORIES,
    coverage_shares,
    exhaustive,
    hit,
    hit_rate,
    recommend,
    scorable,
)
from src.sources import CONTROLS, load_config
from src.stats_tests import two_proportion_z

lg = get_logger("nb06", phase="phase6")
df = load_clean()
cfg = load_config()
ctl_rows = pd.read_csv(CONTROLS).to_dict(orient="records")
tid = set(json.loads((MODELS / "attack_test_ids.json").read_text(encoding="utf-8"))["source_file"])
act = df[df[[f"action_{c}" for c in CATEGORIES]].sum(axis=1) > 0]
tr, te = act[~act["source_file"].isin(tid)], act[act["source_file"].isin(tid)]
cov = coverage_shares(tr, ctl_rows)
pd.DataFrame(cov).T.to_csv(OUT / "06_control_coverage.csv")
bundle = build_bundle(cfg, cov, "phase6")
ctl, skipped = scorable(bundle)
log_event(lg, "bundle", scorable=list(ctl), skipped=skipped, train=len(tr), test=len(te))

# %% [markdown]
# ## Reference profiles and greedy vs exhaustive

# %%
REF = [
    {
        "name": "small retail shop",
        "sector": "Retail Trade",
        "size": "small",
        "assets": ["asset_user_device", "asset_server"],
        "controls": [],
        "budget_inr": 50000,
    },
    {
        "name": "medium clinic with MFA, no budget",
        "sector": "Health Care and Social Assistance",
        "size": "medium",
        "assets": ["asset_server", "asset_media"],
        "controls": ["MFA"],
        "budget_inr": 0,
    },
    {
        "name": "small consultancy, tiny budget",
        "sector": "Professional, Scientific, and Technical Services",
        "size": "small",
        "assets": ["asset_server"],
        "controls": [],
        "budget_inr": 1000,
    },
    {
        "name": "large finance firm, big budget",
        "sector": "Finance and Insurance",
        "size": "large",
        "assets": ["asset_server", "asset_network", "asset_user_device"],
        "controls": [],
        "budget_inr": 1000000,
    },
    {
        "name": "other sector, unknown size",
        "sector": "Other",
        "size": "unknown",
        "assets": ["asset_media"],
        "controls": [],
        "budget_inr": 35000,
    },
]
refs, gaps = [], []
for p in REF:
    r = recommend(p, bundle)
    base = {c["category"]: c["expected_loss_inr"] for c in r["categories"]}
    start = [k for k in p["controls"] if k in ctl]
    eb, ev = exhaustive(base, ctl, start, p["budget_inr"])
    gv = r["totals"]["loss_after_plan_inr"]
    gap = 0.0 if ev == 0 else (gv - ev) / ev
    gaps.append(
        {
            "profile": p["name"],
            "greedy_loss": gv,
            "exhaustive_loss": ev,
            "gap_pct": 100 * gap,
            "greedy_plan": "; ".join(x["control"] for x in r["plan"]),
            "exhaustive_plan": "; ".join(eb),
        }
    )
    refs.append(r)
gp = pd.DataFrame(gaps)
gp.to_csv(OUT / "06_greedy_vs_exhaustive.csv", index=False)
fx = {"generated_by": "notebooks/06_recommendation_engine.py", "profiles": refs}
write_json(fx, A / "tests" / "fixtures" / "reference.json")
wf = A.parent / "web" / "tests" / "fixtures"
wf.mkdir(parents=True, exist_ok=True)
shutil.copy(A / "tests" / "fixtures" / "reference.json", wf / "reference.json")
max_gap = float(gp["gap_pct"].max())
log_event(lg, "greedy vs exhaustive", max_gap_pct=max_gap, rows=gp.to_dict(orient="records"))
gp.round(4)

# %%
r0 = refs[0]
cl = pd.DataFrame(r0["categories"]).set_index("category")
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.bar(cl.index, cl["expected_loss_inr"] / 1e5, color="#c44e52")
ax.set_title(f"Expected annual loss by attack category, {REF[0]['name']} (estimate)")
ax.set_xlabel("Attack category")
ax.set_ylabel("Expected loss (INR lakh per year)")
save_fig(fig, "06_expected_loss_reference.png")

# %% [markdown]
# ## Coverage hit rate on held-out incidents only

# %%
TOK = {c["control"]: c["mitigates"] for c in bundle["controls"]}
BIG = sum(c["cost"] for c in ctl.values()) + 1


def incident_profile(row):
    return {
        "sector": row["sector"],
        "size": row["size"],
        "assets": [a for a in PROFILE_ASSETS if row[a] == 1],
        "controls": [],
        "budget_inr": BIG,
    }


def top3(row):
    return [x["control"] for x in recommend(incident_profile(row), bundle)["plan"]][:3]


def flags(row):
    return {
        k: int(v)
        for k, v in row.items()
        if isinstance(v, int | np.integer | float) and k.startswith(("v_", "vec_", "action_"))
    }


tr_top = [top3(r) for _, r in tr.iterrows()]
pop = pd.Series([k for t in tr_top for k in t]).value_counts()
BASE3 = pop.head(3).index.tolist()
ev_rows = []
for _, r in te.iterrows():
    t = top3(r)
    f = flags(r)
    ev_rows.append(
        {
            "sector": r["sector"],
            "size": r["size"],
            "hit": hit(t, f, TOK),
            "hit_baseline": hit(BASE3, f, TOK),
            "top3": "; ".join(t),
        }
    )
ev = pd.DataFrame(ev_rows)
ev.to_csv(OUT / "06_hit_rate_test_incidents.csv", index=False)
h, hb = hit_rate(ev["hit"]), hit_rate(ev["hit_baseline"])
zt = two_proportion_z(int(ev["hit"].sum()), len(ev), int(ev["hit_baseline"].sum()), len(ev))
same = float((ev["top3"] == "; ".join(BASE3)).mean())
bys = (
    ev.groupby("sector")[["hit", "hit_baseline"]]
    .mean()
    .assign(n=ev.groupby("sector").size())
    .sort_values("n", ascending=False)
)
byz = ev.groupby("size")[["hit", "hit_baseline"]].mean().assign(n=ev.groupby("size").size())
bys.to_csv(OUT / "06_hit_rate_by_sector.csv")
byz.to_csv(OUT / "06_hit_rate_by_size.csv")
fig, axs = plt.subplots(1, 2, figsize=(13, 5))
b8 = bys.head(8)
xi = np.arange(len(b8))
axs[0].barh(xi - 0.2, b8["hit"], 0.4, label="CyCRS top 3")
axs[0].barh(xi + 0.2, b8["hit_baseline"], 0.4, label="3 most common controls")
axs[0].set_yticks(xi, [s[:28] for s in b8.index])
axs[0].set_title("Coverage hit rate by sector (test incidents)")
axs[0].set_xlabel("Hit rate")
axs[0].set_ylabel("Sector")
axs[0].legend()
xz = np.arange(len(byz))
axs[1].bar(xz - 0.2, byz["hit"], 0.4, label="CyCRS top 3")
axs[1].bar(xz + 0.2, byz["hit_baseline"], 0.4, label="3 most common controls")
axs[1].set_xticks(xz, byz.index)
axs[1].set_title(f"By size (overall {h:.3f} vs {hb:.3f})")
axs[1].set_xlabel("Size bucket")
axs[1].set_ylabel("Hit rate")
axs[1].legend()
save_fig(fig, "06_hit_rate.png")
log_event(
    lg,
    "hit rate",
    n=len(ev),
    cycrs=h,
    baseline=hb,
    baseline_controls=BASE3,
    z=zt["statistic"],
    p=zt["p_value"],
    same_as_baseline=same,
)

# %% [markdown]
# ## Cards

# %%
inp = r0["inputs"]
cards_src = ["attack-likelihood", "mlr-impact"]
lc = cl.sort_values("expected_loss_inr", ascending=False)
imax = max(c["impact_inr"] for r in refs for c in r["categories"])
iratio = imax / cfg["breach_total_cost_inr"]
small_i = max(c["impact_inr"] for c in r0["categories"])
topc = lc.index[0]
card_e = {
    "id": "expected-loss",
    "title": "Expected yearly loss in rupees",
    "module": "6: Probability and expected value",
    "stage": "decide",
    "used_live": True,
    "order": 14,
    "question": "How much is each kind of attack expected to cost this business per year, in rupees?",
    "data_in": {
        "dataset": "Outputs of attack-likelihood and mlr-impact, plus sourced values in config.yaml",
        "n_rows": len(REF),
        "variables": [
            var("p_c", "numeric", "ratio", "probability of category c given an incident"),
            var("pi", "numeric", "ratio", "annual_incident_prob"),
            var("I_c", "numeric", "ratio", "records x per_record_cost_inr"),
        ],
        "prep_steps": [
            "p_c from the attack-likelihood logistic models",
            "Records from the business MLR with only category c switched on",
            "Cost per record from config (IBM India, derived)",
        ],
        "sample_rows": [
            {
                "profile": p["name"],
                **{c["category"]: round(c["expected_loss_inr"], 2) for c in r["categories"]},
            }
            for p, r in zip(REF, refs, strict=True)
        ]
        + [
            {"profile": f"{p['name']} p_c", **{c["category"]: round(c["p_c"], 6) for c in r["categories"]}}
            for p, r in zip(REF[:3], refs[:3], strict=True)
        ],
    },
    "why": (
        f"Risk is chance times cost, so each category's expected annual loss is pi x p_c x I_c with pi {cfg['annual_incident_prob']:.3f} "
        f"(fallback level {inp['annual_incident_prob']['fallback_level']}) and a cost per record of INR {cfg['per_record_cost_inr']:,.0f}. "
        "The attack models give p_c given an incident and the impact model gives records lost on the log scale, so the product keeps every "
        "step traceable to one model card."
    ),
    "data_properties": [
        {
            "name": "Annual incident probability",
            "value": cfg["annual_incident_prob"],
            "implication": f"Fallback level {inp['annual_incident_prob']['fallback_level']}.",
        },
        {
            "name": "Cost per record (INR)",
            "value": cfg["per_record_cost_inr"],
            "implication": "Derived from IBM 2026 India total cost / average records.",
        },
        {
            "name": f"Largest expected loss, {REF[0]['name']}",
            "value": f"{topc} INR {lc.iloc[0]['expected_loss_inr']:,.0f}",
            "implication": "First category to defend.",
        },
        {
            "name": "Largest single-incident impact vs IBM India average breach cost",
            "value": round(iratio, 4),
            "implication": f"Impacts for small businesses reach {iratio:.1f} times the average for large Indian organisations, so rupee figures overstate small-business loss.",
        },
    ],
    "alternatives": [
        {
            "model": "Raw incident counts per category",
            "why_not": "Ignores how costly each attack type is; error incidents are common but lose fewer records than malware.",
        },
        {
            "model": "Monte Carlo loss simulation",
            "why_not": "Adds random draws a shop owner cannot retrace; the expected-value formula is exact and reproducible in the browser.",
        },
    ],
    "formula_tex": [
        {"label": "Expected loss per category", "tex": r"L_c = \pi \, p_c \, I_c"},
        {"label": "Impact", "tex": r"I_c = (10^{\hat y_c}-1)\times \text{cost per record}"},
        {"label": "Total", "tex": r"L = \sum_c L_c"},
    ],
    "assumptions": [
        {
            "check": "Categories add up",
            "statistic": None,
            "p_value": None,
            "verdict": "approximation",
            "action_taken": "An incident can involve several categories, so L may double count; shown as an estimate.",
        },
        {
            "check": "Cost per record constant across attack types",
            "statistic": cfg["per_record_cost_inr"],
            "p_value": None,
            "verdict": "simplification",
            "action_taken": "Single IBM India figure applied to all categories.",
        },
    ],
    "results": {
        "key_numbers": {
            "annual_incident_prob": cfg["annual_incident_prob"],
            "per_record_cost_inr": cfg["per_record_cost_inr"],
            **{f"ref_total_{i}": r["totals"]["loss_no_controls_inr"] for i, r in enumerate(refs)},
        },
        "tables": [
            {
                "title": f"Expected loss trace, {REF[0]['name']}",
                "columns": ["category", "p_c", "records", "impact_inr", "expected_loss_inr"],
                "rows": [
                    [
                        c,
                        float(cl.loc[c, "p_c"]),
                        float(cl.loc[c, "records"]),
                        float(cl.loc[c, "impact_inr"]),
                        float(cl.loc[c, "expected_loss_inr"]),
                    ]
                    for c in cl.index
                ],
            }
        ],
        "charts": [
            {
                "type": "bar",
                "title": "Expected annual loss by category (reference profile)",
                "x_label": "Attack category",
                "y_label": "INR per year",
                "data": [{"x": c, "y": float(cl.loc[c, "expected_loss_inr"])} for c in cl.index],
            }
        ],
    },
    "yields": (
        f"For a {REF[0]['name']}, CyCRS estimates about INR {r0['totals']['loss_no_controls_inr']:,.0f} a year of expected loss, most of it from {topc}. "
        "These are estimates built from public averages, and each one carries the source and fallback level of its inputs."
    ),
    "feeds": ["budget-optimiser"],
    "limitations": [
        "Probabilities come from reported incidents, not from Indian small businesses directly.",
        "Categories can overlap within one incident, so the total may overstate loss.",
        "Impact uses IBM India average cost per record for every category.",
        f"For a {REF[0]['name']} one incident is priced up to INR {small_i:,.0f}, above IBM's India average of INR {cfg['breach_total_cost_inr']:,.0f} per breach, because VCDB record counts and IBM costs come from large organisations; use the ranking of categories and controls rather than the rupee level.",
    ],
}
card_e["data_in"]["sample_rows"] = card_e["data_in"]["sample_rows"][:8]
write_card(card_e)

steps0 = refs[0]["greedy_steps"]
card_g = {
    "id": "budget-optimiser",
    "title": "What to buy first for your budget",
    "module": "6: Optimisation under a budget",
    "stage": "decide",
    "used_live": True,
    "order": 15,
    "question": "Which security controls should this business buy first to cut the most expected loss within its budget?",
    "data_in": {
        "dataset": "Expected losses per category and data/raw/controls.csv",
        "n_rows": len(bundle["controls"]),
        "variables": [
            var("effectiveness", "numeric", "ratio", "sourced"),
            var("annual_cost_inr", "numeric", "ratio", "sourced"),
            var("coverage", "numeric", "ratio", "share of category incidents the control addresses"),
        ],
        "prep_steps": [
            f"Only controls with both a sourced effectiveness and a cost are optimised ({len(ctl)} of {len(bundle['controls'])}); the rest are listed as not scored",
            "Coverage share of each control per category measured on training incidents only",
            "Controls already in place start in the chosen set",
        ],
        "sample_rows": [
            {
                "control": c["control"],
                "effectiveness": c["effectiveness"],
                "annual_cost_inr": c["annual_cost_inr"],
                **{k: round(v, 4) for k, v in c["coverage"].items()},
            }
            for c in bundle["controls"][:8]
        ],
    },
    "why": (
        "Each step picks the affordable control that removes the most expected loss per rupee, free controls first, and recomputes after every pick "
        "because controls overlap on the same attacks. "
        f"Against exhaustive search on the {len(REF)} reference profiles the greedy plan is at most {max_gap:.2f}% worse, while every step can be "
        "shown to the user and it runs instantly in the browser."
    ),
    "data_properties": [
        {
            "name": "Controls optimised",
            "value": f"{len(ctl)} of {len(bundle['controls'])}",
            "implication": "Others lack a sourced effectiveness or cost.",
        },
        {
            "name": "Worst greedy gap vs exhaustive (reference profiles)",
            "value": max_gap,
            "implication": "Loss of optimality from choosing greedily.",
        },
        {
            "name": f"Residual risk after plan, {REF[0]['name']}",
            "value": refs[0]["totals"]["residual_risk_pct"],
            "implication": "Share of expected loss left after the plan.",
        },
    ],
    "alternatives": [
        {
            "model": "Exhaustive search over all control sets",
            "why_not": f"Optimal but grows as 2 to the power of the number of controls and cannot explain why one set beat another; the measured gap is {max_gap:.2f}%.",
        },
        {
            "model": "Integer linear programming",
            "why_not": "Control effects multiply, so the objective is not linear; a solver would need an approximation and a library in the browser.",
        },
    ],
    "formula_tex": [
        {"label": "Loss with controls", "tex": r"L_c(S) = L_c \prod_{k \in S}\left(1 - e_k s_{kc}\right)"},
        {"label": "Greedy choice", "tex": r"k^* = \arg\max_{k:\,c_k \le B} \frac{L(S)-L(S\cup\{k\})}{c_k}"},
    ],
    "assumptions": [
        {
            "check": "Controls act independently",
            "statistic": None,
            "p_value": None,
            "verdict": "assumed",
            "action_taken": "Effects multiplied; overlap handled by recomputing after each pick.",
        },
        {
            "check": "Greedy gap vs exhaustive",
            "statistic": max_gap,
            "p_value": None,
            "verdict": "negligible" if max_gap < 1 else "material",
            "action_taken": "Greedy used live.",
        },
    ],
    "results": {
        "key_numbers": {"controls_scored": len(ctl), "max_gap_pct": max_gap},
        "tables": [
            {
                "title": "Greedy vs exhaustive on reference profiles",
                "columns": list(gp.columns),
                "rows": gp.round(4).values.tolist(),
            },
            {
                "title": "Controls not scored",
                "columns": ["control", "reason"],
                "rows": [[s["control"], s["reason"]] for s in skipped],
            },
        ],
        "charts": [
            {
                "type": "bar",
                "title": f"Greedy steps, {REF[0]['name']}",
                "x_label": "Step",
                "y_label": "Expected loss after step (INR)",
                "data": [{"x": s["pick"], "y": float(s["loss_after"])} for s in steps0],
            }
        ],
    },
    "yields": (
        f"For a {REF[0]['name']} with INR {REF[0]['budget_inr']:,} a year, the plan is {', '.join(x['control'] for x in refs[0]['plan']) or 'nothing affordable'}, "
        f"cutting expected loss to {refs[0]['totals']['residual_risk_pct']:.1f}% of the starting estimate. "
        f"Only {len(ctl)} controls have sourced effectiveness and cost, so the others are shown as not yet scored rather than guessed."
    ),
    "feeds": [],
    "limitations": [
        f"{len(skipped)} controls cannot be ranked until their effectiveness or cost is sourced.",
        "Effectiveness figures come from vendor or non-Indian studies.",
        "Independence of controls is an assumption.",
    ],
}
write_card(card_g)

card_h = {
    "id": "coverage-hit-rate",
    "title": "Do the recommendations match real attacks",
    "module": "4 and 2: Evaluation and hypothesis testing",
    "stage": "evaluate",
    "used_live": False,
    "order": 16,
    "question": "For past incidents the models never trained on, would CyCRS's top 3 controls have addressed what actually happened?",
    "data_in": {
        "dataset": "Held-out VCDB incidents from the Phase 4 test split",
        "n_rows": len(ev),
        "variables": [
            var("top3", "categorical", "nominal", "first three controls of the plan"),
            var("v_*, vec_*, action_*", "binary", "nominal", "what happened"),
        ],
        "prep_steps": [
            "Profile rebuilt from each test incident's sector, size and assets, no controls, unlimited budget",
            "Hit if any top-3 control mitigates a variety, vector or category the incident actually had",
            f"Baseline: the 3 controls most often in the top 3 for training incidents ({', '.join(BASE3)})",
        ],
        "sample_rows": ev[["sector", "size", "top3", "hit", "hit_baseline"]]
        .sample(8, random_state=42)
        .to_dict(orient="records"),
    },
    "why": (
        "A hit rate on incidents the models never saw tests the whole chain, not just one model, and the binary hit outcome makes a two-proportion "
        f"z-test the natural comparison with a fixed baseline. "
        f"Only {len(ctl)} controls can be ranked, and {100 * same:.0f}% of test incidents get exactly the baseline set, so the test has little room to show a difference."
    ),
    "data_properties": [
        {
            "name": "CyCRS hit rate",
            "value": h,
            "implication": "Share of test incidents addressed by the top 3.",
        },
        {
            "name": "Baseline hit rate",
            "value": hb,
            "implication": "Same metric for the 3 most common controls.",
        },
        {
            "name": "Share of plans identical to baseline",
            "value": same,
            "implication": "How much personalisation there is to measure.",
        },
    ],
    "alternatives": [
        {
            "model": "McNemar test",
            "why_not": "The paired test is stricter for the same incidents, but the brief asks for the two-proportion z-test; both use the same counts.",
        },
        {
            "model": "Accuracy of category prediction",
            "why_not": "Already measured by AUC in attack-likelihood; this checks whether the advice, not the prediction, fits.",
        },
    ],
    "formula_tex": [
        {
            "label": "Hit rate",
            "tex": r"\mathrm{HR} = \frac{1}{n}\sum_i \mathbf{1}\left[\exists k \in \mathrm{top3}_i : k \text{ mitigates incident } i\right]",
        }
    ],
    "assumptions": [
        {
            "check": "Two-proportion z-test",
            "statistic": zt["statistic"],
            "p_value": zt["p_value"],
            "verdict": "different" if zt["p_value"] < 0.05 else "no detectable difference",
            "action_taken": "Reported; samples are paired, so p is approximate.",
        }
    ],
    "results": {
        "key_numbers": {
            "n_test": len(ev),
            "hit_rate": h,
            "baseline_hit_rate": hb,
            "z": zt["statistic"],
            "p_value": zt["p_value"],
            "cohens_h": zt["effect_size"],
        },
        "tables": [
            {
                "title": "Hit rate by size",
                "columns": ["size", "hit", "hit_baseline", "n"],
                "rows": byz.reset_index().round(4).values.tolist(),
            },
            {
                "title": "Hit rate by sector",
                "columns": ["sector", "hit", "hit_baseline", "n"],
                "rows": bys.reset_index().round(4).values.tolist(),
            },
        ],
        "charts": [
            {
                "type": "bar",
                "title": "Hit rate by size",
                "x_label": "Size",
                "y_label": "Hit rate",
                "data": [
                    {"x": i, "cycrs": float(r["hit"]), "baseline": float(r["hit_baseline"])}
                    for i, r in byz.iterrows()
                ],
            }
        ],
    },
    "yields": (
        f"On {len(ev)} unseen incidents, CyCRS's top 3 controls addressed what happened {100 * h:.1f}% of the time, against {100 * hb:.1f}% for the fixed baseline "
        f"(p {zt['p_value']:.2g}). "
        "Most misses are attacks like errors and misuse whose controls cannot be scored yet, which is where sourcing more effectiveness data would help most."
    ),
    "feeds": [],
    "limitations": [
        "VCDB incidents are not Indian small businesses.",
        "Hit means the control addresses the attack type, not that it would have stopped it.",
        f"Only {len(ctl)} controls are rankable.",
    ],
}
write_card(card_h)

# %% [markdown]
# ## Export for the website

# %%
bundle["version"] = f"vcdb-{pd.Timestamp.today().date().isoformat()}"
fs = export_all(bundle, WEB)
log_event(lg, "exported", files=[str(f.name) for f in fs], sizes={f.name: f.stat().st_size for f in fs})

# %% [markdown]
# ## Reference fixtures from the exported bundle
# Recomputed from web/public/model/model.json (parameters rounded to 8 decimals) so the browser engine can be
# checked against exactly the numbers it will load.

# %%
exported = json.loads((WEB / "model.json").read_text(encoding="utf-8"))
fx = {
    "generated_by": "notebooks/06_recommendation_engine.py",
    "bundle": "web/public/model/model.json",
    "profiles": [recommend(p, exported) for p in REF],
}
write_json(fx, A / "tests" / "fixtures" / "reference.json")
shutil.copy(A / "tests" / "fixtures" / "reference.json", wf / "reference.json")
log_event(lg, "reference fixtures", profiles=len(REF))
