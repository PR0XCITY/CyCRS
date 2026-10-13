import math

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.stattools import durbin_watson, jarque_bera

ALPHA = 0.05
BANDS = {
    "1 to 10": (1, 10),
    "11 to 100": (11, 100),
    "101 to 1000": (101, 1000),
    "1001 to 10000": (1001, 10000),
    "10001 to 25000": (10001, 25000),
    "25001 to 50000": (25001, 50000),
    "50001 to 100000": (50001, 100000),
    "Over 100000": (100001, None),
}


def band_employees(b):
    if b not in BANDS:
        return np.nan
    lo, hi = BANDS[b]
    return float(lo) if hi is None else math.sqrt(lo * hi)


def log_employees(s):
    return np.log10(s.map(band_employees).astype(float))


def dummies(s, levels, prefix):
    return pd.DataFrame({f"{prefix}_{v}": (s == v).astype(float) for v in levels}, index=s.index)


def fit_ols(X, y, robust=False):
    m = sm.OLS(y.astype(float), sm.add_constant(X.astype(float), has_constant="add"))
    return m.fit(cov_type="HC3") if robust else m.fit()


def vif_table(X):
    a = sm.add_constant(X.astype(float), has_constant="add")
    rs = [
        {"variable": c, "vif": float(variance_inflation_factor(a.values, i))} for i, c in enumerate(a.columns)
    ]
    return pd.DataFrame(rs[1:]).sort_values("vif", ascending=False).reset_index(drop=True)


def assumption_checks(r):
    e = r.resid
    jb, jp, sk, ku = jarque_bera(e)
    lm, bp, _, _ = het_breuschpagan(e, r.model.exog)
    return {
        "jarque_bera": float(jb),
        "jarque_bera_p": float(jp),
        "residual_skew": float(sk),
        "residual_kurtosis": float(ku),
        "breusch_pagan": float(lm),
        "breusch_pagan_p": float(bp),
        "durbin_watson": float(durbin_watson(e)),
    }


def backward_eliminate(X, y, alpha=ALPHA, robust=False):
    cs = list(X.columns)
    dropped = []
    while cs:
        r = fit_ols(X[cs], y, robust)
        p = r.pvalues.drop("const")
        w = p.idxmax()
        if p[w] <= alpha:
            return r, cs, dropped
        cs.remove(w)
        dropped.append((w, float(p[w])))
    return fit_ols(X[[]], y, robust), cs, dropped


def rmse(r, X, y):
    p = r.predict(sm.add_constant(X.astype(float), has_constant="add"))
    return float(np.sqrt(np.mean((y.astype(float) - p) ** 2)))


def summary_row(name, r, X, y, n_features):
    return {
        "model": name,
        "features": n_features,
        "n_train": int(r.nobs),
        "r2": float(r.rsquared),
        "adj_r2": float(r.rsquared_adj),
        "aic": float(r.aic),
        "bic": float(r.bic),
        "test_rmse": rmse(r, X, y),
    }


def multipliers(r):
    c = r.conf_int()
    t = pd.DataFrame(
        {
            "term": r.params.index,
            "coef": r.params.values,
            "se": r.bse.values,
            "p_value": r.pvalues.values,
            "ci_low": c[0].values,
            "ci_high": c[1].values,
        }
    )
    t["multiplier"] = 10 ** t["coef"]
    t["mult_low"] = 10 ** t["ci_low"]
    t["mult_high"] = 10 ** t["ci_high"]
    return t
