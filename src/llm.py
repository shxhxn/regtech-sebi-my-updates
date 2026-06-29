import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_structured(prompt: str, schema_model, model: str = "llama-3.3-70b-versatile"):
    schema = schema_model.model_json_schema()
    full_prompt = (
        prompt
        + "\n\nRespond ONLY with a valid JSON object that matches this JSON schema "
        + "(no markdown, no commentary, no code fences):\n"
        + json.dumps(schema, indent=2)
    )
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": full_prompt}],
        response_format={"type": "json_object"},
        temperature=0,
    )
    raw = response.choices[0].message.content
    return schema_model.model_validate_json(raw)
