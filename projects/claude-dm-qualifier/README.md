# Claude DM Qualifier

**Instagram / WhatsApp DM Sales Setter** powered by the Claude API.
Auto-qualify inbound DM conversations, score sales potential 0–100, and ship a
ready-to-send recommended reply straight to your Telegram.

Stop wasting hours triaging DMs. Let Claude tell you which 5 conversations are
actually worth closing today.

## Use case

You run an agency / personal brand / e-com store and receive 50–500 Instagram
or WhatsApp DMs per week. Most are noise (compliments, spam, cold pitches).
A handful are real buyers hiding in the middle. This tool:

1. Ingests a JSON export of your DM threads.
2. Sends each thread to Claude with a hard-tuned sales analyst prompt.
3. Returns a structured JSON: `score`, `intent`, `pain_points`, `objections`,
   `next_action`, `recommended_reply`.
4. Filters by score threshold and pushes the top 10 hottest leads to Telegram.

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
# Basic — score everything, show report
python main.py -i data/conversations.json

# Hot leads only (≥ 75), ship to Telegram
python main.py -i data/conversations.json -t 75 --notify telegram

# Parallel API calls (default 5)
python main.py -i data/conversations.json -c 10
```

### Input format

```json
[
  {
    "handle": "@prospect_handle",
    "messages": [
      {"from": "prospect", "text": "Hey, do you do custom websites?"},
      {"from": "me", "text": "Yes — what's the project?"},
      {"from": "prospect", "text": "Budget is around 3k, need it next month"}
    ]
  }
]
```

### Output

- `data/leads.json` — full structured analysis for every conversation
- Markdown report on stdout
- Telegram message (if `--notify telegram` and creds in `.env`)

## Tests

```bash
pytest tests/
```

## License

MIT — do whatever, just don't blame me if Claude misreads your DMs.
