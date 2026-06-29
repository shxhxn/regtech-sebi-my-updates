# SEBI Regulatory Compiler
**Track 2 — Agentic RegTech Compliance · SEBI Securities Market TechSprint 2026**

## What it does
Turns SEBI master circulars into a structured, source-cited obligation graph — and automatically detects what changed when a circular is amended.

**The problem:** SEBI circulars are dense legal PDFs. Compliance officers read them manually, miss changes, and have no machine-readable record of what they're obligated to do.

**The solution:** Drop in a circular, get back every obligation structured and cited down to the exact clause and verbatim text. Drop in an amended version, get a precise change-impact report showing exactly what is new, modified, or removed.

## Key features
- **Obligation extraction** — LLM extracts every obligation into a structured schema with source clause, verbatim text, required evidence, frequency, and deadline
- **Source-grounded and auditable** — every obligation points back to the exact line in the circular
- **Change-impact engine** — diffs two versions of a circular and auto-generates a change report
- **Gap detection** — flags obligations with missing evidence or undefined deadlines
- **Dashboard** — searchable, filterable UI built on Streamlit

## Demo
Built on the SEBI Investment Adviser master circular pair:
- SEBI/HO/MIRSD-PoD-1/P/CIR/2024/50 dated May 21, 2024
- SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/94 dated June 27, 2025

157+ obligations extracted from the 2025 circular. Change-impact report auto-generated from the 2024 vs 2025 diff.

## Tech stack
- **LLM** — Llama 3.3 70B via Groq API
- **Validation** — Pydantic with structured output and schema enforcement
- **PDF parsing** — pdfplumber
- **Dashboard** — Streamlit
- **Language** — Python 3.12

## Project structure

    sebi-regtech/
    ├── src/
    │   ├── config.py       paths and model config
    │   ├── schema.py       Pydantic obligation schema
    │   ├── llm.py          LLM extraction wrapper
    │   └── ingest.py       PDF to text
    ├── extract_full.py     extract obligations from 2025 circular
    ├── extract_2024.py     extract obligations from 2024 circular
    ├── diff_engine.py      change-impact engine
    ├── dashboard.py        Streamlit UI
    ├── data/raw/           SEBI PDFs (not committed)
    └── output/             extracted JSON graphs (not committed)

## How to run

Install dependencies

    pip install -r requirements.txt

Add your Groq API key to .env

    GROQ_API_KEY=your_key_here

Extract obligations from 2025 circular

    python extract_full.py

Extract obligations from 2024 circular

    python extract_2024.py

Generate change-impact report

    python diff_engine.py

Launch dashboard

    streamlit run dashboard.py

## Evaluation alignment

| SEBI Criterion | How this addresses it |
|---|---|
| Market Impact | Reduces manual compliance work for all SEBI-registered IAs |
| Technology Stack | LLM plus structured output plus Pydantic validation plus agentic pipeline |
| Feasibility | Runs on public SEBI documents, no proprietary data needed |
| Scalability | Schema generalises to any intermediary type or circular |
| SEBI Mandate | Directly improves regulatory compliance and supervision |