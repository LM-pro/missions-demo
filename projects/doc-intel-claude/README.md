# Doc Intel Claude

Personal document-processing demo powered by Claude. It accepts PDF, DOCX or TXT files and returns structured information as JSON or CSV. It has not been deployed or validated for production use.

---

## Why This Exists

This project explores how to extract information from invoices, contracts and reports. Claude handles the language analysis, while Pydantic validates the response schema. Processing time and extraction quality depend on the input files and the API response.

## Use Cases

- **Accounts payable** -- Extract invoice number, vendor, due date, amount, and currency from supplier PDFs. Export directly to your accounting CSV.
- **Contract triage** -- Surface parties, effective dates, renewal clauses, and risk flags for legal first-pass review.
- **Research ingestion** -- Turn a stack of PDFs into structured summaries with key points for a knowledge base.
- **Email/CV screening** -- Classify document type, extract contact info, score relevance.
- **Audit batches** -- Async batch mode with bounded concurrency; provider rate limits still apply.

## Stack

Python 3.11+ | Claude API (anthropic) | pypdf | python-docx | Pydantic v2 | FastAPI (optional) | Poetry | pytest

## Install

```bash
# pip
pip install -r requirements.txt
# poetry
poetry install
# with FastAPI surface
poetry install --extras api
```

Create `.env` from `.env.example` and set `ANTHROPIC_API_KEY`.

## Quick Start

```bash
# Single file
doc-intel data/sample.pdf --out output/results.json

# Batch + CSV export
doc-intel data/*.pdf data/*.docx --out output/all.json --csv output/all.csv

# Custom model
doc-intel data/contract.pdf --model claude-sonnet-4-6
```

### Python API

```python
from doc_intel import DocumentProcessor

proc = DocumentProcessor(concurrency=5)
result = proc.process("data/invoice.pdf")

print(result.insight.summary)
for e in result.entities:
    print(e.type, e.value, e.normalized)
```

### Async Batch

```python
import asyncio
from pathlib import Path
from doc_intel import DocumentProcessor

proc = DocumentProcessor(concurrency=8)
files = list(Path("inbox/").glob("*.pdf"))
results = asyncio.run(proc.process_batch_async(files))
DocumentProcessor.to_csv(results, "output/inbox.csv")
```

### FastAPI

```bash
uvicorn doc_intel.api:app --reload
# POST a file to /extract -- returns the full ExtractionResult JSON
```

## Output Schema

```jsonc
{
  "source_path": "data/invoice.pdf",
  "format": "pdf",
  "char_count": 1842,
  "page_count": 2,
  "latency_ms": 1430,
  "model": "claude-haiku-4-5",
  "insight": {
    "summary": "...", "document_type": "invoice", "language": "en",
    "key_points": [...], "action_items": [...], "risk_flags": [...]
  },
  "entities": [
    {"type": "amount", "value": "$4,250.00", "normalized": "4250.00 USD", "confidence": 0.92}
  ]
}
```

## Performance Profile

| Module          | LOC | Cold latency (Haiku 4.5) | Notes                          |
|-----------------|-----|--------------------------|--------------------------------|
| `extractors.py` | 110 | < 50 ms / page           | pypdf + python-docx, pure I/O  |
| `processor.py`  | 210 | 1.2 - 2.5 s / doc        | One Claude call, bounded input |
| `cli.py`        | 50  | + 200 ms startup         | Rich table render              |
| `api.py`        | 40  | + 80 ms                  | FastAPI optional               |

Batches scale approximately linearly with `concurrency` until you hit your Anthropic tier limit (default 3 concurrent).

## Tests

```bash
pytest -q
```

Tests monkeypatch the Claude call so CI runs free and deterministic. The test suite covers format detection, text extraction, batch processing, CSV/JSON export, and corrupt-document fallback.

## Roadmap

- [ ] OCR fallback for scanned PDFs (Tesseract)
- [ ] Streaming results via SSE on the FastAPI endpoint
- [ ] Pluggable extractors (HTML, EML, XLSX)
- [ ] Cost ledger (tokens per model per run)

## License

MIT
