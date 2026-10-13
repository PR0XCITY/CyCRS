# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
# ---

# %% [markdown]
# # 05 PCA, clustering and factor analysis

# %%
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.cluster.hierarchy import dendrogram


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
from src.classify import profile_features
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
    slug,
    top_sectors,
    var,
    write_json,
)
from src.segment import (
    SEED,
    ari,
    dominant,
    fa_checks,
    fa_eigen,
    fa_fit,
    fit_kmeans,
    kmeans_scan,
    kmo_label,
    loadings,
    name_component,
    pca_fit,
    ward_labels,
)

lg = get_logger("nb05", phase="phase5")
df = load_clean()
top = top_sectors(df)
AC = [f"action_{c}" for c in CATS if c != "environmental"]

# %% [markdown]
# ## PCA on encoded incident features

# %%
VF = [c for c in df.columns if c.startswith(("v_", "vec_"))]
PF = ACTORS + AC + ASSETS + VF
Xp = df[PF].astype(float)
Xp = Xp.loc[:, Xp.std() > 0]
PF = list(Xp.columns)
pr = pca_fit(Xp)
ev, cum, nk, n80 = pr["eigenvalues"], pr["cumulative"], pr["kaiser"], pr["n80"]
K = min(max(nk, 2), 8)
ld = loadings(pr["pca"], PF, K)
ld.to_csv(OUT / "05_pca_loadings.csv")
names = {c: name_component(ld[c]) for c in ld.columns}
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.bar(range(1, len(ev) + 1), ev, color="#4c72b0", label="eigenvalue")
ax.plot(range(1, len(ev) + 1), cum * max(ev), color="red", marker=".", label="cumulative variance (scaled)")
ax.axhline(1, color="grey", ls="--", label="Kaiser line (eigenvalue 1)")
ax.set_title(f"PCA scree: Kaiser keeps {nk}, 80% variance needs {n80} of {len(ev)} components")
ax.set_xlabel("Component")
ax.set_ylabel("Eigenvalue")
ax.legend()
save_fig(fig, "05_pca_scree.png")
fig, ax = plt.subplots(figsize=(10, 9))
sns.heatmap(ld, cmap="vlag", center=0, annot=True, fmt=".2f", annot_kws={"fontsize": 6}, ax=ax)
ax.set_title(f"PCA loadings, first {K} components")
ax.set_xlabel("Component")
ax.set_ylabel("Feature")
save_fig(fig, "05_pca_loadings.png")
sc = pr["pca"].transform(pr["scaler"].transform(Xp))[:, :2]
ix = np.random.default_rng(SEED).choice(len(sc), 1500, replace=False)
fig, ax = plt.subplots(figsize=(9, 7))
ax.scatter(sc[ix, 0], sc[ix, 1], s=5, alpha=0.3)
tl = ld[["PC1", "PC2"]].pow(2).sum(axis=1).sort_values(ascending=False).head(10).index
f = np.abs(sc[ix]).max() / np.abs(ld.loc[tl, ["PC1", "PC2"]].values).max() * 0.8
for t in tl:
    ax.arrow(0, 0, ld.loc[t, "PC1"] * f, ld.loc[t, "PC2"] * f, color="red", head_width=0.05)
    ax.text(ld.loc[t, "PC1"] * f * 1.08, ld.loc[t, "PC2"] * f * 1.08, t, fontsize=7, color="red")
ax.set_title("PCA biplot: 1500 incidents and the 10 strongest loadings")
ax.set_xlabel(f"PC1 ({100 * pr['pca'].explained_variance_ratio_[0]:.1f}%): {names['PC1']}")
ax.set_ylabel(f"PC2 ({100 * pr['pca'].explained_variance_ratio_[1]:.1f}%): {names['PC2']}")
save_fig(fig, "05_pca_biplot.png")
log_event(lg, "pca", features=len(PF), kaiser=nk, n80=n80, names=names)

# %% [markdown]
# ## K-means personas on profile features
# Profile features are all 0/1, so they are already on one scale; standardising would inflate rare sectors.

# %%
Xk = profile_features(df, top)
FK = list(Xk.columns)
scan = kmeans_scan(Xk.values, range(2, 11))
scan.to_csv(OUT / "05_kmeans_scan.csv", index=False)
k = int(scan.loc[scan["silhouette"].idxmax(), "k"])
km = fit_kmeans(Xk.values, k)
df["persona"] = km.labels_
fig, axs = plt.subplots(1, 2, figsize=(12, 4.5))
axs[0].plot(scan["k"], scan["inertia"], marker="o")
axs[0].axvline(k, color="red", ls="--")
axs[0].set_title("Elbow: within-cluster sum of squares")
axs[0].set_xlabel("k")
axs[0].set_ylabel("Inertia")
axs[1].plot(scan["k"], scan["silhouette"], marker="o", color="green")
axs[1].axvline(k, color="red", ls="--", label=f"chosen k = {k}")
axs[1].set_title("Mean silhouette (3000-row sample)")
axs[1].set_xlabel("k")
axs[1].set_ylabel("Silhouette")
axs[1].legend()
save_fig(fig, "05_kmeans_scan.png")

SL = {f"sector_{slug(t)}": t for t in top}
ZL = {"size_medium": "medium", "size_large": "large", "size_unknown": "unknown size"}
AL = {a: a.replace("asset_", "").replace("_", " ") for a in ASSETS}
prof = pd.DataFrame(km.cluster_centers_, columns=FK)
prof["size_small"] = 1 - prof[["size_medium", "size_large", "size_unknown"]].sum(axis=1)
ZL["size_small"] = "small"


def persona_name(r):
    s = dominant(r, "sector_", SL) or "Mixed sector"
    z = dominant(r, "size_", ZL) or "mixed size"
    a = [AL[c] for c in FK if c.startswith("asset_") and r[c] >= 0.5]
    return f"{s}, {z}" + (f", {' and '.join(a)}" if a else "")


prof["name"] = [persona_name(r) for _, r in prof.iterrows()]
mix = df.groupby("persona")[AC].mean()
mix.columns = [c.replace("action_", "") for c in AC]
prof["n"] = df["persona"].value_counts().sort_index().values
pt = pd.concat([prof[["name", "n"]], mix], axis=1)
pt.to_csv(OUT / "05_personas.csv", index_label="persona")
fig, ax = plt.subplots(figsize=(11, 0.6 * k + 2))
mix.set_axis([f"{i}: {n[:40]}" for i, n in enumerate(prof["name"])]).plot.barh(
    stacked=False, ax=ax, width=0.85
)
ax.set_title("Actual attack mix of each persona (share of incidents with each category)")
ax.set_xlabel("Share of persona's incidents")
ax.set_ylabel("Persona")
save_fig(fig, "05_persona_attack_mix.png")
write_json(
    {
        "id": "personas-kmeans",
        "feature_order": FK,
        "scaler": {
            "type": "identity",
            "mean": [0.0] * len(FK),
            "scale": [1.0] * len(FK),
            "reason": "all features are 0/1",
        },
        "centroids": km.cluster_centers_.tolist(),
        "names": prof["name"].tolist(),
        "attack_mix": mix.to_dict(orient="index"),
        "sectors": top,
    },
    MODELS / "personas.json",
)
log_event(lg, "kmeans", k=k, names=prof["name"].tolist(), sizes=prof["n"].tolist())
pt.round(3)

# %% [markdown]
# ## Ward hierarchical clustering on a 500-row sample

# %%
hi = np.random.default_rng(SEED).choice(len(Xk), 500, replace=False)
Xh = Xk.values[hi]
z, hl = ward_labels(Xh, k)
r_ari = ari(hl, km.labels_[hi])
ct = pd.crosstab(pd.Series(km.labels_[hi], name="kmeans"), pd.Series(hl, name="ward"))
ct.to_csv(OUT / "05_ward_vs_kmeans.csv")
fig, ax = plt.subplots(figsize=(12, 5))
dendrogram(z, truncate_mode="lastp", p=30, color_threshold=z[-(k - 1), 2], ax=ax)
ax.set_title(f"Ward dendrogram, 500 incidents (cut at k = {k}; ARI vs K-means {r_ari:.2f})")
ax.set_xlabel("Merged cluster (size in brackets)")
ax.set_ylabel("Ward linkage distance")
save_fig(fig, "05_dendrogram.png")
log_event(lg, "ward", ari=r_ari)

# %% [markdown]
# ## Factor analysis on NCRB state cyber crime
# Eight non-overlapping crime heads reported by at least 20 states, as log10(1 + cases per lakh people).

# %%
NC = A / "data" / "processed" / "ncrb_state.csv"
nc = pd.read_csv(NC)
FH = {
    "identity_theft": "h09_c_identity_theft_sec_66c",
    "cheating_by_personation": "h10_d_cheating_by_personation_by_using_computer_reso",
    "privacy_violation": "h11_e_violation_of_privacy_sec_66e",
    "obscene_content": "h13_publication_transmission_of_obscene_sexually_exp",
    "cyber_stalking": "h28_cyber_stalking_bullying_of_women_children_sec_78",
    "fraud": "h33_fraud_total",
    "cheating": "h43_cheating_section_318_4_bns_section_420_ipc",
    "blackmail": "h50_cyber_blackmailing_threatening_section_351_1_2_3",
}
Xf = pd.DataFrame({k2: np.log10(1 + nc[v] / nc["population_lakh"]) for k2, v in FH.items()})
Xf.index = nc["state"]
fc = fa_checks(Xf)
eg = fa_eigen(Xf)
nf = max(int((eg > 1).sum()), 1)
fa = fa_fit(Xf, nf, rotation="varimax" if nf > 1 else None)
fl = pd.DataFrame(fa.loadings_, index=Xf.columns, columns=[f"F{i + 1}" for i in range(nf)])
fl.to_csv(OUT / "05_fa_loadings.csv")
fnames = {c: " + ".join(fl.index[fl[c] >= 0.5]) or name_component(fl[c]) for c in fl.columns}
fsc = pd.DataFrame(fa.transform(Xf), index=Xf.index, columns=fl.columns).sort_values("F1", ascending=False)
fsc.to_csv(OUT / "05_fa_state_scores.csv")
fig, axs = plt.subplots(1, 2, figsize=(13, 5))
axs[0].plot(range(1, len(eg) + 1), eg, marker="o")
axs[0].axhline(1, color="grey", ls="--")
axs[0].set_title(f"FA scree (KMO {fc['kmo']:.2f}, Bartlett p {fc['bartlett_p']:.2g})")
axs[0].set_xlabel("Factor")
axs[0].set_ylabel("Eigenvalue")
sns.heatmap(fl, annot=True, fmt=".2f", cmap="vlag", center=0, ax=axs[1])
axs[1].set_title(f"Varimax loadings, {nf} factors" if nf > 1 else "Loadings, 1 factor")
axs[1].set_xlabel("Factor")
axs[1].set_ylabel("Crime head")
save_fig(fig, "05_fa.png")
fig, ax = plt.subplots(figsize=(8, 9))
ax.barh(fsc.index[::-1], fsc["F1"].values[::-1], color="#55a868")
ax.set_title(f"State scores on F1 ({fnames['F1'][:60]})")
ax.set_xlabel("Factor score")
ax.set_ylabel("State or UT")
save_fig(fig, "05_fa_state_scores.png")
log_event(lg, "fa", n_factors=nf, names=fnames, **fc)
fl.round(3)

# %% [markdown]
# ## Cards

# %%
evr = pr["pca"].explained_variance_ratio_
card_p = {
    "id": "pca",
    "title": "How many things really describe an incident",
    "module": "5: Principal component analysis",
    "stage": "segment",
    "used_live": False,
    "order": 10,
    "question": "How many independent dimensions are hidden in the dozens of yes/no flags that describe each incident?",
    "data_in": {
        "dataset": "VCDB validated incidents",
        "n_rows": len(Xp),
        "variables": [
            var("actor_*, action_*, asset_*", "binary", "nominal", "standardised"),
            var("v_*, vec_*", "binary", "nominal", "standardised"),
        ],
        "prep_steps": [
            f"Used {len(PF)} 0/1 incident flags with non-zero variance",
            "Standardised each flag to mean 0, SD 1 before PCA",
        ],
        "sample_rows": sample_rows(df, PF[:8]),
    },
    "why": (
        f"The {len(PF)} flags overlap heavily (a ransomware flag implies a malware flag, an error flag often comes with media assets), "
        "so PCA can compress them into a few uncorrelated components. "
        f"Kaiser's rule keeps {nk} components and 80% of the variance needs {n80}, which measures how much redundancy there is."
    ),
    "data_properties": [
        {"name": "Components with eigenvalue above 1", "value": nk, "implication": "Kaiser dimension count."},
        {
            "name": "Components for 80% variance",
            "value": n80,
            "implication": "Dimensions needed to keep most information.",
        },
        {"name": "Variance explained by PC1", "value": float(evr[0]), "implication": names["PC1"]},
        {"name": "Variance explained by PC2", "value": float(evr[1]), "implication": names["PC2"]},
    ],
    "alternatives": [
        {
            "model": "Factor analysis on incident flags",
            "why_not": "Flags are binary and FA assumes continuous, roughly normal indicators; it is used on NCRB rates instead.",
        },
        {
            "model": "Keep all flags",
            "why_not": f"PC1 and PC2 alone carry {100 * (evr[0] + evr[1]):.0f}% of the variance, so plots and clustering on raw flags would be noisy.",
        },
    ],
    "formula_tex": [
        {"label": "Eigen decomposition", "tex": r"\Sigma v_k = \lambda_k v_k"},
        {"label": "Variance explained", "tex": r"\frac{\lambda_k}{\sum_j \lambda_j}"},
        {"label": "Loading", "tex": r"\ell_{jk} = v_{jk}\sqrt{\lambda_k}"},
    ],
    "assumptions": [
        {
            "check": "Kaiser criterion vs 80% rule",
            "statistic": float(nk),
            "p_value": None,
            "verdict": f"{nk} vs {n80} components",
            "action_taken": f"First {K} components interpreted.",
        }
    ],
    "results": {
        "key_numbers": {
            "features": len(PF),
            "kaiser": nk,
            "n80": n80,
            "pc1_var": float(evr[0]),
            "pc2_var": float(evr[1]),
        },
        "tables": [
            {
                "title": "Component names (top two loadings)",
                "columns": ["component", "name", "variance"],
                "rows": [[c, names[c], float(evr[i])] for i, c in enumerate(ld.columns)],
            },
            {
                "title": "Loadings",
                "columns": ["feature", *ld.columns],
                "rows": ld.round(4).reset_index().values.tolist(),
            },
        ],
        "charts": [
            {
                "type": "bar",
                "title": "Scree",
                "x_label": "Component",
                "y_label": "Eigenvalue",
                "data": [
                    {"x": i + 1, "y": float(e), "cum": float(c)}
                    for i, (e, c) in enumerate(zip(ev, cum, strict=True))
                ],
            },
            {
                "type": "heatmap",
                "title": "Loadings",
                "x_label": "Component",
                "y_label": "Feature",
                "data": [
                    {"x": c, "y": f, "value": float(ld.loc[f, c])} for f in ld.index for c in ld.columns
                ],
            },
        ],
    },
    "yields": (
        f"The {len(PF)} incident flags boil down to about {nk} independent patterns by Kaiser's rule ({n80} to keep 80% of the information), "
        f"led by {names['PC1']}. "
        f"That is {100 * nk / len(PF):.0f}% as many dimensions as flags, so the flags overlap but each still adds information; "
        "CyCRS keeps the separate attack categories rather than replacing them with components."
    ),
    "feeds": ["personas-kmeans"],
    "limitations": [
        "PCA on binary flags is descriptive; components are linear summaries, not causal factors.",
        "Rare flags get large standardised values and can dominate later components.",
    ],
}
write_card(card_p)

sbest = float(scan["silhouette"].max())
pnames = prof["name"].tolist()
big = int(prof["n"].idxmax())
lead = mix.loc[big].idxmax()
card_k = {
    "id": "personas-kmeans",
    "title": "Business personas",
    "module": "5: K-means clustering",
    "stage": "segment",
    "used_live": True,
    "order": 11,
    "question": "Which groups of similar businesses appear in the incident data, and what attacks hit each group?",
    "data_in": {
        "dataset": "VCDB validated incidents",
        "n_rows": len(Xk),
        "variables": [
            var("sector", "categorical", "nominal", "dummies, top 8"),
            var("size", "categorical", "ordinal", "dummies"),
            var("asset_*", "binary", "nominal", "asset_person excluded"),
        ],
        "prep_steps": [
            f"Used the same {len(FK)} profile features as the attack models",
            "No scaling: every feature is already 0/1",
            "k chosen by the highest mean silhouette over k = 2 to 10",
        ],
        "sample_rows": sample_rows(df.assign(**Xk), FK[:8]),
    },
    "why": (
        "Personas are built only from what a business can tell CyCRS about itself (sector, size, the IT it relies on), so a new user can be "
        "placed in one instantly by finding the nearest centroid in the browser. "
        f"K-means suits this because assignment is a simple distance to {k} saved centres, and the silhouette peaks at k = {k} ({sbest:.2f})."
    ),
    "data_properties": [
        {"name": "Chosen k", "value": k, "implication": "Number of personas."},
        {
            "name": "Best mean silhouette",
            "value": sbest,
            "implication": "Separation of personas; above 0.5 is strong, below 0.25 weak.",
        },
        {
            "name": "Largest persona",
            "value": f"{pnames[big]} ({int(prof['n'][big])} incidents)",
            "implication": f"Its leading attack is {lead}.",
        },
    ],
    "alternatives": [
        {
            "model": "Hierarchical clustering",
            "why_not": "Cannot place a new business without refitting the tree; K-means needs only the saved centroids.",
        },
        {
            "model": "DBSCAN",
            "why_not": "Not in the syllabus, and on 0/1 profile data the density of points varies hugely between common and rare profiles.",
        },
    ],
    "formula_tex": [
        {"label": "K-means objective", "tex": r"\min \sum_{i}\lVert x_i-\mu_{c(i)}\rVert^2"},
        {"label": "Silhouette", "tex": r"s_i=\frac{b_i-a_i}{\max(a_i,b_i)}"},
        {"label": "Assignment", "tex": r"c(x)=\arg\min_k \lVert x-\mu_k\rVert^2"},
    ],
    "assumptions": [
        {
            "check": "Silhouette at chosen k",
            "statistic": sbest,
            "p_value": None,
            "verdict": "strong" if sbest > 0.5 else "moderate" if sbest > 0.25 else "weak",
            "action_taken": "Personas shown with their actual attack mix, not as hard categories.",
        }
    ],
    "results": {
        "key_numbers": {
            "k": k,
            "silhouette": sbest,
            **{f"n_persona_{i}": int(v) for i, v in enumerate(prof["n"])},
        },
        "tables": [
            {
                "title": "Personas and their attack mix",
                "columns": ["persona", *pt.columns],
                "rows": pt.round(4).reset_index().values.tolist(),
            }
        ],
        "charts": [
            {
                "type": "line",
                "title": "Elbow",
                "x_label": "k",
                "y_label": "Inertia",
                "data": [
                    {"x": int(a), "y": float(b)} for a, b in zip(scan["k"], scan["inertia"], strict=True)
                ],
            },
            {
                "type": "line",
                "title": "Silhouette",
                "x_label": "k",
                "y_label": "Mean silhouette",
                "data": [
                    {"x": int(a), "y": float(b)} for a, b in zip(scan["k"], scan["silhouette"], strict=True)
                ],
            },
            {
                "type": "bar",
                "title": "Attack mix by persona",
                "x_label": "Persona",
                "y_label": "Share of incidents",
                "data": [
                    {"x": pnames[i], **{c: float(mix.loc[i, c]) for c in mix.columns}} for i in mix.index
                ],
            },
        ],
    },
    "yields": (
        f"The data splits into {k} personas, such as {pnames[big]}, whose incidents most often involve {lead}. "
        "CyCRS places each user in the nearest persona from their sector, size and IT, and shows what actually happened to similar businesses."
    ),
    "feeds": ["decision"],
    "limitations": [
        "Personas describe reported incidents, not all businesses.",
        "Asset flags are a proxy for what a business runs.",
    ],
}
write_card(card_k)

stable = "stable" if r_ari >= 0.65 else "partly stable" if r_ari >= 0.3 else "not stable"
mg = z[-10:]
card_h = {
    "id": "hierarchical",
    "title": "Checking the personas another way",
    "module": "5: Hierarchical clustering",
    "stage": "segment",
    "used_live": False,
    "order": 12,
    "question": "Does a different clustering method find the same business personas?",
    "data_in": {
        "dataset": "500 random VCDB incidents (seed 42)",
        "n_rows": 500,
        "variables": [var("profile features", "binary", "nominal", "same as K-means")],
        "prep_steps": [
            "Random sample of 500 incidents because Ward linkage needs all pairwise distances",
            f"Tree cut at k = {k}",
        ],
        "sample_rows": sample_rows(df.assign(**Xk).iloc[hi], FK[:8]),
    },
    "why": (
        "Ward linkage merges the pair of groups that least increases within-group variance, the same quantity K-means minimises, "
        "so agreement between the two is a fair test of persona stability. "
        f"The adjusted Rand index between the two labelings is {r_ari:.2f}, where 1 is identical and 0 is chance."
    ),
    "data_properties": [
        {"name": "Adjusted Rand index vs K-means", "value": r_ari, "implication": f"Personas are {stable}."}
    ],
    "alternatives": [
        {
            "model": "Single or complete linkage",
            "why_not": "On 0/1 data with many tied distances they chain or produce one giant cluster; Ward matches the K-means objective.",
        },
        {
            "model": "Full-data hierarchy",
            "why_not": f"{len(Xk)} incidents need about {len(Xk) ** 2 // 2:,} distances; a 500-row sample is enough to test stability.",
        },
    ],
    "formula_tex": [
        {"label": "Ward merge cost", "tex": r"\Delta(A,B)=\frac{n_A n_B}{n_A+n_B}\lVert \mu_A-\mu_B\rVert^2"}
    ],
    "assumptions": [
        {
            "check": "Agreement with K-means (ARI)",
            "statistic": r_ari,
            "p_value": None,
            "verdict": stable,
            "action_taken": "Reported with the personas.",
        }
    ],
    "results": {
        "key_numbers": {"ari": r_ari, "k": k, "sample": 500},
        "tables": [
            {
                "title": "K-means (rows) vs Ward (columns)",
                "columns": ["kmeans", *[str(c) for c in ct.columns]],
                "rows": ct.reset_index().values.tolist(),
            }
        ],
        "charts": [
            {
                "type": "bar",
                "title": "Last 10 merges",
                "x_label": "Merge",
                "y_label": "Ward distance",
                "data": [{"x": i + 1, "y": float(m[2]), "size": int(m[3])} for i, m in enumerate(mg)],
            }
        ],
    },
    "yields": (
        f"An independent method recovers the personas with an adjusted Rand index of {r_ari:.2f}, so they are {stable}. "
        "CyCRS keeps the K-means personas because they can be assigned instantly, and this check shows they are not an artefact of one algorithm."
        if r_ari >= 0.65
        else f"An independent method only partly recovers the personas (adjusted Rand index {r_ari:.2f}), so their broad shape is real but "
        "the exact boundaries depend on the algorithm. CyCRS uses them for instant assignment and presents them as rough groupings."
        if r_ari >= 0.3
        else f"An independent method agrees with K-means only weakly (adjusted Rand index {r_ari:.2f}), so the personas are {stable}. "
        "CyCRS still uses them for instant assignment but presents them as rough groupings rather than firm types."
    ),
    "feeds": ["personas-kmeans"],
    "limitations": ["Based on a 500-row sample.", "Many identical 0/1 profiles create tied distances."],
}
write_card(card_h)

weak = fc["kmo"] < 0.6
card_f = {
    "id": "factor-analysis",
    "title": "Which cyber crimes move together across India",
    "module": "5: Factor analysis",
    "stage": "segment",
    "used_live": False,
    "order": 13,
    "question": "Across Indian states, which kinds of cyber crime tend to rise and fall together?",
    "data_in": {
        "dataset": "NCRB Crime in India 2024, Table 9A.2 (state-wise crime heads)",
        "n_rows": len(Xf),
        "variables": [var(k2, "numeric", "ratio", "log10(1 + cases per lakh)") for k2 in FH],
        "prep_steps": [
            "Eight non-overlapping crime heads reported by at least 20 states",
            "Divided by 2024 projected population (lakh) and log-transformed",
        ],
        "sample_rows": sample_rows(Xf.reset_index(), ["state", *list(FH)[:5]]),
    },
    "why": (
        f"Crime rates per lakh are continuous and correlated across states, which is what factor analysis models, and Bartlett's test "
        f"(p {fc['bartlett_p']:.2g}) checks that the correlations are not all zero. "
        f"KMO is {fc['kmo']:.2f} ({kmo_label(fc['kmo'])}) with only {len(Xf)} states and UTs, so the factors are "
        + ("tentative." if weak else "usable but based on few cases.")
    ),
    "data_properties": [
        {
            "name": "Bartlett chi-square p",
            "value": fc["bartlett_p"],
            "implication": "Correlations exist to factor."
            if fc["bartlett_p"] < 0.05
            else "Correlations too weak to factor.",
        },
        {"name": "KMO", "value": fc["kmo"], "implication": kmo_label(fc["kmo"])},
        {"name": "Factors with eigenvalue above 1", "value": nf, "implication": "Number of factors kept."},
        {
            "name": "Cases per variable",
            "value": len(Xf) / len(FH),
            "implication": "Well below the usual 10; treat factors as exploratory.",
        },
    ],
    "alternatives": [
        {
            "model": "PCA on the same rates",
            "why_not": "PCA explains total variance; FA separates shared variance from crime-specific noise, which is the question here.",
        },
        {
            "model": "Factor analysis on all 58 crime heads",
            "why_not": f"More variables than the {len(Xf)} states makes the correlation matrix singular.",
        },
    ],
    "formula_tex": [
        {"label": "Factor model", "tex": r"x = \Lambda f + \varepsilon"},
        {"label": "KMO", "tex": r"\mathrm{KMO}=\frac{\sum r_{ij}^2}{\sum r_{ij}^2+\sum p_{ij}^2}"},
    ],
    "assumptions": [
        {
            "check": "Bartlett sphericity",
            "statistic": fc["bartlett_chi2"],
            "p_value": fc["bartlett_p"],
            "verdict": "correlated" if fc["bartlett_p"] < 0.05 else "not correlated",
            "action_taken": "Proceeded with FA." if fc["bartlett_p"] < 0.05 else "FA reported as unreliable.",
        },
        {
            "check": "KMO sampling adequacy",
            "statistic": fc["kmo"],
            "p_value": None,
            "verdict": kmo_label(fc["kmo"]),
            "action_taken": "Results labelled exploratory." if weak else "Factors interpreted.",
        },
    ],
    "results": {
        "key_numbers": {"kmo": fc["kmo"], "bartlett_p": fc["bartlett_p"], "factors": nf, "states": len(Xf)},
        "tables": [
            {
                "title": "Loadings",
                "columns": ["crime_head", *fl.columns],
                "rows": fl.round(4).reset_index().values.tolist(),
            },
            {
                "title": "Factor names",
                "columns": ["factor", "name"],
                "rows": [[c, fnames[c]] for c in fl.columns],
            },
        ],
        "charts": [
            {
                "type": "line",
                "title": "FA scree",
                "x_label": "Factor",
                "y_label": "Eigenvalue",
                "data": [{"x": i + 1, "y": float(e)} for i, e in enumerate(eg)],
            },
            {
                "type": "bar",
                "title": "State scores on F1",
                "x_label": "State or UT",
                "y_label": "Factor score",
                "data": [{"x": s2, **{c: float(fsc.loc[s2, c]) for c in fl.columns}} for s2 in fsc.index],
            },
        ],
    },
    "yields": (
        f"Across {len(Xf)} states and UTs, {nf} factor{'s' if nf > 1 else ''} summarise{'' if nf > 1 else 's'} the eight crime rates; F1 groups {fnames['F1']}, "
        f"and {fsc.index[0]} scores highest on it. "
        "CyCRS uses this only as context about Indian crime patterns, not as an input to its recommendations."
    ),
    "feeds": [],
    "limitations": [
        f"Only {len(Xf)} cases for {len(FH)} variables.",
        "NCRB counts reported FIRs, which depend on how readily each state registers cyber crime.",
    ],
}
write_card(card_f)
log_event(lg, "cards written", ids=["pca", "personas-kmeans", "hierarchical", "factor-analysis"])
