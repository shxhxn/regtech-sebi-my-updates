from pydantic import BaseModel
from src.llm import extract_structured

class Ping(BaseModel):
    ok: bool
    message: str

result = extract_structured(
    "Return ok=true and a one-line hello message for a SEBI RegTech hackathon project.",
    Ping
)
print("ok:", result.ok)
print("message:", result.message)
