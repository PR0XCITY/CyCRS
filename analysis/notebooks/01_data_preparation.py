# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
# ---

# %% [markdown]
# # 01 Data preparation
# VCDB validated incidents flattened to one row per incident, profiled and cleaned.

# %%
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats


def find_root():
    try:
        c = Path(__file__).resolve().parent
    except NameError:
        c = Path.cwd()
    for p in (c, *c.parents):
        if (p / "src" / "cards.py").exists():
            return p
        if (p / "analysis" / "src" / "cards.py").exists():
            return p / "analysis"
    raise FileNotFoundError("analysis root not found")


A = find_root()
sys.path.insert(0, str(A))

from src.cards import write_card
from src.load_vcdb import (
    VALIDATED,
    flatten_incident,
    list_incident_files,
    load_sectors,
    load_vcdb,
    read_incident,
)
from src.log import get_logger, log_event

FIG = A / "figures"
OUT = A / "outputs"
PROC = A / "data" / "processed"
for p in (FIG, OUT, PROC):
    p.mkdir(parents=True, exist_ok=True)
lg = get_logger("nb01", phase="phase1")
rng = np.random.default_rng(42)

# %% [markdown]
# ## Load and flatten

# %%
fs = list_incident_files(VALIDATED)
sm = load_sectors()
df = load_vcdb(VALIDATED, sm)
n_raw, n_flat = len(fs), len(df)
log_event(lg, "flattened", raw=n_raw, rows=n_flat, cols=df.shape[1])

# %% [markdown]
# ## Variable types and scales

# %%
FLAGS = [c for c in df.columns if df[c].dropna().isin([0, 1]).all() and c not in ("breach",)]
NOMINAL = ["sector_code", "sector", "country", "motive", "data_disclosure", "discovery_unit"]
ORDINAL = ["employee_count", "size"]
RATIO = ["data_total", "discovery_days"]


def describe_variable(c):
    if c in ("incident_id", "source_file"):
        return c, "identifier", "nominal", "dropped before modelling"
    if c == "breach":
        return c, "binary target", "nominal", "1 Yes, 0 No, else missing"
    if c in RATIO:
        return c, "numeric continuous", "ratio", "log10(1 + x)" if c == "data_total" else "none"
    if c == "year":
        return c, "numeric discrete", "interval", "none"
    if c in ORDINAL:
        return c, "categorical", "ordinal", "ordered levels, Unknown kept as level"
    if c in NOMINAL:
        return c, "categorical", "nominal", "one-hot, Unknown kept as level"
    return c, "binary flag", "nominal", "0/1 as is"


vt = pd.DataFrame(
    [describe_variable(c) for c in df.columns], columns=["variable", "type", "scale", "transform"]
)
vt.to_csv(OUT / "01_variable_types.csv", index=False)
vt["type"].value_counts()

# %% [markdown]
# ## Missing values
# VERIS records unknowns explicitly as "Unknown", and a missing attribute section as absent.
# Both are treated as missing for the audit below.

# %%
UNK = {"Unknown", "Not coded", "NA", "00"}


def missing_mask(s):
    if s.dtype == object or str(s.dtype) in ("string", "str"):
        return s.isna() | s.isin(UNK)
    return s.isna()


AUDIT = [
    "sector",
    "size",
    "country",
    "motive",
    "data_disclosure",
    "data_total",
    "discovery_days",
    "year",
    "breach",
]
mm = pd.DataFrame({c: missing_mask(df[c]) for c in AUDIT})
mt = pd.DataFrame({"variable": AUDIT, "missing": mm.sum().values, "pct": (100 * mm.mean()).round(2).values})
mt.to_csv(OUT / "01_missing_values.csv", index=False)

fig, ax = plt.subplots(figsize=(9, 5))
ix = np.sort(rng.choice(len(mm), size=min(1500, len(mm)), replace=False))
sns.heatmap(mm.iloc[ix].astype(int).T, cbar=False, cmap="Greys", ax=ax, xticklabels=False)
ax.set_title("Missing or Unknown values, 1500 random incidents (black = missing)")
ax.set_xlabel("Incident (random sample, seed 42)")
ax.set_ylabel("Variable")
fig.tight_layout()
fig.savefig(FIG / "01_missing_heatmap.png", dpi=200)
plt.close(fig)
mt

# %% [markdown]
# ## Handling of "Unknown"
# Categorical Unknown is kept as its own level: in VERIS it means the reporter did not know,
# which is informative and not random. Numeric gaps are not imputed; each model drops
# rows missing its own target or numeric inputs.

# %%
lw = int(mm.any(axis=1).sum())
lw_pct = 100 * lw / n_flat
dt = df["data_total"].dropna()
mean_dt, med_dt = float(dt.mean()), float(dt.median())

# %% [markdown]
# ## Records lost: skewness and outliers

# %%
lr = np.log10(1 + dt)
sk0, sk1 = float(stats.skew(dt)), float(stats.skew(lr))
k2, p_norm = stats.normaltest(lr)


def iqr_outliers(s):
    q1, q3 = np.percentile(s, [25, 75])
    r = q3 - q1
    return int(((s < q1 - 1.5 * r) | (s > q3 + 1.5 * r)).sum()), float(q1), float(q3)


o0, q1a, q3a = iqr_outliers(dt)
o1, q1b, q3b = iqr_outliers(lr)
fig, axs = plt.subplots(1, 2, figsize=(11, 4.5))
axs[0].hist(dt, bins=60, color="#4c72b0")
axs[0].set_title(f"Records lost, raw (skewness {sk0:.1f})")
axs[0].set_xlabel("Records lost")
axs[0].set_ylabel("Incidents")
axs[1].hist(lr, bins=40, color="#55a868")
axs[1].set_title(f"Records lost, log10(1 + x) (skewness {sk1:.2f})")
axs[1].set_xlabel("log10(1 + records lost)")
axs[1].set_ylabel("Incidents")
fig.tight_layout()
fig.savefig(FIG / "01_records_skewness.png", dpi=200)
plt.close(fig)
sk = pd.DataFrame(
    {
        "measure": ["skewness", "iqr_outliers", "q1", "q3"],
        "raw": [sk0, o0, q1a, q3a],
        "log10_1p": [sk1, o1, q1b, q3b],
    }
)
sk.to_csv(OUT / "01_records_skewness.csv", index=False)
log_event(lg, "skewness", raw=sk0, log=sk1, outliers_raw=o0, outliers_log=o1)
sk

# %% [markdown]
# ## Target and modelling sets

# %%
df["log_records"] = np.log10(1 + df["data_total"])
cls = df[df["breach"].notna()]
reg = df[df["data_total"].notna()]
n_cls, n_reg = len(cls), len(reg)
n_pos = int((cls["breach"] == 1).sum())
n_neg = int((cls["breach"] == 0).sum())
pos_pct = 100 * n_pos / n_cls
dc = df["data_disclosure"].value_counts()
lin = pd.DataFrame(
    {
        "step": [
            "raw validated files",
            "flattened incidents",
            "classifier set (Yes or No)",
            "regression set",
        ],
        "rows": [n_raw, n_flat, n_cls, n_reg],
        "rule": [
            "data/json/validated/*.json",
            "one row per incident",
            "data_disclosure Yes=1; No or no confidentiality section (Not coded)=0; Potentially, Unknown dropped",
            "data_total known (numeric, at least 0)",
        ],
    }
)
lin.to_csv(OUT / "01_lineage.csv", index=False)
log_event(lg, "sets", cls=n_cls, pos=n_pos, neg=n_neg, reg=n_reg)
lin

# %% [markdown]
# ## Encoding plan

# %%
top_c = df.loc[df["country"] != "Unknown", "country"].value_counts().head(10).index.tolist()
ep = pd.DataFrame(
    [
        ("sector", "one-hot, sectors under 1% merged to Other", df["sector"].nunique()),
        ("size", "ordinal small < medium < large, plus unknown dummy", df["size"].nunique()),
        ("country", "one-hot top 10, rest Other", len(top_c) + 1),
        ("motive", "one-hot", df["motive"].nunique()),
        (
            "action_*, v_*, vec_*, asset_*",
            "binary 0/1 as is",
            len([c for c in FLAGS if c[:2] in ("ac", "v_", "ve", "as")]),
        ),
        ("data_total", "log10(1 + x), missing left missing", 1),
        ("discovery_days", "log10(1 + x) where used, missing left missing", 1),
        ("year", "numeric", 1),
    ],
    columns=["variable", "encoding", "levels_or_columns"],
)
ep.to_csv(OUT / "01_encoding_plan.csv", index=False)

# %% [markdown]
# ## Save

# %%
df.to_parquet(PROC / "vcdb_clean.parquet", index=False)
shape = df.shape
log_event(lg, "saved", rows=shape[0], cols=shape[1])
shape

# %% [markdown]
# ## Example incident

# %%
KEEP = {
    "victim": ("industry", "employee_count", "country"),
    "actor": None,
    "action": None,
    "asset": ("assets",),
    "attribute": None,
    "timeline": ("incident", "discovery"),
}
DROP = {"notes", "name", "cve", "victim_id", "data_victim", "region", "state"}


def strip_text(v):
    if isinstance(v, dict):
        return {k: strip_text(x) for k, x in v.items() if k not in DROP}
    if isinstance(v, list):
        return [strip_text(x) for x in v]
    return v


def trim_incident(j):
    o = {}
    for k, ks in KEEP.items():
        v = j.get(k) or {}
        o[k] = strip_text({x: v[x] for x in ks if x in v} if ks else v)
    return o


ef = fs[int(rng.integers(len(fs)))]
ej = read_incident(ef)
er = flatten_incident(ej, sm)
er.pop("incident_id")
er.pop("source_file", None)
ex = {"source": "VCDB data/json/validated", "incident": trim_incident(ej), "flattened": er}
(PROC / "example_incident.json").write_text(json.dumps(ex, indent=2, default=float), encoding="utf-8")

# %% [markdown]
# ## Card

# %%
SC = [
    "sector",
    "size",
    "motive",
    "action_hacking",
    "action_error",
    "data_disclosure",
    "data_total",
    "log_records",
]
sr = df[SC].sample(8, random_state=42)
sr = sr.astype(object).where(sr.notna(), None).to_dict(orient="records")
hb, he = np.histogram(lr, bins=20)
card = {
    "id": "data-preparation",
    "title": "Preparing the breach records",
    "module": "1: Descriptive statistics and data preparation",
    "stage": "prepare",
    "used_live": False,
    "order": 1,
    "question": "Which incident records can we trust and use, and in what form, to learn how breaches happen?",
    "data_in": {
        "dataset": "VERIS Community Database (VCDB), validated incidents",
        "n_rows": n_flat,
        "variables": vt[~vt["variable"].isin(["incident_id", "source_file"])]
        .rename(columns={"variable": "name"})
        .to_dict(orient="records"),
        "prep_steps": [
            f"Read {n_raw} validated incident files and flattened each into one row of {shape[1] - 2} fields plus two ids",
            "Mapped the first two NAICS digits to the Census 2022 sector name",
            "Grouped employee counts into small (up to 100, or VERIS Small), medium (101 to 1000), large",
            "Kept Unknown as its own category instead of filling it in",
            f"Took log10(1 + records lost) for the {n_reg} incidents with a known count",
            f"Breach target: Yes is 1; No, or no confidentiality section at all, is 0 (VERIS records that section only when data was affected); Potentially and Unknown dropped, leaving {n_cls} incidents",
        ],
        "sample_rows": sr,
    },
    "why": (
        f"Records lost is extremely right skewed (skewness {sk0:.1f}): the mean is {mean_dt:,.0f} "
        f"while the median is {med_dt:,.0f}, so a few mega breaches dominate any raw average. "
        f"After log10(1 + x) the skewness falls to {sk1:.2f}, which makes regression and distance "
        f"based methods usable. Dropping every row with any gap would remove {lw_pct:.0f}% of incidents, "
        "so Unknown is kept as a category and only each model's own inputs must be present."
    ),
    "data_properties": [
        {
            "name": "Skewness of records lost (raw)",
            "value": round(sk0, 4),
            "implication": "A few huge breaches dominate; raw averages and linear fits would be misleading.",
        },
        {
            "name": "Skewness of log10(1 + records lost)",
            "value": round(sk1, 4),
            "implication": "Close to symmetric, so the log scale is used for every model of breach size.",
        },
        {
            "name": "IQR outliers in records lost, raw then log",
            "value": f"{o0} then {o1}",
            "implication": "The log scale turns most extreme values into ordinary ones, so none are deleted.",
        },
        {
            "name": "Share of breach target that is Yes",
            "value": f"{pos_pct:.2f}% ({n_pos} Yes, {n_neg} No)",
            "implication": "Very unbalanced classes: accuracy is meaningless, use ROC AUC and class weights.",
        },
        {
            "name": "Rows with at least one missing or Unknown field",
            "value": f"{lw_pct:.1f}%",
            "implication": "Listwise deletion would throw away most of the data.",
        },
    ],
    "alternatives": [
        {
            "model": "Mean imputation of records lost",
            "why_not": (
                f"The mean ({mean_dt:,.0f}) is far above the median ({med_dt:,.0f}) because of skewness "
                f"{sk0:.1f}, so filling gaps with it would invent huge breaches."
            ),
        },
        {
            "model": "Listwise deletion across all fields",
            "why_not": f"It would drop {lw} of {n_flat} incidents ({lw_pct:.0f}%), mostly because Unknown is common.",
        },
        {
            "model": "Treating Potentially as Yes for the target",
            "why_not": (
                f"{int(dc.get('Potentially', 0))} incidents say only Potentially; counting them as breaches "
                "would mix confirmed and suspected losses."
            ),
        },
    ],
    "formula_tex": [
        {"label": "Log transform", "tex": r"y = \log_{10}(1 + x)"},
        {
            "label": "Sample skewness",
            "tex": r"g_1 = \frac{\frac{1}{n}\sum_{i=1}^{n}(x_i-\bar{x})^3}{\left(\frac{1}{n}\sum_{i=1}^{n}(x_i-\bar{x})^2\right)^{3/2}}",
        },
        {
            "label": "IQR outlier fences",
            "tex": r"x < Q_1 - 1.5\,\mathrm{IQR} \;\text{or}\; x > Q_3 + 1.5\,\mathrm{IQR}",
        },
    ],
    "assumptions": [
        {
            "check": "Normality of log10(1 + records lost), D'Agostino K squared",
            "statistic": round(float(k2), 4),
            "p_value": float(p_norm),
            "verdict": "not normal" if p_norm < 0.05 else "normal",
            "action_taken": "Keep log scale for symmetry; later models use tests robust to non-normality where needed.",
        }
    ],
    "results": {
        "key_numbers": {
            "raw_files": n_raw,
            "flattened_rows": n_flat,
            "columns": shape[1],
            "classifier_rows": n_cls,
            "breach_yes": n_pos,
            "breach_no": n_neg,
            "regression_rows": n_reg,
            "skew_raw": sk0,
            "mean_records_lost": mean_dt,
            "median_records_lost": med_dt,
            "skew_log": sk1,
        },
        "tables": [
            {
                "title": "Row counts at each step",
                "columns": ["step", "rows", "rule"],
                "rows": lin.values.tolist(),
            },
            {
                "title": "Missing or Unknown values",
                "columns": ["variable", "missing", "pct"],
                "rows": mt.values.tolist(),
            },
            {
                "title": "Data disclosure values",
                "columns": ["value", "incidents"],
                "rows": [[k, int(v)] for k, v in dc.items()],
            },
        ],
        "charts": [
            {
                "type": "bar",
                "title": "Incidents kept at each step",
                "x_label": "Step",
                "y_label": "Incidents",
                "data": [{"x": s, "y": int(r)} for s, r in zip(lin["step"], lin["rows"], strict=True)],
            },
            {
                "type": "histogram",
                "title": "Records lost on the log scale",
                "x_label": "log10(1 + records lost)",
                "y_label": "Incidents",
                "data": [
                    {"x0": float(he[i]), "x1": float(he[i + 1]), "y": int(hb[i])} for i in range(len(hb))
                ],
            },
        ],
    },
    "yields": (
        f"Out of {n_flat} public incident reports, {n_cls} clearly say whether data was exposed and "
        f"{n_reg} say how many records were lost. CyCRS learns how breaches happen from these rows and measures "
        "breach size on a log scale so one giant leak does not distort the picture for a small business."
    ),
    "feeds": [],
    "limitations": [
        f"Only {n_neg} incidents ({100 * n_neg / n_cls:.1f}%) are No, so the breach classifier still has far fewer negatives than positives.",
        f"{int(dc.get('Not coded', 0))} incidents have no confidentiality section and are counted as no disclosure; this assumes the coder would have recorded any data exposure.",
        "VCDB is built from public news reports, so large and US organisations are over represented.",
        "VERIS Small (up to 1000 staff) cannot be split and is counted as small.",
        f"Discovery time in days is known for only {int(df['discovery_days'].notna().sum())} incidents.",
    ],
}
write_card(card)
log_event(lg, "card written", id=card["id"])
