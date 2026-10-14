# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
# ---

# %% [markdown]
# # 07 Case replay and sensitivity
# Documented Indian incidents run through the live engine, and the engine's response to shifts in its inputs.

# %%
import json
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
from src.export_web import WEB, cards_export, schema_md, sources_export, write_export
from src.log import get_logger, log_event
from src.nbutil import OUT, save_fig, slug, var
from src.recommender import recommend
from src.replay import NOT_ASSESSABLE, actual_categories, case_profile, verdict
from src.sensitivity import SCENARIOS, sensitivity, stable_controls, tornado
from src.sources import CASES

lg = get_logger("nb07", phase="phase9")
M = json.loads((WEB / "model.json").read_text(encoding="utf-8"))
BUDGET = 50000
REQ = [
    "name",
    "year",
    "sector",
    "size_bucket",
    "assets",
    "actual_actions",
    "summary",
    "source_url",
    "accessed",
]
cs = pd.read_csv(CASES, dtype=str)
valid = cs.dropna(subset=REQ)
valid = valid[valid["source_url"].str.startswith("https://")]
if len(valid) < 4:
    raise SystemExit(f"Only {len(valid)} valid cases in cases.csv; at least 4 are needed")
TOK = {c["control"]: c["mitigates"] for c in M["controls"]}

# %% [markdown]
# ## Case replay at a ₹50,000 budget

# %%
rows, traces = [], {}
for _, c in valid.iterrows():
    p = case_profile(c, M["sectors"], BUDGET)
    r = recommend(p, M)
    top = [x["control"] for x in r["plan"]][:3]
    act = actual_categories(c["actual_actions"])
    v, hit = verdict(top, act, TOK)
    traces[c["name"]] = r
    rows.append(
        {
            "case": c["name"],
            "year": c["year"],
            "sector_used": p["sector"],
            "size_used": p["size"],
            "assets_used": "; ".join(p["assets"]) or "none stated",
            "actual_categories": "; ".join(act) or "unknown",
            "top3": "; ".join(top),
            "verdict": v,
            "covered_categories": "; ".join(hit),
            "loss_no_controls_inr": r["totals"]["loss_no_controls_inr"],
            "residual_risk_pct": r["totals"]["residual_risk_pct"],
        }
    )
rp = pd.DataFrame(rows)
rp.to_csv(OUT / "07_case_replay.csv", index=False)
vc = rp["verdict"].value_counts()
log_event(lg, "replay", rows=rp[["case", "top3", "verdict"]].to_dict(orient="records"))
rp[["case", "actual_categories", "top3", "verdict"]]

# %% [markdown]
# ## Sensitivity for the three largest personas
# Each persona is turned into a profile from its centroid: the dominant sector and size (or Other and mixed when no
# level reaches half), and every asset present in at least half of its incidents.

# %%
per = M["personas"]
fo = per["feature_order"]
SN = {f"sector_{slug(s)}": s for s in M["sectors"]}
pn = pd.read_csv(OUT / "05_personas.csv")
pick = pn.sort_values("n", ascending=False).head(3)["persona"].tolist()


def persona_profile(i):
    c = dict(zip(fo, per["centroids"][i], strict=True))
    sec = max((k for k in c if k.startswith("sector_")), key=c.get)
    sz = {
        "small": 1 - sum(c[k] for k in c if k.startswith("size_")),
        **{k[5:]: c[k] for k in c if k.startswith("size_")},
    }
    z = max(sz, key=sz.get)
    return {
        "name": per["names"][i],
        "sector": SN[sec] if c[sec] >= 0.5 else "Other",
        "size": z,
        "assets": [k for k in c if k.startswith("asset_") and c[k] >= 0.5],
        "controls": [],
        "budget_inr": BUDGET,
    }


srows, tor, stab = [], [], []
for i in pick:
    p = persona_profile(i)
    base, rs = sensitivity(p, M)
    for r in rs:
        srows.append(
            {"persona": p["name"], **{k: (v if k != "plan" else "; ".join(v)) for k, v in r.items()}}
        )
    for t in tornado(base, rs):
        tor.append({"persona": p["name"], **t})
    stab.append(
        {
            "persona": p["name"],
            "base_plan": "; ".join(x["control"] for x in base["plan"]),
            "stable_controls": "; ".join(stable_controls(base, rs)),
            "scenarios_same_order": int(sum(r["same_order"] for r in rs)),
            "scenarios": len(rs),
        }
    )
sd = pd.DataFrame(srows)
td = pd.DataFrame(tor)
st = pd.DataFrame(stab)
sd.to_csv(OUT / "07_sensitivity_scenarios.csv", index=False)
td.to_csv(OUT / "07_tornado.csv", index=False)
st.to_csv(OUT / "07_stable_controls.csv", index=False)
order_changes = int(len(sd) - sd["same_order"].sum())
set_changes = int(len(sd) - sd["same_set"].sum())
log_event(lg, "sensitivity", order_changes=order_changes, set_changes=set_changes, n=len(sd))

fig, axs = plt.subplots(1, len(pick), figsize=(5 * len(pick), 4.5), sharex=False)
for ax, (nm, g) in zip(np.atleast_1d(axs), td.groupby("persona", sort=False), strict=True):
    g = g.iloc[::-1]
    y = np.arange(len(g))
    ax.barh(y, g["high"] - g["base"], left=g["base"], color="#E4572E", label="input raised")
    ax.barh(y, g["low"] - g["base"], left=g["base"], color="#2A9D8F", label="input lowered")
    ax.axvline(g["base"].iloc[0], color="#141414", lw=0.8)
    ax.set_yticks(y, [f.replace("_", " ") for f in g["factor"]])
    ax.set_title(nm[:38], fontsize=9)
    ax.set_xlabel("Expected loss after plan (INR per year)")
    ax.set_ylabel("Input changed")
np.atleast_1d(axs)[0].legend(fontsize=8)
fig.suptitle("Tornado: expected loss after the plan when each input moves")
save_fig(fig, "07_tornado.png")
td.round(2)

# %% [markdown]
# ## Cards

# %%
cases_n = len(rp)
assessable = rp[rp["verdict"] != NOT_ASSESSABLE]
n_cov = int((assessable["verdict"] == "covered").sum())
COLS = ["case", "year", "sector_used", "size_used", "assets_used", "actual_categories", "top3", "verdict"]
card_r = {
    "id": "case-replay",
    "title": "Replaying real Indian incidents",
    "module": "6: Decision analysis (evaluation on documented cases)",
    "stage": "evaluate",
    "used_live": False,
    "order": 17,
    "question": "If these Indian organisations had asked CyCRS for a plan at a ₹50,000 budget, would its top 3 controls have addressed what actually happened?",
    "data_in": {
        "dataset": "data/raw/cases.csv: documented Indian incidents from news and government sources",
        "n_rows": cases_n,
        "variables": [
            var("sector", "categorical", "nominal", "Other when outside the model's top 8"),
            var("size_bucket", "categorical", "ordinal", "unknown when the source does not say"),
            var("assets", "categorical", "nominal", "mapped to asset flags"),
            var("actual_actions", "categorical", "nominal", "VERIS action categories stated in the source"),
        ],
        "prep_steps": [
            "Only facts stated in each fetched source were recorded",
            f"Each case run through the live engine with no controls in place and a budget of INR {BUDGET:,}",
            "Verdict compares the action categories the top 3 controls address with the categories the source reports",
        ],
        "sample_rows": (
            rp[["case", "sector_used", "size_used", "actual_categories", "top3", "verdict"]].to_dict(
                orient="records"
            )
            * 2
        )[:8],
    },
    "why": (
        f"Only {cases_n} Indian incidents are documented well enough to replay, too few for a hit rate, so each case is judged on its own. "
        "A verdict per case shows a reader exactly where the advice matches reality and where the source is too thin to judge."
    ),
    "data_properties": [
        {
            "name": "Cases replayed",
            "value": cases_n,
            "implication": "Small qualitative check, not a statistical test.",
        },
        {
            "name": "Cases with known attack categories",
            "value": len(assessable),
            "implication": "Only these can get a verdict.",
        },
        {
            "name": "Covered among assessable cases",
            "value": f"{n_cov} of {len(assessable)}",
            "implication": "How often the top 3 addressed what happened.",
        },
    ],
    "alternatives": [
        {
            "model": "Coverage hit rate on Indian cases",
            "why_not": f"With {cases_n} cases a rate would swing by {100 / cases_n:.0f} points per case; the VCDB hit rate is the statistical check.",
        },
        {
            "model": "Guessing missing attack details",
            "why_not": "Sources that do not state the method are marked not assessable instead of filled in.",
        },
    ],
    "formula_tex": [
        {
            "label": "Verdict",
            "tex": r"\text{covered} \iff A_{\text{actual}} \subseteq \bigcup_{k\in \text{top3}} A_k",
        }
    ],
    "assumptions": [
        {
            "check": "Source states the attack category",
            "statistic": float(len(assessable)),
            "p_value": None,
            "verdict": f"{len(assessable)} of {cases_n}",
            "action_taken": "Others shown as not assessable.",
        },
        {
            "check": "Case profile from source only",
            "statistic": None,
            "p_value": None,
            "verdict": "unknown size and assets left unknown",
            "action_taken": "Engine uses its reference levels for unknowns.",
        },
    ],
    "results": {
        "key_numbers": {
            "cases": cases_n,
            "assessable": len(assessable),
            "covered": n_cov,
            "budget_inr": BUDGET,
        },
        "tables": [{"title": "Case replay results", "columns": COLS, "rows": rp[COLS].values.tolist()}],
        "charts": [
            {
                "type": "bar",
                "title": "Verdicts",
                "x_label": "Verdict",
                "y_label": "Cases",
                "data": [{"x": k, "y": int(v)} for k, v in vc.items()],
            }
        ],
    },
    "yields": (
        f"For {n_cov} of the {len(assessable)} cases whose sources say how the attack worked, CyCRS's top 3 controls at INR {BUDGET:,} address that kind of attack. "
        f"{cases_n - len(assessable)} case{'s do' if cases_n - len(assessable) != 1 else ' does'} not state the method, so it is shown without a verdict rather than counted as a success."
    ),
    "feeds": [],
    "limitations": [
        "Four public cases from large organisations, not small businesses.",
        "Addressing an attack type does not prove the control would have stopped that incident.",
    ],
}
write_card(card_r)

tt = td.groupby("factor")["swing"].mean().sort_values(ascending=False)


def tied(v):
    return " and the ".join(f.replace("_", " ") for f in tt.index[np.isclose(tt.values, v, rtol=1e-9)])


top_f = tied(tt.iloc[0])
low_f = tied(tt.iloc[-1])
TC = ["persona", "factor", "low", "base", "high", "swing"]
card_s = {
    "id": "sensitivity",
    "title": "How much the answer depends on the inputs",
    "module": "7: Sensitivity analysis",
    "stage": "evaluate",
    "used_live": False,
    "order": 18,
    "question": "If the published figures behind CyCRS are off, how much do the rupee amounts and the order of recommended controls change?",
    "data_in": {
        "dataset": "Exported model bundle (model.json) applied to the three largest personas",
        "n_rows": len(sd),
        "variables": [
            var("per_record_cost_inr", "numeric", "ratio", "x0.5 and x1.5"),
            var("effectiveness", "numeric", "ratio", "x0.8 and x1.2, capped at 1"),
            var("p_c", "numeric", "ratio", "x0.8 and x1.2, capped at 1"),
            var("annual_incident_prob", "numeric", "ratio", "x0.5 and x1.5, capped at 1"),
        ],
        "prep_steps": [
            "Three largest personas turned into profiles from their centroids",
            f"Budget INR {BUDGET:,}, no controls in place",
            f"{len(SCENARIOS)} one-at-a-time scenarios per persona",
        ],
        "sample_rows": sd[["persona", "factor", "side", "multiplier", "loss_after_plan_inr", "same_order"]]
        .head(8)
        .to_dict(orient="records"),
    },
    "why": (
        "Every rupee figure multiplies a few published inputs, so moving one input at a time and watching the result shows which sources matter most. "
        f"{order_changes} of {len(sd)} scenarios change the order of the plan and {set_changes} change which controls are in it, which separates rupee uncertainty from advice uncertainty."
    ),
    "data_properties": [
        {"name": "Input with the largest swing", "value": top_f, "implication": "The source to check first."},
        {
            "name": "Input with the smallest swing",
            "value": low_f,
            "implication": "Least influential on the rupee figure.",
        },
        {
            "name": "Scenarios changing plan order",
            "value": f"{order_changes} of {len(sd)}",
            "implication": "Ranking robustness.",
        },
        {
            "name": "Scenarios changing the set of controls",
            "value": f"{set_changes} of {len(sd)}",
            "implication": "Which controls to buy is robust when this is 0.",
        },
    ],
    "alternatives": [
        {
            "model": "Monte Carlo over all inputs at once",
            "why_not": "Needs distributions for each input that the sources do not give; one-at-a-time ranges stay traceable to each source.",
        },
        {
            "model": "No sensitivity check",
            "why_not": f"The per-record cost alone moves results by up to {td['swing'].max():,.0f} INR a year for these personas.",
        },
    ],
    "formula_tex": [
        {"label": "Swing", "tex": r"\Delta_f = \left|L(f_{\text{high}}) - L(f_{\text{low}})\right|"}
    ],
    "assumptions": [
        {
            "check": "Inputs varied one at a time",
            "statistic": float(len(SCENARIOS)),
            "p_value": None,
            "verdict": "interactions ignored",
            "action_taken": "Ranges chosen per input type as briefed.",
        }
    ],
    "results": {
        "key_numbers": {"scenarios": len(sd), "order_changes": order_changes, "set_changes": set_changes},
        "tables": [
            {
                "title": "Tornado data (expected loss after plan, INR)",
                "columns": TC,
                "rows": td[TC].round(2).values.tolist(),
            },
            {
                "title": "Controls stable under every scenario",
                "columns": list(st.columns),
                "rows": st.values.tolist(),
            },
        ],
        "charts": [
            {
                "type": "bar",
                "title": f"Tornado: {nm}",
                "x_label": "Input",
                "y_label": "Expected loss after plan (INR)",
                "data": [
                    {
                        "x": r["factor"],
                        "low": float(r["low"]),
                        "base": float(r["base"]),
                        "high": float(r["high"]),
                    }
                    for _, r in g.iterrows()
                ],
            }
            for nm, g in td.groupby("persona", sort=False)
        ],
    },
    "yields": (
        f"The rupee figures move most with the {top_f} and least with the {low_f}, so the rupee level is only as good as those published averages. "
        + (
            "The set of controls to buy stays the same in every scenario, so the advice holds even when the rupee estimates are off."
            if set_changes == 0
            else f"The set of controls changes in {set_changes} scenarios, so treat those picks as borderline."
        )
    ),
    "feeds": [],
    "limitations": [
        "One-at-a-time ranges ignore inputs moving together.",
        "Only four controls can be scored, which limits how much the plan can change.",
    ],
}
write_card(card_s)
log_event(lg, "cards written", ids=["case-replay", "sensitivity"])

# %% [markdown]
# ## Re-export for the website

# %%
fs = [write_export("cards.json", cards_export()), write_export("sources.json", sources_export())]
(WEB / "SCHEMA.md").write_text(schema_md(), encoding="utf-8")
log_event(lg, "exported", files=[f.name for f in fs], sizes={f.name: f.stat().st_size for f in fs})
