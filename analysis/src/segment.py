import factor_analyzer.factor_analyzer as fam
import numpy as np
import pandas as pd
from factor_analyzer import FactorAnalyzer
from factor_analyzer.factor_analyzer import calculate_bartlett_sphericity, calculate_kmo
from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler
from sklearn.utils import check_array

SEED = 42


def check_array_compat(X, force_all_finite=True, **kw):
    return check_array(X, ensure_all_finite=force_all_finite, **kw)


fam.check_array = check_array_compat


def pca_fit(X):
    s = StandardScaler().fit(X)
    p = PCA(random_state=SEED).fit(s.transform(X))
    ev = p.explained_variance_
    cum = np.cumsum(p.explained_variance_ratio_)
    return {
        "scaler": s,
        "pca": p,
        "eigenvalues": ev,
        "cumulative": cum,
        "kaiser": int((ev > 1).sum()),
        "n80": int(np.searchsorted(cum, 0.8) + 1),
    }


def loadings(p, cols, k):
    return pd.DataFrame(
        p.components_[:k].T * np.sqrt(p.explained_variance_[:k]),
        index=cols,
        columns=[f"PC{i + 1}" for i in range(k)],
    )


def name_component(col, n=2):
    s = col.reindex(col.abs().sort_values(ascending=False).index).head(n)
    return " / ".join(f"{'+' if v > 0 else '-'}{i}" for i, v in s.items())


def kmeans_scan(X, ks, sample=3000):
    rs = []
    for k in ks:
        m = KMeans(n_clusters=k, n_init=10, random_state=SEED).fit(X)
        sc = silhouette_score(X, m.labels_, sample_size=min(sample, len(X)), random_state=SEED)
        rs.append({"k": k, "inertia": float(m.inertia_), "silhouette": float(sc)})
    return pd.DataFrame(rs)


def fit_kmeans(X, k):
    return KMeans(n_clusters=k, n_init=10, random_state=SEED).fit(X)


def assign(x, centroids):
    d = ((np.asarray(centroids, dtype=float) - np.asarray(x, dtype=float)) ** 2).sum(axis=1)
    return int(np.argmin(d))


def ward_labels(X, k):
    z = linkage(np.asarray(X, dtype=float), method="ward")
    return z, fcluster(z, k, criterion="maxclust") - 1


def ari(a, b):
    return float(adjusted_rand_score(a, b))


def dominant(row, prefix, labels, cut=0.5):
    s = row[[c for c in row.index if c.startswith(prefix)]]
    if s.empty or s.max() < cut:
        return None
    return labels.get(s.idxmax(), s.idxmax())


def fa_checks(X):
    chi, p = calculate_bartlett_sphericity(X)
    _, kmo = calculate_kmo(X)
    return {"bartlett_chi2": float(chi), "bartlett_p": float(p), "kmo": float(kmo)}


def kmo_label(v):
    for c, t in (
        (0.9, "marvellous"),
        (0.8, "meritorious"),
        (0.7, "middling"),
        (0.6, "mediocre"),
        (0.5, "miserable"),
    ):
        if v >= c:
            return t
    return "unacceptable"


def fa_fit(X, n, rotation="varimax"):
    f = FactorAnalyzer(n_factors=n, rotation=rotation, method="minres")
    f.fit(X)
    return f


def fa_eigen(X):
    f = FactorAnalyzer(rotation=None, method="minres")
    f.fit(X)
    return f.get_eigenvalues()[0]
