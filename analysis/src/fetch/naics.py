import csv
from datetime import date

import pandas as pd
import requests

from src.fetch.common import ROOT, record_dataset, sha256_file
from src.log import get_logger, log_event

URL = "https://www.census.gov/naics/2022NAICS/2-6%20digit_2022_Codes.xlsx"
RAW = ROOT / "data" / "raw" / "naics" / "2-6_digit_2022_Codes.xlsx"
OUT = ROOT / "data" / "sources" / "naics_sectors.csv"


def download_naics(p=RAW):
    p.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    p.write_bytes(r.content)
    return p


def expand_code(c):
    if "-" in c:
        a, b = c.split("-")
        return [str(i) for i in range(int(a), int(b) + 1)]
    return [c]


def parse_sectors(p=RAW):
    df = pd.read_excel(p, dtype=str)
    df.columns = [str(c).strip() for c in df.columns]
    cc = [c for c in df.columns if "Code" in c][0]
    tc = [c for c in df.columns if "Title" in c][0]
    rs = []
    for c, t in zip(df[cc].fillna(""), df[tc].fillna(""), strict=True):
        c = c.strip()
        if len(c) == 2 or (len(c) == 5 and "-" in c):
            for k in expand_code(c):
                rs.append({"code2": k, "sector": t.strip().rstrip("T").strip()})
    return rs


def fetch_naics():
    lg = get_logger("fetch.naics", phase="phase1")
    p = download_naics()
    rs = parse_sectors(p)
    d = date.today().isoformat()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=("code2", "sector", "url", "publisher", "year", "access_date"))
        w.writeheader()
        for r in rs:
            w.writerow({**r, "url": URL, "publisher": "U.S. Census Bureau", "year": "2022", "access_date": d})
    record_dataset(
        {
            "dataset": "NAICS 2022 codes",
            "publisher": "U.S. Census Bureau",
            "url": URL,
            "version": "2022",
            "access_date": d,
            "sha256": sha256_file(p),
            "files": 1,
            "notes": "2-digit sectors extracted to data/sources/naics_sectors.csv",
        }
    )
    log_event(lg, "naics fetched", sectors=len(rs))
    return rs


if __name__ == "__main__":
    fetch_naics()
