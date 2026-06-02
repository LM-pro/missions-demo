# Claude AI Tools Suite 🤖

Production-grade AI automation tools built with **Claude API** and **Python 3.11+**.

Specialized in **sales automation**, **CRM enrichment**, and **document intelligence**.

---

## 📦 Projects

### 1. **Claude DM Qualifier** — Sales Lead Scoring
Automatically analyze and score Instagram/WhatsApp DM conversations using Claude AI.

- **Use case:** Identify qualified sales leads from direct messages
- **Tech:** Python, Claude API, Async, Telegram notifications
- **Status:** Production-ready

**Quick start:**
```bash
cd projects/claude-dm-qualifier
pip install -r requirements.txt
cp .env.example .env  # Configure CLAUDE_API_KEY
python main.py
```

[→ Full documentation](./projects/claude-dm-qualifier/README.md)

---

### 2. **CRM Claude Bridge** — Lead Enrichment Pipeline
Enrich and auto-qualify leads using Claude's analysis capabilities.

- **Use case:** Accelerate lead qualification with AI-powered scoring
- **Tech:** Python, Claude API, Async, SQLite caching, Notion export
- **Status:** Production-ready

**Quick start:**
```bash
cd projects/crm-claude-bridge
pip install -r requirements.txt
cp .env.example .env
python -m bridge --input data/leads.json --output results.json
```

[→ Full documentation](./projects/crm-claude-bridge/README.md)

---

### 3. **Doc Intel Claude** — Document Intelligence System
Extract structured data from PDFs, Word docs, and text files.

- **Use case:** Automate data extraction from contracts, research papers, invoices
- **Tech:** Python, Claude API, PyPDF2, Pydantic v2, async/sync modes
- **Status:** Production-ready

**Quick start:**
```bash
cd projects/doc-intel-claude
pip install -r requirements.txt
python processor.py --file sample.pdf --format json
```

[→ Full documentation](./projects/doc-intel-claude/README.md)

---

## 🎯 Architecture

All projects follow **consistent patterns** for easy integration:

- **Async-first** design for concurrent API calls
- **Structured output** with Pydantic models
- **Error handling** and retry logic built-in
- **Zero hardcoded secrets** (.env templates provided)
- **Production logging** with configurable levels

```
missions-demo/
├── projects/
│   ├── claude-dm-qualifier/      # DM sales scorer
│   ├── crm-claude-bridge/        # Lead enrichment
│   └── doc-intel-claude/         # Document extraction
├── README.md                      # This file
└── .gitignore
```

---

## 🚀 Getting Started

### Requirements
- Python 3.11+
- Claude API key (from [Anthropic Console](https://console.anthropic.com))
- `pip` or `poetry`

### Installation (Any Project)

```bash
# Clone & navigate
cd projects/[project-name]

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your CLAUDE_API_KEY
```

---

## 📊 Upwork Missions Alignment

These projects directly address **top-demand Claude/AI jobs on Upwork:**

| Project | Upwork Use Case | Potential Budget |
|---------|---|---|
| `claude-dm-qualifier` | Instagram DM automation, lead gen | $700–1500 |
| `crm-claude-bridge` | Lead qualification, CRM integration | $500–1500 |
| `doc-intel-claude` | Legal doc analysis, invoice processing | $75–120/h |

---

## 💡 Key Features

✅ **Async/Await Support** — Non-blocking API calls for 10x throughput  
✅ **Intelligent Caching** — Avoid re-processing identical inputs  
✅ **Batch Processing** — Process 100+ documents in one run  
✅ **Pydantic Models** — Type-safe, validated outputs  
✅ **Comprehensive Tests** — 6+ unit tests per project  
✅ **Error Recovery** — Graceful handling of network failures  
✅ **CLI + Lib Mode** — Use as command-line tool or Python module  

---

## 🔧 Development

Each project includes:

- **test_*.py** — Unit tests for core functions
- **requirements.txt** — Pinned dependencies
- **pyproject.toml** — Modern Python packaging (poetry-compatible)
- **README.md** — Detailed per-project documentation
- **.env.example** — Safe configuration template

### Run Tests

```bash
cd projects/[project-name]
pytest -v
```

---

## 📝 Environment Configuration

All projects require a `.env` file:

```env
CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxx
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

Find your API key: [Anthropic Console](https://console.anthropic.com/account/keys)

---

## 📖 Documentation

- [Claude DM Qualifier Docs](./projects/claude-dm-qualifier/README.md)
- [CRM Claude Bridge Docs](./projects/crm-claude-bridge/README.md)
- [Doc Intel Claude Docs](./projects/doc-intel-claude/README.md)

---

## 🎓 Deployment Tips

### Production Checklist
- [ ] Set `LOG_LEVEL=WARNING` in .env
- [ ] Configure `.env` with production API keys
- [ ] Run full test suite: `pytest`
- [ ] Review rate limits for Claude API
- [ ] Monitor token usage (logs include token counts)

### Recommended Stack
- **Hosting:** AWS Lambda / Google Cloud Functions (async workloads)
- **Task Queue:** Celery / APScheduler for periodic jobs
- **DB:** PostgreSQL for transactional data
- **Monitoring:** Sentry for error tracking

---

## 📄 License

MIT — See individual project directories

---

## 🤝 Support

For questions or issues, refer to each project's README or consult Claude API documentation.

**Built with ❤️ for Upwork mission-solvers**

---

**Last updated:** June 2, 2026  
**Status:** ✅ Production-ready
