"""DocumentProcessor — orchestrates extraction + Claude analysis + export.

Pipeline:
    raw file -> text extraction -> Claude structured call -> Pydantic models
             -> JSON/CSV serialization.

Supports single-file and batched processing with bounded concurrency.
"""
from __future__ import annotations

import asyncio
import csv
import json
import logging
import os
import time
from pathlib import Path
from typing import Iterable, Optional

from pydantic import ValidationError

from doc_intel.extractors import extract_text
from doc_intel.models import (
    DocFormat,
    DocumentInsight,
    ExtractedEntity,
    ExtractionResult,
)

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-haiku-4-5"
DEFAULT_MAX_TOKENS = 4096
MAX_INPUT_CHARS = 60_000  # keep prompt below ~15k tokens for cost discipline


_SYSTEM_PROMPT = """You are a document intelligence engine. Read the document text
and return a STRICT JSON object with this shape (no markdown, no commentary):

{
  "insight": {
    "summary": "<2-4 sentence executive summary>",
    "document_type": "invoice|contract|report|email|cv|other",
    "language": "<ISO 639-1>",
    "key_points": ["..."],
    "action_items": ["..."],
    "sentiment": "positive|neutral|negative|null",
    "risk_flags": ["..."]
  },
  "entities": [
    {
      "type": "person|organization|location|date|amount|email|phone|reference|other",
      "value": "<raw text>",
      "normalized": "<ISO date / decimal amount / null>",
      "confidence": 0.0,
      "context": "<<=120 chars>"
    }
  ]
}

Rules:
- Return ONLY the JSON object, no prose, no code fences.
- Dates -> ISO 8601 in `normalized`.
- Amounts -> decimal string + currency code if visible.
- Skip duplicates. Cap entities at 50.
- If document is empty or unreadable, return empty arrays and summary "EMPTY".
"""


class DocumentProcessor:
    """Single-process orchestrator. Stateless except for the Claude client."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        concurrency: int = 3,
    ) -> None:
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model or os.getenv("CLAUDE_MODEL", DEFAULT_MODEL)
        self.max_tokens = max_tokens
        self.concurrency = concurrency
        self._client = None  # lazy

    # ------------------------------------------------------------------ client

    def _get_client(self):
        if self._client is None:
            if not self.api_key:
                raise RuntimeError("ANTHROPIC_API_KEY missing")
            from anthropic import Anthropic
            self._client = Anthropic(api_key=self.api_key)
        return self._client

    # -------------------------------------------------------------- core call

    def _call_claude(self, text: str) -> dict:
        """Send extracted text to Claude, expect strict JSON back."""
        client = self._get_client()
        snippet = text[:MAX_INPUT_CHARS]
        message = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"DOCUMENT:\n\n{snippet}"}],
        )
        raw = "".join(block.text for block in message.content if block.type == "text")
        return json.loads(raw)

    # ---------------------------------------------------------------- single

    def process(self, path: str | Path) -> ExtractionResult:
        """Run the full pipeline on one document."""
        path = Path(path)
        t0 = time.perf_counter()
        try:
            text, fmt, pages = extract_text(path)
        except FileNotFoundError as exc:
            return ExtractionResult(
                source_path=str(path),
                format=DocFormat.UNKNOWN,
                char_count=0,
                error=str(exc),
            )

        result = ExtractionResult(
            source_path=str(path),
            format=fmt,
            char_count=len(text),
            page_count=pages,
            model=self.model,
        )

        if not text.strip():
            result.error = "empty_or_unreadable_document"
            result.latency_ms = int((time.perf_counter() - t0) * 1000)
            return result

        try:
            payload = self._call_claude(text)
            insight_data = payload.get("insight") or {}
            entities_data = payload.get("entities") or []
            result.insight = DocumentInsight(**insight_data) if insight_data else None
            result.entities = [
                ExtractedEntity(**e) for e in entities_data if isinstance(e, dict)
            ]
        except (ValidationError, json.JSONDecodeError) as exc:
            result.error = f"parse_error: {exc}"
        except Exception as exc:  # network / API / quota
            result.error = f"api_error: {exc}"

        result.latency_ms = int((time.perf_counter() - t0) * 1000)
        return result

    # ----------------------------------------------------------------- batch

    def process_batch(self, paths: Iterable[str | Path]) -> list[ExtractionResult]:
        """Sequential batch — safest for rate limits."""
        return [self.process(p) for p in paths]

    async def process_batch_async(
        self, paths: Iterable[str | Path]
    ) -> list[ExtractionResult]:
        """Bounded-concurrency async batch using a thread pool under the hood."""
        sem = asyncio.Semaphore(self.concurrency)

        async def _one(p: str | Path) -> ExtractionResult:
            async with sem:
                return await asyncio.to_thread(self.process, p)

        return await asyncio.gather(*[_one(p) for p in paths])

    # ----------------------------------------------------------------- export

    @staticmethod
    def to_json(results: list[ExtractionResult], out: str | Path) -> Path:
        out = Path(out)
        out.write_text(
            json.dumps([r.model_dump(mode="json") for r in results], indent=2),
            encoding="utf-8",
        )
        return out

    @staticmethod
    def to_csv(results: list[ExtractionResult], out: str | Path) -> Path:
        """One row per entity. Useful for spreadsheet review."""
        out = Path(out)
        with out.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(
                [
                    "source", "format", "doc_type", "entity_type",
                    "value", "normalized", "confidence", "summary",
                ]
            )
            for r in results:
                doc_type = r.insight.document_type if r.insight else ""
                summary = (r.insight.summary[:160] if r.insight else "")
                if not r.entities:
                    writer.writerow(
                        [r.source_path, r.format.value, doc_type, "", "", "", "", summary]
                    )
                for e in r.entities:
                    writer.writerow(
                        [
                            r.source_path, r.format.value, doc_type,
                            e.type.value, e.value, e.normalized or "",
                            f"{e.confidence:.2f}", summary,
                        ]
                    )
        return out
