# CRM-Claude Bridge

Personal Python demo that reads sample lead records from JSON or CSV, asks the
Claude API to classify and score them, caches results locally and exports a
ranked CSV. The generated attributes are model outputs, not independently
verified company research. Notion export is a possible extension and is not
implemented. The pipeline has not been deployed for a client or validated for
production use.

---

## Architecture

```
            ┌─────────────────────────────────────────────────────────┐
            │                    CRM-Claude Bridge                     │
            └─────────────────────────────────────────────────────────┘

  data/leads.json ──► load_leads() ──► [ Lead ]
                                          │
                                          ▼
                                   ┌─────────────┐
                                   │ LeadCache   │  SQLite, keyed by
                                   │ (sqlite3)   │  Lead.fingerprint()
                                   └──────┬──────┘
                                  HIT │       │ MISS
                                      │       ▼
                                      │   ┌────────────────────┐
                                      │   │ enrich_lead()      │
                                      │   │   Claude API       │  industry,
                                      │   │   ENRICH_PROMPT    │  seniority,
                                      │   └─────────┬──────────┘  signals…
                                      │             ▼
                                      │   ┌────────────────────┐
                                      │   │ qualify_lead()     │
                                      │   │   Claude API       │  score 0-100
                                      │   │   QUALIFY_PROMPT   │  + rationale
                                      │   └─────────┬──────────┘
                                      │             ▼
                                      └────►  ProcessedLead  ────► cache.put()
                                                    │
                                                    ▼
                                            ┌──────────────┐
                                            │ export_csv() │ → out/qualified.csv
                                            │ (Notion: TBD)│
                                            └──────────────┘
```

Concurrency is bounded by `asyncio.Semaphore(MAX_CONCURRENCY)`, but provider
rate limits still apply. Failed calls back off exponentially with
jitter and surface as `LeadStatus.FAILED` rows rather than crashing the run.

---

## Quickstart

```bash
# 1. Install
poetry install            # or: pip install -r requirements.txt

# 2. Configure
export ANTHROPIC_API_KEY=sk-ant-...
export CLAUDE_MODEL=claude-haiku-4-5     # optional, default shown
export BRIDGE_CONCURRENCY=5              # optional

# 3. Run
poetry run crm-bridge \
    --input  data/sample-leads.json \
    --output out/qualified.csv \
    --cache  cache/leads.sqlite \
    --verbose
```

Re-running the same input is a no-op: the cache returns prior results
instantly. Delete `cache/leads.sqlite` to force a full re-process.

---

## Project layout

```
crm-claude-bridge/
├── src/
│   ├── bridge.py         # async pipeline + CLI
│   └── models.py         # Lead / Enrichment / Qualification / ProcessedLead
├── data/
│   └── sample-leads.json # 4 fake leads — safe to commit
├── tests/
│   └── test_bridge.py    # deterministic tests, no API calls
├── pyproject.toml        # Poetry + ruff + pytest config
├── requirements.txt      # pip fallback
└── README.md
```

---

## Testing

```bash
poetry run pytest -q
```

Tests are offline: they cover the tier ladder, fingerprint stability, the
SQLite cache round-trip, the CSV exporter, and the JSON loader.

---

## Extending

* **Notion export** — implement `export_notion(leads)` in `bridge.py` using
  the official `notion-client` package; keep `export_csv` as the fallback.
* **Real LinkedIn scrape** — swap the `ENRICH_PROMPT` synthesis step for an
  actual Proxycurl/Apify call; cache key stays the same.
* **Custom scoring** — edit `QUALIFY_PROMPT` or replace `qualify_lead` with
  a rule-based scorer. The contract (`Qualification`) is stable.

---

## License

MIT.
