"""Local conversation settings, inspired by cmh95209's feature branch."""
import json
import os
import tempfile
from pathlib import Path

PATH = Path(__file__).resolve().parent / "data" / "conversation_settings.json"
DEFAULTS = {"context_budget": 40000, "voice_retention": 100}


def validate(values):
    if not isinstance(values, dict) or set(values) != set(DEFAULTS):
        raise ValueError("Provide a context budget and voice retention limit.")
    for key, low, high in (("context_budget", 500, 1000000), ("voice_retention", 1, 10000)):
        if type(values[key]) is not int or not low <= values[key] <= high:
            raise ValueError(f"{key} must be an integer between {low} and {high}.")
    return dict(values)


def load():
    try:
        return validate(json.loads(PATH.read_text(encoding="utf-8")))
    except (FileNotFoundError, ValueError):
        return dict(DEFAULTS)


def save(values):
    values = validate(values)
    PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=PATH.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            json.dump(values, output)
        os.replace(temporary, PATH)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return values


def estimate_tokens(text):
    # Rough multilingual estimate: ASCII ~4 characters/token; other scripts ~1.
    return 4 + sum(1 if ord(char) < 128 else 4 for char in text) // 4


def trim_history(messages, budget):
    """Keep a contiguous recent suffix; never truncate the incoming message.

    The newest message may exceed the history budget on its own. Personality,
    timing, output schema, and response tokens are outside this estimate.
    """
    selected = []
    used = 0
    for message in reversed(messages):
        cost = estimate_tokens(message["content"])
        if selected and used + cost > budget:
            break
        selected.append(message)
        used += cost
    selected.reverse()
    # Avoid an orphaned assistant reply at the start of the retained history.
    while len(selected) > 1 and selected[0]["role"] == "assistant":
        selected.pop(0)
    return selected
