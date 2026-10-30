"""
download_data.py
================
Utility script to download the Formula 1 Ergast Database CSV files
directly and place them in data/raw/.

Primary Source:
  https://raw.githubusercontent.com/rfordatascience/tidytuesday/master/data/2021/2021-09-07/
Fallback Source:
  http://ergast.com/downloads/f1db_csv.zip
"""

import os
import sys
import shutil
import urllib.request
from pathlib import Path

# Fix Windows console UTF-8 output if possible
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCRIPT_DIR   = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

# Reliable online mirror repository for Ergast CSVs
GITHUB_BASE_URL = "https://raw.githubusercontent.com/rfordatascience/tidytuesday/master/data/2021/2021-09-07/"

REQUIRED_FILES = [
    "races.csv",
    "circuits.csv",
    "drivers.csv",
    "constructors.csv",
    "results.csv",
    "status.csv",
    "lap_times.csv",
    "pit_stops.csv",
]

def print_header(msg: str):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")

def print_step(msg: str):
    print(f"  >> {msg}")

def download_file(url: str, dest: Path):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) F1-Race-Intelligence-ETL/1.0"}
    )
    with urllib.request.urlopen(req, timeout=60) as response, open(dest, "wb") as out_file:
        shutil.copyfileobj(response, out_file)

def verify_files(output_dir: Path, required: list):
    print_step("Verifying downloaded files...")
    all_ok = True
    for fname in required:
        fpath = output_dir / fname
        if fpath.exists() and fpath.stat().st_size > 0:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                rows = sum(1 for _ in f) - 1
            size_kb = fpath.stat().st_size // 1024
            print(f"  [OK] {fname:<20} {rows:>8,d} rows ({size_kb:,} KB)")
        else:
            print(f"  [X]  {fname:<20} MISSING or EMPTY")
            all_ok = False
    return all_ok

def main():
    print_header("F1 Race Intelligence - Ergast Dataset Downloader")
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    print_step(f"Target Directory: {RAW_DATA_DIR}")

    existing = [f for f in REQUIRED_FILES if (RAW_DATA_DIR / f).exists() and (RAW_DATA_DIR / f).stat().st_size > 0]
    if len(existing) == len(REQUIRED_FILES):
        print_step("All required CSV files already exist.")
        verify_files(RAW_DATA_DIR, REQUIRED_FILES)
        print_header("Data ready - Run: python scripts/preprocess_f1_data.py")
        return

    print_header("Downloading 8 CSV Datasets from Repository")
    for fname in REQUIRED_FILES:
        target = RAW_DATA_DIR / fname
        if target.exists() and target.stat().st_size > 0:
            print(f"  [SKIPPED] {fname} already exists.")
            continue
        url = GITHUB_BASE_URL + fname
        print(f"  [DOWNLOADING] {fname} ...", end="", flush=True)
        try:
            download_file(url, target)
            size_kb = target.stat().st_size // 1024
            print(f" Done ({size_kb:,} KB)")
        except Exception as e:
            print(f" FAILED: {e}")

    print_header("Verification & Summary")
    if verify_files(RAW_DATA_DIR, REQUIRED_FILES):
        print_header("ETL Source Data Ready!")
        print("  Next step:")
        print("  python scripts/preprocess_f1_data.py\n")
    else:
        print_header("Incomplete download - Please check your network connection.")
        sys.exit(1)

if __name__ == "__main__":
    main()
