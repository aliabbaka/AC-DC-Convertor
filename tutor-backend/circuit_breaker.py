"""
Two-layer safety gate for the AI Circuit Tutor.

Ported from duckpath's AdvisorPath circuit_breaker.py (same two-layer shape —
block bad input before it reaches the model, validate the model's output
before anything is allowed to act on it) but re-armed for this app's domain:
input screening keeps questions inside RLC/circuits territory instead of
academic-advising territory, and output validation clamps a proposed
"circuit-set" demo action to the sliders' real ranges instead of checking
resource links/IDs against a database.
"""
import json
import re

# ---------------------------------------------------------------------------
# input screening
# ---------------------------------------------------------------------------

_PROMPT_INJECTION = re.compile(
    r"(ignore (all|any|previous) instructions|disregard (the|your) (system|previous)|"
    r"you are now|pretend to be|reveal (your|the) (system )?prompt|"
    r"jailbreak|override your (rules|instructions))",
    re.I,
)

_UNSAFE = re.compile(
    r"\b(how to (hack|build a (bomb|weapon)|make (a bomb|explosives)|steal)|"
    r"malware|ransomware|self[- ]harm|suicide)\b",
    re.I,
)

# Any of these words in the message counts as "this is plausibly about the lab".
_ON_TOPIC_HINTS = re.compile(
    r"\b(r|l|c|rlc|resist\w*|induct\w*|capacit\w*|ohm|henry|farad|circuit\w*|current|"
    r"voltage|imped\w*|phase|reson\w*|damp\w*|eigen\w*|matrix|regime|"
    r"quality factor|q factor|transient|steady[- ]state|frequency|hertz|hz|"
    r"kirchhoff|overdamp\w*|underdamp\w*|critical\w*|alpha|omega|decay|ring\w*|"
    r"schematic|switch|energiz\w*|slider|graph|bode|phasor)\b",
    re.I,
)

# Common off-topic asks a general chatbot gets, none of which this tutor should answer.
_OFF_TOPIC_ASKS = re.compile(
    r"\b(write (me |us )?(a|an) (poem|story|song|essay|joke)\b|"
    r"what'?s the weather|sports score|"
    r"relationship advice|dating advice|medical advice|legal advice|"
    r"stock (tip|advice)|translate this)",
    re.I,
)


def screen_input(text):
    """Returns (allowed: bool, reason: str | None). Runs before the LLM call."""
    if not text or not text.strip():
        return False, "Ask me something about the circuit first."
    if _PROMPT_INJECTION.search(text):
        return False, "That reads like an attempt to change my instructions, which I can't do."
    if _UNSAFE.search(text):
        return False, "I can't help with that."
    word_count = len(text.split())
    if word_count > 3 and _OFF_TOPIC_ASKS.search(text) and not _ON_TOPIC_HINTS.search(text):
        return False, (
            "I'm scoped to this RLC circuit lab — ask me about R, L, C, damping, "
            "resonance, impedance, eigenvalues, or the matrix behind them."
        )
    return True, None


# ---------------------------------------------------------------------------
# output validation
# ---------------------------------------------------------------------------

ACTION_FENCE = re.compile(r"```circuit-set\s*(\{.*?\})\s*```", re.S)

# Mirrors main.html's RANGE object exactly — keep these in sync if the sliders' bounds change.
RANGES = {
    "R_ohms": (1, 1000),
    "L_mH": (0.1, 1000),
    "C_uF": (0.1, 1000),
    "f_Hz": (1, 2000),
}


def _clamp(value, lo, hi):
    return max(lo, min(hi, value))


def verify_agent_output(raw_text):
    """
    Looks for a single ```circuit-set fenced JSON block in the model's reply.
    Returns (action: dict | None, issues: list[str]).

    Out-of-range numeric fields are clamped rather than rejected outright;
    non-numeric or unrecognized fields are dropped. A dict is only returned
    when at least one usable field survives — the front end treats a None
    action as "no demo was authorized".
    """
    m = ACTION_FENCE.search(raw_text or "")
    if not m:
        return None, []

    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return None, ["circuit-set block was not valid JSON — dropped."]

    if not isinstance(data, dict):
        return None, ["circuit-set block was not a JSON object — dropped."]

    issues = []
    action = {}
    for key, (lo, hi) in RANGES.items():
        val = data.get(key)
        if val is None:
            continue
        try:
            val = float(val)
        except (TypeError, ValueError):
            issues.append(f"{key} was not numeric — dropped.")
            continue
        clamped = _clamp(val, lo, hi)
        if clamped != val:
            issues.append(f"{key}={val} was out of range — clamped to {clamped}.")
        action[key] = clamped

    mode = data.get("mode")
    if mode in ("AC", "DC"):
        action["mode"] = mode
    elif mode is not None:
        issues.append(f"mode={mode!r} was not AC/DC — dropped.")

    if not action:
        return None, issues or ["circuit-set block had no usable fields — dropped."]
    return action, issues


def build_repair_prompt(issues):
    return (
        "Your last reply's circuit-set block had problems: "
        + "; ".join(issues)
        + ". Reissue the block with valid numeric fields inside range, or omit it."
    )
