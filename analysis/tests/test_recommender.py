import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from src.cards import validate_card
from src.classify import profile_features
from src.export_web import SCHEMA, WEB, schema_md, validate, write_export
from src.load_vcdb import load_vcdb
from src.recommender import (
    combined_factor,
    encode_profile,
    expected_loss,
    greedy,
    hit,
    hit_rate,
    recommend,
)

FX = Path(__file__).parent / "fixtures"
CTL = {
    "free_a": {"effectiveness": 0.5, "cost": 0.0, "coverage": {"a": 1.0}},
    "cheap_b": {"effectiveness": 0.5, "cost": 100.0, "coverage": {"b": 1.0}},
    "dear_ab": {"effectiveness": 0.9, "cost": 1000.0, "coverage": {"a": 0.5, "b": 0.5}},
}
BASE = {"a": 100.0, "b": 50.0}


def load(name):
    return json.loads((WEB / name).read_text(encoding="utf-8"))


def test_expected_loss_without_and_with_controls():
    assert expected_loss(BASE, [], CTL) == pytest.approx(150)
    assert expected_loss(BASE, ["free_a"], CTL) == pytest.approx(100)


def test_independent_controls_multiply():
    c = {
        "x": {"effectiveness": 0.5, "coverage": {"a": 1.0}},
        "y": {"effectiveness": 0.5, "coverage": {"a": 1.0}},
    }
    assert combined_factor(["x", "y"], "a", c) == pytest.approx(0.25)
    assert combined_factor(["x"], "b", c) == pytest.approx(1.0)


def test_greedy_budget_zero_takes_only_free():
    s, spent, steps = greedy(BASE, CTL, [], 0)
    assert s == ["free_a"] and spent == 0
    assert all(q["cost"] == 0 for q in steps[0]["candidates"])


def test_greedy_below_cheapest_paid():
    s, spent, _ = greedy(BASE, CTL, [], 99)
    assert s == ["free_a"] and spent == 0


def test_greedy_above_all_takes_everything_useful():
    s, spent, steps = greedy(BASE, CTL, [], 10_000)
    assert s[0] == "free_a" and set(s) == set(CTL)
    assert spent == pytest.approx(1100)
    assert steps[-1]["loss_after"] == pytest.approx(expected_loss(BASE, s, CTL))


def test_greedy_keeps_controls_in_place():
    s, spent, _ = greedy(BASE, CTL, ["cheap_b"], 0)
    assert s[0] == "cheap_b" and "free_a" in s and spent == 0


def test_hit_and_hit_rate():
    tok = {"m": ["v_x"], "all_k": ["all"], "n": ["action_y"]}
    assert hit(["m"], {"v_x": 1}, tok)
    assert not hit(["m", "n"], {"v_x": 0, "action_y": 0}, tok)
    assert hit(["all_k"], {}, tok)
    assert hit_rate([True, False, True, True]) == pytest.approx(0.75)
    assert math.isnan(hit_rate([]))


def test_flatten_encode_matches_training_features():
    df = load_vcdb(FX / "vcdb")
    m = load("model.json")
    X = profile_features(df, m["attack"]["sectors"])
    assert list(X.columns) == m["attack"]["feature_order"]
    for i, r in df.iterrows():
        p = {"sector": r["sector"], "size": r["size"], "assets": [a for a in m["assets"] if r[a] == 1]}
        v = encode_profile(p, m["attack"]["feature_order"], m["attack"]["sectors"])
        assert [v[f] for f in X.columns] == X.loc[i].tolist()


def test_train_export_predict_matches_sklearn(tmp_path):
    m = load("model.json")
    fo = m["attack"]["feature_order"]
    g = np.random.default_rng(42)
    X = pd.DataFrame(g.integers(0, 2, size=(400, len(fo))).astype(float), columns=fo)
    y = (g.random(400) < 1 / (1 + np.exp(-(X.values @ g.normal(size=len(fo)) - 1)))).astype(int)
    sk = LogisticRegression(C=np.inf, max_iter=5000).fit(X, y)
    mod = {
        "intercept": float(sk.intercept_[0]),
        "coefficients": dict(zip(fo, map(float, sk.coef_[0]), strict=True)),
    }
    m["attack"]["models"] = {c: mod for c in m["categories"]}
    out = json.loads(write_export("model.json", m, tmp_path).read_text(encoding="utf-8"))
    p = {
        "sector": m["sectors"][0],
        "size": "small",
        "assets": [m["assets"][0]],
        "controls": [],
        "budget_inr": 0,
    }
    r = recommend(p, out)
    v = encode_profile(p, fo, m["attack"]["sectors"])
    want = sk.predict_proba(pd.DataFrame([[v[f] for f in fo]], columns=fo))[0, 1]
    assert all(abs(c["p_c"] - want) < 1e-6 for c in r["categories"])


@pytest.mark.parametrize("name", list(SCHEMA))
def test_exported_json_matches_schema(name):
    assert validate(load(name), SCHEMA[name]) == []
    assert (WEB / name).stat().st_size < 2 * 1024 * 1024


def test_schema_md_in_sync():
    assert (WEB / "SCHEMA.md").read_text(encoding="utf-8") == schema_md()


def test_every_exported_card_valid():
    cs = load("cards.json")
    assert [c["order"] for c in cs] == sorted(c["order"] for c in cs)
    for c in cs:
        validate_card(c["card"])


def test_reference_profiles_reproduce():
    ref = json.loads((FX / "reference.json").read_text(encoding="utf-8"))
    m = load("model.json")
    assert len(ref["profiles"]) == 5
    for r in ref["profiles"]:
        n = recommend(r["profile"], m)
        assert [x["control"] for x in n["plan"]] == [x["control"] for x in r["plan"]]
        for k in ("loss_no_controls_inr", "loss_after_plan_inr"):
            assert n["totals"][k] == pytest.approx(r["totals"][k], rel=1e-6)
    w = Path(__file__).parents[2] / "web" / "tests" / "fixtures" / "reference.json"
    assert w.read_text(encoding="utf-8") == (FX / "reference.json").read_text(encoding="utf-8")
    assert not (WEB / "reference.json").exists()


def test_impact_cap_by_size():
    m = load("model.json")
    cap = m["config"]["impact_cap_small_inr"]["value"]
    p = {
        "sector": m["sectors"][0],
        "size": "small",
        "assets": ["asset_server"],
        "controls": [],
        "budget_inr": 0,
    }
    r = recommend(p, m)
    for c in r["categories"]:
        assert c["impact_inr"] == pytest.approx(min(c["impact_uncapped_inr"], cap))
        assert c["capped"] == (c["impact_uncapped_inr"] > cap)
    big = recommend({**p, "size": "large"}, m)
    assert all(c["impact_cap_inr"] is None and not c["capped"] for c in big["categories"])
