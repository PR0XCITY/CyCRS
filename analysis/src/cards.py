import json
import math
from pathlib import Path

import numpy as np

CARDS = Path(__file__).resolve().parents[1] / "outputs" / "cards"

STAGES = ("prepare", "explore", "impact", "likelihood", "segment", "decide", "evaluate")

KEYS = (
    "id",
    "title",
    "module",
    "stage",
    "used_live",
    "order",
    "question",
    "data_in",
    "why",
    "data_properties",
    "alternatives",
    "formula_tex",
    "assumptions",
    "results",
    "yields",
    "feeds",
    "limitations",
)

DATA_IN = ("dataset", "n_rows", "variables", "prep_steps", "sample_rows")
VARIABLE = ("name", "type", "scale", "transform")
PROPERTY = ("name", "value", "implication")
ALTERNATIVE = ("model", "why_not")
FORMULA = ("label", "tex")
ASSUMPTION = ("check", "statistic", "p_value", "verdict", "action_taken")
RESULTS = ("key_numbers", "tables", "charts")
TABLE = ("title", "columns", "rows")
CHART = ("type", "title", "x_label", "y_label", "data")
BANNED = ("victim_name", "summary", "notes", "reference", "incident_id", "source_id", "source_file")
EM_DASH = "—"


class CardError(ValueError):
    pass


def to_plain(v):
    if isinstance(v, dict):
        return {str(k): to_plain(x) for k, x in v.items()}
    if isinstance(v, list | tuple):
        return [to_plain(x) for x in v]
    if isinstance(v, np.bool_):
        return bool(v)
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, float | np.floating):
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return None
        return round(f, 8)
    if isinstance(v, np.ndarray):
        return to_plain(v.tolist())
    return v


def count_sentences(s):
    t = s.replace("e.g.", "eg").replace("i.e.", "ie")
    for c in "!?":
        t = t.replace(c, ".")
    return len([p for p in t.split(". ") if p.strip()])


def check_keys(d, ks, where, errs):
    if not isinstance(d, dict):
        errs.append(f"{where}: not an object")
        return False
    m = [k for k in ks if k not in d]
    if m:
        errs.append(f"{where}: missing {m}")
        return False
    return True


def check_list(v, ks, where, errs, n=0):
    if not isinstance(v, list):
        errs.append(f"{where}: not a list")
        return
    if len(v) < n:
        errs.append(f"{where}: needs at least {n}")
    for i, x in enumerate(v):
        check_keys(x, ks, f"{where}[{i}]", errs)


def find_em_dash(v, path, errs):
    if isinstance(v, str):
        if EM_DASH in v:
            errs.append(f"{path}: em dash")
    elif isinstance(v, dict):
        for k, x in v.items():
            find_em_dash(x, f"{path}.{k}", errs)
    elif isinstance(v, list):
        for i, x in enumerate(v):
            find_em_dash(x, f"{path}[{i}]", errs)


def validate_card(c):
    e = []
    if not check_keys(c, KEYS, "card", e):
        raise CardError("; ".join(e))
    for k in ("id", "title", "module", "question", "why", "yields"):
        if not isinstance(c[k], str) or not c[k].strip():
            e.append(f"{k}: must be non-empty string")
    if c["stage"] not in STAGES:
        e.append(f"stage: {c['stage']} not in {STAGES}")
    if not isinstance(c["used_live"], bool):
        e.append("used_live: must be bool")
    if not isinstance(c["order"], int) or isinstance(c["order"], bool):
        e.append("order: must be int")
    if isinstance(c["why"], str) and not 2 <= count_sentences(c["why"]) <= 4:
        e.append("why: needs 2 to 4 sentences")
    if isinstance(c["yields"], str) and not 2 <= count_sentences(c["yields"]) <= 3:
        e.append("yields: needs 2 to 3 sentences")
    di = c["data_in"]
    if check_keys(di, DATA_IN, "data_in", e):
        check_list(di["variables"], VARIABLE, "data_in.variables", e, 1)
        if not isinstance(di["prep_steps"], list) or not all(isinstance(s, str) for s in di["prep_steps"]):
            e.append("data_in.prep_steps: list of strings")
        sr = di["sample_rows"]
        if not isinstance(sr, list) or len(sr) != 8:
            e.append("data_in.sample_rows: needs exactly 8 rows")
        else:
            for i, r in enumerate(sr):
                if not isinstance(r, dict):
                    e.append(f"data_in.sample_rows[{i}]: not an object")
                elif any(b in r for b in BANNED):
                    e.append(f"data_in.sample_rows[{i}]: banned column")
    check_list(c["data_properties"], PROPERTY, "data_properties", e, 1)
    check_list(c["alternatives"], ALTERNATIVE, "alternatives", e, 2)
    check_list(c["formula_tex"], FORMULA, "formula_tex", e)
    check_list(c["assumptions"], ASSUMPTION, "assumptions", e)
    rs = c["results"]
    if check_keys(rs, RESULTS, "results", e):
        if not isinstance(rs["key_numbers"], dict):
            e.append("results.key_numbers: not an object")
        check_list(rs["tables"], TABLE, "results.tables", e)
        check_list(rs["charts"], CHART, "results.charts", e)
        for i, t in enumerate(rs["tables"] if isinstance(rs["tables"], list) else []):
            if isinstance(t, dict) and isinstance(t.get("rows"), list):
                for j, r in enumerate(t["rows"]):
                    if not isinstance(r, list) or len(r) != len(t.get("columns", [])):
                        e.append(f"results.tables[{i}].rows[{j}]: width mismatch")
    if not isinstance(c["feeds"], list) or not all(isinstance(s, str) for s in c["feeds"]):
        e.append("feeds: list of ids")
    if not isinstance(c["limitations"], list) or not all(isinstance(s, str) for s in c["limitations"]):
        e.append("limitations: list of strings")
    find_em_dash(c, "card", e)
    if e:
        raise CardError("; ".join(e))
    return c


def write_card(c, out=None):
    d = to_plain(c)
    validate_card(d)
    p = Path(out or CARDS)
    p.mkdir(parents=True, exist_ok=True)
    f = p / f"{d['id']}.json"
    f.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
    return f


def load_cards(src=None):
    p = Path(src or CARDS)
    return [json.loads(f.read_text(encoding="utf-8")) for f in sorted(p.glob("*.json"))]
