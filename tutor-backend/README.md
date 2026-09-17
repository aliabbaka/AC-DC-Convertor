# AI Circuit Tutor — backend

A small Flask service that powers the "Ask AI Tutor" drawer in `main.html`.
It's built the same way as duckpath's AdvisorPath (`agents.py`'s lazy Groq
client, same model id, and a `circuit_breaker.py` with the same two-layer
shape), just re-armed for RLC circuits instead of academic advising.

## Setup (about 5 minutes)

```bash
cd tutor-backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and paste in a Groq API key from https://console.groq.com
python3 app.py
```

The server listens on `http://localhost:5001`. `main.html`'s `TUTOR_ENDPOINT`
constant already points there — open `main.html` in a browser and the "Ask AI
Tutor" button should work as soon as this is running.

## How it works

- `POST /api/tutor/chat` takes `{ message, history, circuit_state }`, screens
  the message with `circuit_breaker.screen_input()`, then streams the model's
  reply back as plain text (`agents.stream_tutor_reply`).
- If the model ends its reply with a fenced ` ```circuit-set ` block proposing
  new R/L/C/f values to demonstrate something, `circuit_breaker.verify_agent_output()`
  parses it, clamps every field to the sliders' real ranges, and drops anything
  malformed. Only that validated action is appended to the stream (as a
  `<<CIRCUIT_ACTION>>...<<END>>` marker) — the front end is the one that
  actually animates the sliders.
- `screen_input()` blocks prompt-injection attempts, unsafe requests, and
  questions with no plausible connection to the circuit lab. It's a keyword
  heuristic, not a classifier — expect occasional false positives/negatives.

## Notes

- `CORS(app)` is wide open, which is fine for `localhost` development but
  should be restricted (or replaced with a same-origin deployment) before this
  is ever exposed publicly.
- `GROQ_API_KEY` must never be put in `main.html` or any client-side file —
  it only ever lives in this backend's `.env`.
