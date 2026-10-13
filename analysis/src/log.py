import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

LOGS = Path(__file__).resolve().parents[1] / "logs"


class JsonFormatter(logging.Formatter):
    def format(self, r):
        d = {
            "ts": datetime.fromtimestamp(r.created, UTC).isoformat(timespec="seconds"),
            "level": r.levelname,
            "logger": r.name,
            "msg": r.getMessage(),
        }
        x = getattr(r, "data", None)
        if x:
            d["data"] = x
        if r.exc_info:
            d["exc"] = self.formatException(r.exc_info)
        return json.dumps(d, default=str)


def get_logger(name, phase=None, stream=False):
    lg = logging.getLogger(name)
    if lg.handlers:
        return lg
    lg.setLevel(logging.INFO)
    lg.propagate = False
    f = JsonFormatter()
    if phase:
        LOGS.mkdir(parents=True, exist_ok=True)
        h = logging.FileHandler(LOGS / f"{phase}.log", encoding="utf-8")
        h.setFormatter(f)
        lg.addHandler(h)
    if stream or not phase:
        s = logging.StreamHandler(sys.stderr)
        s.setFormatter(f)
        lg.addHandler(s)
    return lg


def log_event(lg, msg, **kw):
    lg.info(msg, extra={"data": kw})
