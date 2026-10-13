import hashlib
import subprocess
from datetime import date

from src.fetch.common import ROOT, record_dataset
from src.load_vcdb import list_incident_files
from src.log import get_logger, log_event

RAW = ROOT / "data" / "raw" / "vcdb"
URL = "https://github.com/vz-risk/VCDB.git"


def clone_vcdb(d=RAW):
    if (d / ".git").exists():
        subprocess.run(["git", "-C", str(d), "pull", "--depth", "1", "-q"], check=True)
    else:
        d.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--depth", "1", "-q", URL, str(d)], check=True)
    r = subprocess.run(["git", "-C", str(d), "rev-parse", "HEAD"], check=True, capture_output=True, text=True)
    return r.stdout.strip()


def manifest_sha256(d=RAW):
    fs = list_incident_files(d / "data" / "json" / "validated")
    h = hashlib.sha256()
    for f in fs:
        h.update(f.name.encode())
        h.update(hashlib.sha256(f.read_bytes()).hexdigest().encode())
    return h.hexdigest(), len(fs)


def fetch_vcdb():
    lg = get_logger("fetch.vcdb", phase="phase1")
    c = clone_vcdb()
    s, n = manifest_sha256()
    record_dataset(
        {
            "dataset": "VCDB",
            "publisher": "VERIS Community Database (vz-risk)",
            "url": URL,
            "version": c,
            "access_date": date.today().isoformat(),
            "sha256": s,
            "files": n,
            "notes": "sha256 over sorted name+sha256 of data/json/validated/*.json (any case)",
        }
    )
    log_event(lg, "vcdb fetched", commit=c, files=n, sha256=s)
    return c, s, n


if __name__ == "__main__":
    fetch_vcdb()
