import json
import ollama
from src.config import EXTRACTION_MODEL

# 300s (not Ollama's default). At roughly 15 tokens/sec, an obligation-dense
# chunk can legitimately need 100-170s just to write out all its JSON. A
# tighter timeout disproportionately kills the densest chunks -- i.e. the
# ones with the most obligations -- which silently undercounts the final
# total rather than raising an obvious error. Always err high here.
REQUEST_TIMEOUT_SECONDS = 300


def extract_structured(prompt: str, schema_model, model: str = EXTRACTION_MODEL):
    """
    model defaults to config.EXTRACTION_MODEL (single source of truth) instead
    of a hardcoded string. Previously this defaulted to "qwen2.5:14b" -- the
    model that caused unrecoverable hangs during batch runs -- so any call
    site that forgot to pass model= explicitly would silently get the model
    known to be unsafe for sustained work. Now there's one place (config.py)
    that decides which model the whole pipeline uses.
    """
    schema = schema_model.model_json_schema()
    full_prompt = (
        prompt
        + "\n\nRespond ONLY with a valid JSON object that matches this JSON schema "
        + "(no markdown, no commentary, no code fences):\n"
        + json.dumps(schema, indent=2)
    )

    client = ollama.Client(timeout=REQUEST_TIMEOUT_SECONDS)
    response = client.chat(
        model=model,
        messages=[{"role": "user", "content": full_prompt}],
        format="json",
        options={
            "temperature": 0,
            # Ollama defaults to a 4096-token context window. Your prompt
            # (instructions + ~3000-char chunk + full JSON schema) plus the
            # model's JSON output was hitting that ceiling, leaving almost no
            # room to generate -- so dense chunks stalled. 8192 gives headroom.
            "num_ctx": 8192,
        },
    )
    raw = response.message.content
    return schema_model.model_validate_json(raw)
