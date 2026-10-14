import math
from pathlib import Path

import pytest

from src.load_vcdb import (
    breach_target,
    discovery_days,
    list_incident_files,
    load_sectors,
    load_vcdb,
    primary_motive,
    sector_of,
    size_bucket,
)

FX = Path(__file__).parent / "fixtures" / "vcdb"


@pytest.fixture(scope="module")
def sm():
    return load_sectors()


@pytest.fixture(scope="module")
def df(sm):
    return load_vcdb(FX, sm).set_index("incident_id")


def row(df, p):
    return df.loc[[i for i in df.index if i.upper().startswith(p.upper())][0]]


def test_reads_all_fixtures_any_case(df):
    assert len(list_incident_files(FX)) == 5
    assert len(df) == 5


def test_sector_mapping(sm):
    assert sector_of("624190", sm) == ("62", "Health Care and Social Assistance")
    assert sector_of("447110", sm) == ("44", "Retail Trade")
    assert sector_of("33", sm) == ("33", "Manufacturing")
    assert sector_of("000", sm) == ("00", "Unknown")
    assert sector_of(None, sm) == ("00", "Unknown")


def test_size_bucket():
    assert size_bucket("1 to 10") == "small"
    assert size_bucket("Small") == "small"
    assert size_bucket("101 to 1000") == "medium"
    assert size_bucket("Over 100000") == "large"
    assert size_bucket("Large") == "large"
    assert size_bucket("Unknown") == "unknown"


def test_discovery_conversion():
    assert discovery_days({"discovery": {"unit": "Months", "value": 3}}) == pytest.approx(91.3125)
    assert discovery_days({"discovery": {"unit": "Hours", "value": 7.0}}) == pytest.approx(7 / 24)
    assert discovery_days({"discovery": {"unit": "Weeks", "value": 2}}) == 14
    assert math.isnan(discovery_days({"discovery": {"unit": "Days"}}))
    assert math.isnan(discovery_days({"discovery": {"unit": "Unknown", "value": 4}}))
    assert math.isnan(discovery_days({}))


def test_target_rules():
    assert breach_target("Yes") == 1
    assert breach_target("No") == 0
    assert math.isnan(breach_target("Potentially"))
    assert math.isnan(breach_target("Unknown"))
    assert breach_target("Not coded") == 0
    assert math.isnan(breach_target(None))


def test_primary_motive_skips_unknown():
    assert (
        primary_motive({"external": {"motive": ["Unknown"]}, "internal": {"motive": ["Grudge"]}}) == "Grudge"
    )
    assert primary_motive({"internal": {"motive": ["NA"]}}) == "Unknown"


def test_yes_with_records(df):
    r = row(df, "E85BC744")
    assert r["breach"] == 1
    assert r["data_total"] == 7250
    assert r["sector"] == "Health Care and Social Assistance"
    assert r["size"] == "small"
    assert r["discovery_days"] == pytest.approx(91.3125)
    assert r["year"] == 2013


def test_no_disclosure(df):
    r = row(df, "801F8A1E")
    assert r["breach"] == 0
    assert r["size"] == "large"
    assert r["action_physical"] == 1
    assert r["v_skimmer"] == 1
    assert r["discovery_days"] == pytest.approx(7 / 24)


def test_potentially_dropped_and_not_coded_is_no(df):
    p = row(df, "e36f5ee0")
    n = row(df, "2468560D")
    assert p["data_disclosure"] == "Potentially"
    assert n["data_disclosure"] == "Not coded"
    assert p["breach"] is None or str(p["breach"]) == "<NA>"
    assert n["breach"] == 0
    assert p["v_ransomware"] == 1
    assert n["availability"] == 1 and n["integrity"] == 1


def test_phishing_flags(df):
    r = row(df, "A3ACED45")
    assert r["action_social"] == 1 and r["action_hacking"] == 1
    assert r["v_phishing"] == 1 and r["v_stolen_creds"] == 1
    assert r["vec_email"] == 1 and r["vec_web_app"] == 1
    assert r["asset_person"] == 1 and r["asset_server"] == 1
    assert r["asset_media"] == 0
    assert r["actor_external"] == 1 and r["actor_internal"] == 0
    assert r["motive"] == "Ideology"
    assert math.isnan(r["discovery_days"])
