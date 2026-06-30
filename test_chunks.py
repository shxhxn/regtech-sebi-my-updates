"""
Quick validation BEFORE a full re-run.

Re-runs extraction on the specific chunks that timed out last time, and times
each one. Reuses the exact same chunking and prompt as extract_full.py, so it
faithfully reproduces real conditions.

    python test_chunks.py

Read the result:
  - All four finish (well under 300s) and return obligations  -> fix worked,
    go do the full re-run.
  - They finish but are slow (>150s each)                     -> switch to the
    smaller qwen2.5:7b for ~2x speed (see chat).
  - They still time out at 300s                               -> deeper issue;
    send me the output.
"""
import time
from src.ingest import pdf_to_text
from src.schema import ObligationList
from src.llm import extract_structured
from src.config import IA_CIRCULAR_2025, EXTRACTION_MODEL
from extract_full import chunk_text, PROMPT

full_text = pdf_to_text(IA_CIRCULAR_2025)
chunks = chunk_text(full_text)
print(f"Total chunks: {len(chunks)}  |  model: {EXTRACTION_MODEL}\n")

# 1-indexed chunk numbers that timed out in your last run:
to_test = [6, 18, 30, 44]

for n in to_test:
    chunk = chunks[n - 1]
    t = time.time()
    try:
        result = extract_structured(
            PROMPT.format(excerpt=chunk), ObligationList, model=EXTRACTION_MODEL
        )
        print(f"chunk {n}: found {len(result.obligations)} obligations in {time.time() - t:.0f}s")
    except Exception as e:
        print(f"chunk {n}: ERROR ({e}) after {time.time() - t:.0f}s")
