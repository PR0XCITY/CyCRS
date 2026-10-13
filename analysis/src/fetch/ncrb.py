import re
from datetime import date

import pandas as pd
import pdfplumber
import requests

from src.fetch.common import ROOT, record_dataset, sha256_file
from src.log import get_logger, log_event

YEAR = 2024
BASE = "https://www.ncrb.gov.in/uploads/files/"
INDEX = "https://www.ncrb.gov.in/crime-in-india-table-content?year=2024"
TABLES = {"9A.1": "TABLE9A12.pdf", "9A.2": "TABLE9A21.pdf", "9A.3": "TABLE9A31.pdf"}
RAW = ROOT / "data" / "raw" / "ncrb"
OUT = ROOT / "data" / "processed" / "ncrb_state.csv"
N_STATES, N_UTS = 28, 8
SPOT = ("Karnataka", "Telangana", "Uttar Pradesh")

NUM = r"(?:-?\d+(?:\.\d+)?|-)"
TOTALS = ("TOTAL STATE(S)", "TOTAL UT(S)", "TOTAL ALL INDIA")
T1 = ("cases_2022", "cases_2023", "cases_2024", "population_lakh", "crime_rate_2024", "chargesheet_rate_2024")

HEAD_SUMS = {
    5: (6, 7),
    4: (5, 8, 9, 10, 11),
    13: (14, 15, 16, 17, 18),
    26: (3, 4, 12, 13, 19, 20, 21, 22, 23, 24, 25),
    33: (34, 35, 36, 37, 38, 39, 40, 41, 42),
    47: (48, 49),
    53: (27, 28, 29, 30, 31, 32, 33, 43, 44, 45, 46, 47, 50, 51, 52),
    59: (54, 55, 56, 57, 58),
    60: (26, 53, 59),
}


class ValidationError(ValueError):
    pass


def download_tables(d=RAW):
    d.mkdir(parents=True, exist_ok=True)
    h = {"User-Agent": "Mozilla/5.0"}
    ps = {}
    for t, f in TABLES.items():
        r = requests.get(BASE + f, headers=h, timeout=120)
        r.raise_for_status()
        if not r.content.startswith(b"%PDF"):
            raise ValidationError(f"{BASE + f} did not return a PDF; download it manually into {d}")
        (d / f).write_bytes(r.content)
        ps[t] = d / f
    return ps


def to_number(s):
    if s == "-":
        return None
    return float(s) if "." in s else int(s)


def clean(s):
    return re.sub(r"\s+", " ", (s or "").replace("\n", " ")).strip()


def clean_header(s):
    s = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", s or "")
    s = re.sub(r"(\w)\n([a-z]{1,3})\b", r"\1\2", s)
    return re.sub(r"(\w)- (\w)", r"\1\2", clean(s))


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:48]


def page_columns(pg):
    tb = pg.extract_tables()[0]
    ix = next((k for k, r in enumerate(tb) if r and clean(r[0]) == "[1]"), None)
    hs = tb[:ix] if ix is not None else tb[:1]
    cs = []
    for j in range(2, len(tb[0])):
        nm = ""
        for r in hs:
            if j < len(r) and clean(r[j]):
                nm = clean_header(r[j])
        code = None
        if ix is not None:
            m = re.search(r"\[(\d+)\]", clean(tb[ix][j]))
            code = int(m.group(1)) if m else None
        cs.append((code, nm))
    return cs


def parse_lines(tx, k):
    rx = re.compile(rf"^(\d{{1,2}})\s*(.*?)\s*((?:{NUM}\s+){{{k - 1}}}{NUM})$")
    tr = re.compile(rf"^({'|'.join(re.escape(t) for t in TOTALS)})\s+((?:{NUM}\s+){{{k - 1}}}{NUM})$")
    ls = [x.strip() for x in tx.splitlines()]
    rs, ts, sec = [], {}, None
    for i, x in enumerate(ls):
        if x.startswith("STATES:"):
            sec = "state"
            x = x[len("STATES:") :].strip()
        elif x.startswith("UNION TERRITORIES:"):
            sec = "ut"
            continue
        m = tr.match(x)
        if m:
            ts[m.group(1)] = [to_number(v) for v in m.group(2).split()]
            continue
        m = rx.match(x)
        if not m:
            continue
        nm = m.group(2)
        if not nm:
            nm = f"{ls[i - 1]} {ls[i + 1]}"
        rs.append(
            {
                "sl": int(m.group(1)),
                "state": nm,
                "type": sec,
                "values": [to_number(v) for v in m.group(3).split()],
            }
        )
    return rs, ts


def parse_table(p):
    rows, tots, cols = {}, {}, []
    with pdfplumber.open(p) as pdf:
        for pg in pdf.pages:
            cs = page_columns(pg)
            rs, ts = parse_lines(pg.extract_text(), len(cs))
            cols.extend(cs)
            for r in rs:
                e = rows.setdefault(
                    r["sl"], {"sl": r["sl"], "state": r["state"], "type": r["type"], "values": []}
                )
                e["values"].extend(r["values"])
            for t, v in ts.items():
                tots.setdefault(t, []).extend(v)
    return cols, rows, tots


def frame_table(cols, rows, names):
    df = pd.DataFrame(
        [
            {
                "sl": r["sl"],
                "state": r["state"],
                "type": r["type"],
                **dict(zip(names, r["values"], strict=True)),
            }
            for r in rows.values()
        ]
    )
    return df.sort_values("sl").reset_index(drop=True)


def head_names(cols):
    return [f"h{c:02d}_{slug(n)}" for c, n in cols]


def motive_names(cols):
    return [f"m_{slug(n)}" for _, n in cols]


def check_counts(df, t, errs):
    ns, nu = int((df["type"] == "state").sum()), int((df["type"] == "ut").sum())
    if ns != N_STATES or nu != N_UTS or df["sl"].tolist() != list(range(1, N_STATES + N_UTS + 1)):
        errs.append(f"{t}: {ns} states and {nu} UTs, expected {N_STATES} and {N_UTS}")
    return ns, nu


def check_column_totals(df, tots, names, t, errs, skip=()):
    n = 0
    for k, sec in (("TOTAL STATE(S)", "state"), ("TOTAL UT(S)", "ut")):
        for c, v in zip(names, tots[k], strict=True):
            if c in skip or v is None:
                continue
            s = df.loc[df["type"] == sec, c].fillna(0).sum()
            n += 1
            if abs(s - v) > 1e-6:
                errs.append(f"{t}: {k} {c} sums to {s}, printed {v}")
    for c, a, b, v in zip(
        names, tots["TOTAL STATE(S)"], tots["TOTAL UT(S)"], tots["TOTAL ALL INDIA"], strict=True
    ):
        if c in skip or v is None:
            continue
        n += 1
        if abs((a or 0) + (b or 0) - v) > 1e-6:
            errs.append(f"{t}: ALL INDIA {c} is {v}, states plus UTs give {(a or 0) + (b or 0)}")
    return n


def check_head_sums(df, tots, names, errs):
    by = {int(c[1:3]): c for c in names}
    al = dict(zip(names, tots["TOTAL ALL INDIA"], strict=True))
    n = 0
    for p, ks in HEAD_SUMS.items():
        s = df[[by[k] for k in ks]].fillna(0).sum(axis=1)
        bad = df.loc[(s - df[by[p]].fillna(0)).abs() > 0, "state"].tolist()
        n += len(df)
        if bad:
            errs.append(f"9A.2: [{p}] not equal to sum of {ks} for {bad}")
        if sum(al[by[k]] or 0 for k in ks) != al[by[p]]:
            errs.append(f"9A.2: ALL INDIA [{p}] not equal to sum of {ks}")
    return n


def check_motive_sums(df, names, errs):
    s = df[names[:-1]].fillna(0).sum(axis=1)
    bad = df.loc[s != df[names[-1]], "state"].tolist()
    if bad:
        errs.append(f"9A.3: motives do not sum to Total for {bad}")
    return len(df)


def check_rates(df, errs):
    lo = df["cases_2024"] / (df["population_lakh"] + 0.05) - 0.05
    hi = df["cases_2024"] / (df["population_lakh"] - 0.05) + 0.05
    bad = df.loc[(df["crime_rate_2024"] < lo - 1e-9) | (df["crime_rate_2024"] > hi + 1e-9), "state"].tolist()
    if bad:
        errs.append(f"9A.1: crime rate does not match cases / population for {bad}")
    return len(df)


def spot_check(p, df, cols, lg, errs):
    with pdfplumber.open(p) as pdf:
        tx = "\n".join(pg.extract_text(layout=True) for pg in pdf.pages)
    out = []
    for s in SPOT:
        ln = next((x for x in tx.splitlines() if re.search(rf"\b\d+\s+{re.escape(s)}\b", x)), "")
        got = [to_number(v) for v in re.findall(NUM, ln.split(s, 1)[-1])]
        r = df.loc[df["state"] == s, list(cols)].iloc[0].tolist()
        ok = got == r
        out.append({"state": s, "pdf": got, "parsed": r, "match": ok})
        log_event(lg, "ncrb spot check", state=s, pdf_line=ln.strip(), parsed=r, match=ok)
        if not ok:
            errs.append(f"spot check failed for {s}")
    return out


def extract_ncrb(ps):
    errs = []
    c1, r1, t1 = parse_table(ps["9A.1"])
    if len(c1) != len(T1):
        raise ValidationError(f"9A.1 has {len(c1)} data columns, expected {len(T1)}")
    a = frame_table(c1, r1, T1)
    c2, r2, t2 = parse_table(ps["9A.2"])
    n2 = head_names(c2)
    b = frame_table(c2, r2, n2)
    c3, r3, t3 = parse_table(ps["9A.3"])
    n3 = motive_names(c3)
    c = frame_table(c3, r3, n3)
    st = {}
    for t, d in (("9A.1", a), ("9A.2", b), ("9A.3", c)):
        st[t] = check_counts(d, t, errs)
    nc = check_column_totals(
        a,
        dict(zip(TOTALS, [t1[k] for k in TOTALS], strict=True)),
        T1,
        "9A.1",
        errs,
        skip=("crime_rate_2024", "chargesheet_rate_2024", "population_lakh"),
    )
    nc += check_column_totals(b, t2, n2, "9A.2", errs)
    nc += check_column_totals(c, t3, n3, "9A.3", errs)
    nr = check_head_sums(b, t2, n2, errs) + check_motive_sums(c, n3, errs) + check_rates(a, errs)
    if not (a["cases_2024"].tolist() == b[n2[-1]].tolist() == c[n3[-1]].tolist()):
        errs.append("2024 totals differ across tables 9A.1, 9A.2, 9A.3")
    df = a.merge(b.drop(columns=["state", "type"]), on="sl").merge(c.drop(columns=["state", "type"]), on="sl")
    return df, errs, {"states_uts": st, "column_total_checks": nc, "row_total_checks": nr}


def fetch_ncrb():
    lg = get_logger("fetch.ncrb", phase="phase1b")
    ps = download_tables()
    d = date.today().isoformat()
    for t, p in ps.items():
        record_dataset(
            {
                "dataset": f"NCRB Crime in India {YEAR} Table {t}",
                "publisher": "National Crime Records Bureau",
                "url": BASE + TABLES[t],
                "version": f"Crime in India {YEAR}",
                "access_date": d,
                "sha256": sha256_file(p),
                "files": 1,
                "notes": f"listed at {INDEX}; chapter 9A Cyber Crimes, also in Volume II",
            }
        )
    df, errs, st = extract_ncrb(ps)
    sp = spot_check(ps["9A.1"], df, T1, lg, errs)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    log_event(lg, "ncrb extracted", rows=len(df), cols=df.shape[1], errors=errs, spot=sp, **st)
    return df, errs


if __name__ == "__main__":
    fetch_ncrb()
