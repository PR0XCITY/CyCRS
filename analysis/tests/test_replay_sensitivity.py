import json

import pytest

from src.export_web import WEB
from src.recommender import recommend
from src.replay import (
    NOT_ASSESSABLE,
    actual_categories,
    case_profile,
    control_categories,
    token_categories,
    verdict,
)
from src.sensitivity import SCENARIOS, run_scenario, scaled_bundle, sensitivity, stable_controls, tornado

M = json.loads((WEB / "model.json").read_text(encoding="utf-8"))
TOK = {
    "backup": ["v_ransomware", "action_malware"],
    "mfa": ["v_stolen_creds"],
    "ir": ["all"],
    "mail": ["vec_email"],
}
PROFILE = {
    "sector": M["sectors"][0],
    "size": "small",
    "assets": ["asset_server"],
    "controls": [],
    "budget_inr": 50000,
}


def test_token_categories_from_veris_pairs():
    tc = token_categories()
    assert tc["v_ransomware"] == {"malware"}
    assert tc["v_stolen_creds"] == {"hacking"}
    assert tc["vec_email"] == {"social", "malware"}
    assert control_categories(["all"], tc) == {"hacking", "malware", "social", "error", "misuse", "physical"}


def test_actual_categories_and_profile():
    assert actual_categories("Malware") == ["malware"]
    assert actual_categories("Hacking; Social") == ["hacking", "social"]
    assert actual_categories("Unknown") == []
    p = case_profile(
        {"name": "x", "sector": "Nowhere", "size_bucket": "large", "assets": "Server"}, M["sectors"], 50000
    )
    assert p["sector"] == "Other" and p["size"] == "large" and p["assets"] == ["asset_server"]


def test_verdicts():
    assert verdict(["backup"], ["malware"], TOK)[0] == "covered"
    assert verdict(["backup"], ["malware", "error"], TOK)[0] == "partially covered"
    assert verdict(["mfa"], ["physical"], TOK)[0] == "missed"
    assert verdict(["ir"], ["physical"], TOK)[0] == "covered"
    assert verdict(["backup"], [], TOK)[0] == NOT_ASSESSABLE


def test_scaled_bundle_does_not_mutate_and_clamps():
    b = scaled_bundle(M, "effectiveness", 1.2)
    assert all(c["effectiveness"] is None or c["effectiveness"] <= 1 for c in b["controls"])
    assert M["config"]["per_record_cost_inr"]["value"] == pytest.approx(
        scaled_bundle(M, "per_record_cost", 0.5)["config"]["per_record_cost_inr"]["value"] * 2
    )


def test_cost_scales_loss_linearly_and_keeps_plan():
    base = recommend(PROFILE, M)
    r = run_scenario(PROFILE, M, "per_record_cost", 1.5)
    assert r["totals"]["loss_no_controls_inr"] == pytest.approx(1.5 * base["totals"]["loss_no_controls_inr"])
    assert [x["control"] for x in r["plan"]] == [x["control"] for x in base["plan"]]


def test_probability_scale_clamped():
    r = recommend(PROFILE, M, p_scale=100)
    assert all(c["p_c"] <= 1 for c in r["categories"])


def test_sensitivity_tornado_and_stable():
    base, rows = sensitivity(PROFILE, M)
    assert len(rows) == len(SCENARIOS)
    t = tornado(base, rows)
    assert [x["swing"] for x in t] == sorted((x["swing"] for x in t), reverse=True)
    s = stable_controls(base, rows)
    assert set(s) <= {x["control"] for x in base["plan"]}
