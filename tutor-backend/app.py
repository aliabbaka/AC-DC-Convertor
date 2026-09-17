import json
import os

from dotenv import load_dotenv
from flask import Flask, Response, request, stream_with_context
from flask_cors import CORS

from agents import stream_tutor_reply
from circuit_breaker import screen_input, verify_agent_output
from prompts import build_system_prompt

load_dotenv()

app = Flask(__name__)
CORS(app)  # wide open for local dev only — lock this down before deploying anywhere public

ACTION_MARKER_START = "\n<<CIRCUIT_ACTION>>"
ACTION_MARKER_END = "<<END>>"


@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/tutor/chat")
def chat():
    body = request.get_json(force=True, silent=True) or {}
    message = (body.get("message") or "").strip()
    history = body.get("history") or []
    circuit_state = body.get("circuit_state") or {}

    allowed, reason = screen_input(message)
    if not allowed:
        return Response(reason, mimetype="text/plain", headers={"X-Tutor-Blocked": "true"})

    system_prompt = build_system_prompt(circuit_state)

    def generate():
        full_text = ""
        for delta in stream_tutor_reply(system_prompt, history, message):
            full_text += delta
            yield delta

        action, issues = verify_agent_output(full_text)
        if action:
            yield ACTION_MARKER_START + json.dumps(action) + ACTION_MARKER_END
        if issues:
            # clamped/dropped fields are logged, not surfaced in the chat —
            # a silently-corrected demo is less confusing than an error message
            app.logger.info("circuit-set issues: %s", issues)

    return Response(stream_with_context(generate()), mimetype="text/plain")


if __name__ == "__main__":
    if "GROQ_API_KEY" not in os.environ:
        print("Warning: GROQ_API_KEY is not set — copy .env.example to .env and add your key.")
    app.run(port=5001, debug=True)
