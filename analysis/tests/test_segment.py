import numpy as np
import pandas as pd
import pytest

from src.segment import (
    ari,
    assign,
    dominant,
    fa_checks,
    fa_fit,
    kmeans_scan,
    kmo_label,
    loadings,
    name_component,
    pca_fit,
    ward_labels,
)


def blobs():
    g = np.random.default_rng(42)
    c = np.array([[0, 0], [10, 0], [0, 10]])
    return np.vstack([g.normal(m, 0.5, size=(40, 2)) for m in c]), np.repeat([0, 1, 2], 40)


def test_kmeans_scan_finds_three_blobs():
    X, _ = blobs()
    s = kmeans_scan(X, range(2, 6))
    assert int(s.loc[s["silhouette"].idxmax(), "k"]) == 3
    assert s["inertia"].is_monotonic_decreasing


def test_assign_nearest_centroid():
    assert assign([9, 1], [[0, 0], [10, 0], [0, 10]]) == 1
    assert assign([0, 0], [[0, 0], [10, 0]]) == 0


def test_ward_matches_truth():
    X, y = blobs()
    _, lb = ward_labels(X, 3)
    assert ari(lb, y) == pytest.approx(1.0)


def test_pca_counts_and_names():
    g = np.random.default_rng(1)
    a = g.normal(size=500)
    X = pd.DataFrame({"a": a, "a2": a + g.normal(scale=0.1, size=500), "b": g.normal(size=500)})
    r = pca_fit(X)
    assert r["kaiser"] == 1 or r["eigenvalues"][1] < 1.1
    assert r["n80"] == 2
    ld = loadings(r["pca"], X.columns, 2)
    assert set(name_component(ld["PC1"]).replace("+", "").replace("-", "").split(" / ")) == {"a", "a2"}


def test_dominant_label():
    r = pd.Series({"sector_x": 0.7, "sector_y": 0.2, "size_large": 0.3})
    assert dominant(r, "sector_", {"sector_x": "X"}) == "X"
    assert dominant(r, "size_", {}) is None


def test_fa_checks_and_fit():
    g = np.random.default_rng(42)
    f = g.normal(size=(200, 1))
    X = pd.DataFrame(
        np.hstack([f + g.normal(scale=0.3, size=(200, 1)) for _ in range(4)]), columns=list("abcd")
    )
    c = fa_checks(X)
    assert c["bartlett_p"] < 0.001 and c["kmo"] > 0.7
    assert kmo_label(c["kmo"]) in ("middling", "meritorious", "marvellous")
    assert kmo_label(0.4) == "unacceptable"
    ld = fa_fit(X, 1, rotation=None).loadings_
    assert (np.abs(ld) > 0.8).all()
