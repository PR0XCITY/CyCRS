import csv
import re
from pathlib import Path
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parents[1]
VALUES = ROOT / "data" / "sources" / "values.csv"
CONFIG = ROOT / "config.yaml"
CONTROLS = ROOT / "data" / "raw" / "controls.csv"

EMPLOYEES = 10
MONTHS = 12
REQUIRED = ("breach_total_cost_inr", "breach_avg_records", "annual_incident_prob", "usd_inr")
PROVENANCE = ("publisher", "title", "year", "url", "accessed", "excerpt")
CONTROL_FIELDS = (
    "control",
    "mitigates",
    "effectiveness",
    "effectiveness_key",
    "annual_cost_inr",
    "cost_basis",
    "cost_url",
    "cost_accessed",
    "cost_excerpt",
)

CONTROLS_SPEC = (
    ("MFA", "v_stolen_creds;v_brute_force", "eff_mfa", "price_mfa_security_defaults_inr", "inr"),
    (
        "Offline or cloud backups",
        "v_ransomware;action_malware",
        "eff_offline_backups",
        "price_google_one_basic_inr",
        "flat",
    ),
    ("Patch management", "v_exploit_vuln", "eff_patch_management", "price_windows_update_inr", "inr"),
    (
        "Endpoint protection",
        "action_malware;v_ransomware;v_backdoor_c2",
        "eff_endpoint_protection",
        "price_defender_antivirus_inr",
        "inr",
    ),
    (
        "Phishing awareness training",
        "v_phishing;v_pretexting",
        "eff_phishing_training",
        "price_ncsc_staff_training_inr",
        "inr",
    ),
    (
        "Email filtering",
        "v_phishing;vec_email",
        "eff_email_filtering",
        "price_google_workspace_starter_inr",
        "inr",
    ),
    (
        "Password manager",
        "v_stolen_creds;v_brute_force",
        "eff_password_manager",
        "price_bitwarden_teams_usd",
        "usd",
    ),
    ("Router and firewall hardening", "vec_remote_access;v_dos", "eff_router_firewall_hardening", None, None),
    ("Staff access reviews", "v_privilege_abuse", "eff_access_reviews", None, None),
    ("Device encryption", "v_theft;v_loss", "eff_device_encryption", "price_device_encryption_inr", "inr"),
    ("Payment and UPI fraud controls", "v_skimmer;v_pretexting", "eff_upi_fraud_controls", None, None),
    ("Incident response plan", "all", "eff_incident_response_plan", None, None),
)


def read_values(p=VALUES):
    with Path(p).open(newline="", encoding="utf-8") as f:
        return {r["key"]: r for r in csv.DictReader(f)}


def is_missing(r):
    return r is None or not str(r.get("value", "")).strip()


def number(vs, k):
    r = vs.get(k)
    return None if is_missing(r) else float(r["value"])


def resolve(spec, vs):
    if "key" in spec:
        return number(vs, spec["key"])
    a, b = (number(vs, k) for k in spec["of"])
    if a is None or b is None:
        return None
    if spec["derive"] == "divide":
        return a / b
    if spec["derive"] == "multiply":
        return a * b
    raise ValueError(f"unknown derivation {spec['derive']}")


def load_config(p=CONFIG, vp=None):
    c = yaml.safe_load(Path(p).read_text(encoding="utf-8"))
    vs = read_values(vp or ROOT / c["values_file"])
    o = {k: resolve(s, vs) for k, s in c["inputs"].items()}
    o["effectiveness"] = {k: number(vs, v) for k, v in c["effectiveness"].items()}
    return o


def annual_cost(vs, pk, cur):
    p = number(vs, pk)
    if p is None:
        return None
    t = p * MONTHS if cur == "flat" else p * EMPLOYEES * MONTHS
    return t * number(vs, "usd_inr") if cur == "usd" else t


def cost_basis(vs, pk, cur):
    r = vs[pk]
    if cur == "flat":
        return f"{r['value']} {r['unit']} x 1 shared plan x {MONTHS} months (assumed 10-employee business)"
    b = f"{r['value']} {r['unit']} x {EMPLOYEES} users x {MONTHS} months (assumed 10-employee business)"
    if cur == "usd":
        b += f", converted at usd_inr {vs['usd_inr']['value']} ({vs['usd_inr']['accessed']})"
    return b


def build_controls(vs=None, out=CONTROLS):
    vs = vs or read_values()
    rs = []
    for c, m, ek, pk, cur in CONTROLS_SPEC:
        e = number(vs, ek)
        r = {"control": c, "mitigates": m, "effectiveness": "" if e is None else e, "effectiveness_key": ek}
        if pk and not is_missing(vs.get(pk)):
            p = vs[pk]
            r.update(
                annual_cost_inr=round(annual_cost(vs, pk, cur), 2),
                cost_basis=cost_basis(vs, pk, cur),
                cost_url=p["url"],
                cost_accessed=p["accessed"],
                cost_excerpt=p["excerpt"],
            )
        else:
            r.update(annual_cost_inr="", cost_basis="MISSING", cost_url="", cost_accessed="", cost_excerpt="")
        rs.append(r)
    out.parent.mkdir(parents=True, exist_ok=True)
    with Path(out).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CONTROL_FIELDS)
        w.writeheader()
        w.writerows(rs)
    return rs


def missing_keys(vs=None):
    vs = vs or read_values()
    return [k for k, r in vs.items() if is_missing(r)]


SOURCES_MD = ROOT / "data" / "sources" / "SOURCES.md"
DATASETS = ROOT / "data" / "sources" / "datasets.csv"
CASES = ROOT / "data" / "raw" / "cases.csv"


def read_rows(p):
    with Path(p).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def source_key(r):
    return (r[0], r[2])


def write_sources_md(out=SOURCES_MD):
    rs = {}
    for r in read_values().values():
        if not is_missing(r):
            rs.setdefault(r["url"], [r["publisher"], r["title"], r["year"], r["url"], []])[4].append(r["key"])
    for r in read_rows(DATASETS):
        m = re.search(r"(19|20)\d{2}", r["version"])
        y = m.group(0) if m else r["access_date"][:4]
        rs.setdefault(r["url"], [r["publisher"], r["dataset"], y, r["url"], []])[4].append("dataset")
    for r in read_rows(CASES):
        h = urlparse(r["source_url"]).netloc.removeprefix("www.")
        rs.setdefault(r["source_url"], [h, r["name"], r["year"], r["source_url"], []])[4].append("case")
    ls = [
        "# Sources",
        "",
        "| Publisher | Title | Year | Link | Used for |",
        "| --- | --- | --- | --- | --- |",
    ]
    for p, t, y, u, ks in sorted(rs.values(), key=source_key):
        ls.append(f"| {p} | {t} | {y} | <{u}> | {', '.join(ks)} |")
    Path(out).write_text("\n".join(ls) + "\n", encoding="utf-8")
    return len(rs)


def missing_checklist(vs=None):
    vs = vs or read_values()
    cs = [r["control"] for r in read_rows(CONTROLS) if r["cost_basis"] == "MISSING"]
    cn = len(read_rows(CASES))
    return {"values": missing_keys(vs), "control_costs": cs, "cases": cn, "cases_needed": max(0, 4 - cn)}


if __name__ == "__main__":
    from src.log import get_logger, log_event

    build_controls()
    n = write_sources_md()
    log_event(get_logger("sources", phase="phase1b"), "sources built", sources=n, missing=missing_checklist())
