from src.ingest import pdf_to_text
from src.schema import ObligationList
from src.llm import extract_structured
from src.config import IA_CIRCULAR_2025, EXTRACTION_MODEL

PROMPT = """You are a SEBI compliance analyst. Below is an excerpt from the SEBI Master Circular
for Investment Advisers (SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/94, dated 27-Jun-2025).

Extract every distinct regulatory OBLIGATION an Investment Adviser must comply with in this excerpt.
For each, capture the exact source clause number and the verbatim text that states it.
Do NOT invent obligations not present in the text. If none are present, return an empty list.

EXCERPT:
---
{excerpt}
---
"""

def main():
    full_text = pdf_to_text(IA_CIRCULAR_2025)
    excerpt = full_text[6000:10000]
    result = extract_structured(PROMPT.format(excerpt=excerpt), ObligationList, model=EXTRACTION_MODEL)

    print(f"\nExtracted {len(result.obligations)} obligation(s):\n")
    for ob in result.obligations:
        print("-" * 64)
        print(f"[{ob.obligation_id}] {ob.title}")
        print(f"  Action   : {ob.required_action}")
        print(f"  Evidence : {ob.evidence}")
        print(f"  When     : {ob.frequency.value}   Deadline: {ob.deadline}")
        print(f"  Source   : {ob.source_clause}")

if __name__ == "__main__":
    main()
