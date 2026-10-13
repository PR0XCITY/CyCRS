from pathlib import Path

import pytest

from src.fetch.ncrb import (
    T1,
    TOTALS,
    check_column_totals,
    check_counts,
    check_rates,
    frame_table,
    parse_table,
)

FX = Path(__file__).parent / "fixtures" / "ncrb" / "TABLE9A12.pdf"


@pytest.fixture(scope="module")
def parsed():
    c, r, t = parse_table(FX)
    return c, frame_table(c, r, T1), t


def test_columns_and_rows(parsed):
    c, df, t = parsed
    assert len(c) == len(T1)
    assert len(df) == 36
    assert set(t) == set(TOTALS)


def test_states_and_uts(parsed):
    e = []
    assert check_counts(parsed[1], "9A.1", e) == (28, 8)
    assert e == []


def test_wrapped_name_joined(parsed):
    df = parsed[1]
    assert df.loc[df["sl"] == 31, "state"].iloc[0] == "D&N Haveli and Daman & Diu"


def test_totals_match_printed(parsed):
    _, df, t = parsed
    e = []
    check_column_totals(
        df, t, T1, "9A.1", e, skip=("crime_rate_2024", "chargesheet_rate_2024", "population_lakh")
    )
    check_rates(df, e)
    assert e == []
    assert t["TOTAL ALL INDIA"][2] == 101928


def test_known_row(parsed):
    r = parsed[1].set_index("state").loc["Karnataka"]
    assert (r["cases_2022"], r["cases_2023"], r["cases_2024"]) == (12556, 21889, 21993)
    assert r["crime_rate_2024"] == pytest.approx(32.2)


def test_dash_is_missing(parsed):
    r = parsed[1].set_index("state").loc["Manipur"]
    assert r["chargesheet_rate_2024"] is None or r["chargesheet_rate_2024"] != r["chargesheet_rate_2024"]
