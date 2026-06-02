"""Pydantic models for structured document intelligence output."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DocFormat(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    UNKNOWN = "unknown"


class EntityType(str, Enum):
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    DATE = "date"
    AMOUNT = "amount"
    EMAIL = "email"
    PHONE = "phone"
    REFERENCE = "reference"
    OTHER = "other"


class ExtractedEntity(BaseModel):
    """A single typed entity extracted by Claude."""
    type: EntityType
    value: str = Field(..., description="Raw textual value of the entity")
    normalized: Optional[str] = Field(None, description="Canonical form (ISO date, decimal amount)")
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    context: Optional[str] = Field(None, description="Short surrounding context snippet")


class DocumentInsight(BaseModel):
    """High-level analytical view emitted by the LLM."""
    summary: str
    document_type: str = Field(..., description="invoice / contract / report / email / other")
    language: str = "en"
    key_points: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)
    sentiment: Optional[str] = None
    risk_flags: list[str] = Field(default_factory=list)


class ExtractionResult(BaseModel):
    """Final structured payload for one processed document."""
    source_path: str
    format: DocFormat
    char_count: int
    page_count: Optional[int] = None
    processed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    latency_ms: int = 0
    model: str = ""
    entities: list[ExtractedEntity] = Field(default_factory=list)
    insight: Optional[DocumentInsight] = None
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None
