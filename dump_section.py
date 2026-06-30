import sys
from src.ingest import pdf_to_text
from src.config import IA_CIRCULAR_2025

def main():
    text = pdf_to_text(IA_CIRCULAR_2025)
    if len(sys.argv) >= 3:
        start, end = int(sys.argv[1]), int(sys.argv[2])
        suffix = sys.argv[3] if len(sys.argv) >= 4 else ""
        section = text[start:end]
        out_path = f"data/gold/section_raw{suffix}.txt"
        with open(out_path, "w") as f:
            f.write(section)
        print(f"Saved characters {start}-{end} ({len(section)} chars) to {out_path}")
        print("\n--- preview ---\n")
        print(section[:600])
    else:
        print(f"Total document length: {len(text)} characters\n")
        print("Pass a start and end character range, and optionally a suffix for a second/third section, e.g.:")
        print("  python dump_section.py 30000 36000")
        print("  python dump_section.py 60000 66000 _2\n")
        print("--- first 1500 chars (for orientation) ---\n")
        print(text[:1500])

if __name__ == "__main__":
    main()
