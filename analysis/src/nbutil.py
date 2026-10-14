import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.cards import to_plain

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "figures"
OUT = ROOT / "outputs"
MODELS = OUT / "models"
CLEAN = ROOT / "data" / "processed" / "vcdb_clean.parquet"
CATS = ["hacking", "malware", "social", "error", "misuse", "physical", "environmental"]
ACTORS = ["actor_external", "actor_internal", "actor_partner"]
ASSETS = ["asset_server", "asset_user_device", "asset_person", "asset_network", "asset_media"]
SIZES = ["small", "medium", "large", "unknown"]


def load_clean():
    return pd.read_parquet(CLEAN)


def top_sectors(df, n=8):
    return df.loc[df["sector"] != "Unknown", "sector"].value_counts().head(n).index.tolist()


def sector_group(df, top):
    return df["sector"].where(df["sector"].isin(top), "Other")


def save_fig(fig, name):
    fig.tight_layout()
    fig.savefig(FIG / name, dpi=200)
    plt.close(fig)


def sample_rows(df, cols, n=8):
    s = df[cols].dropna().sample(n, random_state=42)
    return s.astype(object).where(s.notna(), None).to_dict(orient="records")


def var(n, t, s, tr="none"):
    return {"name": n, "type": t, "scale": s, "transform": tr}


def short(s, n=22):
    return s if len(s) <= n else s[: n - 2].rstrip(" ,") + "."


def slug(s):
    return "".join(c if c.isalnum() else "_" for c in s.lower()).strip("_")


def write_json(obj, p):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(to_plain(obj), indent=2), encoding="utf-8")
    return p


def indian_group(n):
    s = str(int(round(abs(n))))
    if len(s) <= 3:
        return s
    h, t = s[:-3], s[-3:]
    ps = []
    while len(h) > 2:
        ps.insert(0, h[-2:])
        h = h[:-2]
    if h:
        ps.insert(0, h)
    return ",".join(ps) + "," + t


def inr(v):
    a = abs(v)
    sg = "-" if v < 0 else ""
    if a >= 1e7:
        return f"{sg}₹{a / 1e7:.2f} crore"
    if a >= 1e5:
        return f"{sg}₹{a / 1e5:.2f} lakh"
    return f"{sg}₹{indian_group(a)}"
