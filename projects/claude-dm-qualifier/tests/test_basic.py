"""Tests basiques — parsing, formatting, report rendering."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from main import Lead, format_conversation, load_conversations, render_report


def test_format_conversation():
    conv = {
        "handle": "@john",
        "messages": [
            {"from": "john", "text": "hi"},
            {"from": "me", "text": "yo"},
        ],
    }
    out = format_conversation(conv)
    assert "@john" in out
    assert "[john] hi" in out
    assert "[me] yo" in out


def test_load_conversations(tmp_path: Path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps([{"handle": "@a", "messages": []}]))
    convs = load_conversations(p)
    assert len(convs) == 1
    assert convs[0]["handle"] == "@a"


def test_load_conversations_missing(tmp_path: Path):
    with pytest.raises(SystemExit):
        load_conversations(tmp_path / "nope.json")


def test_render_report_empty():
    out = render_report([], threshold=60)
    assert "No leads" in out


def test_render_report_filters():
    hot = Lead(
        lead_name="Alice", score=88, intent="hot",
        pain_points=["slow site"], objections=[],
        next_action="Send proposal",
        recommended_reply="Let's hop on a call tomorrow.",
        reasoning="explicit budget + urgency", raw_handle="@alice",
    )
    cold = Lead(
        lead_name="Bob", score=12, intent="cold",
        pain_points=[], objections=[],
        next_action="Ignore", recommended_reply="—",
        reasoning="no signal", raw_handle="@bob",
    )
    out = render_report([hot, cold], threshold=60)
    assert "Alice" in out and "Bob" not in out and "88" in out


def test_lead_dataclass_roundtrip():
    l = Lead(
        lead_name="X", score=50, intent="warm",
        pain_points=["p"], objections=["o"],
        next_action="n", recommended_reply="r", reasoning="why",
    )
    d = l.to_dict()
    assert d["score"] == 50 and d["pain_points"] == ["p"]
