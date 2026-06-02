"""
CRM-Claude Bridge — async ETL pipeline.

Flow:
    JSON/CSV  ─►  Lead  ─►  [cache?]  ─►  Claude enrich  ─►  Claude qualify
                                                                  │
                              CSV  ◄─────── ProcessedLead  ◄──────┘
                              Notion (optional)

Design notes
------------
* Fully async: API calls run in a bounded `asyncio.Semaphore` pool.
* Cache: SQLite keyed on `Lead.fingerprint()`. Idempotent reruns are free.
* Resilience: exponential backoff on transient errors (429/5xx/network).
* Zero hard dependency on Notion — exporter is pluggable.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import logging
import os
import random
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, Optional

from models import (
    Enrichment,
    Lead,
    LeadStatus,
    ProcessedLead,
    Qualification,
    tier_from_score,
)

try:
    from anthropic import AsyncAnthropic  # type: ignore
except ImportError:  # pragma: no cover - allows offline dev
    AsyncAnthropic = None  # type: ignore

logger = logging.getLogger("crm_bridge")

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5")
MAX_CONCURRENCY = int(os.getenv("BRIDGE_CONCURRENCY", "5"))
MAX_RETRIES = 4


# ---------------------------------------------------------------- cache ----
class LeadCache:
    """Thin SQLite wrapper. Stores serialized `ProcessedLead` blobs."""

    def __init__(self, path: Path) -> None:
        self.path = path
        with closing(sqlite3.connect(self.path)) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS leads "
                "(fp TEXT PRIMARY KEY, payload TEXT NOT NULL, ts TEXT NOT NULL)"
            )
            conn.commit()

    def get(self, fp: str) -> Optional[dict[str, Any]]:
        with closing(sqlite3.connect(self.path)) as conn:
            row = conn.execute(
                "SELECT payload FROM leads WHERE fp = ?", (fp,)
            ).fetchone()
        return json.loads(row[0]) if row else None

    def put(self, fp: str, payload: dict[str, Any]) -> None:
        with closing(sqlite3.connect(self.path)) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO leads VALUES (?, ?, datetime('now'))",
                (fp, json.dumps(payload, ensure_ascii=False)),
            )
            conn.commit()


# ----------------------------------------------------------- I/O loaders ---
def load_leads(path: Path) -> list[Lead]:
    """Read leads from .json or .csv. Unknown fields are ignored."""
    raw: list[dict[str, Any]]
    if path.suffix.lower() == ".json":
        raw = json.loads(path.read_text(encoding="utf-8"))
    elif path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8") as fh:
            raw = list(csv.DictReader(fh))
    else:
        raise ValueError(f"Unsupported input format: {path.suffix}")

    allowed = Lead.__dataclass_fields__.keys()
    return [Lead(**{k: v for k, v in row.items() if k in allowed and v}) for row in raw]


def export_csv(leads: list[ProcessedLead], path: Path) -> None:
    """Flat CSV export, one row per lead."""
    fieldnames = [
        "full_name", "company", "email", "title",
        "industry", "seniority", "score", "tier",
        "next_action", "summary",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for pl in leads:
            writer.writerow({
                "full_name": pl.lead.full_name,
                "company": pl.lead.company,
                "email": pl.lead.email or "",
                "title": pl.lead.title or "",
                "industry": pl.enrichment.industry or "",
                "seniority": pl.enrichment.seniority or "",
                "score": pl.qualification.score,
                "tier": pl.qualification.tier.value,
                "next_action": pl.qualification.next_action,
                "summary": pl.enrichment.summary or "",
            })


# ------------------------------------------------------------- Claude IO ---
ENRICH_PROMPT = """You are a B2B sales research analyst.
Given the following lead, produce a JSON object with keys:
industry, company_size, seniority, pain_points (list), buying_signals (list),
summary (max 2 sentences), confidence (0..1).
Use only plausible inference — do NOT invent named clients or revenue figures.

Lead: {lead_json}

Respond with JSON only.
"""

QUALIFY_PROMPT = """You score B2B leads for an AI-services agency.
Given the enriched lead, return JSON with keys:
score (0-100 int), rationale (1-2 sentences), next_action (one concrete step).

Enriched lead: {payload_json}

Respond with JSON only.
"""


async def _call_claude(client: Any, prompt: str) -> dict[str, Any]:
    """Single Claude call with retry/backoff, returns parsed JSON."""
    for attempt in range(MAX_RETRIES):
        try:
            resp = await client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}],
            )
            text = resp.content[0].text.strip()
            # Tolerate ```json fences
            if text.startswith("```"):
                text = text.strip("`").split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(text)
        except Exception as exc:  # noqa: BLE001
            wait = (2 ** attempt) + random.random()
            logger.warning("Claude call failed (%s). Retry in %.1fs", exc, wait)
            await asyncio.sleep(wait)
    raise RuntimeError("Claude unreachable after retries")


async def enrich_lead(client: Any, lead: Lead) -> Enrichment:
    """LLM-augmented context for one lead."""
    data = await _call_claude(
        client, ENRICH_PROMPT.format(lead_json=json.dumps(lead.to_dict()))
    )
    return Enrichment(
        industry=data.get("industry"),
        company_size=data.get("company_size"),
        seniority=data.get("seniority"),
        pain_points=data.get("pain_points", []) or [],
        buying_signals=data.get("buying_signals", []) or [],
        summary=data.get("summary"),
        confidence=float(data.get("confidence", 0.0)),
    )


async def qualify_lead(client: Any, lead: Lead, enr: Enrichment) -> Qualification:
    """Score + rationale + next action."""
    payload = {"lead": lead.to_dict(), "enrichment": enr.to_dict()}
    data = await _call_claude(
        client, QUALIFY_PROMPT.format(payload_json=json.dumps(payload))
    )
    score = max(0, min(100, int(data.get("score", 0))))
    return Qualification(
        score=score,
        tier=tier_from_score(score),
        rationale=data.get("rationale", ""),
        next_action=data.get("next_action", ""),
    )


# ------------------------------------------------------------- pipeline ----
async def process_one(
    lead: Lead,
    client: Any,
    cache: LeadCache,
    sem: asyncio.Semaphore,
) -> ProcessedLead:
    """Cache lookup → enrich → qualify → cache write."""
    fp = lead.fingerprint()
    cached = cache.get(fp)
    if cached:
        logger.info("CACHE HIT  %s (%s)", lead.full_name, fp)
        return _rehydrate(cached)

    async with sem:
        logger.info("PROCESS    %s @ %s", lead.full_name, lead.company)
        try:
            enr = await enrich_lead(client, lead)
            qual = await qualify_lead(client, lead, enr)
        except Exception as exc:  # noqa: BLE001
            logger.error("FAILED     %s: %s", lead.full_name, exc)
            return ProcessedLead(
                lead=lead,
                enrichment=Enrichment(),
                qualification=Qualification(0, tier_from_score(0), str(exc), "review"),
                status=LeadStatus.FAILED,
            )

    pl = ProcessedLead(lead=lead, enrichment=enr, qualification=qual)
    cache.put(fp, pl.to_dict())
    return pl


def _rehydrate(payload: dict[str, Any]) -> ProcessedLead:
    """Inverse of `ProcessedLead.to_dict()`."""
    lead = Lead(**payload["lead"])
    enr = Enrichment(**payload["enrichment"])
    q = payload["qualification"]
    qual = Qualification(
        score=q["score"],
        tier=tier_from_score(q["score"]),
        rationale=q["rationale"],
        next_action=q["next_action"],
    )
    return ProcessedLead(
        lead=lead, enrichment=enr, qualification=qual,
        status=LeadStatus(payload.get("status", "qualified")),
        processed_at=payload.get("processed_at", ""),
    )


async def run_pipeline(
    input_path: Path,
    output_path: Path,
    cache_path: Path,
) -> list[ProcessedLead]:
    """Top-level orchestrator."""
    if AsyncAnthropic is None:
        raise RuntimeError("Install `anthropic` package: pip install anthropic")
    leads = load_leads(input_path)
    logger.info("Loaded %d leads from %s", len(leads), input_path)

    cache = LeadCache(cache_path)
    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    client = AsyncAnthropic()

    results = await asyncio.gather(
        *(process_one(ld, client, cache, sem) for ld in leads),
        return_exceptions=False,
    )
    export_csv(results, output_path)
    logger.info("Exported %d rows → %s", len(results), output_path)
    return results


# --------------------------------------------------------------- CLI -------
def _cli() -> None:
    parser = argparse.ArgumentParser(description="CRM-Claude Bridge")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", default=Path("out/qualified.csv"), type=Path)
    parser.add_argument("--cache", default=Path("cache/leads.sqlite"), type=Path)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s  %(levelname)-7s %(message)s",
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.cache.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(run_pipeline(args.input, args.output, args.cache))


if __name__ == "__main__":
    _cli()
