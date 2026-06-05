"""
claude-dm-qualifier — Instagram/WhatsApp DM Sales Setter
=========================================================

Analyse les conversations DM avec Claude pour identifier les leads qualifiés,
attribuer un score de potentiel commercial (0-100), et envoyer un résumé
actionnable via Telegram ou email.

Usage:
    python main.py --input data/conversations.json --notify telegram
    python main.py --input data/export_ig.json --notify email --threshold 60

Author: OMEGA Stack (Thorsen Industries)
License: MIT
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import httpx
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
log = logging.getLogger("dm-qualifier")

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


SYSTEM_PROMPT = """You are an elite B2B sales qualification analyst.

Given an Instagram/WhatsApp DM conversation, return a STRICT JSON object:
{
  "lead_name": "string",
  "score": 0-100,
  "intent": "cold|warm|hot|customer|spam",
  "pain_points": ["..."],
  "objections": ["..."],
  "next_action": "string — concrete next step",
  "recommended_reply": "string — 2-3 sentences, direct, no fluff",
  "reasoning": "string — 1 sentence why this score"
}

Scoring rubric:
- 0-30: cold / no clear intent / spam
- 31-60: curious, no budget signal
- 61-85: pain identified, budget plausible, timing soon
- 86-100: ready to buy, explicit intent + budget + urgency

Output JSON ONLY. No prose, no markdown."""


@dataclass
class Lead:
    """Représente un lead qualifié issu d'une conversation DM."""

    lead_name: str
    score: int
    intent: str
    pain_points: list[str]
    objections: list[str]
    next_action: str
    recommended_reply: str
    reasoning: str
    raw_handle: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_conversations(path: Path) -> list[dict[str, Any]]:
    """Charge un export JSON de conversations DM.

    Format attendu: [{"handle": "@user", "messages": [{"from": "...", "text": "..."}]}].
    """
    if not path.exists():
        log.error("Input file not found: %s", path)
        sys.exit(1)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Expected a JSON list of conversations.")
    return data


def format_conversation(conv: dict[str, Any]) -> str:
    """Sérialise une conversation pour le prompt Claude."""
    lines = [f"# Conversation with {conv.get('handle', 'unknown')}"]
    for msg in conv.get("messages", []):
        sender = msg.get("from", "?")
        text = msg.get("text", "").strip()
        lines.append(f"[{sender}] {text}")
    return "\n".join(lines)


async def qualify_one(
    client: AsyncAnthropic, conv: dict[str, Any]
) -> Lead | None:
    """Qualifie une seule conversation via Claude."""
    handle = conv.get("handle", "unknown")
    try:
        resp = await client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": format_conversation(conv)}],
        )
        raw = resp.content[0].text.strip()
        # Strip possible ```json fences
        if raw.startswith("```"):
            raw = raw.strip("`").lstrip("json").strip()
        parsed = json.loads(raw)
        return Lead(raw_handle=handle, **parsed)
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        log.warning("Parse failure for %s: %s", handle, e)
        return None
    except Exception as e:  # network, rate-limit, etc.
        log.error("Claude API error for %s: %s", handle, e)
        return None


async def qualify_all(
    conversations: list[dict[str, Any]], concurrency: int = 5
) -> list[Lead]:
    """Qualifie toutes les conversations en parallèle (bornée)."""
    if not ANTHROPIC_KEY:
        log.error("ANTHROPIC_API_KEY missing in environment.")
        sys.exit(1)

    client = AsyncAnthropic(api_key=ANTHROPIC_KEY)
    sem = asyncio.Semaphore(concurrency)

    async def _run(conv: dict[str, Any]) -> Lead | None:
        async with sem:
            return await qualify_one(client, conv)

    results = await asyncio.gather(*(_run(c) for c in conversations))
    return [r for r in results if r is not None]


def render_report(leads: list[Lead], threshold: int) -> str:
    """Construit un rapport markdown lisible des leads >= threshold."""
    qualified = sorted(
        [l for l in leads if l.score >= threshold], key=lambda x: -x.score
    )
    if not qualified:
        return f"📭 No leads ≥ {threshold}/100 in {len(leads)} conversations."

    lines = [
        f"DM Qualifier - {len(qualified)} hot leads (threshold {threshold})",
        "",
    ]
    for l in qualified[:10]:
        lines += [
            f"*{l.lead_name}* ({l.raw_handle}) — score *{l.score}* [{l.intent}]",
            f"  Pain: {', '.join(l.pain_points) or '—'}",
            f"  Next: {l.next_action}",
            f"  Reply: _{l.recommended_reply}_",
            "",
        ]
    return "\n".join(lines)


async def send_telegram(message: str) -> bool:
    """Envoie le rapport sur Telegram (Markdown)."""
    if not (TELEGRAM_TOKEN and TELEGRAM_CHAT_ID):
        log.warning("Telegram credentials missing — skipping notify.")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    async with httpx.AsyncClient(timeout=15.0) as http:
        r = await http.post(
            url,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown",
            },
        )
        ok = r.status_code == 200
        log.info("Telegram notify: %s", "ok" if ok else r.text[:200])
        return ok


def save_leads(leads: list[Lead], out: Path) -> None:
    """Sauvegarde les leads qualifiés en JSON."""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps([l.to_dict() for l in leads], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    log.info("Wrote %d leads → %s", len(leads), out)


async def pipeline(args: argparse.Namespace) -> int:
    """Pipeline complet: load → qualify → report → notify → persist."""
    conversations = load_conversations(Path(args.input))
    log.info("Loaded %d conversations", len(conversations))

    leads = await qualify_all(conversations, concurrency=args.concurrency)
    log.info("Qualified %d/%d leads", len(leads), len(conversations))

    save_leads(leads, Path(args.output))

    report = render_report(leads, args.threshold)
    print(report)

    if args.notify == "telegram":
        await send_telegram(report)

    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Claude DM Qualifier")
    p.add_argument("--input", "-i", required=True, help="Path to conversations JSON")
    p.add_argument("--output", "-o", default="data/leads.json", help="Output JSON path")
    p.add_argument("--threshold", "-t", type=int, default=60, help="Min score to report")
    p.add_argument("--concurrency", "-c", type=int, default=5, help="Parallel API calls")
    p.add_argument(
        "--notify", choices=["none", "telegram"], default="none", help="Notification channel"
    )
    return p.parse_args()


if __name__ == "__main__":
    sys.exit(asyncio.run(pipeline(parse_args())))
