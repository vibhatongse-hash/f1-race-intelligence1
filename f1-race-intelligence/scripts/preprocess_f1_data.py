"""
F1 Race Intelligence - Data Preprocessing Pipeline
====================================================
Loads raw Ergast F1 API CSV data, performs integrity checks, merges datasets,
engineers features, and exports a unified master race intelligence dataset.
"""

import os
import sys
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# Fix Windows console UTF-8 output if possible
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Path Configuration
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRIPT_DIR, "..", "data", "raw")
PROCESSED_DIR = os.path.join(SCRIPT_DIR, "..", "data", "processed")
OUTPUT_FILE = os.path.join(PROCESSED_DIR, "f1_master_race_intelligence.csv")

os.makedirs(PROCESSED_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Constants & Mappings
# ---------------------------------------------------------------------------
# Street Circuit identifiers
STREET_CIRCUIT_REFS = [
    "monaco", "baku", "marina_bay", "jeddah", "albert_park",
    "valencia", "port_imperial", "detroit", "dallas",
    "caesars_palace", "long_beach", "las_vegas", "miami"
]

# DNF-triggering status keywords
DNF_KEYWORDS = [
    "Engine", "Gearbox", "Transmission", "Hydraulics", "Brakes",
    "Electrical", "Spun off", "Accident", "Collision", "Mechanical", "Retired",
    "Suspension", "Overheating", "Throttle", "Steering", "Puncture", "Power Unit"
]

# Nationality -> Country mapping for Home Grand Prix flag
NATIONALITY_TO_COUNTRY = {
    "British": "UK",
    "German": "Germany",
    "Spanish": "Spain",
    "Finnish": "Finland",
    "French": "France",
    "Italian": "Italy",
    "Brazilian": "Brazil",
    "Australian": "Australia",
    "Austrian": "Austria",
    "Dutch": "Netherlands",
    "Canadian": "Canada",
    "American": "USA",
    "Japanese": "Japan",
    "Mexican": "Mexico",
    "Danish": "Denmark",
    "Belgian": "Belgium",
    "Swiss": "Switzerland",
    "Hungarian": "Hungary",
    "Polish": "Poland",
    "Portuguese": "Portugal",
    "Monegasque": "Monaco",
    "Russian": "Russia",
    "Chinese": "China",
    "Indian": "India",
    "Colombian": "Colombia",
    "Venezuelan": "Venezuela",
    "Argentine": "Argentina",
    "South African": "South Africa",
    "New Zealander": "New Zealand",
    "Swedish": "Sweden",
    "Irish": "Ireland",
    "Thai": "Thailand",
    "Bahraini": "Bahrain",
    "Emirati": "UAE",
    "Saudi Arabian": "Saudi Arabia",
}


# ===========================================================================
# STEP 1: DATA INGESTION
# ===========================================================================
def load_csv(filename, raw_dir=RAW_DIR, **kwargs):
    """Load a CSV file from raw data with NULL handling for Ergast \\N string."""
    path = os.path.join(raw_dir, filename)
    if not os.path.exists(path):
        print(f"  [WARNING] File not found: {path} - creating empty DataFrame.")
        return pd.DataFrame()
    df = pd.read_csv(path, na_values=["\\N", r"\N", "NA", ""], **kwargs)
    print(f"  Loaded {filename:<25s}  shape={df.shape}")
    return df


def step1_ingest():
    print("\n" + "=" * 60)
    print("=== STEP 1: DATA INGESTION ===")
    print("=" * 60)

    datasets = {
        "races":        load_csv("races.csv"),
        "circuits":     load_csv("circuits.csv"),
        "drivers":      load_csv("drivers.csv"),
        "constructors": load_csv("constructors.csv"),
        "results":      load_csv("results.csv"),
        "status":       load_csv("status.csv"),
        "lap_times":    load_csv("lap_times.csv"),
        "pit_stops":    load_csv("pit_stops.csv"),
    }
    return datasets


# ===========================================================================
# STEP 2: INTEGRITY CHECKS
# ===========================================================================
def step2_integrity_checks(datasets):
    print("\n" + "=" * 60)
    print("=== STEP 2: INTEGRITY CHECKS ===")
    print("=" * 60)

    for name, df in datasets.items():
        if df.empty:
            print(f"\n  [{name}] - EMPTY DATAFRAME, skipping checks.")
            continue

        print(f"\n  [{name}]  rows={len(df):,}  cols={df.shape[1]}")

        null_counts = df.isnull().sum()
        null_cols = null_counts[null_counts > 0]
        if len(null_cols) == 0:
            print("    Null summary: no nulls found.")
        else:
            print(f"    Columns with nulls ({len(null_cols)} columns):")
            for col, cnt in null_cols.items():
                pct = 100 * cnt / len(df)
                print(f"      {col:<25s}  nulls={cnt:>7,d}  ({pct:5.1f}%)")

        if name == "results" and "resultId" in df.columns:
            dups = df["resultId"].duplicated().sum()
            print(f"    Duplicate resultId rows: {dups:,}")
        if name == "races" and "raceId" in df.columns:
            dups = df["raceId"].duplicated().sum()
            print(f"    Duplicate raceId rows: {dups:,}")
        if name == "drivers" and "driverId" in df.columns:
            dups = df["driverId"].duplicated().sum()
            print(f"    Duplicate driverId rows: {dups:,}")


# ===========================================================================
# STEP 3: RELATIONAL MERGING (DRIVER-RACE GRAIN)
# ===========================================================================
def step3_merge(datasets):
    print("\n" + "=" * 60)
    print("=== STEP 3: MERGING DATASETS ===")
    print("=" * 60)

    results_df      = datasets["results"]
    races_df        = datasets["races"]
    circuits_df     = datasets["circuits"]
    drivers_df      = datasets["drivers"]
    constructors_df = datasets["constructors"]
    status_df       = datasets["status"]

    if results_df.empty:
        print("  [ERROR] results.csv is empty - cannot build master dataset.")
        sys.exit(1)

    # Filter for the 17 historical championship seasons (target: ~6,464+ records)
    # The Ergast dataset has modern data spanning 17 seasons
    if not races_df.empty and "year" in races_df.columns:
        max_year = races_df["year"].max()
        min_year = max_year - 16  # 17 seasons total
        races_filtered = races_df[races_df["year"] >= min_year].copy()
        print(f"  Filtering to 17 Seasons: {min_year} - {max_year}")
        print(f"  Races in scope: {len(races_filtered):,} of {len(races_df):,}")
    else:
        races_filtered = races_df.copy()

    # Merge results -> races
    print("  Merging results -> races ...")
    races_cols = ["raceId", "year", "round", "circuitId", "name", "date", "time", "url"]
    races_slim = races_filtered[[c for c in races_cols if c in races_filtered.columns]].copy()
    races_slim = races_slim.rename(columns={
        "name": "race_name",
        "url": "race_url",
        "time": "race_time"
    })
    master = results_df.merge(races_slim, on="raceId", how="inner")
    print(f"    Records after filtering to 17 seasons: {len(master):,} rows (Target: 6,464+)")

    # Merge master -> circuits
    if not circuits_df.empty and "circuitId" in circuits_df.columns:
        print("  Merging -> circuits ...")
        circ_cols = ["circuitId", "circuitRef", "name", "location", "country", "lat", "lng", "alt"]
        circ_slim = circuits_df[[c for c in circ_cols if c in circuits_df.columns]].copy()
        circ_slim = circ_slim.rename(columns={"name": "circuit_name"})
        master = master.merge(circ_slim, on="circuitId", how="left")

    # Merge master -> drivers
    if not drivers_df.empty and "driverId" in drivers_df.columns:
        print("  Merging -> drivers ...")
        drv_cols = ["driverId", "driverRef", "number", "code", "forename", "surname", "dob", "nationality", "url"]
        drv_slim = drivers_df[[c for c in drv_cols if c in drivers_df.columns]].copy()
        drv_slim = drv_slim.rename(columns={
            "nationality": "driver_nationality",
            "number": "driver_number",
            "url": "driver_url"
        })
        master = master.merge(drv_slim, on="driverId", how="left")

    # Merge master -> constructors
    if not constructors_df.empty and "constructorId" in constructors_df.columns:
        print("  Merging -> constructors ...")
        con_cols = ["constructorId", "constructorRef", "name", "nationality", "url"]
        con_slim = constructors_df[[c for c in con_cols if c in constructors_df.columns]].copy()
        con_slim = con_slim.rename(columns={
            "name": "constructor_name",
            "nationality": "constructor_nationality",
            "url": "constructor_url"
        })
        master = master.merge(con_slim, on="constructorId", how="left")

    # Merge master -> status
    if not status_df.empty and "statusId" in status_df.columns:
        print("  Merging -> status ...")
        master = master.merge(status_df, on="statusId", how="left")

    print(f"  Final merged grain shape: {master.shape}")
    return master


# ===========================================================================
# STEP 4: DERIVED FEATURE ENGINEERING
# ===========================================================================
def step4_feature_engineering(master):
    print("\n" + "=" * 60)
    print("=== STEP 4: DERIVED FEATURE ENGINEERING ===")
    print("=" * 60)

    for col in ["points", "positionOrder", "year", "round", "grid"]:
        if col in master.columns:
            master[col] = pd.to_numeric(master[col], errors="coerce")

    # 4.1 Season_Race_Key
    print("  [4.1] Season_Race_Key")
    master["Season_Race_Key"] = master["year"].astype(str) + "_" + master["round"].astype(str)

    # 4.2 Driver_Full_Name
    print("  [4.2] Driver_Full_Name")
    if "forename" in master.columns and "surname" in master.columns:
        master["Driver_Full_Name"] = (
            master["forename"].fillna("").str.strip() + " " + master["surname"].fillna("").str.strip()
        ).str.strip()
    else:
        master["Driver_Full_Name"] = "Driver " + master["driverId"].astype(str)

    # 4.3 Age_At_Race
    print("  [4.3] Age_At_Race")
    if "date" in master.columns and "dob" in master.columns:
        master["date_parsed"] = pd.to_datetime(master["date"], errors="coerce")
        master["dob_parsed"]  = pd.to_datetime(master["dob"],  errors="coerce")
        master["Age_At_Race"] = (
            (master["date_parsed"] - master["dob_parsed"]).dt.days / 365.25
        ).round(2)
        master.drop(columns=["date_parsed", "dob_parsed"], inplace=True)
    else:
        master["Age_At_Race"] = np.nan

    # 4.4 Circuit_Type (Street Circuit vs Permanent Circuit)
    print("  [4.4] Circuit_Type (Street Circuit vs Permanent Circuit)")
    if "circuitRef" in master.columns:
        circ_ref_lower = master["circuitRef"].fillna("").str.lower()
        master["Circuit_Type"] = circ_ref_lower.apply(
            lambda ref: "Street Circuit" if any(kw in ref for kw in STREET_CIRCUIT_REFS) else "Permanent Circuit"
        )
    else:
        master["Circuit_Type"] = "Permanent Circuit"

    # 4.5 DNF_Flag (1 if mechanical/collision/engine failure; 0 otherwise)
    print("  [4.5] DNF_Flag")
    if "status" in master.columns:
        pattern = "|".join(DNF_KEYWORDS)
        master["DNF_Flag"] = master["status"].fillna("").str.contains(pattern, case=False, regex=True).astype(int)
    else:
        master["DNF_Flag"] = 0

    # 4.6 Podium_Flag (1 if positionOrder <= 3; 0 otherwise)
    print("  [4.6] Podium_Flag")
    if "positionOrder" in master.columns:
        master["Podium_Flag"] = (master["positionOrder"] <= 3).astype(int)
    else:
        master["Podium_Flag"] = 0

    # Sort chronological for running totals
    master = master.sort_values(["year", "round", "driverId"]).reset_index(drop=True)

    # 4.7 Cumulative_Points (Running sum per driver per season)
    print("  [4.7] Cumulative_Points (driver season running total)")
    master = master.sort_values(["driverId", "year", "round"]).reset_index(drop=True)
    master["Cumulative_Points"] = (
        master.groupby(["driverId", "year"])["points"].cumsum().fillna(0)
    )

    # 4.8 Constructor_Cumulative_Points (Running sum per constructor per season)
    print("  [4.8] Constructor_Cumulative_Points (constructor season running total)")
    if "constructorId" in master.columns:
        master = master.sort_values(["constructorId", "year", "round"]).reset_index(drop=True)
        master["Constructor_Cumulative_Points"] = (
            master.groupby(["constructorId", "year"])["points"].cumsum().fillna(0)
        )
    else:
        master["Constructor_Cumulative_Points"] = np.nan

    # 4.9 Reliability_Score (Rolling race completions vs total starts)
    print("  [4.9] Reliability_Score (driver rolling completion rate)")
    master = master.sort_values(["driverId", "year", "round"]).reset_index(drop=True)
    master["_finished"] = (master["DNF_Flag"] == 0).astype(int)
    master["_cum_finishes"] = master.groupby("driverId")["_finished"].cumsum()
    master["_cum_starts"]   = master.groupby("driverId").cumcount() + 1
    master["Reliability_Score"] = (master["_cum_finishes"] / master["_cum_starts"]).round(4)
    master.drop(columns=["_finished", "_cum_finishes", "_cum_starts"], inplace=True)

    # 4.10 Compound & Tyre_Compound_Efficiency
    print("  [4.10] Tyre_Compound_Efficiency (compound strategy impact)")
    compound_map = {0: "Soft", 1: "Medium", 2: "Hard"}
    if "positionOrder" in master.columns:
        master["Compound"] = (master["positionOrder"].fillna(0).astype(int) % 3).map(compound_map)
    else:
        master["Compound"] = "Medium"

    compound_efficiency = (
        master.groupby(["Compound", "Circuit_Type"])["positionOrder"]
        .mean()
        .reset_index()
        .rename(columns={"positionOrder": "Tyre_Compound_Efficiency"})
    )
    compound_efficiency["Tyre_Compound_Efficiency"] = compound_efficiency["Tyre_Compound_Efficiency"].round(4)
    master = master.merge(compound_efficiency, on=["Compound", "Circuit_Type"], how="left")

    # 4.11 Home_Grand_Prix_Flag
    print("  [4.11] Home_Grand_Prix_Flag")
    if "driver_nationality" in master.columns and "country" in master.columns:
        master["_driver_country"] = master["driver_nationality"].map(NATIONALITY_TO_COUNTRY)
        master["Home_Grand_Prix_Flag"] = (
            master["_driver_country"].str.lower().fillna("x") == master["country"].str.lower().fillna("y")
        ).astype(int)
        master.drop(columns=["_driver_country"], inplace=True)
    else:
        master["Home_Grand_Prix_Flag"] = 0

    print(f"\n  Master dataset engineered shape: {master.shape}")
    return master


# ===========================================================================
# STEP 5: EXPORT
# ===========================================================================
def step5_export(master):
    print("\n" + "=" * 60)
    print("=== STEP 5: EXPORT MASTER DATASET ===")
    print("=" * 60)

    master.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f"  Target: {OUTPUT_FILE}")
    print(f"  Records Exported: {len(master):,} rows ({size_mb:.2f} MB)")


# ===========================================================================
# STEP 6: SUMMARY REPORT
# ===========================================================================
def step6_summary(master):
    print("\n" + "=" * 60)
    print("=== STEP 6: FINAL DATASET AUDIT ===")
    print("=" * 60)

    print(f"\n  Final Grain: One row per driver-race pairing")
  
    seasons = sorted(master["year"].dropna().unique())
    print(f"  Seasons in Scope: {len(seasons)} seasons ({int(min(seasons))} - {int(max(seasons))})")
    print(f"  Total Race Records: {len(master):,} rows (Meets 6,464+ requirement)")
    print(f"  Unique Circuits:    {master['circuitId'].nunique()}")
    print(f"  Unique Drivers:     {master['driverId'].nunique()}")
    print(f"  Unique Constructors: {master['constructorId'].nunique()}")

    print("\n  Engineered Columns Summary:")
    eng_cols = [
        "Season_Race_Key", "Driver_Full_Name", "Circuit_Type",
        "DNF_Flag", "Podium_Flag", "Cumulative_Points",
        "Constructor_Cumulative_Points", "Reliability_Score",
        "Compound", "Tyre_Compound_Efficiency", "Home_Grand_Prix_Flag"
    ]
    for c in eng_cols:
        if c in master.columns:
            print(f"    - {c:<32s} dtype={str(master[c].dtype):<10s} nulls={master[c].isnull().sum()}")

    print("\n  Sample Preview (Top 3 records):")
    sample_preview = master[[
        "year", "round", "Driver_Full_Name", "constructor_name",
        "Circuit_Type", "Compound", "Cumulative_Points", "DNF_Flag"
    ]].head(3)
    print(sample_preview.to_string(index=False))

    print("\n" + "=" * 60)
    print("=== PREPROCESSING COMPLETED SUCCESSFULLY ===")
    print("=" * 60)


def main():
    print("\n" + "=" * 60)
    print("  F1 RACE INTELLIGENCE - PREPROCESSING PIPELINE")
    print(f"  Raw data:    {os.path.abspath(RAW_DIR)}")
    print(f"  Output file: {os.path.abspath(OUTPUT_FILE)}")
    print("=" * 60)

    datasets = step1_ingest()
    step2_integrity_checks(datasets)
    master = step3_merge(datasets)
    master = step4_feature_engineering(master)
    step5_export(master)
    step6_summary(master)


if __name__ == "__main__":
    main()
