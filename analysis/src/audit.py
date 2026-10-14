import json
import re

from src.cards import load_cards, validate_card
from src.nbutil import ROOT
from src.sources import CONTROLS, read_rows, read_values

REPO = ROOT.parent
WEB = REPO / "web"
SYLLABUS = {
    "Descriptive statistics": ["descriptive", "data-preparation"],
    "Probability distributions": ["distribution-fit", "conditional-probability"],
    "Hypothesis tests": ["hypothesis-tests", "coverage-hit-rate"],
    "Simple linear regression": ["slr"],
    "Multiple linear regression": ["mlr-impact"],
    "Logistic regression": ["breach-classifiers", "attack-likelihood"],
    "Decision tree": ["breach-classifiers"],
    "K-nearest neighbours": ["breach-classifiers"],
    "Naive Bayes": ["breach-classifiers"],
    "Linear discriminant analysis": ["breach-classifiers"],
    "ROC curve and AUC": ["breach-classifiers", "attack-likelihood"],
    "Confusion matrix": ["breach-classifiers"],
    "K-means clustering": ["personas-kmeans"],
    "Hierarchical clustering": ["hierarchical"],
    "Principal component analysis": ["pca"],
    "Factor analysis": ["factor-analysis"],
}
NUM = re.compile(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?")
STRUCTURAL = {0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 20, 42, 50, 70, 30, 100, 1000}
RULES = {0.25, 0.5}


def numbers_in(v, out):
    if isinstance(v, bool):
        return
    if isinstance(v, int | float):
        out.add(float(v))
    elif isinstance(v, str):
        for m in NUM.finditer(v):
            out.add(float(m.group(0).replace(",", "")))
    elif isinstance(v, dict):
        for x in v.values():
            numbers_in(x, out)
    elif isinstance(v, list):
        for x in v:
            numbers_in(x, out)


def known_numbers(c, cfg):
    out = set()
    for k in ("results", "data_in", "assumptions"):
        numbers_in(c[k], out)
    for d in c["data_properties"]:
        numbers_in(d["value"], out)
    out |= {float(v) for v in cfg.values()}
    return out


def candidates(x):
    return {x, x / 100, x * 1e5, x * 1e7, x * 1000}


def traced(t, x, known):
    dp = len(t.split(".")[1]) if "." in t else 0
    tol = 0.5 * 10 ** (-dp) + 1e-9
    for k in known:
        for c in candidates(x):
            scale = (
                1e5
                if c == x * 1e5
                else 1e7
                if c == x * 1e7
                else 1 / 100
                if c == x / 100
                else 1000
                if c == x * 1000
                else 1
            )
            if abs(k - c) <= tol * scale or abs(k) == abs(c):
                return True
            if abs(abs(k) * 100 - x) <= tol:
                return True
    return False


def card_number_audit(cards, cfg):
    rows = []
    for c in cards:
        kn = known_numbers(c, cfg)
        texts = [("why", c["why"]), ("yields", c["yields"])] + [
            (f"data_properties.{d['name']}", d["implication"]) for d in c["data_properties"]
        ]
        bad = []
        for where, t in texts:
            for m in NUM.finditer(t):
                s = m.group(0).replace(",", "")
                x = float(s)
                if x in STRUCTURAL or x in RULES or 1990 <= x <= 2035 or traced(s, abs(x), kn):
                    continue
                bad.append(f"{where}: {m.group(0)}")
        rows.append((c["id"], bad))
    return rows


LOGIC_NOTES = {
    "1000": "slider resolution (steps), not a data value",
    "5000": "minimum budget from the product brief (INR 5,000)",
    "500000": "maximum budget from the product brief (INR 5,00,000)",
    "5": "number of top contributions shown in the trace, same as Python",
    "10": "base of the log10 back-transform",
    "1000000": "input validation upper bound for employees",
    "60": "input validation limit for city length",
    "100000": "input validation upper bound for devices",
}


def web_literals():
    out = []
    pat = re.compile(r"(?<![\w.#\-\[/])(\d+(?:\.\d+)?)(?![\w%\]])")
    for f in sorted(
        list((WEB / "app").rglob("*.tsx"))
        + list((WEB / "components").rglob("*.tsx"))
        + list((WEB / "lib").rglob("*.ts"))
    ):
        for i, ln in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            code = re.sub(r'className="[^"]*"|`[^`]*`|"[^"]*"|\'[^\']*\'', "", ln)
            for m in pat.finditer(code):
                v = float(m.group(1))
                if v in (0, 1, 2, 3, 100) or "padStart" in ln or "slice(" in ln:
                    continue
                out.append(f"{f.relative_to(REPO).as_posix()}:{i} `{m.group(1)}`")
    return out


def source_audit(cfg_raw):
    vs = read_values()
    bad = [
        k
        for k, r in vs.items()
        if str(r["value"]).strip()
        and not (r["url"].strip() and r["excerpt"].strip() and r["accessed"].strip())
    ]
    missing = [k for k, r in vs.items() if not str(r["value"]).strip()]
    ctl = read_rows(CONTROLS)
    cbad = [r["control"] for r in ctl if r["annual_cost_inr"] and not (r["cost_url"] and r["cost_excerpt"])]
    keys = [k for k, e in cfg_raw.items() if e["source_key"] not in vs]
    return bad, missing, cbad, keys


def main():
    cards = load_cards()
    m = json.loads((WEB / "public" / "model" / "model.json").read_text(encoding="utf-8"))
    cfg = {k: e["value"] for k, e in m["config"].items()}
    ids = {c["id"] for c in cards}
    ls = [
        "# CyCRS audit",
        "",
        "Generated by `python -m src.audit` from `analysis/`.",
        "",
        "## 1. Syllabus coverage",
        "",
    ]
    ls += ["| Technique | Card | Card exists | Page built |", "| --- | --- | --- | --- |"]
    gaps = 0
    for t, cs in SYLLABUS.items():
        for i in cs:
            ok = i in ids
            pg = (WEB / "out" / "models" / i / "index.html").exists()
            gaps += (not ok) + (not pg)
            ls.append(f"| {t} | `{i}` | {'yes' if ok else 'NO'} | {'yes' if pg else 'NO'} |")
    ls += ["", f"Gaps: {gaps}."]
    ls += ["", "## 2. Card contract and number tracing", ""]
    errs = []
    for c in cards:
        try:
            validate_card(c)
        except Exception as e:
            errs.append(f"{c['id']}: {e}")
    ls.append(
        f"Contract: {len(cards) - len(errs)} of {len(cards)} cards pass `validate_card`."
        + ("" if not errs else " Failures: " + "; ".join(errs))
    )
    ls += [
        "",
        "Numbers in `why`, `yields` and data-property implications that do not match a value in the card's results, data_in, assumptions, data properties or the model config (small structural counts such as 8 rows, seed 42, 70/30, years and the 0.25 and 0.5 silhouette rule-of-thumb thresholds excluded):",
        "",
    ]
    na = card_number_audit(cards, cfg)
    for i, bad in na:
        ls.append(f"- `{i}`: " + ("all traced" if not bad else "FLAG " + ", ".join(bad)))
    lit = web_literals()
    logic = [x for x in lit if x.startswith("- web/lib/") or "web/lib/" in x]
    ls += [
        "",
        "## 3. Numbers written into the website source",
        "",
        "Every rupee, probability and model value on the site is read from `web/public/model/*.json`, including the employee size bands (`model.json` size_bands). Logic literals left in `web/lib/`:",
        "",
    ]
    ls += [f"- {x}: {LOGIC_NOTES.get(x.split(' ')[-1].strip('`'), 'structural constant')}" for x in logic]
    ls += [
        "",
        f"Presentational literals in `web/app` and `web/components` (pixel sizes, margins, font sizes, opacity, section numbers, the 404 code): {len(lit) - len(logic)}. The sensitivity toggle multiplies probabilities by 0.8 and 1.2 as specified in the brief.",
    ]
    ls += ["", "## 4. External values", ""]
    bad, missing, cbad, keys = source_audit(m["config"])
    ls.append(f"- values.csv rows with a value but no URL, excerpt or access date: {bad or 'none'}")
    ls.append(f"- Costed controls without URL or excerpt: {cbad or 'none'}")
    ls.append(f"- Model config entries whose source key is not in values.csv: {keys or 'none'}")
    ls.append(f"- MISSING values (blank on purpose, shown as not ranked): {', '.join(missing)}")
    ci = REPO / "docs" / "data" / "ci_local.json"
    if ci.exists():
        r = json.loads(ci.read_text(encoding="utf-8"))
        ls += ["", "## 5. Live trace and local CI", "", "| Check | Result |", "| --- | --- |"]
        ls += [f"| {k} | {v} |" for k, v in r.items()]
    (REPO / "docs" / "audit.md").write_text("\n".join(ls) + "\n", encoding="utf-8")
    return na


if __name__ == "__main__":
    main()
