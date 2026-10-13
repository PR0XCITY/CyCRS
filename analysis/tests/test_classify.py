import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from src.classify import (
    PROFILE_ASSETS,
    cv_auc,
    fit_logit,
    metrics,
    odds_table,
    predict_logit,
    profile_features,
    roc_points,
    separation_drops,
    youden,
)
from src.nbutil import ASSETS


def test_metrics_known_confusion():
    y = [1, 1, 1, 0, 0]
    p = [0.9, 0.8, 0.2, 0.6, 0.1]
    m = metrics(y, p)
    assert (m["tp"], m["fn"], m["fp"], m["tn"]) == (2, 1, 1, 1)
    assert m["precision"] == pytest.approx(2 / 3)
    assert m["recall"] == pytest.approx(2 / 3)
    assert m["specificity"] == pytest.approx(0.5)
    assert m["accuracy"] == pytest.approx(0.6)
    assert m["auc"] == pytest.approx(5 / 6)


def test_youden_perfect_split():
    r = youden([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9])
    assert r["j"] == pytest.approx(1.0)
    assert 0.2 < r["threshold"] <= 0.8


def test_logit_and_browser_prediction_match():
    g = np.random.default_rng(42)
    X = pd.DataFrame({"a": g.integers(0, 2, 400), "b": g.normal(size=400)})
    y = pd.Series((g.random(400) < 1 / (1 + np.exp(-(-0.5 + 1.5 * X["a"] - X["b"])))).astype(int))
    r = fit_logit(X, y)
    assert r.params["a"] == pytest.approx(1.5, abs=0.5)
    p = predict_logit(r.params["const"], {"a": r.params["a"], "b": r.params["b"]}, X)
    assert np.allclose(p, r.predict(np.column_stack([np.ones(400), X.values])))
    t = odds_table(r).set_index("term")
    assert t.loc["a", "odds_ratio"] == pytest.approx(np.exp(r.params["a"]))


def test_separation_drops():
    X = pd.DataFrame({"only_pos": [1, 1, 0, 0], "rare": [0, 0, 0, 0], "ok": [1, 0, 1, 0]})
    y = pd.Series([1, 1, 0, 0])
    d = dict(separation_drops(X, y, k=1))
    assert "only_pos" in d and "rare" in d and "ok" not in d


def test_profile_feature_order():
    df = pd.DataFrame(
        {"sector": ["A", "B", "Z"], "size": ["small", "large", "unknown"], **{a: [0, 1, 0] for a in ASSETS}}
    )
    X = profile_features(df, ["A", "B"])
    assert list(X.columns) == [
        "sector_a",
        "sector_b",
        "size_medium",
        "size_large",
        "size_unknown",
        *PROFILE_ASSETS,
    ]
    assert "asset_person" not in X.columns
    assert X.loc[2, ["sector_a", "sector_b"]].sum() == 0


def test_cv_auc_and_roc_points():
    g = np.random.default_rng(1)
    X = g.normal(size=(200, 2))
    y = (X[:, 0] + g.normal(scale=0.5, size=200) > 0).astype(int)
    m, s = cv_auc(LogisticRegression(), X, y)
    assert m > 0.8 and s >= 0
    pts = roc_points(y, X[:, 0])
    assert pts[0]["fpr"] == 0 and pts[-1]["tpr"] == 1
