from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
OUTPUT = ROOT / "output"

IA_CIRCULAR_2025 = str(DATA_RAW / "ia_master_circular_2025.pdf")
IA_CIRCULAR_2024 = str(DATA_RAW / "ia_master_circular_2024.pdf")

EXTRACTION_MODEL = "qwen2.5:7b"
