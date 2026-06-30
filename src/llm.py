import json
import ollama

# Raised from 90s. At ~15 tokens/sec, obligation-dense chunks legitimately need
# 100-170s just to write out all their JSON. The 90s cap was killing exactly the
# chunks that matter most (the ones with many obligations) -- that is why the
# last run produced 38 instead of ~198.
REQUEST_TIMEOUT_SECONDS = 300


def extract_structured(prompt: str, schema_model, model: str = "qwen2.5:14b"):
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
