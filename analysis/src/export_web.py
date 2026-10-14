import csv
import json
import re
from pathlib import Path

from src.cards import load_cards, to_plain, validate_card
from src.classify import PROFILE_ASSETS
from src.nbutil import MODELS, OUT, ROOT
from src.recommender import CATEGORIES, SIZES, split_tokens
from src.replay import actual_categories, case_profile
from src.sources import CASES, CONTROLS, DATASETS, SOURCES_MD, read_values

WEB = ROOT.parent / "web" / "public" / "model"
MAX_BYTES = 2 * 1024 * 1024
NUM = "number"
STR = "string"
OPT_NUM = "number|null"
LOGIT = {"intercept": NUM, "coefficients": {"*": NUM}}
CONFIG_ENTRY = {"value": NUM, "unit": STR, "fallback_level": STR, "source_key": STR}

SCHEMA = {
    "model.json": {
        "version": STR,
        "sectors": [STR],
        "sizes": [STR],
        "assets": [STR],
        "categories": [STR],
        "attack": {
            "feature_order": [STR],
            "sectors": [STR],
            "reference_levels": {"sector": STR, "size": STR},
            "models": {"*": LOGIT},
        },
        "impact": {
            "target": STR,
            "features": [STR],
            "intercept": NUM,
            "coefficients": {"*": NUM},
            "residual_sd": NUM,
            "reference_levels": {"sector": STR, "size": STR},
            "sectors": [STR],
        },
        "personas": {
            "feature_order": [STR],
            "scaler": {"type": STR, "mean": [NUM], "scale": [NUM], "reason": STR},
            "centroids": [[NUM]],
            "names": [STR],
            "attack_mix": {"*": {"*": NUM}},
        },
        "controls": [
            {
                "control": STR,
                "mitigates": [STR],
                "effectiveness": OPT_NUM,
                "effectiveness_key": STR,
                "effectiveness_url": STR,
                "effectiveness_fallback_level": STR,
                "annual_cost_inr": OPT_NUM,
                "cost_basis": STR,
                "cost_url": STR,
                "cost_excerpt": STR,
                "coverage": {"*": NUM},
            }
        ],
        "config": {"*": CONFIG_ENTRY},
    },
    "sources.json": {
        "values": [
            {
                "key": STR,
                "value": NUM,
                "unit": STR,
                "publisher": STR,
                "url": STR,
                "excerpt": STR,
                "fallback_level": STR,
            }
        ],
        "bibliography": [{"publisher": STR, "title": STR, "year": STR, "url": STR, "used_for": STR}],
        "cases": [
            {
                "name": STR,
                "year": STR,
                "sector": STR,
                "size_bucket": STR,
                "assets": STR,
                "actual_actions": STR,
                "summary": STR,
                "source_url": STR,
                "accessed": STR,
                "profile": {"sector": STR, "size": STR, "assets": [STR]},
                "actual_categories": [STR],
            }
        ],
    },
    "lineage.json": {
        "steps": [{"step": STR, "rows": NUM, "rule": STR}],
        "example_incident": {"source": STR, "incident": "object", "flattened": "object"},
        "datasets": [
            {
                "dataset": STR,
                "publisher": STR,
                "url": STR,
                "version": STR,
                "access_date": STR,
                "sha256": STR,
                "files": STR,
                "notes": STR,
            }
        ],
    },
    "cards.json": [
        {"id": STR, "order": NUM, "stage": STR, "used_live": "boolean", "title": STR, "card": "object"}
    ],
}

CONFIG_KEYS = {
    "annual_incident_prob": "annual_incident_prob",
    "per_record_cost_inr": "breach_total_cost_inr",
    "breach_total_cost_inr": "breach_total_cost_inr",
    "breach_avg_records": "breach_avg_records",
    "usd_inr": "usd_inr",
}


def type_ok(v, t):
    ts = t.split("|")
    for x in ts:
        if x == "null" and v is None:
            return True
        if x == NUM and isinstance(v, int | float) and not isinstance(v, bool):
            return True
        if x == STR and isinstance(v, str):
            return True
        if x == "boolean" and isinstance(v, bool):
            return True
        if x == "object" and isinstance(v, dict):
            return True
    return False


def validate(v, s, path="$", errs=None):
    errs = [] if errs is None else errs
    if isinstance(s, str):
        if not type_ok(v, s):
            errs.append(f"{path}: expected {s}, got {type(v).__name__}")
    elif isinstance(s, list):
        if not isinstance(v, list):
            errs.append(f"{path}: expected array")
        else:
            for i, x in enumerate(v):
                validate(x, s[0], f"{path}[{i}]", errs)
    elif "*" in s:
        if not isinstance(v, dict):
            errs.append(f"{path}: expected map")
        else:
            for k, x in v.items():
                validate(x, s["*"], f"{path}.{k}", errs)
    else:
        if not isinstance(v, dict):
            errs.append(f"{path}: expected object")
            return errs
        for k in s:
            if k not in v:
                errs.append(f"{path}.{k}: missing")
            else:
                validate(v[k], s[k], f"{path}.{k}", errs)
        for k in v:
            if k not in s:
                errs.append(f"{path}.{k}: not in schema")
    return errs


def flatten_schema(s, p=""):
    if isinstance(s, str):
        return [(p, s)]
    if isinstance(s, list):
        return flatten_schema(s[0], f"{p}[]")
    out = []
    for k, x in s.items():
        out += flatten_schema(x, f"{p}.{k}" if p else k)
    return out


def schema_md():
    ls = [
        "# Model export schema",
        "",
        "Generated from analysis/src/export_web.py. Keys and shapes only. "
        "`[]` marks an array, `*` any map key.",
        "Numbers are rounded to 8 decimals. Each file is under 2 MB.",
    ]
    for f, s in SCHEMA.items():
        ls += ["", f"## {f}", "", "| Path | Type |", "| --- | --- |"]
        ls += [f"| `{p or '(root)'}` | {t} |" for p, t in flatten_schema(s)]
    return "\n".join(ls) + "\n"


def num_or_none(v):
    return None if v in ("", None) else float(v)


def controls_export(coverage):
    vs = read_values()
    with Path(CONTROLS).open(newline="", encoding="utf-8") as f:
        rs = list(csv.DictReader(f))
    out = []
    for r in rs:
        ev = vs.get(r["effectiveness_key"], {})
        out.append(
            {
                "control": r["control"],
                "mitigates": split_tokens(r["mitigates"]),
                "effectiveness": num_or_none(r["effectiveness"]),
                "effectiveness_key": r["effectiveness_key"],
                "effectiveness_url": ev.get("url", ""),
                "effectiveness_fallback_level": ev.get("fallback_level", ""),
                "annual_cost_inr": num_or_none(r["annual_cost_inr"]),
                "cost_basis": r["cost_basis"],
                "cost_url": r["cost_url"],
                "cost_excerpt": r["cost_excerpt"],
                "coverage": coverage[r["control"]],
            }
        )
    return out


def config_export(cfg):
    vs = read_values()
    out = {}
    for k, sk in CONFIG_KEYS.items():
        r = vs[sk]
        unit = (
            "INR per record (derived: breach_total_cost_inr / breach_avg_records)"
            if k == "per_record_cost_inr"
            else r["unit"]
        )
        out[k] = {
            "value": float(cfg[k]),
            "unit": unit,
            "fallback_level": r["fallback_level"],
            "source_key": sk,
        }
    return out


def build_bundle(cfg, coverage, version):
    att = json.loads((MODELS / "attack_models.json").read_text(encoding="utf-8"))
    imp = json.loads((MODELS / "mlr_impact.json").read_text(encoding="utf-8"))
    per = json.loads((MODELS / "personas.json").read_text(encoding="utf-8"))
    return {
        "version": version,
        "sectors": att["sectors"],
        "sizes": list(SIZES),
        "assets": PROFILE_ASSETS,
        "categories": list(CATEGORIES),
        "attack": {k: att[k] for k in ("feature_order", "sectors", "reference_levels")}
        | {"models": {c: att["models"][c] for c in CATEGORIES}},
        "impact": {
            k: imp[k]
            for k in (
                "target",
                "features",
                "intercept",
                "coefficients",
                "residual_sd",
                "reference_levels",
                "sectors",
            )
        },
        "personas": {k: per[k] for k in ("feature_order", "scaler", "centroids", "names")}
        | {"attack_mix": {str(k): v for k, v in per["attack_mix"].items()}},
        "controls": controls_export(coverage),
        "config": config_export(cfg),
    }


def bibliography():
    rs = []
    for ln in Path(SOURCES_MD).read_text(encoding="utf-8").splitlines()[4:]:
        c = [x.strip() for x in ln.strip().strip("|").split("|")]
        if len(c) == 5:
            rs.append(
                {"publisher": c[0], "title": c[1], "year": c[2], "url": c[3].strip("<>"), "used_for": c[4]}
            )
    return rs


def sources_export():
    vs = [
        {k: r[k] for k in ("key", "unit", "publisher", "url", "excerpt", "fallback_level")}
        | {"value": float(r["value"])}
        for r in read_values().values()
        if str(r["value"]).strip()
    ]
    with Path(CASES).open(newline="", encoding="utf-8") as f:
        cs = list(csv.DictReader(f))
    top = json.loads((MODELS / "attack_models.json").read_text(encoding="utf-8"))["sectors"]
    for c in cs:
        q = case_profile(c, top, 0)
        c["profile"] = {"sector": q["sector"], "size": q["size"], "assets": q["assets"]}
        c["actual_categories"] = actual_categories(c["actual_actions"])
    return {"values": vs, "bibliography": bibliography(), "cases": cs}


def lineage_export():
    c = json.loads((OUT / "cards" / "data-preparation.json").read_text(encoding="utf-8"))
    t = next(x for x in c["results"]["tables"] if x["title"].startswith("Row counts"))
    ex = json.loads((ROOT / "data" / "processed" / "example_incident.json").read_text(encoding="utf-8"))
    with Path(DATASETS).open(newline="", encoding="utf-8") as f:
        ds = list(csv.DictReader(f))
    return {
        "steps": [dict(zip(t["columns"], r, strict=True)) for r in t["rows"]],
        "example_incident": ex,
        "datasets": ds,
    }


def card_order(c):
    return (c["order"], c["id"])


def cards_export(src=None):
    cs = sorted(load_cards(src), key=card_order)
    for c in cs:
        validate_card(c)
    return [
        {
            "id": c["id"],
            "order": c["order"],
            "stage": c["stage"],
            "used_live": c["used_live"],
            "title": c["title"],
            "card": c,
        }
        for c in cs
    ]


def write_export(name, obj, out=WEB):
    d = to_plain(obj)
    e = validate(d, SCHEMA[name])
    if e:
        raise ValueError(f"{name}: " + "; ".join(e[:10]))
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    s = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
    if len(s.encode()) > MAX_BYTES:
        raise ValueError(f"{name} is over 2 MB")
    (out / name).write_text(s, encoding="utf-8")
    return out / name


def export_all(bundle, out=WEB):
    fs = [
        write_export("model.json", bundle, out),
        write_export("sources.json", sources_export(), out),
        write_export("lineage.json", lineage_export(), out),
        write_export("cards.json", cards_export(), out),
    ]
    (Path(out) / "SCHEMA.md").write_text(schema_md(), encoding="utf-8")
    return fs


def em_dash_free(p):
    return not re.search(chr(0x2014), Path(p).read_text(encoding="utf-8"))
