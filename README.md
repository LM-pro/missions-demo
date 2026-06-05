# Claude AI Tools Suite

Production-grade AI automation tools built with Claude API and Python.

I specialize in sales automation, CRM enrichment, and document intelligence using Claude API. These projects represent the core patterns I implement for clients on Upwork.

---

## Projects

### 1. Claude DM Qualifier — Sales Lead Scoring

Automatically analyze and score Instagram and WhatsApp DM conversations using Claude AI to identify qualified sales leads.

- **Use case:** Identify qualified sales leads from direct messages
- **Tech stack:** Python, Claude API, Async, Telegram notifications
- **Status:** Production-ready

```bash
cd projects/claude-dm-qualifier
pip install -r requirements.txt
cp .env.example .env
python main.py
```

[Full documentation](./projects/claude-dm-qualifier/README.md)

---

### 2. CRM Claude Bridge — Lead Enrichment Pipeline

Enrich and auto-qualify leads using Claude's analysis capabilities. Scores prospects for sales priority.

- **Use case:** Accelerate lead qualification with AI-powered scoring
- **Tech stack:** Python, Claude API, Async, SQLite caching, Notion export
- **Status:** Production-ready

```bash
cd projects/crm-claude-bridge
pip install -r requirements.txt
cp .env.example .env
python -m bridge --input data/leads.json --output results.json
```

[Full documentation](./projects/crm-claude-bridge/README.md)

---

### 3. Doc Intel Claude — Document Intelligence System

Extract structured data from PDFs, Word docs, and text files. Designed for contracts, invoices, and research papers.

- **Use case:** Automate data extraction from contracts, invoices, research papers
- **Tech stack:** Python, Claude API, PyPDF2, Pydantic v2, async/sync modes
- **Status:** Production-ready

```bash
cd projects/doc-intel-claude
pip install -r requirements.txt
python processor.py --file sample.pdf --format json
```

[Full documentation](./projects/doc-intel-claude/README.md)

---

## Architecture

All projects follow consistent patterns for easy integration:

- Async-first design for concurrent API calls
- Structured output with Pydantic models
- Error handling and retry logic built in
- Zero hardcoded secrets (.env templates provided)
- Production logging with configurable levels

```
missions-demo/
├── projects/
│   ├── claude-dm-qualifier/      # DM sales scorer
│   ├── crm-claude-bridge/        # Lead enrichment
│   └── doc-intel-claude/         # Document extraction
├── README.md
└── .gitignore
```

---

## Getting Started

### Requirements
- Python 3.11+
- Claude API key (from [Anthropic Console](https://console.anthropic.com))
- pip or poetry

### Installation (Any Project)

```bash
cd projects/[project-name]
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Then edit `.env` with your `CLAUDE_API_KEY`.

---

## Current Upwork Availability

I am available for new projects in the following areas:

| Focus Area | Typical Use Case | Typical Budget |
|------------|-----------------|----------------|
| DM automation | Instagram DM triage, lead scoring | $700-1,500 |
| CRM pipelines | Lead enrichment, auto-qualification | $500-1,500 |
| Document intelligence | PDF extraction, invoice processing | $75-120/hr |

My rate is $49/hr for ongoing work, or fixed-price depending on scope.

---

## Key Features

All projects include:

- Async/await support for non-blocking API calls
- Intelligent caching to avoid re-processing identical inputs
- Batch processing for 100+ items
- Pydantic models for type-safe, validated outputs
- Comprehensive tests (6+ per project)
- Error recovery with graceful handling
- CLI and library modes

---

## Development

Each project includes:
- Unit tests for core functions
- Pinned dependencies in requirements.txt
- pyproject.toml for modern Python packaging
- Detailed per-project README
- .env.example for safe configuration

```bash
cd projects/[project-name]
pytest -v
```

---

## Contact

Available for immediate start on Claude API projects. I work in UTC+2 (flexible). Reach out for custom solutions or if you need something specific not listed here.

---

**Last updated:** June 5, 2026
**Status:** Available for new projects
