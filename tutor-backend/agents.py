"""
Thin Groq wrapper for the AI Circuit Tutor.

Mirrors AdvisorPath's agents.py — same lazy client, same model id — but
built around a streaming chat completion instead of one-shot .create() calls,
since the tutor drawer renders tokens as they arrive.
"""
import os

from groq import Groq

# Same model AdvisorPath settled on. If Groq deprecates it, check available
# models with: python3 -c "from groq import Groq; print(Groq().models.list())"
MODEL = "openai/gpt-oss-120b"

_client = None


def get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=os.environ["GROQ_API_KEY"])
    return _client


def stream_tutor_reply(system_prompt, history, user_message):
    """Yields text deltas from Groq as they arrive."""
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    stream = get_client().chat.completions.create(
        model=MODEL,
        messages=messages,
        stream=True,
        temperature=0.4,
        max_tokens=700,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
