import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIRS = ("analysis/tests/", "web/tests/")
SECRET_NAMES = re.compile(r"(^|/)(\.env(\..*)?|.*\.pem|.*\.key|id_rsa.*|.*credentials.*\.json)$")


def tracked():
    r = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    return r.stdout.split("\n")


def test_no_env_or_key_files_tracked():
    bad = [f for f in tracked() if f and SECRET_NAMES.search(f) and f != ".env.example"]
    assert bad == []


def test_env_example_has_no_values():
    for ln in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        if ln.strip() and not ln.startswith("#"):
            assert ln.split("=", 1)[1].strip() == ""


def test_fixtures_only_inside_tests():
    bad = [f for f in tracked() if "fixture" in f.lower() and not f.startswith(FIXTURE_DIRS)]
    assert bad == []


def test_no_demo_data_or_reference_profiles_shipped():
    pub = [f for f in tracked() if f.startswith("web/public/")]
    assert not [f for f in pub if re.search(r"demo|sample|fixture|reference", f, re.I)]
    for f in pub:
        if f.endswith(".json"):
            assert '"profiles"' not in (ROOT / f).read_text(encoding="utf-8")


def test_gitignore_keeps_secrets_out_and_model_in():
    g = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".env" in g
    ignored = [x.strip().rstrip("/") for x in g if x.strip() and not x.startswith("!")]
    assert "web/public/model" not in ignored and "web/public" not in ignored
