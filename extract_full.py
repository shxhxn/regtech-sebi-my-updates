import json
import time
from pathlib import Path
from src.ingest import pdf_to_text
from src.schema import ObligationList
from src.llm import extract_structured
from src.config import IA_CIRCULAR_2025, EXTRACTION_MODEL, OUTPUT

# Process this many chunks per run, then stop so the Mac can cool between batches.
# 53 chunks / 14 is about 4 runs. Lower it if it still runs too hot; raise it to
# finish in fewer runs.
CHUNKS_PER_RUN = 14

PROMPT = """You are a SEBI compliance analyst. Below is an excerpt from the SEBI Master Circular
for Investment Advisers (SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/94, dated 27-Jun-2025).

Extract every distinct regulatory OBLIGATION an Investment Adviser must comply with in this excerpt.
For each obligation capture the exact source clause number and the verbatim text that states it.
Do NOT invent obligations not present in the text. If none are present, return an empty list.

CRITICAL EXTRACTION RULES -- follow these strictly:
1. Extract each distinct requirement as its OWN separate obligation, even if it appears in the
   same paragraph or sentence cluster as another requirement. Do NOT merge multiple requirements
   into a single obligation.
2. Pay special attention to a "shall" sentence immediately followed by a "shall not" sentence in
   the same paragraph (e.g. "IAs shall accept fees via X. IAs shall not accept cash deposits.") --
   these are TWO separate obligations, not one.
3. Each lettered or numbered sub-clause -- (a), (b), (c) or i, ii, iii or step 1, step 2 -- is its
   own separate obligation, even if closely related to the one before it.
4. Check footnotes carefully. If a footnote contains its own requirement or deadline (often marked
   with a superscript number in the text), extract it as a separate obligation with its own
   source_clause noting it is a footnote.
5. When in doubt, extract MORE granular obligations rather than merging them -- under-extraction
   (missing an obligation) is a worse error than over-extraction (a few closely related items).

EXCERPT:
---
{excerpt}
---
"""

def chunk_text(text: str, chunk_size: int = 3000, overlap: int = 200):
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def main():
    OUTPUT.mkdir(exist_ok=True)
    out_path = OUTPUT / "obligations_2025.json"

    # Load existing obligations if resuming
    if out_path.exists():
        with open(out_path) as f:
            existing = json.load(f)
        seen_ids = {ob["obligation_id"] for ob in existing}
        all_obligations = existing
        print(f"Resuming -- {len(all_obligations)} obligations already saved")
    else:
        all_obligations = []
        seen_ids = set()

    # Load progress tracker
    progress_path = OUTPUT / "progress.json"
    if progress_path.exists():
        with open(progress_path) as f:
            start_chunk = json.load(f)["next_chunk"]
        print(f"Resuming from chunk {start_chunk + 1}")
    else:
        start_chunk = 0

    print("Reading PDF...")
    full_text = pdf_to_text(IA_CIRCULAR_2025)
    chunks = chunk_text(full_text)
    print(f"Total chunks: {len(chunks)}, processing from chunk {start_chunk + 1}")
    print(f"This run will process up to {CHUNKS_PER_RUN} chunks, then stop so the Mac can cool.\n")

    processed_this_run = 0
    last_done = start_chunk
    failed_chunks = []

    for i, chunk in enumerate(chunks):
        if i < start_chunk:
            continue
        if processed_this_run >= CHUNKS_PER_RUN:
            break
        processed_this_run += 1

        print(f"Processing chunk {i+1}/{len(chunks)}...", end=" ", flush=True)
        try:
            result = extract_structured(
                PROMPT.format(excerpt=chunk),
                ObligationList,
                model=EXTRACTION_MODEL
            )
            new = 0
            for ob in result.obligations:
                if ob.obligation_id not in seen_ids:
                    seen_ids.add(ob.obligation_id)
                    all_obligations.append(ob.model_dump())
                    new += 1
            print(f"found {len(result.obligations)}, added {new} new")
        except Exception as e:
            print(f"ERROR: {e}")
            failed_chunks.append(i + 1)

        # Save after EVERY chunk (success or error) so resume is always accurate
        with open(out_path, "w") as f:
            json.dump(all_obligations, f, indent=2)
        with open(progress_path, "w") as f:
            json.dump({"next_chunk": i + 1}, f)
        last_done = i + 1

        time.sleep(2)

    remaining = len(chunks) - last_done
    print()
    if remaining > 0:
        print(f"Batch complete -- {last_done}/{len(chunks)} chunks done, {remaining} remaining.")
        print(f"Let the Mac cool for a few minutes, then run  python extract_full.py  again to continue.")
    else:
        print(f"All {len(chunks)} chunks complete!")
    print(f"Total unique obligations so far: {len(all_obligations)}")
    print(f"Saved to: {out_path}")
    if failed_chunks:
        print(f"Chunks that errored and were skipped (can re-run later): {failed_chunks}")

if __name__ == "__main__":
    main()
