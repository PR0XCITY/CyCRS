# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
# ---

# %% [markdown]
# # 04 Classification
# Part A: which incidents end in confirmed data disclosure. Part B: which attack categories a business profile faces.

# %%
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_score, train_test_split
from sklearn.naive_bayes import BernoulliNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier, export_text, plot_tree


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
from src.classify import (
    LEAKY,
    SEED,
    cv_auc,
    fit_logit,
    incident_features,
    metrics,
    odds_table,
    predict_logit,
    profile_features,
    roc_points,
    separation_drops,
    youden,
)
from src.log import get_logger, log_event
from src.nbutil import CATS, MODELS, OUT, load_clean, sample_rows, save_fig, top_sectors, var, write_json

lg = get_logger("nb04", phase="phase4")
df = load_clean()
top = top_sectors(df)
CV = StratifiedKFold(5, shuffle=True, random_state=SEED)

# %% [markdown]
# ## Part A: breach classifier

# %%
b = df[df["breach"].notna()].copy()
yb = b["breach"].astype(int)
Xb = incident_features(b, top)
itr, ite = train_test_split(b.index, test_size=0.3, random_state=SEED, stratify=yb)
sep = separation_drops(Xb.loc[itr], yb.loc[itr])
Xb = Xb.drop(columns=[c for c, _ in sep])
FB = list(Xb.columns)
Xtr, Xte, ytr, yte = Xb.loc[itr], Xb.loc[ite], yb.loc[itr], yb.loc[ite]
bal = {
    "train_yes": int(ytr.sum()),
    "train_no": int((ytr == 0).sum()),
    "test_yes": int(yte.sum()),
    "test_no": int((yte == 0).sum()),
}
log_event(lg, "breach split", features=len(FB), dropped=sep, **bal)

lo = fit_logit(Xtr, ytr)
ob = odds_table(lo).sort_values("p_value")
ob.to_csv(OUT / "04_breach_logit_odds.csv", index=False)

tree_gs = GridSearchCV(
    DecisionTreeClassifier(class_weight="balanced", random_state=SEED),
    {"max_depth": list(range(1, 11)), "min_samples_leaf": [1, 5, 10, 20, 50]},
    cv=CV,
    scoring="roc_auc",
)
tree_gs.fit(Xtr, ytr)
tp = tree_gs.best_params_

ks = list(range(1, 41))
kerr = []
for k in ks:
    m = make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=k))
    kerr.append(1 - cross_val_score(m, Xtr, ytr, cv=CV, scoring="balanced_accuracy").mean())
k_best = ks[int(np.argmin(kerr))]
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(ks, kerr, marker="o")
ax.axvline(k_best, color="red", ls="--", label=f"chosen k = {k_best}")
ax.set_title("KNN: 5-fold CV error (1 - balanced accuracy) by k")
ax.set_xlabel("k (neighbours)")
ax.set_ylabel("CV balanced error")
ax.legend()
save_fig(fig, "04_knn_elbow.png")

MODELS_A = {
    "logistic": make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=2000)),
    "decision_tree": DecisionTreeClassifier(class_weight="balanced", random_state=SEED, **tp),
    "knn": make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=k_best)),
    "naive_bayes": BernoulliNB(),
    "lda": make_pipeline(StandardScaler(), LinearDiscriminantAnalysis()),
}
WHY = {
    "logistic": f"Binary target with {len(FB)} binary predictors; class weights offset the {bal['train_no']} No cases in training.",
    "decision_tree": f"Finds interactions between attack and asset flags as readable rules; depth {tp['max_depth']} and leaf {tp['min_samples_leaf']} chosen by CV AUC.",
    "knn": f"Non-parametric baseline on scaled flags; k = {k_best} minimised CV balanced error.",
    "naive_bayes": "All predictors are 0/1 flags, so Bernoulli Naive Bayes is the matching likelihood.",
    "lda": "Linear boundary with shared covariance; a classical comparison for logistic regression.",
}
rows, rocs, cms, prob = [], {}, {}, {}
for n, m in MODELS_A.items():
    m.fit(Xtr, ytr)
    p = m.predict_proba(Xte)[:, 1]
    mu, sd = cv_auc(m, Xtr, ytr)
    r = metrics(yte, p)
    rows.append({"model": n, **r, "cv_auc_mean": mu, "cv_auc_sd": sd})
    rocs[n] = roc_points(yte, p)
    cms[n] = [[r["tn"], r["fp"]], [r["fn"], r["tp"]]]
    prob[n] = p
cmp = pd.DataFrame(rows)
cmp.to_csv(OUT / "classifier_comparison.csv", index=False)
best = cmp.loc[cmp["cv_auc_mean"].idxmax(), "model"]
log_event(lg, "breach models", rows=cmp.round(4).to_dict(orient="records"), best=best)

fig, ax = plt.subplots(figsize=(7, 6))
for n in MODELS_A:
    ax.plot(
        [q["fpr"] for q in rocs[n]],
        [q["tpr"] for q in rocs[n]],
        label=f"{n} (AUC {cmp.set_index('model').loc[n, 'auc']:.2f})",
    )
ax.plot([0, 1], [0, 1], "k--", lw=0.8)
ax.set_title(f"Breach classifiers: ROC on test set ({bal['test_no']} No, {bal['test_yes']} Yes)")
ax.set_xlabel("False positive rate (1 - specificity)")
ax.set_ylabel("True positive rate (recall)")
ax.legend()
save_fig(fig, "04_roc_breach.png")

fig, axs = plt.subplots(1, 5, figsize=(18, 3.8))
for ax, n in zip(axs, MODELS_A, strict=True):
    c = np.array(cms[n])
    ax.imshow(c, cmap="Blues")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, c[i, j], ha="center", va="center")
    ax.set_title(n)
    ax.set_xticks([0, 1], ["No", "Yes"])
    ax.set_yticks([0, 1], ["No", "Yes"])
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
save_fig(fig, "04_confusion_breach.png")

tr = MODELS_A["decision_tree"]
rules = export_text(tr, feature_names=FB, max_depth=4)
(OUT / "04_tree_rules.txt").write_text(rules, encoding="utf-8")
fig, ax = plt.subplots(figsize=(18, 9))
plot_tree(tr, feature_names=FB, class_names=["No", "Yes"], max_depth=4, filled=True, fontsize=6, ax=ax)
ax.set_title(f"Decision tree for data disclosure (shown to depth 4 of {tr.get_depth()})")
save_fig(fig, "04_tree.png")

yj = youden(yte, prob[best])
m05 = metrics(yte, prob[best], 0.5)
mj = metrics(yte, prob[best], yj["threshold"])
log_event(lg, "youden", model=best, **yj, before=m05, after=mj)
cmp.round(4)

# %% [markdown]
# ## Part B: attack-type models on profile features

# %%
a = df[df[[f"action_{c}" for c in CATS]].sum(axis=1) > 0].copy()
Xa = profile_features(a, top)
FA = list(Xa.columns)
strat = a[[f"action_{c}" for c in CATS]].idxmax(axis=1)
jtr, jte = train_test_split(a.index, test_size=0.3, random_state=SEED, stratify=strat)
write_json(
    {
        "key": "source_file",
        "source_file": a.loc[jte, "source_file"].tolist(),
        "n_train": len(jtr),
        "n_test": len(jte),
    },
    MODELS / "attack_test_ids.json",
)
AT = [c for c in CATS if c != "environmental"]
res, coefs, oddsr, rocb = [], {}, [], {}
for c in AT:
    yc = a[f"action_{c}"].astype(int)
    r = fit_logit(Xa.loc[jtr], yc.loc[jtr])
    co = {f: float(r.params[f]) for f in FA}
    p = predict_logit(float(r.params["const"]), co, Xa.loc[jte])
    mu, sd = cv_auc(LogisticRegression(C=np.inf, max_iter=2000), Xa.loc[jtr], yc.loc[jtr])
    res.append(
        {
            "category": c,
            "prevalence_train": float(yc.loc[jtr].mean()),
            "test_auc": metrics(yc.loc[jte], p)["auc"],
            "cv_auc_mean": mu,
            "cv_auc_sd": sd,
            "pseudo_r2": float(r.prsquared),
        }
    )
    coefs[c] = {"intercept": float(r.params["const"]), "coefficients": co}
    t = odds_table(r)
    t = t[t["p_value"] < 0.05].reindex(t["coef"].abs().sort_values(ascending=False).index).dropna().head(5)
    for _, q in t.iterrows():
        oddsr.append({"category": c, **q.to_dict()})
    rocb[c] = roc_points(yc.loc[jte], p)
ra = pd.DataFrame(res)
ra.to_csv(OUT / "04_attack_auc.csv", index=False)
od = pd.DataFrame(oddsr)
od.to_csv(OUT / "04_attack_odds.csv", index=False)
write_json(
    {
        "id": "attack-likelihood",
        "feature_order": FA,
        "sectors": top,
        "reference_levels": {"sector": "Other", "size": "small"},
        "models": coefs,
    },
    MODELS / "attack_models.json",
)
fig, ax = plt.subplots(figsize=(7, 6))
for c in AT:
    ax.plot(
        [q["fpr"] for q in rocb[c]],
        [q["tpr"] for q in rocb[c]],
        label=f"{c} (AUC {ra.set_index('category').loc[c, 'test_auc']:.2f})",
    )
ax.plot([0, 1], [0, 1], "k--", lw=0.8)
ax.set_title("Attack-type logistic models: ROC on held-out incidents")
ax.set_xlabel("False positive rate")
ax.set_ylabel("True positive rate")
ax.legend()
save_fig(fig, "04_roc_attack.png")
log_event(lg, "attack models", rows=ra.round(4).to_dict(orient="records"))
ra.round(4)

# %% [markdown]
# ## Cards

# %%
cb = cmp.set_index("model")
COLS = ["model", "accuracy", "precision", "recall", "specificity", "f1", "auc", "cv_auc_mean", "cv_auc_sd"]
top_rule = rules.splitlines()[0].strip() if rules else ""
top_or = (
    ob[ob["p_value"] < 0.05].reindex(ob["coef"].abs().sort_values(ascending=False).index).dropna().head(3)
)
or_txt = (
    ", ".join(f"{t} (odds ratio {v:.2f})" for t, v in zip(top_or["term"], top_or["odds_ratio"], strict=True))
    or "no single flag at p < 0.05"
)
card_b = {
    "id": "breach-classifiers",
    "title": "Which incidents end in data loss",
    "module": "4: Classification (logistic regression, decision tree, KNN, Naive Bayes, LDA, ROC, confusion matrix)",
    "stage": "likelihood",
    "used_live": False,
    "order": 8,
    "question": "Can the kind of attack, attacker and assets involved tell us whether an incident ends in confirmed data disclosure?",
    "data_in": {
        "dataset": "VCDB incidents with data_disclosure Yes or No",
        "n_rows": len(b),
        "variables": [
            var("breach", "binary", "nominal", "target, 1 = Yes"),
            var("actor_*, action_*, asset_*", "binary", "nominal"),
            var("sector", "categorical", "nominal", "dummies, reference Other"),
            var("size", "categorical", "ordinal", "dummies, reference small"),
        ],
        "prep_steps": [
            f"Stratified 70/30 split (random_state 42): train {bal['train_yes']} Yes / {bal['train_no']} No, test {bal['test_yes']} Yes / {bal['test_no']} No",
            "Dropped flags that, in the training rows, occur in only one class or fewer than 5 times: "
            + (", ".join(c for c, _ in sep) or "none"),
            "Standard scaling inside the pipeline for logistic, KNN and LDA; class_weight balanced for logistic and tree",
            "asset_person left out: " + LEAKY["asset_person"],
        ],
        "sample_rows": sample_rows(
            b, ["breach", "actor_external", "action_hacking", "action_error", "asset_server", "size"]
        ),
    },
    "why": (
        f"The target is binary and only {100 * bal['train_no'] / (bal['train_no'] + bal['train_yes']):.1f}% of training incidents are No, "
        "so models are compared on AUC and recall/specificity rather than accuracy, and class weights are used where supported. "
        "Each model has a data-based reason: "
        + "; ".join(f"{k}, {v[0].lower() + v[1:].rstrip('.')}" for k, v in WHY.items())
        + "."
    ),
    "data_properties": [
        {
            "name": "Share of No in training",
            "value": bal["train_no"] / (bal["train_no"] + bal["train_yes"]),
            "implication": "Severe imbalance: accuracy is misleading.",
        },
        {
            "name": "No cases in test set",
            "value": bal["test_no"],
            "implication": "Test AUC and specificity are estimated from very few cases.",
        },
        {
            "name": "Best model by CV AUC",
            "value": f"{best} ({cb.loc[best, 'cv_auc_mean']:.3f} +/- {cb.loc[best, 'cv_auc_sd']:.3f})",
            "implication": "Model used for the Youden threshold.",
        },
        {
            "name": "Youden threshold for best model",
            "value": yj["threshold"],
            "implication": f"J = {yj['j']:.3f}; balances recall and specificity.",
        },
    ],
    "alternatives": [
        {
            "model": "Accuracy as the selection metric",
            "why_not": f"Predicting Yes for every incident already scores {bal['test_yes'] / (bal['test_yes'] + bal['test_no']):.3f} accuracy.",
        },
        {
            "model": "SMOTE oversampling",
            "why_not": f"Synthesising {bal['train_no']} rare cases of binary flags creates unrealistic incidents; class weights are simpler and in the syllabus.",
        },
    ],
    "formula_tex": [
        {"label": "Logistic model", "tex": r"P(y=1)=\frac{1}{1+e^{-(\beta_0+\beta^\top x)}}"},
        {
            "label": "Bernoulli Naive Bayes",
            "tex": r"P(y\mid x)\propto P(y)\prod_j p_{jy}^{x_j}(1-p_{jy})^{1-x_j}",
        },
        {"label": "Youden's J", "tex": r"J=\text{sensitivity}+\text{specificity}-1"},
    ],
    "assumptions": [
        {
            "check": "Class balance (No share in training)",
            "statistic": bal["train_no"] / (bal["train_no"] + bal["train_yes"]),
            "p_value": None,
            "verdict": "severely imbalanced",
            "action_taken": "Class weights, AUC-based selection, Youden threshold.",
        },
        {
            "check": "Logit convergence after separation drops",
            "statistic": float(lo.llf),
            "p_value": float(lo.llr_pvalue),
            "verdict": "converged" if lo.mle_retvals["converged"] else "not converged",
            "action_taken": "Odds ratios read from the statsmodels fit.",
        },
    ],
    "results": {
        "key_numbers": {
            "best_model": best,
            "youden_j": yj["j"],
            "best_cv_auc": cb.loc[best, "cv_auc_mean"],
            "youden_threshold": yj["threshold"],
            "k_knn": k_best,
            "tree_depth": tp["max_depth"],
            "tree_min_leaf": tp["min_samples_leaf"],
        },
        "tables": [
            {
                "title": "Classifier comparison (test set, threshold 0.5)",
                "columns": COLS,
                "rows": cmp[COLS].round(4).values.tolist(),
            },
            {
                "title": f"Youden threshold for {best}",
                "columns": ["threshold", "tn", "fp", "fn", "tp", "recall", "specificity"],
                "rows": [
                    [
                        m05["threshold"],
                        m05["tn"],
                        m05["fp"],
                        m05["fn"],
                        m05["tp"],
                        m05["recall"],
                        m05["specificity"],
                    ],
                    [
                        mj["threshold"],
                        mj["tn"],
                        mj["fp"],
                        mj["fn"],
                        mj["tp"],
                        mj["recall"],
                        mj["specificity"],
                    ],
                ],
            },
            {
                "title": "Strongest significant logistic odds ratios",
                "columns": ["term", "odds_ratio", "p_value"],
                "rows": top_or[["term", "odds_ratio", "p_value"]].values.tolist(),
            },
            {
                "title": "Decision tree rules (depth 4)",
                "columns": ["rule"],
                "rows": [[x] for x in rules.splitlines()[:40]],
            },
        ],
        "charts": [
            *[
                {
                    "type": "line",
                    "title": f"ROC {n}",
                    "x_label": "False positive rate",
                    "y_label": "True positive rate",
                    "data": rocs[n],
                }
                for n in MODELS_A
            ],
            *[
                {
                    "type": "matrix",
                    "title": f"Confusion matrix {n}",
                    "x_label": "Predicted (No, Yes)",
                    "y_label": "Actual (No, Yes)",
                    "data": cms[n],
                }
                for n in MODELS_A
            ],
            {
                "type": "line",
                "title": "KNN CV error by k",
                "x_label": "k",
                "y_label": "CV balanced error",
                "data": [{"x": k, "y": float(e)} for k, e in zip(ks, kerr, strict=True)],
            },
        ],
    },
    "yields": (
        f"{best.replace('_', ' ').capitalize()} separates data-loss incidents best (CV AUC {cb.loc[best, 'cv_auc_mean']:.2f}), and the strongest "
        f"logistic signals are {or_txt}. "
        f"With only {bal['train_no']} No cases to learn from, CyCRS treats most incidents as likely to expose data and uses this model "
        "only to explain which attack features matter, not to promise a business it is safe."
    ),
    "feeds": ["attack-likelihood"],
    "limitations": [
        f"Only {bal['train_no'] + bal['test_no']} incidents are confirmed No, so every No-side metric is uncertain.",
        "Potentially and Unknown disclosures were dropped; incidents with no confidentiality section count as No, which assumes VERIS coders recorded every exposure.",
        f"CV AUC SD for the best model is {cb.loc[best, 'cv_auc_sd']:.3f}, so model ranks may change with a new sample.",
    ],
}
write_card(card_b)

rb = ra.set_index("category")
bc = rb["test_auc"].idxmax()
wc = rb["test_auc"].idxmin()
odr = od.copy()
odr["term"] = odr["term"].astype(str)
ocols = ["category", "term", "odds_ratio", "or_low", "or_high", "p_value"]
card_a = {
    "id": "attack-likelihood",
    "title": "Which attacks a business is most exposed to",
    "module": "4: Logistic regression and ROC",
    "stage": "likelihood",
    "used_live": True,
    "order": 9,
    "question": "Given a business's sector, size and the kinds of IT assets it relies on, which attack categories are most likely if it has an incident?",
    "data_in": {
        "dataset": "VCDB incidents with at least one known action category",
        "n_rows": len(a),
        "variables": [
            var("action_<category>", "binary", "nominal", "one target per model"),
            var("sector", "categorical", "nominal", "dummies, reference Other"),
            var("size", "categorical", "ordinal", "dummies, reference small"),
            var("asset_*", "binary", "nominal", "proxy for what the business runs"),
        ],
        "prep_steps": [
            "Dropped incidents with no known action category",
            f"One stratified 70/30 split shared by all categories ({len(jtr)} train, {len(jte)} test); test incident ids saved for Phase 6",
            "Environmental attacks left out (too rare for a model)",
            "asset_person left out of the inputs: " + LEAKY["asset_person"],
            f"Fixed feature order of {len(FA)} profile features saved with the coefficients",
        ],
        "sample_rows": sample_rows(
            a, ["sector", "size", "asset_server", "asset_media", "action_hacking", "action_error"]
        ),
    },
    "why": (
        f"Each target is a binary flag and the inputs are a handful of 0/1 profile features, so logistic regression gives a "
        "calibrated probability per category and an odds ratio per feature that a business owner can read. "
        "Its formula is a weighted sum and a sigmoid, so the browser reproduces the exact same number from the saved "
        "coefficients with no server. "
        f"Unweighted fits keep probabilities calibrated to the observed category shares (for example {100 * rb.loc[bc, 'prevalence_train']:.0f}% for {bc})."
    ),
    "data_properties": [
        {
            "name": f"Best category AUC ({bc})",
            "value": rb.loc[bc, "test_auc"],
            "implication": "Profile predicts this attack type well.",
        },
        {
            "name": f"Weakest category AUC ({wc})",
            "value": rb.loc[wc, "test_auc"],
            "implication": "Profile says little about this attack type; show with caution.",
        },
        {
            "name": "Profile features",
            "value": len(FA),
            "implication": "Small, fixed input set entered by the user.",
        },
    ],
    "alternatives": [
        {
            "model": "Decision tree",
            "why_not": f"Its probabilities are leaf shares that jump between profiles, and the breach tree needed depth {tp['max_depth']}; logistic odds ratios are smoother and easier to explain.",
        },
        {
            "model": "Naive Bayes",
            "why_not": "Assumes sector, size and asset flags are independent given the attack, but sector and asset use are related, so its probabilities are poorly calibrated.",
        },
        {
            "model": f"Best breach classifier ({best})",
            "why_not": "Built for a different target; logistic keeps exact browser reproduction and readable coefficients.",
        },
    ],
    "formula_tex": [
        {
            "label": "Probability of category c",
            "tex": r"P(c \mid x)=\frac{1}{1+e^{-(\beta_{0c}+\beta_c^\top x)}}",
        },
        {"label": "Odds ratio", "tex": r"\mathrm{OR}_j = e^{\beta_j}"},
    ],
    "assumptions": [
        {
            "check": f"Held-out AUC, {c}",
            "statistic": float(rb.loc[c, "test_auc"]),
            "p_value": None,
            "verdict": "useful" if rb.loc[c, "test_auc"] >= 0.7 else "weak",
            "action_taken": "Shown with its AUC in the app.",
        }
        for c in AT
    ],
    "results": {
        "key_numbers": {f"auc_{c}": float(rb.loc[c, "test_auc"]) for c in AT},
        "tables": [
            {"title": "Per-category AUC", "columns": list(ra.columns), "rows": ra.round(4).values.tolist()},
            {
                "title": "Strongest significant odds ratios per category",
                "columns": ocols,
                "rows": odr[ocols].round(4).values.tolist(),
            },
        ],
        "charts": [
            {
                "type": "line",
                "title": f"ROC {c}",
                "x_label": "False positive rate",
                "y_label": "True positive rate",
                "data": rocb[c],
            }
            for c in AT
        ],
    },
    "yields": (
        f"A business's profile predicts some attack types much better than others: {bc} reaches AUC {rb.loc[bc, 'test_auc']:.2f} while "
        f"{wc} is only {rb.loc[wc, 'test_auc']:.2f}. "
        "CyCRS runs these models on the user's profile to rank attack categories by probability, then sends each category to "
        "the impact model to price it."
    ),
    "feeds": ["decision"],
    "limitations": [
        "Asset flags record what was hit in past incidents and are used as a proxy for what a business runs.",
        "Probabilities are conditional on an incident happening; the chance of having an incident at all comes from annual_incident_prob.",
        "VCDB over represents large and US organisations.",
    ],
}
write_card(card_a)
log_event(lg, "cards written", ids=["breach-classifiers", "attack-likelihood"])
