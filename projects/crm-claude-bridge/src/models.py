"""
Data models for CRM-Claude Bridge.

Pure dataclasses with serialization helpers — no business logic here.
Keeps the pipeline (`bridge.py`) free of structural noise.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any
import hashlib
import json


class LeadStatus(str, Enum):
    """Lifecycle stages of a lead inside the pipeline."""

    RAW = "raw"
    ENRICHED = "enriched"
    QUALIFIED = "qualified"
    EXPORTED = "exported"
    FAILED = "failed"


class Tier(str, Enum):
    """Qualification tier derived from the numeric score."""

    HOT = "hot"          # score >= 80
    WARM = "warm"        # 50 <= score < 80
    COLD = "cold"        # 25 <= score < 50
    DISQUALIFIED = "disqualified"  # score < 25


@dataclass
class Lead:
    """Raw lead as ingested from JSON/CSV.

    Identity is computed from (email or full_name+company) so the
    same person from different sources collapses to one cache key.
    """

    full_name: str
    company: str
    email: Optional[str] = None
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    website: Optional[str] = None
    source: str = "manual"
    notes: Optional[str] = None

    def fingerprint(self) -> str:
        """Stable cache key — survives re-runs and minor field drift."""
        base = (self.email or f"{self.full_name}|{self.company}").lower().strip()
        return hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Enrichment:
    """LLM-produced context attached to a Lead."""

    industry: Optional[str] = None
    company_size: Optional[str] = None
    seniority: Optional[str] = None
    pain_points: list[str] = field(default_factory=list)
    buying_signals: list[str] = field(default_factory=list)
    summary: Optional[str] = None
    confidence: float = 0.0  # 0..1, self-reported by the model

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Qualification:
    """Numeric score + human-readable rationale."""

    score: int  # 0..100
    tier: Tier
    rationale: str
    next_action: str

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "tier": self.tier.value}


@dataclass
class ProcessedLead:
    """Final pipeline output — what gets exported."""

    lead: Lead
    enrichment: Enrichment
    qualification: Qualification
    status: LeadStatus = LeadStatus.QUALIFIED
    processed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "lead": self.lead.to_dict(),
            "enrichment": self.enrichment.to_dict(),
            "qualification": self.qualification.to_dict(),
            "status": self.status.value,
            "processed_at": self.processed_at,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def tier_from_score(score: int) -> Tier:
    """Single source of truth for tier thresholds."""
    if score >= 80:
        return Tier.HOT
    if score >= 50:
        return Tier.WARM
    if score >= 25:
        return Tier.COLD
    return Tier.DISQUALIFIED
