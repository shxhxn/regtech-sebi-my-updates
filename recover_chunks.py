"""
Re-run specific chunks that failed validation earlier, and merge any
recovered obligations straight into obligations_2025.json. Never touches
chunks that already succeeded.

    python recover_chunks.py            # reads output/failed_chunks.json
    python recover_chunks.py 4 11 12    # or name chunks explicitly
"""
import sys
import json
from src.ingest import pdf_to_text
from src.schema import ObligationList
from src.llm import extract_structured
from src.config import IA_CIRCULAR_2025, EXTRACTION_MODEL, OUTPUT
from extract_full import chunk_text, PROMPT


def main():
    out_path = OUTPUT / "obligations_2025.json"
    fc_path = OUTPUT / "failed_chunks.json"

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

    print("Reading PDF...")
    full_text = pdf_to_text(IA_CIRCULAR_2025)
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
