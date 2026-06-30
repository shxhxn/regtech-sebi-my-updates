"""
Same pipeline as extract_full.py, pointed at the Stock Broker master circular.
Proves the schema and pipeline generalize across intermediary categories --
not just a one-off built for Investment Advisers.
"""
import json
import time
from pathlib import Path
from src.ingest import pdf_to_text
from src.schema import ObligationList
from src.llm import extract_structured
from src.config import OUTPUT, EXTRACTION_MODEL

SB_CIRCULAR_2025 = str(Path(__file__).resolve().parent / "data" / "raw" / "sb_master_circular_2025.pdf")

PROMPT = """You are a SEBI compliance analyst. Below is an excerpt from the SEBI Master Circular
for Stock Brokers (SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/90, dated 17-Jun-2025).

Extract every distinct regulatory OBLIGATION a Stock Broker must comply with in this excerpt.
For each obligation capture the exact source clause number and the verbatim text that states it.
Do NOT invent obligations not present in the text. If none are present, return an empty list.

CRITICAL EXTRACTION RULES -- follow these strictly:
1. Extract each distinct requirement as its OWN separate obligation, even if it appears in the
   same paragraph or sentence cluster as another requirement. Do NOT merge multiple requirements
   into a single obligation.
2. Pay special attention to a "shall" sentence immediately followed by a "shall not" sentence in
   the same paragraph -- these are TWO separate obligations, not one.
3. Each lettered or numbered sub-clause -- (a), (b), (c) or i, ii, iii -- is its own separate
   obligation, even if closely related to the one before it.
4. Check footnotes carefully for their own requirements or deadlines.
5. When in doubt, extract MORE granular obligations rather than merging them.

EXCERPT:
---
{excerpt}
---
"""

def chunk_text(text, chunk_size=3000, overlap=200):
    chunks, start = [], 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def main():
    OUTPUT.mkdir(exist_ok=True)
    out_path = OUTPUT / "obligations_broker_2025.json"
    progress_path = OUTPUT / "progress_broker.json"

    if out_path.exists():
        all_obligations = json.load(open(out_path))
        seen_ids = {o["obligation_id"] for o in all_obligations}
        print(f"Resuming -- {len(all_obligations)} already saved")
    else:
        all_obligations, seen_ids = [], set()

    start_chunk = json.load(open(progress_path))["next_chunk"] if progress_path.exists() else 0

    print("Reading Stock Broker circular PDF...")
    full_text = pdf_to_text(SB_CIRCULAR_2025)
    chunks = chunk_text(full_text)
    print(f"Total chunks: {len(chunks)}, processing from chunk {start_chunk + 1}")

    for i, chunk in enumerate(chunks):
        if i < start_chunk:
            continue
        print(f"Processing chunk {i+1}/{len(chunks)}...", end=" ", flush=True)
        try:
            result = extract_structured(PROMPT.format(excerpt=chunk), ObligationList, model=EXTRACTION_MODEL)
            new = 0
            for ob in result.obligations:
                if ob.obligation_id not in seen_ids:
                    seen_ids.add(ob.obligation_id)
                    all_obligations.append(ob.model_dump())
                    new += 1
            print(f"found {len(result.obligations)}, added {new} new")
            json.dump(all_obligations, open(out_path, "w"), indent=2)
            json.dump({"next_chunk": i + 1}, open(progress_path, "w"))
        except Exception as e:
            if "429" in str(e):
                print("RATE LIMIT hit -- stopping. Run again later to resume.")
                break
            print(f"ERROR: {e}")
        time.sleep(2)

    print(f"\nDone. Total unique obligations: {len(all_obligations)}")
    print(f"Saved to: {out_path}")

if __name__ == "__main__":
    main()
