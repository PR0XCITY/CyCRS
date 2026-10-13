import numpy as np
import pandas as pd
import pytest

from src.stats_tests import (
    anova,
    chi_square,
    cohens_h,
    cramers_v,
    decide,
    dunn,
    effect_label,
    holm,
    kruskal,
    mann_whitney,
    normality,
    tukey,
    two_proportion_z,
)


def test_chi_square_known_answer():
    r = chi_square([[10, 20], [20, 10]])
    assert r["statistic"] == pytest.approx(20 / 3)
    assert r["dof"] == 1
    assert r["p_value"] == pytest.approx(0.009823, abs=1e-5)


def test_cramers_v_bounds():
    assert cramers_v([[10, 0], [0, 10]]) == pytest.approx(1.0)
    assert cramers_v([[10, 10], [10, 10]]) == pytest.approx(0.0)


def test_mann_whitney_separated():
    r = mann_whitney([1, 2, 3], [4, 5, 6])
    assert r["statistic"] == 0
    assert r["effect_size"] == pytest.approx(1.0)


def test_kruskal_identical_groups():
    r = kruskal([[1, 2, 3], [1, 2, 3]])
    assert r["statistic"] == pytest.approx(0.0)
    assert r["p_value"] == pytest.approx(1.0)


def test_anova_known_answer():
    r = anova([[1, 2, 3], [4, 5, 6]])
    assert r["statistic"] == pytest.approx(13.5)
    assert r["effect_size"] == pytest.approx(13.5 / 17.5)


def test_two_proportion_equal():
    r = two_proportion_z(50, 100, 50, 100)
    assert r["statistic"] == pytest.approx(0.0)
    assert r["effect_size"] == pytest.approx(0.0)


def test_cohens_h_known():
    assert cohens_h(0.5, 0.25) == pytest.approx(0.5236, abs=1e-4)


def test_holm_known_answer():
    assert np.allclose(holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])
    assert np.allclose(holm([0.5, 0.9]), [1.0, 1.0])


def test_normality_switches_test():
    x = np.random.default_rng(42).normal(size=200)
    assert normality(x)["test"] == "Shapiro-Wilk"
    assert normality(np.random.default_rng(42).normal(size=6000))["test"] == "Anderson-Darling"
    assert not normality(np.random.default_rng(42).exponential(size=6000))["normal"]


def test_posthocs_shapes():
    d = pd.DataFrame({"v": [1, 2, 3, 10, 11, 12, 20, 21, 22], "g": list("aaabbbccc")})
    assert dunn(d, "v", "g").shape == (3, 3)
    assert len(tukey(d["v"], d["g"])) == 3


def test_decide_and_labels():
    assert decide(0.01) == "reject H0"
    assert decide(0.5) == "do not reject H0"
    assert decide(None) == "not applicable"
    assert effect_label("Cramer's V", 0.05) == "negligible"
    assert effect_label("Cohen's h", 0.9) == "large"
