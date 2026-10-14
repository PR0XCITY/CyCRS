from src.load_vcdb import VARIETIES, VECTORS
from src.recommender import ALL, CATEGORIES

ASSET_WORDS = {
    "server": "asset_server",
    "user device": "asset_user_device",
    "network": "asset_network",
    "media": "asset_media",
}
NOT_ASSESSABLE = "not assessable (actions unknown)"


def token_categories():
    out = {f"action_{c}": {c} for c in CATEGORIES}
    for k, ps in {**VARIETIES, **VECTORS}.items():
        out[k] = {c for c, _ in ps if c in CATEGORIES}
    return out


def control_categories(tokens, tc=None):
    tc = tc or token_categories()
    if ALL in tokens:
        return set(CATEGORIES)
    out = set()
    for t in tokens:
        out |= tc.get(t, set())
    return out


def split_field(s):
    return [x.strip() for x in str(s or "").replace(",", ";").split(";") if x.strip()]


def actual_categories(s):
    return sorted({x.lower() for x in split_field(s)} & set(CATEGORIES))


def case_profile(row, sectors, budget):
    a = [ASSET_WORDS[w.lower()] for w in split_field(row["assets"]) if w.lower() in ASSET_WORDS]
    z = row["size_bucket"] if row["size_bucket"] in ("small", "medium", "large") else "unknown"
    return {
        "name": row["name"],
        "sector": row["sector"] if row["sector"] in sectors else "Other",
        "size": z,
        "assets": a,
        "controls": [],
        "budget_inr": budget,
    }


def verdict(top, actual, tokens_by_control, tc=None):
    if not actual:
        return NOT_ASSESSABLE, []
    tc = tc or token_categories()
    cov = set()
    for k in top:
        cov |= control_categories(tokens_by_control.get(k, []), tc)
    hit = [c for c in actual if c in cov]
    if len(hit) == len(actual):
        return "covered", hit
    return ("partially covered" if hit else "missed"), hit
