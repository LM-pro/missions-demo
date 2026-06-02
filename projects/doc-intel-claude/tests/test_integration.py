"""Integration & unit tests for doc-intel-claude.

These tests avoid hitting the Claude API by monkeypatching `_call_claude`.
That keeps CI free and deterministic.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from doc_intel.extractors import detect_format, extract_text
from doc_intel.models import DocFormat
from doc_intel.processor import DocumentProcessor


SAMPLE_TXT = Path(__file__).parent.parent / "data" / "sample.txt"


@pytest.fixture(scope="module", autouse=True)
def ensure_sample():
    SAMPLE_TXT.parent.mkdir(parents=True, exist_ok=True)
    SAMPLE_TXT.write_text(
        "Invoice #2026-001\nClient: Acme Corp\nAmount due: $4,250.00\n"
        "Due date: 2026-07-15\nContact: billing@acme.com",
        encoding="utf-8",
    )


def test_detect_format():
    assert detect_format("a.pdf") == DocFormat.PDF
    assert detect_format("b.DOCX") == DocFormat.DOCX
    assert detect_format("c.txt") == DocFormat.TXT
    assert detect_format("d.zip") == DocFormat.UNKNOWN


def test_extract_txt():
    text, fmt, pages = extract_text(SAMPLE_TXT)
    assert fmt == DocFormat.TXT
    assert "Acme Corp" in text
    assert pages is None


def test_extract_missing_file():
    with pytest.raises(FileNotFoundError):
        extract_text("/tmp/__definitely_not_here__.pdf")


def test_process_with_mocked_claude(monkeypatch):
    proc = DocumentProcessor(api_key="test-key")

    def fake_call(_self, _text):
        return {
            "insight": {
                "summary": "Invoice for Acme Corp totaling $4,250.",
                "document_type": "invoice",
                "language": "en",
                "key_points": ["Amount due $4,250.00", "Due 2026-07-15"],
                "action_items": ["Pay before 2026-07-15"],
                "sentiment": "neutral",
                "risk_flags": [],
            },
            "entities": [
                {"type": "organization", "value": "Acme Corp", "confidence": 0.95},
                {"type": "amount", "value": "$4,250.00", "normalized": "4250.00 USD", "confidence": 0.9},
                {"type": "date", "value": "2026-07-15", "normalized": "2026-07-15", "confidence": 0.99},
                {"type": "email", "value": "billing@acme.com", "confidence": 0.97},
            ],
        }

    monkeypatch.setattr(DocumentProcessor, "_call_claude", fake_call)

    result = proc.process(SAMPLE_TXT)
    assert result.ok
    assert result.format == DocFormat.TXT
    assert result.char_count > 0
    assert result.latency_ms >= 0
    assert result.insight is not None
    assert result.insight.document_type == "invoice"
    assert len(result.entities) == 4
    types = {e.type.value for e in result.entities}
    assert {"organization", "amount", "date", "email"} <= types


def test_batch_and_export(monkeypatch, tmp_path):
    proc = DocumentProcessor(api_key="test-key")
    monkeypatch.setattr(
        DocumentProcessor,
        "_call_claude",
        lambda self, t: {"insight": {"summary": "ok", "document_type": "other"}, "entities": []},
    )
    results = proc.process_batch([SAMPLE_TXT, SAMPLE_TXT])
    assert len(results) == 2
    json_out = proc.to_json(results, tmp_path / "r.json")
    csv_out = proc.to_csv(results, tmp_path / "r.csv")
    data = json.loads(json_out.read_text())
    assert isinstance(data, list) and len(data) == 2
    assert csv_out.read_text().splitlines()[0].startswith("source,format")


def test_corrupt_document_handled(tmp_path, monkeypatch):
    bad = tmp_path / "broken.pdf"
    bad.write_bytes(b"not a real pdf")
    proc = DocumentProcessor(api_key="test-key")
    # _call_claude should not even be reached because extraction will yield ""
    monkeypatch.setattr(DocumentProcessor, "_call_claude", lambda self, t: {})
    result = proc.process(bad)
    assert result.error == "empty_or_unreadable_document"
