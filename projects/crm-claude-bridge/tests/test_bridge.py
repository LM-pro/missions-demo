"""Unit tests for the deterministic parts of the bridge.

We don't hit the Claude API in tests — instead we exercise the
fingerprint, tier mapping, cache, and CSV exporter.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from bridge import LeadCache, export_csv, load_leads  # noqa: E402
from models import (  # noqa: E402
    Enrichment,
    Lead,
    ProcessedLead,
    Qualification,
    Tier,
    tier_from_score,
)


def _make_processed(name: str, score: int) -> ProcessedLead:
    lead = Lead(full_name=name, company="Acme", email=f"{name.lower()}@acme.example")
    enr = Enrichment(industry="SaaS", seniority="VP", summary="Test summary.")
    qual = Qualification(score=score, tier=tier_from_score(score),
                         rationale="r", next_action="email")
    return ProcessedLead(lead=lead, enrichment=enr, qualification=qual)


def test_tier_thresholds() -> None:
    """Boundaries of the tier ladder are stable."""
    assert tier_from_score(100) is Tier.HOT
    assert tier_from_score(80) is Tier.HOT
    assert tier_from_score(79) is Tier.WARM
    assert tier_from_score(50) is Tier.WARM
    assert tier_from_score(49) is Tier.COLD
    assert tier_from_score(25) is Tier.COLD
    assert tier_from_score(24) is Tier.DISQUALIFIED
    assert tier_from_score(0) is Tier.DISQUALIFIED


def test_fingerprint_is_stable_and_email_normalised() -> None:
    """Same email → same fingerprint regardless of case/whitespace."""
    a = Lead(full_name="Jane Doe", company="Acme", email="Jane@Acme.Example ")
    b = Lead(full_name="J. Doe",   company="Acme Inc", email="jane@acme.example")
    assert a.fingerprint() == b.fingerprint()


def test_cache_roundtrip(tmp_path: Path) -> None:
    """LeadCache stores and retrieves the same payload."""
    cache = LeadCache(tmp_path / "c.sqlite")
    pl = _make_processed("Ada Lovelace", 87)
    cache.put(pl.lead.fingerprint(), pl.to_dict())
    out = cache.get(pl.lead.fingerprint())
    assert out is not None
    assert out["qualification"]["score"] == 87
    assert out["lead"]["full_name"] == "Ada Lovelace"


def test_export_csv_columns_and_rows(tmp_path: Path) -> None:
    """CSV export has the expected schema and one row per lead."""
    out = tmp_path / "qualified.csv"
    export_csv([_make_processed("Ada", 90), _make_processed("Bob", 10)], out)
    content = out.read_text(encoding="utf-8").splitlines()
    assert content[0].split(",")[0] == "full_name"
    assert len(content) == 3  # header + 2 rows
    assert "hot" in content[1]
    assert "disqualified" in content[2]


def test_load_leads_json(tmp_path: Path) -> None:
    """JSON loader ignores unknown fields, keeps known ones."""
    payload = [{"full_name": "X", "company": "Y", "weird_field": "drop me"}]
    p = tmp_path / "leads.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    leads = load_leads(p)
    assert len(leads) == 1 and leads[0].full_name == "X"
