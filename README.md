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
A fully local LLM (qwen2.5:7b, self-hosted via Ollama -- no external API,
nothing leaves the machine) reads the circular in overlapping chunks and
extracts every obligation into a strict Pydantic schema: source clause,
verbatim text, required action, evidence, frequency, deadline. Nothing is
accepted unless it validates against the schema. Extraction runs in
thermally-batched passes with progress saved after every chunk, so a long
run can pause and resume without losing work.

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

## Why local inference
Every extraction runs entirely on-device via Ollama -- no circular text and
no extracted obligation ever leaves the machine, and no third-party API sits
between the source PDF and the output. For a tool whose premise is
regulatory compliance and auditability, that's not just a technical choice:
it means every decision the pipeline makes can be traced to a specific,
inspectable set of local model weights, with nothing to trust blindly.

## Demo
Built and tested on real, public SEBI documents:
- SEBI/HO/MIRSD-PoD-1/P/CIR/2024/50 (Investment Advisers, May 21 2024)
- SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/94 (Investment Advisers, Jun 27 2025)

The live SEBI monitor's first run against SEBI's actual site immediately
flagged that a newer Investment Adviser circular (Feb 6, 2026) exists beyond
the one this project's extraction pipeline is built on (Jun 27, 2025) --
proof the monitor checks the live internet, not a canned snapshot, and
correctly surfaces exactly the kind of staleness a compliance team needs to
act on. Logged and hash-chained in `output/audit_log.json` (event index 3,
2026-06-30T05:59:56 UTC).

## Tech stack
- LLM: qwen2.5:7b, self-hosted via Ollama -- local inference, no API key, no
  data leaves the machine
- Validation: Pydantic v2, strict schema enforcement with defensive
  coercion for common small-model output quirks (list-vs-string fields,
  invalid enum values, malformed JSON fragments)
- Verification: rapidfuzz (grounding checks), sentence-transformers
  (semantic diff, on-device)
- PDF parsing: pdfplumber
- Monitoring: requests + BeautifulSoup against SEBI's live site
- Dashboard: Streamlit
- Audit log: SHA-256 hash chain, pure Python

## Project structure

    sebi-regtech/
    ├── src/
    │   ├── config.py            paths and model config
    │   ├── schema.py            Pydantic obligation schema
    │   ├── llm.py               LLM extraction wrapper (Ollama)
    │   ├── ingest.py            PDF to text
    │   ├── semantic_match.py    embedding-based diff matching
    │   └── audit_log.py         hash-chained audit trail
    ├── extract_full.py          extract obligations from the 2025 IA circular
    ├── extract_2024.py          extract obligations from the 2024 IA circular
    ├── extract_broker.py        extract obligations from the 2025 broker circular
    ├── recover_chunks.py        retry chunks that failed during the 2025 run
    ├── recover_chunks_2024.py   retry chunks that failed during the 2024 run
    ├── verify.py                grounding verification + confidence scoring
    ├── benchmark.py             gold-standard precision/recall/F1 benchmark
    ├── dump_section.py          helper to select a section for gold labeling
    ├── diff_engine.py           change-impact engine (exact + semantic match)
    ├── operations.py            compliance register, executable rules, calendar
    ├── sebi_monitor.py          live SEBI circular change monitor
    ├── build_audit_log.py       builds the audit log from pipeline outputs
    ├── dashboard.py             Streamlit dashboard
    ├── demo_extract.py          short, isolated extraction run for demo footage
    ├── test_chunks.py           validates a prompt/model fix before a full re-run
    ├── smoke_test.py            quick end-to-end sanity check of the LLM wrapper
    └── requirements.txt

## Running it
1. Install Ollama and pull the model: `ollama pull qwen2.5:7b`
2. `pip install -r requirements.txt`
3. `python extract_full.py` (2025 circular) and `python extract_2024.py`
   (2024 circular) -- both resume automatically if interrupted partway
4. `python verify.py` to score grounding against the source PDFs
5. `python operations.py` to build the register, executable rules, and
   calendar
6. `python diff_engine.py` to generate the 2024 → 2025 change-impact report
7. `python build_audit_log.py` to log everything to the hash chain
8. `streamlit run dashboard.py`

## Setup

- Dashboard / deployment: `pip install -r requirements.txt`
- Full local pipeline: `pip install -r requirements-pipeline.txt`

Extraction runs entirely on a local Ollama model (qwen2.5:7b) — no API keys, no external calls.
