import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "data" / "sources" / "datasets.csv"
FIELDS = ("dataset", "publisher", "url", "version", "access_date", "sha256", "files", "notes")


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def record_dataset(row, p=SOURCES):
    p.parent.mkdir(parents=True, exist_ok=True)
    rs = []
    if p.exists():
        with p.open(newline="", encoding="utf-8") as f:
            rs = [r for r in csv.DictReader(f) if r["dataset"] != row["dataset"]]
    rs.append(row)
    rs.sort(key=dataset_key)
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rs)


def dataset_key(r):
    return r["dataset"]
