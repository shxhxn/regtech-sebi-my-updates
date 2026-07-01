"""
Re-run specific 2024-circular chunks that failed validation, and merge any
recovered obligations into obligations_2024.json. Mirrors recover_chunks.py
but points at the 2024 source PDF and its own separate failure list.

    python recover_chunks_2024.py       # reads output/failed_chunks_2024.json
    python recover_chunks_2024.py 7 19  # or name chunks explicitly
"""
import sys
import json
from src.ingest import pdf_to_text
from src.schema import ObligationList
from src.llm import extract_structured
from src.config import IA_CIRCULAR_2024, EXTRACTION_MODEL, OUTPUT
from extract_2024 import chunk_text, PROMPT


def main():
    out_path = OUTPUT / "obligations_2024.json"
    fc_path = OUTPUT / "failed_chunks_2024.json"

    if len(sys.argv) > 1:
        targets = [int(x) for x in sys.argv[1:]]
    elif fc_path.exists():
        targets = json.load(open(fc_path))
    else:
        print("No failed chunks recorded, and none given on the command line. Nothing to do.")
        return

    if not targets:
        print("No failed chunks to recover.")
        return

    if out_path.exists():
        all_obligations = json.load(open(out_path))
        seen_ids = {ob["obligation_id"] for ob in all_obligations}
    else:
        all_obligations = []
        seen_ids = set()

    print("Reading 2024 PDF...")
    full_text = pdf_to_text(IA_CIRCULAR_2024)
    chunks = chunk_text(full_text)

    print(f"Recovering {len(targets)} chunk(s): {targets}\n")
    still_failed = []

    for n in targets:
        chunk = chunks[n - 1]
        print(f"Chunk {n}/{len(chunks)}...", end=" ", flush=True)
        try:
            result = extract_structured(PROMPT.format(excerpt=chunk), ObligationList, model=EXTRACTION_MODEL)
            new = 0
            for ob in result.obligations:
                if ob.obligation_id not in seen_ids:
                    seen_ids.add(ob.obligation_id)
                    all_obligations.append(ob.model_dump())
                    new += 1
            print(f"found {len(result.obligations)}, added {new} new")
        except Exception as e:
            print(f"still failing: {e}")
            still_failed.append(n)

    with open(out_path, "w") as f:
        json.dump(all_obligations, f, indent=2)
    with open(fc_path, "w") as f:
        json.dump(still_failed, f)

    print(f"\nTotal unique obligations now: {len(all_obligations)}")
    if still_failed:
        print(f"Still failing after recovery: {still_failed} -- send me the error.")
    else:
        print("All previously-failed chunks recovered.")


if __name__ == "__main__":
    main()
