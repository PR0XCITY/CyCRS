import csv

import pytest

from src.sources import (
    CONTROLS,
    PROVENANCE,
    REQUIRED,
    ROOT,
    is_missing,
    load_config,
    missing_keys,
    read_values,
)

VS = read_values()
CASES = ROOT / "data" / "raw" / "cases.csv"


def rows(p):
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@pytest.mark.parametrize("k", REQUIRED)
def test_required_key_sourced(k):
    assert k in VS
    assert not is_missing(VS[k])


@pytest.mark.parametrize("k", [k for k, r in VS.items() if not is_missing(r)])
def test_row_has_provenance(k):
    r = VS[k]
    for f in PROVENANCE:
        assert r[f].strip(), f"{k} lacks {f}"
    assert len(r["excerpt"].split()) <= 25


FREE = ("free", "no extra cost", "built into", "available on all")


def test_excerpt_contains_value():
    for k, r in VS.items():
        if is_missing(r):
            continue
        v = float(r["value"])
        x = r["excerpt"].replace(",", "")
        if v == 0:
            assert any(s in x.lower() for s in FREE), f"{k}: free value without a page saying so"
            continue
        ok = [
            str(v),
            f"{v:g}",
            f"{v * 100:g}",
            f"{v * 100:.1f}",
            f"{v / 1e6:g}",
            f"{v:.2f}",
            f"{v * 100:.2f}",
        ]
        assert any(s in x for s in ok), f"{k}: {r['value']} not in excerpt"


def test_missing_rows_are_flagged():
    for k in missing_keys(VS):
        assert VS[k]["notes"].startswith("MISSING"), k


def test_one_effectiveness_row_per_control():
    ks = {r["effectiveness_key"] for r in rows(CONTROLS)}
    assert ks <= set(VS)
    assert len(rows(CONTROLS)) == 12


def test_costed_controls_have_provenance():
    for r in rows(CONTROLS):
        if r["annual_cost_inr"]:
            assert r["cost_url"] and r["cost_accessed"] and r["cost_excerpt"]
        else:
            assert r["cost_basis"] == "MISSING"


def test_cases_have_sources():
    assert 4 <= len(rows(CASES)) <= 6
    for r in rows(CASES):
        assert r["source_url"].startswith("https://") and r["accessed"]


def test_config_resolves_without_numbers():
    c = load_config()
    assert c["per_record_cost_inr"] == pytest.approx(c["breach_total_cost_inr"] / c["breach_avg_records"])
    t = (ROOT / "config.yaml").read_text(encoding="utf-8")
    assert not any(ch.isdigit() for ch in t)
