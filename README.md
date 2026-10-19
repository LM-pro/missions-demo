# Claude API — personal Python demos

Three small projects exploring how the Claude API can help organize sales conversations, lead records and documents. They are portfolio demonstrations built with sample data. They have not been deployed for clients or validated for production use.

## Projects

| Project | What the demo does | Documentation |
|---|---|---|
| Claude DM Qualifier | Scores sample direct-message conversations and suggests a response. | [README](projects/claude-dm-qualifier/README.md) |
| CRM Claude Bridge | Enriches and ranks sample lead records, with local caching and CSV export. | [README](projects/crm-claude-bridge/README.md) |
| Doc Intel Claude | Extracts structured information from sample PDF, DOCX and text files. | [README](projects/doc-intel-claude/README.md) |

Each project has its own setup instructions and automated tests. Running the Claude-powered paths requires an Anthropic API key and may incur API charges. The included examples use sample data; they do not contain real client records.

## Repository layout

```text
projects/
  claude-dm-qualifier/
  crm-claude-bridge/
  doc-intel-claude/
```

## What this work shows

- Python scripts and command-line interfaces around the Claude API.
- Structured outputs, input validation and local data handling.
- Automated tests for selected functions.

These demos are a starting point for discussion, not evidence of client delivery. A production deployment would need additional testing with real use cases, security review, monitoring and a clear handling policy for personal data.
