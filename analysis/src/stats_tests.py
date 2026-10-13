import math

import numpy as np
import pandas as pd
import scikit_posthocs as sp
from scipy import stats
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.proportion import proportions_ztest

ALPHA = 0.05


def cramers_v(t):
    a = np.asarray(t, dtype=float)
    c = stats.chi2_contingency(a, correction=False)[0]
    n = a.sum()
    k = min(a.shape) - 1
    return math.sqrt(c / (n * k)) if k > 0 and n > 0 else float("nan")


def chi_square(t):
    a = np.asarray(t, dtype=float)
    c, p, d, e = stats.chi2_contingency(a, correction=False)
    return {
        "statistic": float(c),
        "p_value": float(p),
        "dof": int(d),
        "effect_size": cramers_v(a),
        "effect_name": "Cramer's V",
        "min_expected": float(e.min()),
        "share_expected_below_5": float((e < 5).mean()),
    }


def normality(x):
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if len(x) <= 5000:
        w, p = stats.shapiro(x)
        return {
            "test": "Shapiro-Wilk",
            "statistic": float(w),
            "p_value": float(p),
            "normal": bool(p >= ALPHA),
        }
    r = stats.anderson(x, dist="norm", method="interpolate")
    p = float(r.pvalue)
    return {
        "test": "Anderson-Darling",
        "statistic": float(r.statistic),
        "p_value": p,
        "normal": bool(p >= ALPHA),
    }


def mann_whitney(x, y):
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    u, p = stats.mannwhitneyu(x, y, alternative="two-sided")
    r = 1 - 2 * u / (len(x) * len(y))
    return {
        "statistic": float(u),
        "p_value": float(p),
        "effect_size": float(r),
        "effect_name": "rank-biserial r",
    }


def kruskal(gs):
    gs = [np.asarray(g, dtype=float) for g in gs]
    h, p = stats.kruskal(*gs)
    n, k = sum(len(g) for g in gs), len(gs)
    e = (h - k + 1) / (n - k)
    return {
        "statistic": float(h),
        "p_value": float(p),
        "effect_size": float(e),
        "effect_name": "epsilon squared",
    }


def anova(gs):
    gs = [np.asarray(g, dtype=float) for g in gs]
    f, p = stats.f_oneway(*gs)
    a = np.concatenate(gs)
    m = a.mean()
    sb = sum(len(g) * (g.mean() - m) ** 2 for g in gs)
    st = ((a - m) ** 2).sum()
    return {
        "statistic": float(f),
        "p_value": float(p),
        "effect_size": float(sb / st),
        "effect_name": "eta squared",
    }


def levene(gs):
    w, p = stats.levene(*[np.asarray(g, dtype=float) for g in gs])
    return {"statistic": float(w), "p_value": float(p), "equal_variance": bool(p >= ALPHA)}


def cohens_h(p1, p2):
    return 2 * math.asin(math.sqrt(p1)) - 2 * math.asin(math.sqrt(p2))


def two_proportion_z(k1, n1, k2, n2):
    z, p = proportions_ztest([k1, k2], [n1, n2])
    return {
        "statistic": float(z),
        "p_value": float(p),
        "effect_size": cohens_h(k1 / n1, k2 / n2),
        "effect_name": "Cohen's h",
    }


def dunn(df, v, g):
    return sp.posthoc_dunn(df, val_col=v, group_col=g, p_adjust="holm")


def tukey(v, g):
    r = pairwise_tukeyhsd(np.asarray(v, dtype=float), np.asarray(g), alpha=ALPHA)
    d = r.summary().data
    return pd.DataFrame(d[1:], columns=d[0])


def holm(ps):
    ps = np.asarray(ps, dtype=float)
    m = len(ps)
    o = np.argsort(ps)
    a = np.empty(m)
    c = 0.0
    for i, j in enumerate(o):
        c = max(c, min(1.0, (m - i) * ps[j]))
        a[j] = c
    return a


def decide(p):
    if p is None or (isinstance(p, float) and math.isnan(p)):
        return "not applicable"
    return "reject H0" if p < ALPHA else "do not reject H0"


def effect_label(name, v):
    a = abs(v)
    if name == "Cramer's V":
        cuts = (0.1, 0.3, 0.5)
    elif name in ("rank-biserial r",):
        cuts = (0.1, 0.3, 0.5)
    elif name == "Cohen's h":
        cuts = (0.2, 0.5, 0.8)
    else:
        cuts = (0.01, 0.06, 0.14)
    if a < cuts[0]:
        return "negligible"
    if a < cuts[1]:
        return "small"
    if a < cuts[2]:
        return "medium"
    return "large"
