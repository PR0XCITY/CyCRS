import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.metrics import confusion_matrix, roc_auc_score, roc_curve
from sklearn.model_selection import StratifiedKFold, cross_val_score

from src.nbutil import ACTORS, ASSETS, CATS, slug
from src.regression import dummies

SEED = 42
MIN_COUNT = 5
PROFILE_ASSETS = [a for a in ASSETS if a != "asset_person"]
LEAKY = {
    "asset_person": (
        "VERIS codes the targeted person as an asset in every social attack, so it restates the label"
    )
}


def sector_dummies(df, top):
    g = df["sector"].where(df["sector"].isin(top), "Other")
    d = dummies(g, top, "sector")
    return d.rename(columns={f"sector_{t}": f"sector_{slug(t)}" for t in top})


def size_dummies(df):
    return dummies(df["size"], ["medium", "large", "unknown"], "size")


def profile_features(df, top):
    return pd.concat([sector_dummies(df, top), size_dummies(df), df[PROFILE_ASSETS].astype(float)], axis=1)


def incident_features(df, top):
    ac = [f"action_{c}" for c in CATS]
    return pd.concat(
        [df[ACTORS + ac + PROFILE_ASSETS].astype(float), sector_dummies(df, top), size_dummies(df)], axis=1
    )


def separation_drops(X, y, k=MIN_COUNT):
    out = []
    for c in X.columns:
        a = X.loc[y == 1, c].sum()
        b = X.loc[y == 0, c].sum()
        if a + b < k:
            out.append((c, f"only {int(a + b)} incidents have it"))
        elif a == 0 or b == 0:
            out.append((c, "appears in one class only (separation)"))
    return out


def fit_logit(X, y):
    return sm.Logit(y.astype(float), sm.add_constant(X.astype(float), has_constant="add")).fit(
        disp=0, maxiter=200
    )


def sigmoid(z):
    return 1 / (1 + np.exp(-z))


def predict_logit(intercept, coefs, X):
    z = intercept + X[list(coefs)].astype(float).values @ np.array(list(coefs.values()), dtype=float)
    return sigmoid(z)


def odds_table(r):
    c = r.conf_int()
    t = pd.DataFrame(
        {
            "term": r.params.index,
            "coef": r.params.values,
            "p_value": r.pvalues.values,
            "odds_ratio": np.exp(r.params.values),
            "or_low": np.exp(c[0].values),
            "or_high": np.exp(c[1].values),
        }
    )
    return t[t["term"] != "const"].reset_index(drop=True)


def metrics(y, p, thr=0.5):
    yh = (np.asarray(p) >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, yh, labels=[0, 1]).ravel()
    pr = tp / (tp + fp) if tp + fp else 0.0
    rc = tp / (tp + fn) if tp + fn else 0.0
    return {
        "threshold": float(thr),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
        "accuracy": (tp + tn) / (tp + tn + fp + fn),
        "precision": pr,
        "recall": rc,
        "specificity": tn / (tn + fp) if tn + fp else 0.0,
        "f1": 2 * pr * rc / (pr + rc) if pr + rc else 0.0,
        "auc": float(roc_auc_score(y, p)),
    }


def youden(y, p):
    f, t, th = roc_curve(y, p)
    j = t - f
    i = int(np.argmax(j))
    return {"threshold": float(min(th[i], 1.0)), "j": float(j[i]), "tpr": float(t[i]), "fpr": float(f[i])}


def roc_points(y, p, n=60):
    f, t, _ = roc_curve(y, p)
    ix = np.unique(np.linspace(0, len(f) - 1, min(n, len(f))).round().astype(int))
    return [{"fpr": float(f[i]), "tpr": float(t[i])} for i in ix]


def cv_auc(model, X, y, k=5):
    s = cross_val_score(
        model, X, y, cv=StratifiedKFold(k, shuffle=True, random_state=SEED), scoring="roc_auc"
    )
    return float(s.mean()), float(s.std())
