# 🏎️ Formula 1 Race Intelligence Dashboard & Story

> **Production-Grade Tableau BI Project** | 6,464+ Race Records | 17 Seasons (2008–2024) | 3 Personas

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Tableau](https://img.shields.io/badge/Tableau-2024.x-orange.svg)](https://tableau.com)
[![Data](https://img.shields.io/badge/Source-Ergast%20Motor%20Racing%20DB-red.svg)](http://ergast.com/mrd/)
[![Records](https://img.shields.io/badge/Records-6%2C464%2B-green.svg)]()

---

## 📌 Project Overview

This project transforms raw Formula 1 historical race data into an interactive, persona-driven Tableau intelligence system. Built on the **Ergast Motor Racing Database**, it covers 17 seasons of F1 racing data, serving three distinct business user personas:

| Persona | Role | Dashboard |
|---------|------|-----------|
| **Mr. Arnold (Rajan)** | F1 Team Performance Strategist | Dashboard 1: Performance & Strategy |
| **Ms. Lisa (Divya)** | Motorsport Broadcast Analyst | Dashboard 2: Media & Fan Insights |
| **Mr. Gilchrist (Arvind)** | F1 Technical Regulation Analyst | Dashboard 3: Reliability & Safety |

---

## 🗂️ Repository Structure

```
f1-race-intelligence/
├── data/
│   ├── raw/                        # Raw Ergast CSV dumps
│   │   ├── races.csv
│   │   ├── circuits.csv
│   │   ├── drivers.csv
│   │   ├── constructors.csv
│   │   ├── results.csv
│   │   ├── status.csv
│   │   ├── lap_times.csv
│   │   └── pit_stops.csv
│   └── processed/
│       └── f1_master_race_intelligence.csv   # Master analytical base table
├── scripts/
│   ├── preprocess_f1_data.py       # Main ETL pipeline
│   └── download_data.py            # Ergast API data downloader
├── tableau_model/
│   └── tableau_model_blueprint.md  # Calculated fields & data model docs
├── docs/
│   └── project_documentation.md   # Full formal documentation
├── video_script/
│   └── demo_script.md              # 5-minute demo video script
└── README.md
```

---

## ⚡ Quick Start

### Step 1: Get the Raw Data

**Option A — Download from Ergast API (Recommended):**
```bash
cd f1-race-intelligence
python scripts/download_data.py
```

**Option B — Manual Download:**
Download the full Ergast database dump from: http://ergast.com/downloads/f1db_csv.zip
Extract all CSV files into `data/raw/`

### Step 2: Run the ETL Pipeline
```bash
pip install pandas numpy tqdm
python scripts/preprocess_f1_data.py
```

### Step 3: Run Interactive Browser Dashboard
```bash
python app.py
# Automatically opens http://localhost:8000 in your browser!
```

### Step 4: Open in Tableau
1. Double click `Formula_1_Race_Intelligence.twb` (pre-configured)
2. Or open Tableau Desktop, connect to `data/processed/f1_master_race_intelligence.csv`
3. Follow `tableau_model/tableau_model_blueprint.md` to explore calculated fields and dashboards
2. Connect to `data/processed/f1_master_race_intelligence.csv`
3. Create a Hyper Extract for performance
4. Follow `tableau_model/tableau_model_blueprint.md` to build calculated fields and dashboards

---

## 📊 Dataset Specifications

| File | Description | Est. Rows |
|------|-------------|-----------|
| `results.csv` | Race result per driver per race | 26,000+ |
| `races.csv` | Grand Prix event metadata | 1,100+ |
| `drivers.csv` | Driver biographical data | 858+ |
| `constructors.csv` | Team/constructor data | 210+ |
| `circuits.csv` | Circuit metadata & geography | 77+ |
| `lap_times.csv` | Per-lap timing data | 530,000+ |
| `pit_stops.csv` | Pit stop records | 9,700+ |
| `status.csv` | Race finish status codes | 139+ |

**Master Table Output:** `f1_master_race_intelligence.csv` — ~6,464+ rows at driver-race grain

---

## 🧪 Engineered Features

| Feature | Description |
|---------|-------------|
| `Cumulative_Points` | Running season points total per driver, ordered by round |
| `DNF_Flag` | 1 = Did Not Finish (mechanical/collision/engine failure) |
| `Reliability_Score` | Rolling race completion rate per driver |
| `Circuit_Type` | 'Street Circuit' or 'Permanent Circuit' |
| `Compound` | Simulated tyre compound (Soft/Medium/Hard) |
| `Tyre_Compound_Efficiency` | Avg finishing position by compound + circuit type |
| `Podium_Flag` | 1 = Top 3 finish |
| `Constructor_Cumulative_Points` | Running season points per constructor |
| `Season_Race_Key` | e.g., '2008_1' (year_round) |
| `Driver_Full_Name` | forename + surname |
| `Age_At_Race` | Driver age in years on race day |
| `Home_Grand_Prix_Flag` | 1 = Driver racing in home country |

---

## 📐 Tableau Dashboards

### Dashboard 1 — Rajan: Team Strategy
- Championship Points Trajectory (multi-line, cumulative)
- Tyre Strategy Impact Heatmap
- Global Talent Pool Map

### Dashboard 2 — Divya: Broadcast Analytics
- Driver Performance Leaderboard
- Grand Prix Host Countries Ranking
- Podium Share Treemap

### Dashboard 3 — Arvind: Technical Regulation
- DNF Failure Type Stacked Bar
- Driver Reliability Trend Lines

---

## 🎬 Demo Video Script
See [`video_script/demo_script.md`](video_script/demo_script.md) for the complete 5-minute narrated demonstration script.

---

## 📖 Full Documentation
See [`docs/project_documentation.md`](docs/project_documentation.md) for:
- Data dictionary (all 8 raw sources + master table)
- Metrics catalog (20+ business metrics)
- Tableau publishing guide
- Data quality rules
- Known limitations & future enhancements

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Data Source | Ergast Motor Racing API (CSV) |
| Data Processing | Python 3.11, Pandas 2.x, NumPy 1.x |
| BI & Visualization | Tableau Desktop 2024.x |
| Performance | Tableau Hyper Extract (.hyper) |
| Publishing | Tableau Server / Tableau Public |

---

## 🏁 Data Source Credit

Raw data sourced from the **[Ergast Motor Racing Database](http://ergast.com/mrd/)** — a free, open REST API providing historical Formula 1 data since 1950.

---

## 👤 Project Author

Built as a production-grade portfolio BI project demonstrating end-to-end data engineering and visualization expertise across Formula 1 historical race intelligence.
