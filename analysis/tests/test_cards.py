import copy
import json

import numpy as np
import pytest

from src.cards import CARDS, CardError, load_cards, validate_card, write_card


def make_card():
    return {
        "id": "t",
        "title": "Test card",
        "module": "1: Descriptive statistics",
        "stage": "prepare",
        "used_live": False,
        "order": 1,
        "question": "Does the validator work?",
        "data_in": {
            "dataset": "fixture",
            "n_rows": 8,
            "variables": [{"name": "x", "type": "numeric", "scale": "ratio", "transform": "none"}],
            "prep_steps": ["none"],
            "sample_rows": [{"x": i} for i in range(8)],
        },
        "why": "The data is small. A test is enough.",
        "data_properties": [{"name": "n", "value": 8, "implication": "tiny"}],
        "alternatives": [{"model": "a", "why_not": "b"}, {"model": "c", "why_not": "d"}],
        "formula_tex": [{"label": "mean", "tex": r"\bar{x}"}],
        "assumptions": [
            {"check": "c", "statistic": 1.0, "p_value": 0.5, "verdict": "ok", "action_taken": "none"}
        ],
        "results": {
            "key_numbers": {"n": 8},
            "tables": [{"title": "t", "columns": ["a", "b"], "rows": [[1, 2]]}],
            "charts": [
                {"type": "bar", "title": "c", "x_label": "x", "y_label": "y", "data": [{"x": 1, "y": 2}]}
            ],
        },
        "yields": "It works. Nothing else.",
        "feeds": [],
        "limitations": ["fixture only"],
    }


def test_valid_card_passes():
    validate_card(make_card())


@pytest.mark.parametrize("k", ["id", "why", "data_in", "results", "limitations"])
def test_missing_key_fails(k):
    c = make_card()
    c.pop(k)
    with pytest.raises(CardError):
        validate_card(c)


def test_bad_stage_fails():
    c = make_card()
    c["stage"] = "train"
    with pytest.raises(CardError):
        validate_card(c)


def test_needs_two_alternatives():
    c = make_card()
    c["alternatives"] = c["alternatives"][:1]
    with pytest.raises(CardError):
        validate_card(c)


def test_needs_eight_sample_rows():
    c = make_card()
    c["data_in"]["sample_rows"] = c["data_in"]["sample_rows"][:7]
    with pytest.raises(CardError):
        validate_card(c)


def test_banned_sample_column():
    c = make_card()
    c["data_in"]["sample_rows"][0]["summary"] = "text"
    with pytest.raises(CardError):
        validate_card(c)


def test_em_dash_rejected():
    c = make_card()
    c["yields"] = f"It works {chr(0x2014)} really. Nothing else."
    with pytest.raises(CardError):
        validate_card(c)


def test_sentence_counts():
    c = make_card()
    c["why"] = "One sentence only."
    with pytest.raises(CardError):
        validate_card(c)
    c = make_card()
    c["yields"] = "A. B. C. D."
    with pytest.raises(CardError):
        validate_card(c)


def test_table_width_mismatch():
    c = make_card()
    c["results"]["tables"][0]["rows"] = [[1]]
    with pytest.raises(CardError):
        validate_card(c)


def test_write_rounds_and_converts(tmp_path):
    c = make_card()
    c["results"]["key_numbers"] = {"a": np.float64(1.123456789123), "b": np.int64(3), "c": float("nan")}
    f = write_card(c, tmp_path)
    d = json.loads(f.read_text(encoding="utf-8"))
    assert d["results"]["key_numbers"] == {"a": 1.12345679, "b": 3, "c": None}


def test_write_does_not_mutate(tmp_path):
    c = make_card()
    o = copy.deepcopy(c)
    write_card(c, tmp_path)
    assert c == o


def test_all_project_cards_valid():
    for c in load_cards(CARDS):
        validate_card(c)
