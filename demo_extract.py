"""
Short, isolated extraction run for demo footage. Runs the EXACT same
prompt/schema/model as the real pipeline -- nothing faked or simplified --
but on just a chunk or two, so it finishes inside a tight demo window.

Defaults to chunk 13 of the 2025 circular: confirmed in the real full run to
find 8 obligations cleanly (no errors), a solid non-trivial result without
the ~164s generation time a denser chunk like chunk 43 (20 obligations)
costs -- output length scales with obligation count, so density trades
directly against demo time. Override the chunk if you want more drama and
don't mind the wait, or less and want it faster.

Writes to its own file (output/demo_extraction.json) and never touches
obligations_2025.json, obligations_2024.json, or either progress tracker --
safe to re-run as many times as you want while rehearsing, zero risk to
your real submission data.

    python demo_extract.py                # chunk 13 of the 2025 circular (8 found, moderate speed)
    python demo_extract.py 2025 44 1       # chunk 44 (5 found, likely faster)
    python demo_extract.py 2025 43 1       # chunk 43 (20 found, ~164s -- most dramatic, slowest)
"""
import sys
import json
import time
from src.ingest import pdf_to_text
from src.schema import ObligationList
from src.llm import extract_structured
from src.config import IA_CIRCULAR_2025, IA_CIRCULAR_2024, EXTRACTION_MODEL, OUTPUT
from extract_full import chunk_text, PROMPT

DEFAULT_START = 13
DEFAULT_COUNT = 1


def main():
    year = sys.argv[1] if len(sys.argv) > 1 else "2025"
    start = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_START
    n_chunks = int(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_COUNT
    pdf_path = IA_CIRCULAR_2025 if year == "2025" else IA_CIRCULAR_2024

    print(f"DEMO RUN -- {year} circular, chunk {start} to {start + n_chunks - 1}.")
    print("Isolated from your real pipeline output -- safe to re-run anytime.\n")
    print("Reading PDF...")
    full_text = pdf_to_text(pdf_path)
    all_chunks = chunk_text(full_text)
    chunks = all_chunks[start - 1: start - 1 + n_chunks]

    all_obligations = []
    for idx, chunk in enumerate(chunks):
        chunk_num = start + idx
        print(f"Processing chunk {chunk_num}/{len(all_chunks)}...", end=" ", flush=True)
        t = time.time()
        try:
            result = extract_structured(PROMPT.format(excerpt=chunk), ObligationList, model=EXTRACTION_MODEL)
            for ob in result.obligations:
                all_obligations.append(ob.model_dump())
            print(f"found {len(result.obligations)} obligations   ({time.time()-t:.0f}s)")
        except Exception as e:
            print(f"ERROR: {e}   ({time.time()-t:.0f}s)")

    out_path = OUTPUT / "demo_extraction.json"
    with open(out_path, "w") as f:
        json.dump(all_obligations, f, indent=2)
    print(f"\nDemo run complete. {len(all_obligations)} obligations extracted.")
    print(f"Saved to: {out_path}")

if __name__ == "__main__":
    main()
