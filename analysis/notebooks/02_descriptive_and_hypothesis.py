# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
# ---

# %% [markdown]
# # 02 Descriptive statistics, distributions and hypothesis tests

# %%
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import squarify
from scipy import stats


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
from src.stats_tests import (
    anova,
    chi_square,
    decide,
    dunn,
    effect_label,
    holm,
    kruskal,
    levene,
    mann_whitney,
    normality,
    tukey,
    two_proportion_z,
)

FIG = A / "figures"
OUT = A / "outputs"
lg = get_logger("nb02", phase="phase2")
df = pd.read_parquet(A / "data" / "processed" / "vcdb_clean.parquet")
CATS = ["hacking", "malware", "social", "error", "misuse", "physical", "environmental"]
AC = [f"action_{c}" for c in CATS]
EXACT = [
    "1 to 10",
    "11 to 100",
    "101 to 1000",
    "1001 to 10000",
    "10001 to 25000",
    "25001 to 50000",
    "50001 to 100000",
    "Over 100000",
]
SIZES = ["small", "medium", "large"]


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIG / name, dpi=200)
    plt.close(fig)


def short(s):
    return s if len(s) <= 22 else s[:20].rstrip(" ,") + "."


def primary_action(r):
    hs = [c for c in CATS if r[f"action_{c}"] == 1]
    if len(hs) == 1:
        return hs[0]
    return "multiple" if hs else "unknown"


def actor_type(r):
    hs = [k for k in ("external", "internal", "partner") if r[f"actor_{k}"] == 1]
    if len(hs) == 1:
        return hs[0]
    return "multiple" if hs else "unknown"


df["action_primary"] = df.apply(primary_action, axis=1)
df["actor_type"] = df.apply(actor_type, axis=1)
df["emp_code"] = df["employee_count"].map({k: i + 1 for i, k in enumerate(EXACT)})
df["log_discovery"] = np.log10(1 + df["discovery_days"])
top8 = df.loc[df["sector"] != "Unknown", "sector"].value_counts().head(8).index.tolist()
log_event(lg, "loaded", rows=len(df), top8=top8)

# %% [markdown]
# ## Summary statistics
# Employee count is reported in bands, so it is summarised on the ordinal band code (1 = 1 to 10, 8 = over 100000)
# for the incidents with an exact band; the mean of a band code is shown for completeness only.

# %%


def summarise(s, name, unit):
    x = s.dropna().astype(float)
    m = stats.mode(x, keepdims=False)
    q1, q3 = np.percentile(x, [25, 75])
    return {
        "variable": name,
        "unit": unit,
        "n": len(x),
        "mean": x.mean(),
        "median": x.median(),
        "mode": float(m.mode),
        "sd": x.std(ddof=1),
        "variance": x.var(ddof=1),
        "iqr": q3 - q1,
        "skewness": float(stats.skew(x)),
        "kurtosis": float(stats.kurtosis(x)),
    }


st = pd.DataFrame(
    [
        summarise(df["data_total"], "records_lost", "records"),
        summarise(df["log_records"], "log10_records_lost", "log10(1 + records)"),
        summarise(df["discovery_days"], "discovery_days", "days"),
        summarise(df["emp_code"], "employee_band", "ordinal band 1 to 8"),
    ]
)
st.to_csv(OUT / "02_summary_stats.csv", index=False)
log_event(lg, "summary", rows=st.round(4).to_dict(orient="records"))
st.round(3)

# %% [markdown]
# ## Charts

# %%
lr = df["log_records"].dropna()
fig, ax = plt.subplots(figsize=(8, 4.5))
hb, he, _ = ax.hist(lr, bins=30, color="#4c72b0")
ax.set_title("Records lost per incident (log scale)")
ax.set_xlabel("log10(1 + records lost)")
ax.set_ylabel("Incidents")
save(fig, "02_hist_log_records.png")

ac = df[AC].sum().rename(index=dict(zip(AC, CATS, strict=True))).sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.bar(ac.index, ac.values, color="#55a868")
ax.set_title("Incidents involving each action category")
ax.set_xlabel("Action category (an incident can have several)")
ax.set_ylabel("Incidents")
save(fig, "02_bar_action_categories.png")

at = df["actor_type"].value_counts()
fig, ax = plt.subplots(figsize=(6, 6))
ax.pie(at.values, labels=at.index, autopct="%1.1f%%", startangle=90)
ax.set_title("Who caused the incident (actor type)")
save(fig, "02_pie_actor_type.png")

bx = df[df["sector"].isin(top8) & df["log_records"].notna()]
od = bx.groupby("sector")["log_records"].median().sort_values().index
fig, ax = plt.subplots(figsize=(10, 5.5))
sns.boxplot(data=bx, y="sector", x="log_records", order=od, ax=ax, color="#8da0cb")
ax.set_yticks(range(len(od)), [short(s) for s in od])
ax.set_title("Records lost by sector, top 8 sectors (log scale)")
ax.set_xlabel("log10(1 + records lost)")
ax.set_ylabel("Sector")
save(fig, "02_box_log_records_by_sector.png")

sc = df[["log_discovery", "log_records"]].dropna()
rho_sc, p_sc = stats.spearmanr(sc["log_discovery"], sc["log_records"])
fig, ax = plt.subplots(figsize=(7, 5))
ax.scatter(sc["log_discovery"], sc["log_records"], s=6, alpha=0.4)
ax.set_title(f"Discovery time vs records lost (Spearman rho {rho_sc:.2f}, n {len(sc)})")
ax.set_xlabel("log10(1 + days to discovery)")
ax.set_ylabel("log10(1 + records lost)")
save(fig, "02_scatter_discovery_records.png")

tm = df[df["sector"].isin(top8)].melt(id_vars="sector", value_vars=AC, var_name="action", value_name="f")
tm = tm[tm["f"] == 1].groupby(["sector", "action"]).size().reset_index(name="n")
tm = tm[tm["n"] > 0].sort_values(["sector", "n"], ascending=[True, False])
tot = tm.groupby("sector")["n"].sum().sort_values(ascending=False)
pal = dict(zip(tot.index, sns.color_palette("tab10", len(tot)), strict=True))
tm["sector"] = pd.Categorical(tm["sector"], categories=tot.index, ordered=True)
tm = tm.sort_values(["sector", "n"], ascending=[True, False])
lb = [
    f"{short(s)[:12]}\n{a.replace('action_', '')}" if n / tm["n"].sum() > 0.012 else ""
    for s, a, n in zip(tm["sector"], tm["action"], tm["n"], strict=True)
]
fig, ax = plt.subplots(figsize=(13, 8))
squarify.plot(
    sizes=tm["n"],
    label=lb,
    color=[pal[s] for s in tm["sector"]],
    alpha=0.85,
    ax=ax,
    text_kwargs={"fontsize": 7},
)
ax.set_title("Sector > action category, top 8 sectors (area = incidents, colour = sector)")
ax.set_xlabel("Treemap area is proportional to incident count")
ax.set_ylabel("")
ax.set_xticks([])
ax.set_yticks([])
save(fig, "02_treemap_sector_action.png")

yr = df[(df["year"] >= 2010) & (df["year"] <= 2025)].groupby("year")[AC].sum()
yr.columns = CATS
fig, ax = plt.subplots(figsize=(10, 5))
for c in CATS:
    ax.plot(yr.index.astype(int), yr[c], marker="o", label=c)
ax.set_title("Incidents per action category by incident year, 2010 to 2025")
ax.set_xlabel("Incident year")
ax.set_ylabel("Incidents")
ax.legend()
save(fig, "02_line_actions_by_year.png")

# %% [markdown]
# ## Normal vs lognormal fit for records lost
# Parameters are estimated from the same data, so the KS p-values are optimistic (Lilliefors issue);
# the KS statistic D is used to compare the two fits.

# %%
x = df["data_total"].dropna().astype(float).values
mu, sd = stats.norm.fit(x)
s_ln, _, sc_ln = stats.lognorm.fit(x, floc=0)
ks_n = stats.kstest(x, "norm", args=(mu, sd))
ks_l = stats.kstest(x, "lognorm", args=(s_ln, 0, sc_ln))
fit = pd.DataFrame(
    [
        {"distribution": "normal", "param_1": mu, "param_2": sd, "ks_d": ks_n.statistic, "ks_p": ks_n.pvalue},
        {
            "distribution": "lognormal",
            "param_1": s_ln,
            "param_2": sc_ln,
            "ks_d": ks_l.statistic,
            "ks_p": ks_l.pvalue,
        },
    ]
)
fit.to_csv(OUT / "02_distribution_fit.csv", index=False)
fig, axs = plt.subplots(1, 2, figsize=(11, 4.5))
stats.probplot(x, dist="norm", plot=axs[0])
axs[0].set_title(f"Normal QQ plot, raw records (KS D {ks_n.statistic:.3f})")
axs[0].set_xlabel("Theoretical normal quantiles")
axs[0].set_ylabel("Records lost")
stats.probplot(np.log(x), dist="norm", plot=axs[1])
axs[1].set_title(f"Normal QQ plot, ln(records), lognormal check (KS D {ks_l.statistic:.3f})")
axs[1].set_xlabel("Theoretical normal quantiles")
axs[1].set_ylabel("ln(records lost)")
save(fig, "02_qq_records.png")
log_event(lg, "fit", normal_d=ks_n.statistic, lognormal_d=ks_l.statistic, sigma=s_ln, scale=sc_ln)
fit

# %% [markdown]
# ## P(action category | sector)

# %%
cp = df[df["sector"].isin(top8)].groupby("sector")[AC].mean()
cp.columns = CATS
cp["n"] = df[df["sector"].isin(top8)].groupby("sector").size()
cp = cp.loc[top8]
cp.to_csv(OUT / "02_conditional_probability.csv")
fig, ax = plt.subplots(figsize=(10, 5.5))
sns.heatmap(cp[CATS], annot=True, fmt=".2f", cmap="Blues", ax=ax, yticklabels=[short(s) for s in cp.index])
ax.set_title("P(action category | sector), top 8 sectors")
ax.set_xlabel("Action category")
ax.set_ylabel("Sector")
save(fig, "02_conditional_probability.png")
cp.round(3)

# %% [markdown]
# ## Spearman correlation heatmap

# %%
df["size_code"] = df["size"].map({"small": 1, "medium": 2, "large": 3})
SP = [
    "log_records",
    "log_discovery",
    "year",
    "size_code",
    *AC,
    "actor_external",
    "actor_internal",
    "actor_partner",
]
cr = df[SP].astype(float).corr(method="spearman")
fig, ax = plt.subplots(figsize=(11, 9))
sns.heatmap(cr, annot=True, fmt=".2f", cmap="vlag", center=0, ax=ax, annot_kws={"fontsize": 7})
ax.set_title("Spearman rank correlation (pairwise complete rows)")
ax.set_xlabel("Variable")
ax.set_ylabel("Variable")
save(fig, "02_spearman_heatmap.png")
cr.to_csv(OUT / "02_spearman.csv")

# %% [markdown]
# ## Hypothesis tests

# %%
RG = {
    "North": [
        "Haryana",
        "Himachal Pradesh",
        "Punjab",
        "Rajasthan",
        "Uttar Pradesh",
        "Uttarakhand",
        "Chandigarh",
        "Delhi",
        "Jammu & Kashmir",
        "Ladakh",
    ],
    "South": [
        "Andhra Pradesh",
        "Karnataka",
        "Kerala",
        "Tamil Nadu",
        "Telangana",
        "Puducherry",
        "Lakshadweep",
        "A&N Islands",
    ],
    "East": ["Bihar", "Jharkhand", "Odisha", "West Bengal", "Chhattisgarh"],
    "West": ["Goa", "Gujarat", "Maharashtra", "Madhya Pradesh", "D&N Haveli and Daman & Diu"],
    "North-East": [
        "Arunachal Pradesh",
        "Assam",
        "Manipur",
        "Meghalaya",
        "Mizoram",
        "Nagaland",
        "Sikkim",
        "Tripura",
    ],
}
rows = []


def add(q, h0, h1, test, why, r, meaning_yes, meaning_no, extra=None):
    rows.append(
        {
            "question": q,
            "h0": h0,
            "h1": h1,
            "test": test,
            "why_this_test": why,
            "statistic": r["statistic"],
            "p_value": r["p_value"],
            "effect_name": r.get("effect_name", ""),
            "effect_size": r.get("effect_size", np.nan),
            "meaning_if_reject": meaning_yes,
            "meaning_if_not": meaning_no,
            **(extra or {}),
        }
    )


s1 = df[df["size"].isin(SIZES) & df["action_primary"].isin(CATS + ["multiple"])]
t1 = pd.crosstab(s1["action_primary"], s1["size"])[SIZES]
t1 = t1[t1.sum(axis=1) >= 5]
r1 = chi_square(t1.values)
add(
    "Does the kind of attack depend on business size?",
    "Action category is independent of victim size",
    "Action category and victim size are associated",
    "Chi-square test of independence",
    f"Both variables are categorical (nominal action, size band); {len(s1)} incidents, minimum expected count "
    f"{r1['min_expected']:.1f}",
    r1,
    "Small, medium and large organisations face a different attack mix, so CyCRS weights threats by size.",
    "The attack mix looks similar across sizes, so size alone does not change which threats come first.",
    {"n": len(s1)},
)

s2 = df[df["sector"].isin(top8) & df["action_primary"].isin(CATS + ["multiple"])]
t2 = pd.crosstab(s2["action_primary"], s2["sector"])
t2 = t2[t2.sum(axis=1) >= 5]
r2 = chi_square(t2.values)
add(
    "Does the kind of attack depend on the sector?",
    "Action category is independent of sector",
    "Action category and sector are associated",
    "Chi-square test of independence",
    f"Both variables are categorical; top 8 sectors, {len(s2)} incidents, minimum expected count "
    f"{r2['min_expected']:.1f}",
    r2,
    "Each sector has its own attack mix, so CyCRS starts from the sector's own threat profile.",
    "Sectors share a similar attack mix, so a general threat profile is enough.",
    {"n": len(s2)},
)

ie = df[df["data_total"].notna()]
xi = ie.loc[ie["actor_type"] == "internal", "data_total"].astype(float)
xe = ie.loc[ie["actor_type"] == "external", "data_total"].astype(float)
ni = normality(np.log10(1 + xi))
ne = normality(np.log10(1 + xe))
r3 = mann_whitney(xi, xe)
add(
    "Do insiders or outsiders cause bigger breaches?",
    "Records lost has the same distribution for internal and external actors",
    "Records lost differs between internal and external actors",
    "Mann-Whitney U",
    f"{ni['test']} rejects normality even on the log scale (internal p {ni['p_value']:.2g}, external p "
    f"{ne['p_value']:.2g}), so a rank test replaces the t-test",
    r3,
    "Breach size differs by who caused it, so insider and outsider threats get different loss estimates.",
    "Breach size is similar whoever caused it.",
    {"n": len(xi) + len(xe), "median_internal": xi.median(), "median_external": xe.median()},
)

dd = df[df["sector"].isin(top8) & df["discovery_days"].notna()]
gs = [g["log_discovery"].values for _, g in dd.groupby("sector")]
r4 = kruskal(gs)
r4a = anova(gs)
lv = levene(gs)
nd = normality(dd["log_discovery"])
dn = dunn(dd, "log_discovery", "sector")
dn.to_csv(OUT / "02_dunn_discovery_sector.csv")
n_sig_dunn = int(((dn.values < 0.05) & ~np.eye(len(dn), dtype=bool)).sum() // 2)
add(
    "Do some sectors take longer to notice a breach?",
    "Discovery time has the same distribution in every sector",
    "At least one sector differs in discovery time",
    "Kruskal-Wallis H with Dunn post-hoc (Holm)",
    f"{nd['test']} rejects normality of log discovery days (p {nd['p_value']:.2g}) and Levene p is "
    f"{lv['p_value']:.2g}, so the rank-based test is primary",
    r4,
    f"Detection speed differs by sector ({n_sig_dunn} sector pairs differ after Dunn), so slow-detecting sectors "
    "get extra weight on monitoring.",
    "Sectors detect breaches at similar speeds.",
    {"n": len(dd)},
)
add(
    "Same question, parametric comparison",
    "Mean log discovery time is equal across sectors",
    "At least one sector mean differs",
    "One-way ANOVA (comparison only)",
    "Shown to compare with Kruskal-Wallis; its normality assumption fails here",
    r4a,
    "The parametric test agrees that sectors differ.",
    "The parametric test finds no difference.",
    {"n": len(dd)},
)

ry = df[df["year"].notna()]
a5 = ry[ry["year"] >= 2020]
b5 = ry[ry["year"] < 2020]
k1, n1, k2, n2 = int(a5["v_ransomware"].sum()), len(a5), int(b5["v_ransomware"].sum()), len(b5)
r5 = two_proportion_z(k1, n1, k2, n2)
n23 = int((ry["year"] == 2023).sum())
r23 = float(ry.loc[ry["year"] == 2023, "v_ransomware"].mean())
add(
    "Has ransomware become more common since 2020?",
    "The share of incidents involving ransomware is the same before and from 2020",
    "The ransomware share differs between the two periods",
    "Two-proportion z-test",
    f"The outcome is binary (ransomware or not) with large samples ({n1} and {n2} incidents)",
    r5,
    f"Ransomware share moved from {100 * k2 / n2:.1f}% before 2020 to {100 * k1 / n1:.1f}% from 2020, so backups and "
    "endpoint protection rank higher.",
    "Ransomware share has not changed.",
    {"n": n1 + n2, "share_2020_on": k1 / n1, "share_before": k2 / n2},
)
a6 = a5[a5["year"] != 2023]
k3, n3 = int(a6["v_ransomware"].sum()), len(a6)
r5b = two_proportion_z(k3, n3, k2, n2)
add(
    "Robustness: has ransomware risen since 2020 without the 2023 batch?",
    "Excluding 2023, the ransomware share is the same before and from 2020",
    "Excluding 2023, the ransomware share differs between the two periods",
    "Two-proportion z-test",
    f"Same binary outcome with {n23} incidents dated 2023 removed, because {100 * r23:.0f}% of them are ransomware and may reflect "
    "how VCDB collected that year",
    r5b,
    f"Without 2023 the share still moves from {100 * k2 / n2:.1f}% to {100 * k3 / n3:.1f}%, so the rise is not only a 2023 collection effect.",
    "Without 2023 the rise disappears, so it is mostly a 2023 collection effect.",
    {"n": n3 + n2, "share_2020_on": k3 / n3, "share_before": k2 / n2},
)

NC = A / "data" / "processed" / "ncrb_state.csv"
if NC.exists():
    nc = pd.read_csv(NC)
    rmap = {s: r for r, ss in RG.items() for s in ss}
    nc["region"] = nc["state"].map(rmap)
    assert nc["region"].notna().all()
    g6 = [g["crime_rate_2024"].values for _, g in nc.groupby("region")]
    r6 = anova(g6)
    tk = tukey(nc["crime_rate_2024"], nc["region"])
    tk.to_csv(OUT / "02_tukey_ncrb_region.csv", index=False)
    n6 = normality(nc["crime_rate_2024"])
    n_sig_tk = int(tk["reject"].astype(bool).sum())
    add(
        "Is cyber crime more common in some regions of India?",
        "Mean cyber crime rate per lakh is equal across the five regions",
        "At least one region has a different mean rate",
        "One-way ANOVA with Tukey HSD",
        f"Requested parametric comparison of a ratio-scale rate over {len(nc)} states and UTs; Shapiro p "
        f"{n6['p_value']:.2g} is reported as a caution",
        r6,
        f"Regional crime rates differ ({n_sig_tk} region pairs differ in Tukey HSD), so CyCRS adjusts for the "
        "user's region.",
        "Regional rate differences are within chance, so region is a weak signal.",
        {"n": len(nc)},
    )
    HD = {
        "computer_related": "h04_computer_related_offences_total",
        "obscene_publication": [c for c in nc.columns if c.startswith("h13_")][0],
        "fraud": "h33_fraud_total",
        "cheating": [c for c in nc.columns if c.startswith("h43_")][0],
    }
    mx = pd.DataFrame({k: nc[v] for k, v in HD.items()})
    mx["other"] = nc["h60_total_cyber_crimes_it_act_ipc_bns_r_w_it_act_sll"] - mx.sum(axis=1)
    mx["region"] = nc["region"]
    t6 = mx.groupby("region").sum()
    r6b = chi_square(t6.values)
    t6.to_csv(OUT / "02_ncrb_region_crime_mix.csv")
    add(
        "Do regions differ in the type of cyber crime?",
        "Crime-type mix is independent of region",
        "Crime-type mix depends on region",
        "Chi-square test of independence",
        f"Counts of {int(t6.values.sum())} cases in {t6.shape[1]} crime types by {t6.shape[0]} regions",
        r6b,
        "The crime mix differs by region, so local crime types are shown to the user.",
        "Regions share a similar crime mix.",
        {"n": int(t6.values.sum())},
    )

ht = pd.DataFrame(rows)
ht["p_holm"] = holm(ht["p_value"].values)
ht["decision"] = [decide(p) for p in ht["p_value"]]
ht["decision_holm"] = [decide(p) for p in ht["p_holm"]]
ht["effect_label"] = [effect_label(n, v) for n, v in zip(ht["effect_name"], ht["effect_size"], strict=True)]
ht["meaning"] = np.where(ht["decision_holm"] == "reject H0", ht["meaning_if_reject"], ht["meaning_if_not"])
ht.drop(columns=["meaning_if_reject", "meaning_if_not"]).to_csv(OUT / "hypothesis_tests.csv", index=False)
log_event(
    lg, "tests", rows=ht[["test", "statistic", "p_value", "p_holm", "effect_size"]].to_dict(orient="records")
)
ht[["question", "test", "statistic", "p_value", "p_holm", "effect_size", "decision_holm"]]

# %% [markdown]
# ## Cards

# %%


def sample(cols):
    s = df[cols].dropna().sample(8, random_state=42)
    return s.astype(object).where(s.notna(), None).to_dict(orient="records")


def var(n, t, s, tr="none"):
    return {"name": n, "type": t, "scale": s, "transform": tr}


rl = st.set_index("variable").loc["records_lost"]
ll = st.set_index("variable").loc["log10_records_lost"]
dy = st.set_index("variable").loc["discovery_days"]
top_ac = ac.index[0]
top_at = at.index[0]
p_ext = at.get("external", 0) / at.sum()
card_d = {
    "id": "descriptive",
    "title": "What the incident records look like",
    "module": "2: Descriptive statistics and probability",
    "stage": "explore",
    "used_live": False,
    "order": 2,
    "question": "How big are typical breaches, how long do they go unnoticed, and which attacks and attackers are most common?",
    "data_in": {
        "dataset": "VCDB validated incidents (vcdb_clean.parquet)",
        "n_rows": len(df),
        "variables": [
            var("data_total", "numeric", "ratio", "log10(1 + x) for charts"),
            var("discovery_days", "numeric", "ratio", "log10(1 + x) for the scatter"),
            var("employee_count", "categorical", "ordinal", "band code 1 to 8"),
            var("action_*", "binary", "nominal"),
            var("actor_type", "categorical", "nominal"),
            var("sector", "categorical", "nominal"),
            var("year", "numeric", "interval"),
        ],
        "prep_steps": [
            "Coded employee bands 1 (1 to 10) to 8 (over 100000); coarse Small, Large and Unknown left out of band stats",
            "Actor type is the single actor class, or multiple, or unknown",
            "Top 8 sectors by incident count, Unknown sector excluded",
        ],
        "sample_rows": sample(
            ["sector", "size", "actor_type", "action_primary", "data_total", "discovery_days"]
        ),
    },
    "why": (
        f"Records lost has mean {rl['mean']:,.0f} but median {rl['median']:,.0f} and skewness {rl['skewness']:.1f}, "
        "so medians, IQRs and log-scale histograms describe it better than means. "
        f"Action category and actor type are nominal, so counts are shown as bars and shares as a pie ({top_at} actors "
        f"are {100 * at.iloc[0] / at.sum():.0f}% of incidents). "
        f"Discovery time and records lost are both skewed ratio variables, so their link is shown on log axes and "
        f"measured with Spearman rho ({rho_sc:.2f}), which does not assume normality."
    ),
    "data_properties": [
        {
            "name": "Skewness of records lost",
            "value": rl["skewness"],
            "implication": "Use medians and log scale.",
        },
        {
            "name": "Kurtosis of records lost",
            "value": rl["kurtosis"],
            "implication": "Extremely heavy tail of mega breaches.",
        },
        {
            "name": "Skewness of log records lost",
            "value": ll["skewness"],
            "implication": "Near symmetric after the log.",
        },
        {
            "name": "Median discovery days",
            "value": dy["median"],
            "implication": f"Half of breaches take over {dy['median']:.0f} days to notice.",
        },
        {
            "name": "Most common action category",
            "value": f"{top_ac} ({int(ac.iloc[0])} incidents)",
            "implication": "First threat to defend against.",
        },
        {
            "name": "Share of incidents with an external actor only",
            "value": round(float(p_ext), 4),
            "implication": "Outsiders dominate, but insiders are not rare.",
        },
    ],
    "alternatives": [
        {
            "model": "Mean and SD only",
            "why_not": f"With skewness {rl['skewness']:.1f} the mean ({rl['mean']:,.0f}) is far above what a typical incident loses ({rl['median']:,.0f}).",
        },
        {
            "model": "Pearson correlation",
            "why_not": "Both variables are heavily skewed with outliers; Pearson would be driven by a few mega breaches.",
        },
        {
            "model": "Pie charts for action categories",
            "why_not": "An incident can have several categories, so shares do not add up to 100%; a bar chart is honest.",
        },
    ],
    "formula_tex": [
        {"label": "Sample variance", "tex": r"s^2 = \frac{1}{n-1}\sum_{i=1}^{n}(x_i-\bar{x})^2"},
        {"label": "Interquartile range", "tex": r"\mathrm{IQR} = Q_3 - Q_1"},
        {
            "label": "Excess kurtosis",
            "tex": r"g_2 = \frac{\frac{1}{n}\sum (x_i-\bar{x})^4}{\left(\frac{1}{n}\sum (x_i-\bar{x})^2\right)^2} - 3",
        },
        {"label": "Spearman rho", "tex": r"\rho = 1 - \frac{6\sum d_i^2}{n(n^2-1)}"},
    ],
    "assumptions": [
        {
            "check": "Spearman: monotonic relation, paired observations",
            "statistic": round(float(rho_sc), 4),
            "p_value": float(p_sc),
            "verdict": "significant" if p_sc < 0.05 else "not significant",
            "action_taken": f"Computed on {len(sc)} incidents with both values known.",
        }
    ],
    "results": {
        "key_numbers": {
            "incidents": len(df),
            "median_records_lost": rl["median"],
            "median_discovery_days": dy["median"],
            "spearman_discovery_records": rho_sc,
        },
        "tables": [
            {"title": "Summary statistics", "columns": list(st.columns), "rows": st.round(4).values.tolist()}
        ],
        "charts": [
            {
                "type": "histogram",
                "title": "Records lost per incident (log scale)",
                "x_label": "log10(1 + records lost)",
                "y_label": "Incidents",
                "data": [
                    {"x0": float(he[i]), "x1": float(he[i + 1]), "y": int(hb[i])} for i in range(len(hb))
                ],
            },
            {
                "type": "bar",
                "title": "Incidents involving each action category",
                "x_label": "Action category",
                "y_label": "Incidents",
                "data": [{"x": k, "y": int(v)} for k, v in ac.items()],
            },
            {
                "type": "pie",
                "title": "Actor type",
                "x_label": "Actor type",
                "y_label": "Incidents",
                "data": [{"x": k, "y": int(v)} for k, v in at.items()],
            },
            {
                "type": "line",
                "title": "Incidents per action category by year",
                "x_label": "Year",
                "y_label": "Incidents",
                "data": [{"x": int(y), **{c: int(yr.loc[y, c]) for c in CATS}} for y in yr.index],
            },
        ],
    },
    "yields": (
        f"A typical breach in the data exposes about {rl['median']:,.0f} records and goes unnoticed for about "
        f"{dy['median']:.0f} days, while a few huge breaches pull the average up to {rl['mean']:,.0f}. "
        f"{top_ac.capitalize()} is the most common kind of attack and outsiders cause most incidents, so CyCRS starts "
        "its threat list there."
    ),
    "feeds": ["distribution-fit", "conditional-probability", "hypothesis-tests"],
    "limitations": [
        "VCDB comes from public reports, so large organisations and the USA are over represented.",
        f"Discovery time is known for only {int(dy['n'])} incidents.",
        "Employee count is banded, so its mean and SD are on band codes, not people.",
    ],
}
write_card(card_d)

better = "lognormal" if ks_l.statistic < ks_n.statistic else "normal"
card_f = {
    "id": "distribution-fit",
    "title": "Which curve fits breach size",
    "module": "2: Probability distributions",
    "stage": "explore",
    "used_live": False,
    "order": 3,
    "question": "Is the number of records lost in a breach closer to a normal or a lognormal distribution?",
    "data_in": {
        "dataset": "VCDB validated incidents with a known record count",
        "n_rows": len(x),
        "variables": [var("data_total", "numeric", "ratio", "none for the fit, ln for the QQ plot")],
        "prep_steps": [
            "Kept incidents with data_total known (all values are at least 1)",
            "Fitted both distributions by maximum likelihood, lognormal location fixed at 0",
        ],
        "sample_rows": sample(["data_total"]),
    },
    "why": (
        f"Records lost is strictly positive with skewness {rl['skewness']:.1f}, the typical shape of a lognormal "
        "variable, while a normal curve allows negative values and is symmetric. "
        f"The Kolmogorov-Smirnov distance is {ks_n.statistic:.3f} for the normal fit and {ks_l.statistic:.3f} for the "
        f"lognormal fit, so the {better} curve is much closer to the data."
    ),
    "data_properties": [
        {
            "name": "KS D, normal fit",
            "value": float(ks_n.statistic),
            "implication": "Large gap between data and normal curve.",
        },
        {
            "name": "KS D, lognormal fit",
            "value": float(ks_l.statistic),
            "implication": "Much smaller gap; log scale is appropriate.",
        },
        {
            "name": "Lognormal sigma (shape)",
            "value": float(s_ln),
            "implication": "Wide spread on the log scale.",
        },
        {
            "name": "Lognormal median (scale)",
            "value": float(sc_ln),
            "implication": "Typical breach size implied by the fit.",
        },
    ],
    "alternatives": [
        {
            "model": "Normal distribution",
            "why_not": f"KS D {ks_n.statistic:.3f}; it predicts negative record counts and misses the long tail.",
        },
        {
            "model": "Pareto (power law) tail only",
            "why_not": "Describes only the largest breaches; CyCRS needs the whole range, including small breaches.",
        },
    ],
    "formula_tex": [
        {
            "label": "Lognormal density",
            "tex": r"f(x)=\frac{1}{x\sigma\sqrt{2\pi}}\exp\left(-\frac{(\ln x-\mu)^2}{2\sigma^2}\right)",
        },
        {"label": "KS statistic", "tex": r"D = \sup_x |F_n(x) - F(x)|"},
    ],
    "assumptions": [
        {
            "check": "KS test against fitted normal",
            "statistic": float(ks_n.statistic),
            "p_value": float(ks_n.pvalue),
            "verdict": "rejected" if ks_n.pvalue < 0.05 else "not rejected",
            "action_taken": "Normal model not used for breach size.",
        },
        {
            "check": "KS test against fitted lognormal",
            "statistic": float(ks_l.statistic),
            "p_value": float(ks_l.pvalue),
            "verdict": "rejected" if ks_l.pvalue < 0.05 else "not rejected",
            "action_taken": "With n this large even small gaps are significant; D is used to compare fits and the log scale is adopted.",
        },
    ],
    "results": {
        "key_numbers": {
            "n": len(x),
            "ks_d_normal": ks_n.statistic,
            "ks_d_lognormal": ks_l.statistic,
            "lognormal_sigma": s_ln,
            "lognormal_scale": sc_ln,
        },
        "tables": [{"title": "Fit comparison", "columns": list(fit.columns), "rows": fit.values.tolist()}],
        "charts": [
            {
                "type": "bar",
                "title": "KS distance by fitted distribution",
                "x_label": "Distribution",
                "y_label": "KS D (lower is better)",
                "data": [
                    {"x": "normal", "y": float(ks_n.statistic)},
                    {"x": "lognormal", "y": float(ks_l.statistic)},
                ],
            }
        ],
    },
    "yields": (
        f"Breach sizes follow a lognormal pattern far better than a bell curve (distance {ks_l.statistic:.3f} vs "
        f"{ks_n.statistic:.3f}). That is why every later model of breach size in CyCRS works on the log of records "
        "lost and converts back to records and rupees at the end."
    ),
    "feeds": ["breach-impact"],
    "limitations": [
        "KS p-values are optimistic because parameters were estimated from the same data.",
        "Even the lognormal fit is rejected at this sample size; it is an approximation, not an exact law.",
    ],
}
write_card(card_f)

cpt = cp.reset_index()
best = {s: cp.loc[s, CATS].idxmax() for s in cp.index}
hc = cp.loc[top8[0], CATS]
card_c = {
    "id": "conditional-probability",
    "title": "Attack chances by sector",
    "module": "2: Probability",
    "stage": "explore",
    "used_live": True,
    "order": 4,
    "question": "Given a business's sector, what share of past incidents involved each kind of attack?",
    "data_in": {
        "dataset": "VCDB validated incidents in the top 8 sectors",
        "n_rows": int(cp["n"].sum()),
        "variables": [var("sector", "categorical", "nominal"), var("action_*", "binary", "nominal")],
        "prep_steps": [
            "Kept incidents in the 8 most common known sectors",
            "Each probability is the share of that sector's incidents with the action flag set",
        ],
        "sample_rows": sample(["sector", *AC]),
    },
    "why": (
        "Sector and action category are both categorical, so the simplest honest estimate of P(action | sector) is "
        "the observed share within each sector. "
        f"Every top sector has at least {int(cp['n'].min())} incidents, enough for stable shares, and the chi-square "
        f"test finds attack mix depends on sector (Cramer's V {r2['effect_size']:.2f})."
    ),
    "data_properties": [
        {
            "name": "Smallest sector sample",
            "value": int(cp["n"].min()),
            "implication": "Shares are estimated from at least this many incidents.",
        },
        {
            "name": f"Top attack in {top8[0]}",
            "value": f"{best[top8[0]]} ({hc.max():.2f})",
            "implication": "Leading threat for the largest sector.",
        },
        {
            "name": "Cramer's V, action vs sector",
            "value": round(r2["effect_size"], 4),
            "implication": "Sector changes the attack mix.",
        },
    ],
    "alternatives": [
        {
            "model": "One overall attack mix for everyone",
            "why_not": f"The chi-square test rejects independence (p {r2['p_value']:.2g}), so ignoring sector loses information.",
        },
        {
            "model": "Logistic regression per action",
            "why_not": "Used later for the live model; this table is the transparent reference it must beat.",
        },
    ],
    "formula_tex": [
        {
            "label": "Conditional probability",
            "tex": r"P(A \mid S) = \frac{P(A \cap S)}{P(S)} \approx \frac{n_{A,S}}{n_S}",
        }
    ],
    "assumptions": [
        {
            "check": "Smallest sector sample size",
            "statistic": float(cp["n"].min()),
            "p_value": None,
            "verdict": "adequate",
            "action_taken": "No smoothing needed for the top 8 sectors.",
        }
    ],
    "results": {
        "key_numbers": {f"n_{k}": int(v) for k, v in cp["n"].items()},
        "tables": [
            {
                "title": "P(action category | sector)",
                "columns": list(cpt.columns),
                "rows": cpt.round(4).values.tolist(),
            }
        ],
        "charts": [
            {
                "type": "heatmap",
                "title": "P(action | sector)",
                "x_label": "Action category",
                "y_label": "Sector",
                "data": [{"x": c, "y": s, "value": float(cp.loc[s, c])} for s in cp.index for c in CATS],
            }
        ],
    },
    "yields": (
        f"In {top8[0]}, {100 * hc.max():.0f}% of past incidents involved {best[top8[0]]}, and each sector has its own "
        "leading threat. CyCRS shows these shares as the simple baseline for a user's sector, and its attack likelihood "
        "model must do better than this table to be used."
    ),
    "feeds": ["attack-likelihood"],
    "limitations": [
        "An incident can have several action categories, so a sector's shares can add up to more than 1.",
        "Shares describe reported incidents, not the chance that a given business is attacked.",
    ],
}
write_card(card_c)

TC = [
    "question",
    "h0",
    "test",
    "why_this_test",
    "statistic",
    "p_value",
    "p_holm",
    "effect",
    "decision",
    "meaning",
]
tr = [
    [
        r["question"],
        r["h0"],
        r["test"],
        r["why_this_test"],
        round(r["statistic"], 4),
        float(r["p_value"]),
        float(r["p_holm"]),
        f"{r['effect_name']} {r['effect_size']:.3f} ({r['effect_label']})",
        r["decision_holm"],
        r["meaning"],
    ]
    for _, r in ht.iterrows()
]
n_rej = int((ht["decision_holm"] == "reject H0").sum())
SHORT = {
    "Does the kind of attack depend on business size?": "attack mix by business size",
    "Does the kind of attack depend on the sector?": "attack mix by sector",
    "Do insiders or outsiders cause bigger breaches?": "breach size by insider or outsider",
    "Do some sectors take longer to notice a breach?": "detection time by sector (Kruskal-Wallis)",
    "Same question, parametric comparison": "detection time by sector (ANOVA)",
    "Has ransomware become more common since 2020?": "the rise in ransomware share",
    "Robustness: has ransomware risen since 2020 without the 2023 batch?": "the ransomware rise without 2023",
    "Is cyber crime more common in some regions of India?": "crime rate by Indian region",
    "Do regions differ in the type of cyber crime?": "crime type mix by Indian region",
}
held = [SHORT[q] for q, d in zip(ht["question"], ht["decision_holm"], strict=True) if d == "reject H0"]
fell = [SHORT[q] for q, d in zip(ht["question"], ht["decision_holm"], strict=True) if d != "reject H0"]
card_h = {
    "id": "hypothesis-tests",
    "title": "Testing what really differs",
    "module": "2: Hypothesis testing",
    "stage": "explore",
    "used_live": False,
    "order": 5,
    "question": "Which differences in attack type, breach size, detection time and regional crime are real rather than chance?",
    "data_in": {
        "dataset": "VCDB validated incidents and NCRB Crime in India 2024 state tables",
        "n_rows": len(df),
        "variables": [
            var("action_primary", "categorical", "nominal"),
            var("size", "categorical", "ordinal"),
            var("sector", "categorical", "nominal"),
            var("data_total", "numeric", "ratio"),
            var("discovery_days", "numeric", "ratio", "log10(1 + x)"),
            var("v_ransomware", "binary", "nominal"),
            var("crime_rate_2024", "numeric", "ratio"),
        ],
        "prep_steps": [
            "Primary action is the single action category, or multiple; unknown dropped for chi-square tests",
            "Action rows with fewer than 5 incidents dropped from contingency tables",
            "Internal vs external compares incidents with only one actor class",
            "States and UTs grouped into five regions by CyCRS (Chhattisgarh in East, Madhya Pradesh in West)",
            "Holm correction applied across all tests in the table",
        ],
        "sample_rows": sample(
            ["action_primary", "size", "sector", "actor_type", "data_total", "v_ransomware"]
        ),
    },
    "why": (
        f"Normality checks fail for breach size (internal p {ni['p_value']:.2g}) and for log discovery time "
        f"(p {nd['p_value']:.2g}), so rank-based tests (Mann-Whitney, Kruskal-Wallis) are primary. "
        "Attack type, size and sector are categorical, so association is tested with chi-square and sized with "
        "Cramer's V, and ransomware share is a proportion, so a two-proportion z-test fits. "
        f"Running {len(ht)} tests raises the chance of a false alarm, so Holm-adjusted p-values decide."
    ),
    "data_properties": [
        {
            "name": f"{ni['test']} p, log records lost, internal",
            "value": ni["p_value"],
            "implication": "Not normal: use a rank test.",
        },
        {
            "name": f"{nd['test']} p, log discovery days",
            "value": nd["p_value"],
            "implication": "Not normal: Kruskal-Wallis is primary.",
        },
        {
            "name": "Levene p, discovery days by sector",
            "value": lv["p_value"],
            "implication": "Unequal spreads also weaken ANOVA.",
        },
        {
            "name": "Tests rejected after Holm",
            "value": f"{n_rej} of {len(ht)}",
            "implication": "Number of differences treated as real.",
        },
    ],
    "alternatives": [
        {
            "model": "Two-sample t-test for breach size",
            "why_not": f"Assumes normal data; {ni['test']} rejects normality even after the log transform.",
        },
        {
            "model": "One-way ANOVA as primary test for discovery time",
            "why_not": f"Normality and equal variance fail (Levene p {lv['p_value']:.2g}); ANOVA is kept only as a comparison row.",
        },
        {
            "model": "Fisher exact test",
            "why_not": f"Expected counts are large (minimum {min(r1['min_expected'], r2['min_expected']):.1f}), so chi-square is accurate and Fisher is unnecessary.",
        },
    ],
    "formula_tex": [
        {"label": "Chi-square", "tex": r"\chi^2 = \sum \frac{(O-E)^2}{E}"},
        {"label": "Cramer's V", "tex": r"V = \sqrt{\frac{\chi^2}{n\,(\min(r,c)-1)}}"},
        {"label": "Mann-Whitney U", "tex": r"U = n_1 n_2 + \frac{n_1(n_1+1)}{2} - R_1"},
        {"label": "Kruskal-Wallis H", "tex": r"H = \frac{12}{N(N+1)}\sum \frac{R_j^2}{n_j} - 3(N+1)"},
        {
            "label": "Two-proportion z",
            "tex": r"z = \frac{\hat p_1-\hat p_2}{\sqrt{\hat p(1-\hat p)(1/n_1+1/n_2)}}",
        },
        {
            "label": "Holm adjustment",
            "tex": r"p_{(i)}^{adj} = \max_{j \le i}\min\left(1, (m-j+1)\,p_{(j)}\right)",
        },
    ],
    "assumptions": [
        {
            "check": f"{ni['test']} on log records lost, internal actors",
            "statistic": ni["statistic"],
            "p_value": ni["p_value"],
            "verdict": "normal" if ni["normal"] else "not normal",
            "action_taken": "Mann-Whitney U instead of t-test.",
        },
        {
            "check": f"{ne['test']} on log records lost, external actors",
            "statistic": ne["statistic"],
            "p_value": ne["p_value"],
            "verdict": "normal" if ne["normal"] else "not normal",
            "action_taken": "Mann-Whitney U instead of t-test.",
        },
        {
            "check": f"{nd['test']} on log discovery days",
            "statistic": nd["statistic"],
            "p_value": nd["p_value"],
            "verdict": "normal" if nd["normal"] else "not normal",
            "action_taken": "Kruskal-Wallis primary, ANOVA for comparison.",
        },
        {
            "check": "Levene equal variance, discovery by sector",
            "statistic": lv["statistic"],
            "p_value": lv["p_value"],
            "verdict": "equal" if lv["equal_variance"] else "unequal",
            "action_taken": "Rank-based test preferred.",
        },
        {
            "check": "Chi-square minimum expected count (size, sector)",
            "statistic": min(r1["min_expected"], r2["min_expected"]),
            "p_value": None,
            "verdict": "adequate"
            if min(r1["min_expected"], r2["min_expected"]) >= 5
            else "some cells below 5",
            "action_taken": "Rare action rows dropped before testing.",
        },
    ],
    "results": {
        "key_numbers": {
            "tests": len(ht),
            "rejected_holm": n_rej,
            "ransomware_share_2020_on": k1 / n1,
            "ransomware_share_before_2020": k2 / n2,
        },
        "tables": [{"title": "Hypothesis tests", "columns": TC, "rows": tr}],
        "charts": [
            {
                "type": "bar",
                "title": "Effect size by test",
                "x_label": "Test",
                "y_label": "Effect size",
                "data": [
                    {"x": r["question"], "y": float(r["effect_size"]), "effect": r["effect_name"]}
                    for _, r in ht.iterrows()
                ],
            }
        ],
    },
    "yields": (
        f"{n_rej} of {len(ht)} tested differences hold up after correcting for multiple tests: "
        f"{', '.join(held)}, while {', '.join(fell) if fell else 'none'} could be chance. "
        "CyCRS uses only the differences that survive as inputs for tailoring its advice, and shows the effect size so a "
        "statistically real but tiny difference is not oversold."
    ),
    "feeds": ["attack-likelihood", "breach-impact"],
    "limitations": [
        "VCDB is not a random sample of businesses, so tests describe reported incidents.",
        "With thousands of incidents even negligible differences can be significant; read the effect size.",
        "The five-region grouping of states is a CyCRS choice and affects the regional tests.",
        f"{n23} incidents are dated 2023 and {100 * r23:.0f}% of them involve ransomware; without them the share from 2020 is "
        f"{100 * k3 / n3:.1f}% instead of {100 * k1 / n1:.1f}% (robustness row), so part of the rise is a collection effect.",
    ],
}
write_card(card_h)
log_event(
    lg,
    "cards written",
    ids=["descriptive", "distribution-fit", "conditional-probability", "hypothesis-tests"],
)
