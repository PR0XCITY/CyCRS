import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.regression import (
    assumption_checks,
    backward_eliminate,
    band_employees,
    dummies,
    fit_ols,
    multipliers,
    rmse,
    vif_table,
)

FX = pd.read_csv(Path(__file__).parent / "fixtures" / "regression" / "linear.csv")


def test_ols_recovers_known_coefficients():
    r = fit_ols(FX[["a", "b"]], FX["y"])
    assert r.params["const"] == pytest.approx(1, abs=0.02)
    assert r.params["a"] == pytest.approx(2, abs=0.02)
    assert r.params["b"] == pytest.approx(-0.5, abs=0.02)
    assert r.rsquared > 0.999


def test_robust_keeps_coefficients():
    a, b = fit_ols(FX[["a", "b"]], FX["y"]), fit_ols(FX[["a", "b"]], FX["y"], robust=True)
    assert np.allclose(a.params, b.params)
    assert b.cov_type == "HC3"


def test_vif_flags_collinear_column():
    v = vif_table(FX[["a", "b", "c_dup"]]).set_index("variable")["vif"]
    assert v["c_dup"] > 10 and v["a"] > 10
    assert v["b"] < 5


def test_backward_drops_noise():
    d = FX.assign(noise=np.random.default_rng(1).normal(size=len(FX)))
    r, kept, dropped = backward_eliminate(d[["a", "b", "noise"]], d["y"])
    assert "noise" not in kept and set(kept) == {"a", "b"}
    assert dropped[0][0] == "noise"


def test_multiplier_is_power_of_ten():
    t = multipliers(fit_ols(FX[["a", "b"]], FX["y"])).set_index("term")
    assert t.loc["a", "multiplier"] == pytest.approx(10 ** t.loc["a", "coef"])
    assert t.loc["a", "mult_low"] < t.loc["a", "multiplier"] < t.loc["a", "mult_high"]


def test_checks_and_rmse():
    r = fit_ols(FX[["a", "b"]], FX["y"])
    c = assumption_checks(r)
    assert 0 < c["durbin_watson"] < 4
    assert 0 <= c["breusch_pagan_p"] <= 1
    assert rmse(r, FX[["a", "b"]], FX["y"]) < 0.02


def test_band_and_dummies():
    assert band_employees("1 to 10") == pytest.approx(math.sqrt(10))
    assert band_employees("Over 100000") == 100001
    assert math.isnan(band_employees("Small"))
    d = dummies(pd.Series(["x", "y", "x"]), ["x", "y"], "s")
    assert d["s_x"].tolist() == [1, 0, 1]
