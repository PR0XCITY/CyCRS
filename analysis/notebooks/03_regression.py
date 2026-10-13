# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
# ---

# %% [markdown]
# # 03 Regression: what drives breach size
# Target: y = log10(1 + records lost) for incidents with a known record count.

# %%
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from sklearn.model_selection import train_test_split


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
from src.log import get_logger, log_event
from src.nbutil import (
    ACTORS,
    ASSETS,
    CATS,
    MODELS,
    OUT,
    load_clean,
    sample_rows,
    save_fig,
    sector_group,
    slug,
    top_sectors,
    var,
    write_json,
)
from src.regression import (
    assumption_checks,
    backward_eliminate,
    dummies,
    fit_ols,
    log_employees,
    multipliers,
    summary_row,
    vif_table,
)
from src.sources import load_config

lg = get_logger("nb03", phase="phase3")
df = load_clean()
d = df[df["log_records"].notna()].copy()
top = top_sectors(df)
d["sector_g"] = sector_group(d, top)
d["log_emp"] = log_employees(d["employee_count"])
d["disc_known"] = d["discovery_days"].notna().astype(float)
d["log_disc"] = np.log10(1 + d["discovery_days"]).fillna(0.0)
y = d["log_records"].astype(float)
log_event(lg, "loaded", rows=len(d))

# %% [markdown]
# ## Simple linear regression: y ~ log10(employees)
# Employee count is banded; each band is placed at its geometric midpoint (the open band "Over 100000" at its
# lower bound), so x is log10 of a representative head count.

# %%
s = d[d["log_emp"].notna()]
slr = fit_ols(s[["log_emp"]], s["log_records"])
b0, b1 = slr.params["const"], slr.params["log_emp"]
xs = np.linspace(s["log_emp"].min(), s["log_emp"].max(), 50)
pr = slr.get_prediction(sm.add_constant(pd.DataFrame({"log_emp": xs}), has_constant="add")).summary_frame(
    alpha=0.05
)
jit = s["log_emp"] + np.random.default_rng(42).uniform(-0.08, 0.08, len(s))
fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(jit, s["log_records"], s=5, alpha=0.3, label="incidents (jittered)")
ax.plot(xs, pr["mean"], color="red", label=f"y = {b0:.2f} + {b1:.3f}x")
ax.fill_between(
    xs, pr["mean_ci_lower"], pr["mean_ci_upper"], color="red", alpha=0.2, label="95% confidence band"
)
ax.set_title(f"SLR: records lost vs organisation size (R2 {slr.rsquared:.3f}, n {int(slr.nobs)})")
ax.set_xlabel("log10(employees, band midpoint)")
ax.set_ylabel("log10(1 + records lost)")
ax.legend()
save_fig(fig, "03_slr.png")
log_event(lg, "slr", b0=b0, b1=b1, r2=slr.rsquared, p=slr.pvalues["log_emp"], n=slr.nobs)

# %% [markdown]
# ## Multiple linear regression features

# %%
AC = [f"action_{c}" for c in CATS if d[f"action_{c}"].sum() > 0]
SEC = [f"sector_{slug(t)}" for t in top]
SZ = ["size_medium", "size_large", "size_unknown"]
X = pd.concat(
    [
        d[ACTORS + AC + ASSETS + ["log_disc", "disc_known"]].astype(float),
        dummies(d["sector_g"], top, "sector").rename(
            columns=dict(zip([f"sector_{t}" for t in top], SEC, strict=True))
        ),
        dummies(d["size"], ["medium", "large", "unknown"], "size"),
    ],
    axis=1,
)
dropped_zero = [f"action_{c}" for c in CATS if f"action_{c}" not in AC]
q = pd.qcut(y, 5, labels=False, duplicates="drop")
itr, ite = train_test_split(d.index, test_size=0.3, random_state=42, stratify=q)
Xtr, Xte, ytr, yte = X.loc[itr], X.loc[ite], y.loc[itr], y.loc[ite]

# %% [markdown]
# ## Multicollinearity: VIF, dropping variables above 10

# %%
vif0 = vif_table(Xtr)
vdrop = []
cols = list(Xtr.columns)
while True:
    v = vif_table(Xtr[cols])
    if v["vif"].iloc[0] <= 10:
        break
    w = v["variable"].iloc[0]
    vdrop.append(
        {"variable": w, "vif": float(v["vif"].iloc[0]), "reason": "VIF above 10; overlaps other predictors"}
    )
    cols.remove(w)
vif1 = vif_table(Xtr[cols])
vif1.to_csv(OUT / "03_vif.csv", index=False)
fig, ax = plt.subplots(figsize=(8, 6))
ax.barh(vif1["variable"], vif1["vif"], color="#4c72b0")
ax.axvline(10, color="red", ls="--", label="VIF 10")
ax.set_title("Variance inflation factors, full model predictors")
ax.set_xlabel("VIF")
ax.set_ylabel("Predictor")
ax.legend()
save_fig(fig, "03_vif.png")
log_event(lg, "vif", max_vif=float(vif1["vif"].max()), dropped=vdrop)

# %% [markdown]
# ## Full model and assumption checks

# %%
full0 = fit_ols(Xtr[cols], ytr)
ch = assumption_checks(full0)
robust = ch["breusch_pagan_p"] < 0.05
full = fit_ols(Xtr[cols], ytr, robust=robust)
fit_v, res_v = full0.fittedvalues, full0.resid
fig, axs = plt.subplots(1, 2, figsize=(12, 4.8))
axs[0].scatter(fit_v, res_v, s=5, alpha=0.3)
axs[0].axhline(0, color="red")
axs[0].set_title(f"Residuals vs fitted (Breusch-Pagan p {ch['breusch_pagan_p']:.2g})")
axs[0].set_xlabel("Fitted log10(1 + records lost)")
axs[0].set_ylabel("Residual")
stats.probplot(res_v, dist="norm", plot=axs[1])
axs[1].set_title(f"Residual QQ plot (Jarque-Bera p {ch['jarque_bera_p']:.2g})")
axs[1].set_xlabel("Theoretical normal quantiles")
axs[1].set_ylabel("Residual quantiles")
save_fig(fig, "03_residual_checks.png")
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(res_v.values, lw=0.4)
ax.set_title(f"Residuals in row order (Durbin-Watson {ch['durbin_watson']:.2f})")
ax.set_xlabel("Training row")
ax.set_ylabel("Residual")
save_fig(fig, "03_residual_order.png")
log_event(lg, "assumptions", robust=robust, **ch)

# %% [markdown]
# ## Backward elimination and the business model
# The business model uses only what a business knows before an attack (sector, size) plus indicators for the
# attack category, so CyCRS can price each attack type for a given business.

# %%
back, bcols, bdrop = backward_eliminate(Xtr[cols], ytr, robust=robust)
BUS = [c for c in AC + SEC + SZ if c in cols]
bus = fit_ols(Xtr[BUS], ytr, robust=robust)
cmp = pd.DataFrame(
    [
        summary_row("full", full, Xte[cols], yte, len(cols)),
        summary_row("backward", back, Xte[bcols], yte, len(bcols)),
        summary_row("business", bus, Xte[BUS], yte, len(BUS)),
    ]
)
cmp.to_csv(OUT / "03_model_comparison.csv", index=False)
best_stat = cmp.loc[cmp["test_rmse"].idxmin(), "model"]
best_bic = cmp.loc[cmp["bic"].idxmin(), "model"]
cb = cmp.set_index("model")
gap = cb.loc["business", "test_rmse"] - cb.loc[best_stat, "test_rmse"]
log_event(lg, "comparison", rows=cmp.to_dict(orient="records"), best_rmse=best_stat, best_bic=best_bic)
cmp.round(4)

# %% [markdown]
# ## Back-transformed effects

# %%
mt = pd.concat([multipliers(bus).assign(model="business"), multipliers(full).assign(model="full")])
mt["significant"] = mt["p_value"] < 0.05
mt.to_csv(OUT / "mlr_coefficients.csv", index=False)
bm = multipliers(bus).set_index("term").drop("const")
ka = bm.loc[[c for c in AC if c in bm.index]].sort_values("coef", ascending=False)
ks = bm.loc[[c for c in SEC + SZ if c in bm.index]].sort_values("coef", ascending=False)
cfg = load_config()
write_json(
    {
        "id": "mlr-impact",
        "target": "log10(1 + records lost)",
        "features": BUS,
        "intercept": bus.params["const"],
        "coefficients": {c: bus.params[c] for c in BUS},
        "residual_sd": float(np.sqrt(bus.scale)),
        "reference_levels": {"sector": "Other", "size": "small"},
        "sectors": top,
        "per_record_cost_key": "per_record_cost_inr",
        "robust_se": robust,
    },
    MODELS / "mlr_impact.json",
)
mt.round(4)

# %% [markdown]
# ## Cards

# %%
st = pd.read_csv(OUT / "02_summary_stats.csv").set_index("variable")
fd = pd.read_csv(OUT / "02_distribution_fit.csv").set_index("distribution")
sk_y = float(st.loc["records_lost", "skewness"])
pts = s[["log_emp", "log_records"]].sample(300, random_state=42)
size_effect = (
    f"multiplies expected records lost by about {10**b1:.2f}"
    if b1 >= 0
    else f"cuts expected records lost to about {100 * 10**b1:.0f}% (larger organisations in VCDB tend to lose fewer records)"
)
card_s = {
    "id": "slr",
    "title": "Does a bigger organisation lose more records?",
    "module": "3: Simple linear regression",
    "stage": "explore",
    "used_live": False,
    "order": 6,
    "question": "How much does the size of an organisation alone explain how many records it loses in a breach?",
    "data_in": {
        "dataset": "VCDB incidents with known records lost and an exact employee band",
        "n_rows": int(slr.nobs),
        "variables": [
            var("employee_count", "categorical", "ordinal", "log10 of band geometric midpoint"),
            var("data_total", "numeric", "ratio", "log10(1 + x)"),
        ],
        "prep_steps": [
            "Kept incidents with a known record count and an exact employee band (coarse Small, Large, Unknown dropped)",
            "Placed each band at its geometric midpoint; Over 100000 at its lower bound",
        ],
        "sample_rows": sample_rows(s, ["employee_count", "log_emp", "log_records"]),
    },
    "why": (
        f"Both variables are on log scales, where breach size is close to symmetric (skewness {st.loc['log10_records_lost', 'skewness']:.2f}), "
        "so a straight line is a fair first model. "
        f"A single predictor shows how much size alone explains before adding attack details; here R2 is {slr.rsquared:.3f}."
    ),
    "data_properties": [
        {
            "name": "Slope (log records per log employee)",
            "value": b1,
            "implication": f"Ten times more staff multiplies expected records lost by {10**b1:.2f}.",
        },
        {
            "name": "R2",
            "value": slr.rsquared,
            "implication": "Share of variation in breach size explained by size alone.",
        },
        {
            "name": "Slope p-value",
            "value": float(slr.pvalues["log_emp"]),
            "implication": "Whether the size effect is distinguishable from zero.",
        },
    ],
    "alternatives": [
        {
            "model": "Raw records on raw employee count",
            "why_not": f"Records lost has skewness {sk_y:.1f}; a raw-scale line would be dominated by a few mega breaches.",
        },
        {
            "model": "Multiple regression",
            "why_not": "Used next; this single-predictor model is the baseline it must improve on.",
        },
    ],
    "formula_tex": [
        {"label": "Fitted line", "tex": rf"\hat y = {b0:.3f} + {b1:.3f}\,\log_{{10}}(\text{{employees}})"}
    ],
    "assumptions": [
        {
            "check": "Slope t-test",
            "statistic": float(slr.tvalues["log_emp"]),
            "p_value": float(slr.pvalues["log_emp"]),
            "verdict": "significant" if slr.pvalues["log_emp"] < 0.05 else "not significant",
            "action_taken": "Size kept as a predictor in the multiple model.",
        }
    ],
    "results": {
        "key_numbers": {
            "intercept": b0,
            "slope": b1,
            "r2": slr.rsquared,
            "p_value": float(slr.pvalues["log_emp"]),
            "n": int(slr.nobs),
        },
        "tables": [
            {
                "title": "SLR coefficients",
                "columns": ["term", "coef", "se", "p_value"],
                "rows": [
                    [t, float(slr.params[t]), float(slr.bse[t]), float(slr.pvalues[t])]
                    for t in slr.params.index
                ],
            }
        ],
        "charts": [
            {
                "type": "scatter",
                "title": "Records lost vs organisation size",
                "x_label": "log10(employees)",
                "y_label": "log10(1 + records lost)",
                "data": [{"x": float(a), "y": float(b)} for a, b in pts.values],
            },
            {
                "type": "line",
                "title": "Fitted line with 95% band",
                "x_label": "log10(employees)",
                "y_label": "log10(1 + records lost)",
                "data": [
                    {"x": float(a), "y": float(m), "lo": float(lo), "hi": float(hi)}
                    for a, m, lo, hi in zip(
                        xs, pr["mean"], pr["mean_ci_lower"], pr["mean_ci_upper"], strict=True
                    )
                ],
            },
        ],
    },
    "yields": (
        f"Each tenfold increase in staff {size_effect}, but size alone explains only "
        f"{100 * slr.rsquared:.1f}% of the variation. "
        "So CyCRS does not judge breach size from company size alone; it adds sector and attack type in the multiple model."
    ),
    "feeds": ["mlr-impact"],
    "limitations": [
        "Employee count is banded, so x takes only eight values.",
        "Large organisations dominate VCDB.",
    ],
}
write_card(card_s)

top_a = ka.index[0].replace("action_", "")
LABEL = {
    **{f"sector_{slug(t)}": f"the {t} sector" for t in top},
    "size_medium": "medium size",
    "size_large": "large size",
    "size_unknown": "unknown size",
}
top_s = LABEL[ks.index[0]]
TBL = ["term", "coef", "se", "p_value", "multiplier", "mult_low", "mult_high"]
asm = [
    {
        "check": "Linearity and constant variance: Breusch-Pagan",
        "statistic": ch["breusch_pagan"],
        "p_value": ch["breusch_pagan_p"],
        "verdict": "heteroscedastic" if robust else "constant variance",
        "action_taken": "HC3 robust standard errors used for all models."
        if robust
        else "Ordinary standard errors kept.",
    },
    {
        "check": "Normal residuals: Jarque-Bera",
        "statistic": ch["jarque_bera"],
        "p_value": ch["jarque_bera_p"],
        "verdict": "not normal" if ch["jarque_bera_p"] < 0.05 else "normal",
        "action_taken": f"With {int(full0.nobs)} training rows the coefficients are still approximately normal (central limit theorem); intervals read with caution.",
    },
    {
        "check": "Independent residuals: Durbin-Watson",
        "statistic": ch["durbin_watson"],
        "p_value": None,
        "verdict": "no autocorrelation" if 1.5 < ch["durbin_watson"] < 2.5 else "possible autocorrelation",
        "action_taken": "None needed." if 1.5 < ch["durbin_watson"] < 2.5 else "Reported as a limitation.",
    },
    {
        "check": "Multicollinearity: maximum VIF",
        "statistic": float(vif1["vif"].max()),
        "p_value": None,
        "verdict": "acceptable" if vif1["vif"].max() <= 10 else "high",
        "action_taken": ("Dropped " + ", ".join(v["variable"] for v in vdrop))
        if vdrop
        else "No variable above 10; none dropped.",
    },
]
card_m = {
    "id": "mlr-impact",
    "title": "How big a breach could be",
    "module": "3: Multiple linear regression",
    "stage": "impact",
    "used_live": True,
    "order": 7,
    "question": "Given a business's sector, size and the type of attack, how many records would a breach be expected to expose?",
    "data_in": {
        "dataset": "VCDB incidents with known records lost",
        "n_rows": len(d),
        "variables": [
            var("data_total", "numeric", "ratio", "log10(1 + x) target"),
            var("action_*", "binary", "nominal"),
            var("actor_*", "binary", "nominal"),
            var("asset_*", "binary", "nominal"),
            var("sector", "categorical", "nominal", "dummies for top 8, reference Other"),
            var("size", "categorical", "ordinal", "dummies, reference small"),
            var("discovery_days", "numeric", "ratio", "log10(1 + x), 0 with a known-flag when missing"),
        ],
        "prep_steps": [
            f"Stratified 70/30 split on target quintiles (random_state 42): {len(itr)} train, {len(ite)} test",
            f"Dropped {', '.join(dropped_zero) if dropped_zero else 'no'} action columns with no positive cases",
            "Discovery time missing for most rows, so the full model uses log days set to 0 plus a disc_known flag",
            "VIF checked and Breusch-Pagan decided robust errors",
        ],
        "sample_rows": sample_rows(d, ["sector_g", "size", *AC, "log_records"]),
    },
    "why": (
        f"Records lost has skewness {sk_y:.1f} and a lognormal curve fits it far better than a normal one (KS D "
        f"{fd.loc['lognormal', 'ks_d']:.3f} vs {fd.loc['normal', 'ks_d']:.3f}), so the target is log10(1 + records). "
        "On that scale effects are multiplicative and OLS gives coefficients a business owner can read as 'this attack "
        "multiplies expected records lost by 10 to the power b'. "
        f"Breusch-Pagan p is {ch['breusch_pagan_p']:.2g}, so "
        + ("HC3 robust standard errors are used." if robust else "ordinary errors are kept.")
    ),
    "data_properties": [
        {"name": "Skewness of records lost", "value": sk_y, "implication": "Log transform needed."},
        {
            "name": "Breusch-Pagan p",
            "value": ch["breusch_pagan_p"],
            "implication": "Robust errors." if robust else "Constant variance.",
        },
        {
            "name": "Jarque-Bera p",
            "value": ch["jarque_bera_p"],
            "implication": "Residuals not exactly normal; large n protects inference.",
        },
        {
            "name": "Durbin-Watson",
            "value": ch["durbin_watson"],
            "implication": "Residual independence check.",
        },
        {
            "name": "Maximum VIF",
            "value": float(vif1["vif"].max()),
            "implication": "Predictors are not redundant.",
        },
        {
            "name": "Test RMSE gap, business vs best model",
            "value": float(gap),
            "implication": "Accuracy given up to use only pre-attack inputs.",
        },
    ],
    "alternatives": [
        {
            "model": "Simple linear regression on size",
            "why_not": f"One predictor explains only {100 * slr.rsquared:.1f}% and misses sector and attack effects.",
        },
        {
            "model": "Full model",
            "why_not": f"Test RMSE {cb.loc['full', 'test_rmse']:.3f} vs {cb.loc['business', 'test_rmse']:.3f}, but it needs actor, asset and discovery details known only after an attack.",
        },
        {
            "model": "Backward elimination model",
            "why_not": f"Keeps {len(bcols)} predictors including post-attack ones; same problem as the full model.",
        },
    ],
    "formula_tex": [
        {
            "label": "Model",
            "tex": r"\log_{10}(1+\text{records}) = \beta_0 + \sum_j \beta_j x_j + \varepsilon",
        },
        {"label": "Back-transformed effect", "tex": r"\text{multiplier}_j = 10^{\beta_j}"},
        {"label": "Expected records", "tex": r"\widehat{\text{records}} = 10^{\hat y} - 1"},
        {
            "label": "Expected cost",
            "tex": r"\widehat{\text{cost}} = \widehat{\text{records}} \times \text{cost per record (INR)}",
        },
    ],
    "assumptions": asm,
    "results": {
        "key_numbers": {
            "r2_business": cb.loc["business", "r2"],
            "adj_r2_business": cb.loc["business", "adj_r2"],
            "test_rmse_business": cb.loc["business", "test_rmse"],
            "test_rmse_full": cb.loc["full", "test_rmse"],
            "per_record_cost_inr": cfg["per_record_cost_inr"],
        },
        "tables": [
            {
                "title": "Business model coefficients and multipliers",
                "columns": TBL,
                "rows": multipliers(bus)[TBL].round(6).values.tolist(),
            },
            {
                "title": "Assumption checks",
                "columns": ["check", "statistic", "p_value", "verdict", "action_taken"],
                "rows": [
                    [a["check"], a["statistic"], a["p_value"], a["verdict"], a["action_taken"]] for a in asm
                ],
            },
            {"title": "Model comparison", "columns": list(cmp.columns), "rows": cmp.round(6).values.tolist()},
        ],
        "charts": [
            {
                "type": "scatter",
                "title": "Residuals vs fitted (full model, 300 rows)",
                "x_label": "Fitted",
                "y_label": "Residual",
                "data": [
                    {"x": float(a), "y": float(b)}
                    for a, b in pd.concat([fit_v, res_v], axis=1).sample(300, random_state=42).values
                ],
            },
            {
                "type": "bar",
                "title": "Multiplier by attack category (business model)",
                "x_label": "Attack category",
                "y_label": "Multiplier on expected records",
                "data": [
                    {
                        "x": i.replace("action_", ""),
                        "y": float(r["multiplier"]),
                        "lo": float(r["mult_low"]),
                        "hi": float(r["mult_high"]),
                    }
                    for i, r in ka.iterrows()
                ],
            },
        ],
    },
    "yields": (
        f"Holding sector and size fixed, {top_a} attacks raise expected records lost the most, multiplying them by "
        f"{ka.iloc[0]['multiplier']:.2f}, and {top_s} has the largest sector or size effect "
        f"({ks.iloc[0]['multiplier']:.2f} times). "
        f"CyCRS uses this model to estimate records lost for each attack type and multiplies by the cost per record "
        f"(INR {cfg['per_record_cost_inr']:,.0f}) to price each attack in rupees."
    ),
    "feeds": ["decision"],
    "limitations": [
        f"Business model explains {100 * cb.loc['business', 'r2']:.1f}% of variation; individual breaches vary widely around the estimate.",
        "Cost per record is derived from IBM India averages and applied to every attack type.",
        "VCDB over represents large and US organisations.",
    ],
}
write_card(card_m)
log_event(lg, "cards written", ids=["slr", "mlr-impact"])
