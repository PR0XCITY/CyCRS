import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
VALIDATED = ROOT / "data" / "raw" / "vcdb" / "data" / "json" / "validated"
NAICS = ROOT / "data" / "sources" / "naics_sectors.csv"

CATEGORIES = ("hacking", "malware", "social", "error", "misuse", "physical", "environmental")
ACTORS = ("external", "internal", "partner")

VARIETIES = {
    "v_ransomware": (("malware", "Ransomware"),),
    "v_phishing": (("social", "Phishing"),),
    "v_pretexting": (("social", "Pretexting"),),
    "v_stolen_creds": (("hacking", "Use of stolen creds"),),
    "v_brute_force": (("hacking", "Brute force"), ("malware", "Brute force")),
    "v_exploit_vuln": (("hacking", "Exploit vuln"), ("malware", "Exploit vuln")),
    "v_backdoor_c2": (
        ("malware", "Backdoor or C2"),
        ("malware", "Backdoor"),
        ("malware", "C2"),
        ("hacking", "Backdoor"),
    ),
    "v_dos": (("hacking", "DoS"), ("malware", "DoS")),
    "v_privilege_abuse": (("misuse", "Privilege abuse"),),
    "v_theft": (("physical", "Theft"),),
    "v_skimmer": (("physical", "Skimmer"),),
    "v_misdelivery": (("error", "Misdelivery"),),
    "v_misconfiguration": (("error", "Misconfiguration"),),
    "v_publishing_error": (("error", "Publishing error"),),
    "v_loss": (("error", "Loss"),),
}

VECTORS = {
    "vec_web_app": (("hacking", "Web application"), ("malware", "Web application")),
    "vec_email": (("social", "Email"), ("malware", "Email")),
    "vec_remote_access": (
        ("hacking", "Desktop sharing"),
        ("hacking", "VPN"),
        ("hacking", "3rd party desktop"),
        ("misuse", "Remote access"),
    ),
    "vec_partner": (("hacking", "Partner"), ("social", "Partner")),
    "vec_direct_install": (("malware", "Direct install"),),
    "vec_lan_access": (("misuse", "LAN access"),),
    "vec_physical_access": (("misuse", "Physical access"),),
    "vec_carelessness": (("error", "Carelessness"),),
}

ASSETS = {
    "asset_server": "S",
    "asset_user_device": "U",
    "asset_person": "P",
    "asset_network": "N",
    "asset_media": "M",
}

UNIT_DAYS = {
    "Seconds": 1 / 86400,
    "Minutes": 1 / 1440,
    "Hours": 1 / 24,
    "Days": 1.0,
    "Weeks": 7.0,
    "Months": 365.25 / 12,
    "Years": 365.25,
}

SMALL = {"1 to 10", "11 to 100", "Small"}
MEDIUM = {"101 to 1000"}
LARGE = {"1001 to 10000", "10001 to 25000", "25001 to 50000", "50001 to 100000", "Over 100000", "Large"}

BREACH = {"Yes": 1, "No": 0, "Not coded": 0}


def load_sectors(p=NAICS):
    with Path(p).open(newline="", encoding="utf-8") as f:
        return {r["code2"]: r["sector"] for r in csv.DictReader(f)}


def sector_of(industry, sm):
    c = str(industry or "").strip()[:2]
    return c if c in sm else "00", sm.get(c, "Unknown")


def size_bucket(ec):
    if ec in SMALL:
        return "small"
    if ec in MEDIUM:
        return "medium"
    if ec in LARGE:
        return "large"
    return "unknown"


def first_country(v):
    cs = [c for c in (v.get("country") or []) if c and c != "Unknown"]
    return cs[0] if cs else "Unknown"


def primary_motive(a):
    for k in ACTORS:
        for m in (a.get(k) or {}).get("motive") or []:
            if m not in ("Unknown", "NA", "Other"):
                return m
    return "Unknown"


def has_any(ac, pairs, field):
    for c, v in pairs:
        for x in (ac.get(c) or {}).get(field) or []:
            if x.startswith(v):
                return 1
    return 0


def discovery_days(t):
    d = (t or {}).get("discovery") or {}
    u, v = d.get("unit"), d.get("value")
    if u in UNIT_DAYS and isinstance(v, int | float) and v >= 0:
        return float(v) * UNIT_DAYS[u]
    return np.nan


def records_lost(c):
    v = (c or {}).get("data_total")
    if isinstance(v, int | float) and not isinstance(v, bool) and v >= 0:
        return float(v)
    return np.nan


def breach_target(dd):
    return BREACH.get(dd, np.nan)


def flatten_incident(j, sm):
    v = j.get("victim") or {}
    a = j.get("actor") or {}
    ac = j.get("action") or {}
    at = j.get("attribute") or {}
    t = j.get("timeline") or {}
    cf = at.get("confidentiality") or {}
    sc, sn = sector_of(v.get("industry"), sm)
    ec = v.get("employee_count") or "Unknown"
    r = {
        "incident_id": j.get("incident_id"),
        "sector_code": sc,
        "sector": sn,
        "employee_count": ec,
        "size": size_bucket(ec),
        "country": first_country(v),
        "actor_external": int("external" in a),
        "actor_internal": int("internal" in a),
        "actor_partner": int("partner" in a),
        "motive": primary_motive(a),
    }
    for c in CATEGORIES:
        r[f"action_{c}"] = int(c in ac)
    for k, ps in VARIETIES.items():
        r[k] = has_any(ac, ps, "variety")
    for k, ps in VECTORS.items():
        r[k] = has_any(ac, ps, "vector")
    pf = {str(x.get("variety", "")).split(" - ")[0] for x in (j.get("asset") or {}).get("assets") or []}
    for k, p in ASSETS.items():
        r[k] = int(p in pf)
    dd = cf.get("data_disclosure") if cf else None
    r["data_disclosure"] = dd if dd else "Not coded"
    r["data_total"] = records_lost(cf)
    r["integrity"] = int("integrity" in at)
    r["availability"] = int("availability" in at)
    r["discovery_unit"] = ((t.get("discovery") or {}).get("unit")) or "Not coded"
    r["discovery_days"] = discovery_days(t)
    y = (t.get("incident") or {}).get("year")
    r["year"] = int(y) if isinstance(y, int) else np.nan
    r["breach"] = breach_target(r["data_disclosure"])
    return r


def is_incident_file(f):
    return f.is_file() and f.suffix.lower() == ".json"


def name_key(f):
    return f.name


def list_incident_files(src=VALIDATED):
    return sorted([f for f in Path(src).iterdir() if is_incident_file(f)], key=name_key)


def read_incident(f):
    return json.loads(Path(f).read_text(encoding="utf-8"))


def load_vcdb(src=VALIDATED, sm=None):
    sm = sm or load_sectors()
    fs = list_incident_files(src)
    df = pd.DataFrame([flatten_incident(read_incident(f), sm) for f in fs])
    df.insert(1, "source_file", [f.name for f in fs])
    df["breach"] = df["breach"].astype("Int64")
    df["year"] = df["year"].astype("Int64")
    return df
