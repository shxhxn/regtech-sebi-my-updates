# SEBI Regulatory Compiler
Track 2 -- Agentic RegTech Compliance · SEBI Securities Market TechSprint 2026

## What it does
Turns SEBI master circulars into a structured, source-cited obligation graph,
independently verifies every extraction against the source text, tracks
fulfilment as a working compliance system, detects what changed when a
circular is amended, and watches SEBI's live site for new circulars.

This is not a chatbot. It is a regulatory compiler: unstructured legal text
in, machine-actionable, auditable compliance logic out.

## The problem
SEBI circulars run to 100+ pages. Compliance teams read them manually, and
when a circular is amended, finding what actually changed means comparing
two long PDFs by hand. There is no structured, machine-readable record of
obligations, no automated way to track fulfilment, and no audit trail.

## Four layers

### 1. Extraction
An LLM (Llama 3.3 70B via Groq) reads the circular in overlapping chunks and
extracts every obligation into a strict Pydantic schema: source clause,
verbatim text, required action, evidence, frequency, deadline. Nothing is
accepted unless it validates against the schema.

### 2. Trust & Verification
Every obligation's verbatim text is independently checked against the actual
source PDF using exact, despaced, and fuzzy matching -- deterministic Python,
no AI in the check itself. This produces a measured "percent verifiably
traceable to source" number, plus a confidence score per obligation. A
hand-labeled gold-standard benchmark (precision/recall/F1 against a human
reading of a real section) provides an honest accuracy measurement, not just
a self-consistency check.

### 3. Operations
The obligation graph becomes a working compliance system: a register
tracking fulfilment status and evidence per obligation, a set of executable
rule objects (trigger, required evidence, deadline, breach action) a real
system could enforce, and a compliance calendar grouped by recurrence.

### 4. Automation
- Semantic diff engine: compares two circular versions using local sentence
  embeddings (sentence-transformers, runs on-device) so a reworded obligation
  is still recognised as the same obligation modified, not a fake
  removal+addition.
- Live SEBI monitor: checks SEBI's actual circulars listing for tracked
  intermediary categories and raises an alert when a new circular appears.
- Tamper-evident audit log: a hash chain over every pipeline run. Altering
  any past entry breaks the chain from that point forward.

## Demo
Built and tested on real, public SEBI documents:
- SEBI/HO/MIRSD-PoD-1/P/CIR/2024/50 (Investment Advisers, May 21 2024)
- SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/94 (Investment Advisers, Jun 27 2025)
- SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/90 (Stock Brokers, Jun 17 2025)

The live SEBI monitor independently detected SEBI's Feb 6 2026 Investment
Adviser master circular -- a real regulatory change that occurred during
development, proving the monitor works against the live internet.

## Tech stack
- LLM: Llama 3.3 70B via Groq API (free tier, no training)
- Validation: Pydantic v2, strict schema enforcement
- Verification: rapidfuzz (grounding checks), sentence-transformers (semantic diff)
- PDF parsing: pdfplumber
- Monitoring: requests + BeautifulSoup against SEBI's live site
- Dashboard: Streamlit
- Audit log: SHA-256 hash chain, pure Python

## Project structure

    sebi-regtech/
    ├── src/
    │   ├── config.py            paths and model config
    │   ├── schema.py            Pydantic obligation schema
    │   ├── llm.py               LLM extraction wrapper
    │   ├── ingest.py            PDF to text
    │   ├── semantic_match.py    embedding-based diff matching
    │   └── audit_log.py         hash-chained audit trail
    ├── extract_full.py          extract obligations from 2025 IA circular
    ├── extract_2024.py          extract obligations from 2024 IA circular
    ├── extract_broker.py        extract obligations from 2025 broker circular
    ├── verify.py                grounding verification + confidence scoring
    ├── benchmark.py             gold-standard precision/recall/F1 benchmark
    ├── dump_section.py          helper to select a section for gold labeling
    ├── diff_engine.py           change-impact engine (exact + semantic match)
    ├── operations.py            compliance register, executable rules, calendar
    ├── sebi_monitor.py          live SEBI circular change monitor
    ├── build_audit_log.py       builds the audit log from pipeline outputs
    ├──