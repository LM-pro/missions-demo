# Claude DM Qualifier

Personal Python demo that scores sample direct-message conversations with the Claude API and suggests a reply. It reads a JSON export rather than connecting to an Instagram or WhatsApp inbox. Scores and suggestions have not been validated against real customer conversations; review them before any use.

## Use Case

The demo takes a JSON list of conversations and processes each thread. It:

1. Ingests a JSON export of your DM threads.
2. Sends each thread to Claude with a tuned sales analyst prompt.
3. Returns structured JSON: score, intent, pain points, objections, next action, recommended reply.
4. Filters by score threshold and can send selected results to Telegram when configured.

## Install

```bash
git clone <repo>
cd claude-dm-qualifier

# With Poetry (recommended)
poetry install
poetry run python main.py --input data/sample.json --notify telegram

# Or with pip
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then fill in your keys
```

## Usage

```bash
# Basic -- score everything, show report
python main.py -i data/conversations.json

# Hot leads only (score >= 75), ship to Telegram
python main.py -i data/conversations.json -t 75 --notify telegram

# Parallel API calls (default 5)
python main.py -i data/conversations.json -c 10
```

### Input Format

```json
[
  {
    "handle": "@prospect_handle",
    "messages": [
      {"from": "prospect", "text": "Hey, do you do custom websites?"},
      {"from": "me", "text": "Yes -- what is the project?"},
      {"from": "prospect", "text": "Budget is around $3k, need it next month"}
    ]
  }
]
```

### Output

- `data/leads.json` -- full structured analysis for every conversation
- Markdown report on stdout
- Telegram message (if `--notify telegram` and credentials in `.env`)

## Tests

```bash
pytest tests/
```

## License

MIT
