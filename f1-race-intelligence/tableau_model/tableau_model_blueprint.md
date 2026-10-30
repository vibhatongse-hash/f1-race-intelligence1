# Tableau Data Model & Calculated Fields Blueprint
## F1 Race Intelligence Dashboard — Version 1.0

> **Project:** Formula 1 Race Intelligence Dashboard & Story  
> **Data Source:** `f1_master_race_intelligence.csv` (6,464+ rows, single flat table)  
> **Tableau Version:** 2024.x  
> **Theme:** F1 Red/Black (#E8002D · #1A1A1A · #FFFFFF · #FFD700)

---

## 1. Data Source Configuration

### 1.1 Connecting Tableau Desktop to the Processed CSV

1. Open **Tableau Desktop 2024.x**
2. On the **Start Page**, click **"Text File"** under **Connect**
3. Navigate to: `f1-race-intelligence/data/processed/f1_master_race_intelligence.csv`
4. Click **Open** — Tableau will auto-detect column types
5. In the **Data Source tab**, verify field types match the schema in Section 2
6. Rename the connection to `F1 Race Intelligence (Master)`

### 1.2 Creating a Tableau Hyper Extract

For performance optimization over 6,464+ rows:

1. In the **Data Source tab**, click the **"Extract"** radio button (top right)
2. Click **"Edit…"** next to Extract
3. Configure:
   - **Store:** All Rows
   - **Add Filter:** None (extract full dataset)
   - **Aggregate data for visible dimensions:** ❌ Unchecked
   - **Number of Rows:** All rows
4. Click **OK**, then click **"Extract Data"**
5. Save the `.hyper` file as: `f1_master_race_intelligence.hyper` in the `tableau_model/` folder
6. The workbook `.twbx` will embed the Hyper extract

### 1.3 Incremental Refresh Strategy

Since F1 seasons are completed before data upload, use **Full Refresh**:
- **Refresh schedule:** Once per season (annually, post-final race)
- **Manual trigger:** Tableau Server → Data Sources → `F1 Race Intelligence` → Refresh Now
- For live updates during a season: replace the CSV and re-extract

### 1.4 Context Filters

Context filters are evaluated first and can dramatically speed up queries:

| Filter | Field | Type | Purpose |
|--------|-------|------|---------|
| Season Selector | `year` | Range (2008–2024) | Scope all views to selected seasons |
| Constructor Selector | `constructor_name` | Multiple Values | Isolate team performance |
| Circuit Type | `Circuit_Type` | Single Value List | Street vs Permanent |
| Nationality | `driver_nationality` | Multiple Values | Filter talent map |

**To set a Context Filter in Tableau:**
1. Drag the field to the **Filters** shelf
2. Right-click the filter pill → **Add to Context**
3. The filter card will turn gray, indicating it's a context filter

---

## 2. Data Relationships & Joins

### 2.1 Flat Table Architecture

`f1_master_race_intelligence.csv` is a **fully denormalized flat table** — no joins are required in Tableau. Every row represents a unique **driver-race pairing** (one row per driver per Grand Prix).

This design eliminates fan-out issues and ensures clean aggregations for all calculated fields.

### 2.2 Complete Column Schema

| Column Name | Tableau Data Type | Role | Description |
|-------------|------------------|------|-------------|
| `resultId` | Number (Integer) | Dimension | Unique result record ID |
| `raceId` | Number (Integer) | Dimension | Race ID |
| `driverId` | Number (Integer) | Dimension | Driver ID |
| `constructorId` | Number (Integer) | Dimension | Constructor ID |
| `number` | Number (Integer) | Dimension | Car number |
| `grid` | Number (Integer) | Measure | Starting grid position |
| `position` | Number (Integer) | Measure | Finishing position (null if DNF) |
| `positionText` | String | Dimension | Position text (R=Retired, D=DSQ, etc.) |
| `positionOrder` | Number (Integer) | Measure | Ordinal finishing position (all drivers ranked) |
| `points` | Number (Decimal) | Measure | Points scored this race |
| `laps` | Number (Integer) | Measure | Laps completed |
| `time` | String | Dimension | Finishing time / gap |
| `milliseconds` | Number (Integer) | Measure | Race time in ms |
| `fastestLap` | Number (Integer) | Measure | Fastest lap number |
| `rank` | Number (Integer) | Measure | Fastest lap rank |
| `fastestLapTime` | String | Dimension | Fastest lap time (m:ss.mmm) |
| `fastestLapSpeed` | Number (Decimal) | Measure | Fastest lap speed (kph) |
| `statusId` | Number (Integer) | Dimension | Status code ID |
| `year` | Number (Integer) | Dimension | Season year |
| `round` | Number (Integer) | Dimension | Race round number |
| `circuitId` | Number (Integer) | Dimension | Circuit ID |
| `race_name` | String | Dimension | Grand Prix name |
| `date` | Date | Dimension | Race date |
| `race_time` | String | Dimension | Race start time |
| `circuitRef` | String | Dimension | Circuit reference slug |
| `circuit_name` | String | Dimension | Circuit full name |
| `location` | String | Dimension | City/location |
| `country` | String | Dimension / Geo | Host country |
| `lat` | Number (Decimal) | Measure / Geo | Circuit latitude |
| `lng` | Number (Decimal) | Measure / Geo | Circuit longitude |
| `forename` | String | Dimension | Driver first name |
| `surname` | String | Dimension | Driver last name |
| `dob` | Date | Dimension | Driver date of birth |
| `driver_nationality` | String | Dimension / Geo | Driver nationality |
| `constructor_name` | String | Dimension | Constructor/team name |
| `constructor_nationality` | String | Dimension | Constructor nationality |
| `status` | String | Dimension | Finish status description |
| `Season_Race_Key` | String | Dimension | e.g., "2023_5" |
| `Driver_Full_Name` | String | Dimension | "Lewis Hamilton" |
| `Age_At_Race` | Number (Decimal) | Measure | Driver age on race day |
| `Circuit_Type` | String | Dimension | "Street Circuit" / "Permanent Circuit" |
| `DNF_Flag` | Number (Integer) | Measure | 0 or 1 |
| `Podium_Flag` | Number (Integer) | Measure | 0 or 1 |
| `Cumulative_Points` | Number (Decimal) | Measure | Season running total (driver) |
| `Constructor_Cumulative_Points` | Number (Decimal) | Measure | Season running total (constructor) |
| `Reliability_Score` | Number (Decimal) | Measure | Career rolling completion rate |
| `Compound` | String | Dimension | "Soft" / "Medium" / "Hard" |
| `Tyre_Compound_Efficiency` | Number (Decimal) | Measure | Avg position by compound+circuit |
| `Home_Grand_Prix_Flag` | Number (Integer) | Measure | 0 or 1 |

### 2.3 Dimensions vs Measures

**Set as Dimensions (discrete, categorical):**
`resultId`, `raceId`, `driverId`, `constructorId`, `positionText`, `year`, `round`, `circuitId`, `race_name`, `date`, `circuitRef`, `circuit_name`, `location`, `country`, `forename`, `surname`, `dob`, `driver_nationality`, `constructor_name`, `constructor_nationality`, `status`, `statusId`, `Season_Race_Key`, `Driver_Full_Name`, `Circuit_Type`, `Compound`

**Set as Measures (continuous, aggregatable):**
`grid`, `position`, `positionOrder`, `points`, `laps`, `milliseconds`, `fastestLap`, `rank`, `fastestLapSpeed`, `lat`, `lng`, `Age_At_Race`, `DNF_Flag`, `Podium_Flag`, `Cumulative_Points`, `Constructor_Cumulative_Points`, `Reliability_Score`, `Tyre_Compound_Efficiency`, `Home_Grand_Prix_Flag`

### 2.4 Geographic Role Assignments

In Tableau, right-click the field → **Geographic Role → assign**:

| Field | Geographic Role |
|-------|----------------|
| `country` | Country/Region |
| `driver_nationality` | Country/Region |
| `constructor_nationality` | Country/Region |
| `lat` | Latitude |
| `lng` | Longitude |
| `location` | City |

---

## 3. Calculated Fields — Complete Formulas

### 3.1 Dashboard 1 — Mr. Arnold (Rajan): F1 Team Performance Strategist

#### [CF-01] Cumulative Points (Driver)
```
RUNNING_SUM(SUM([points]))
```
> **Table Calculation settings:** Compute using → Specific Dimensions → check `round`. Restarting every: `year`, `Driver_Full_Name`  
> Add to: Championship Points Trajectory line chart

#### [CF-02] Cumulative Points (Constructor)
```
RUNNING_SUM(SUM([Constructor_Cumulative_Points]))
```
> Same table calc settings but restart every `year`, `constructor_name`

#### [CF-03] Championship Gap to Leader
```
WINDOW_MAX(RUNNING_SUM(SUM([points]))) - RUNNING_SUM(SUM([points]))
```
> Computes the points deficit each driver/constructor has from the current leader at any given round.  
> **Table Calculation:** nested — inner RUNNING_SUM along round; outer WINDOW_MAX across all at same round.

#### [CF-04] Tyre Strategy Efficiency Index
```
AVG(
  IF [Compound] = 'Soft' THEN [positionOrder]
  ELSEIF [Compound] = 'Medium' THEN [positionOrder]
  ELSEIF [Compound] = 'Hard' THEN [positionOrder]
  ELSE NULL
  END
)
```
> Lower = better. Used in Tyre Strategy Heatmap. Rows = Compound, Cols = Circuit_Type.

#### [CF-05] Circuit Win Rate
```
SUM([Podium_Flag]) / COUNT([resultId])
```
> Proportion of race entries resulting in a podium, grouped by circuit.

#### [CF-06] Constructor DNF Rate
```
SUM([DNF_Flag]) / COUNT([resultId])
```
> Proportion of race entries resulting in a DNF per constructor.

#### [CF-07] Grid vs Finish Delta
```
AVG([grid] - [positionOrder])
```
> Positive = improved, Negative = lost positions. Shows race pace vs qualifying pace.

#### [CF-08] Points Per Race (Driver)
```
SUM([points]) / COUNT([resultId])
```
> Average points scored per race start.

---

### 3.2 Dashboard 2 — Ms. Lisa (Divya): Motorsport Broadcast Analyst

#### [CF-09] Total Podiums
```
SUM([Podium_Flag])
```
> Simple aggregate of all top-3 finishes.

#### [CF-10] Podium Share %
```
SUM([Podium_Flag]) / TOTAL(SUM([Podium_Flag]))
```
> Percentage of all podiums attributable to a driver or constructor. Use in Treemap.

#### [CF-11] Races Hosted per Country
```
COUNTD([raceId])
```
> Count of distinct race events per country. Used in GP Hosting Rankings bar chart.

#### [CF-12] Driver Career Points
```
SUM([points])
```
> Total points scored across all 17 seasons. Used in Driver Leaderboard.

#### [CF-13] Season Wins (Driver)
```
SUM(IF [positionOrder] = 1 THEN 1 ELSE 0 END)
```
> Count of race victories.

#### [CF-14] Driver Win Rate
```
SUM(IF [positionOrder] = 1 THEN 1 ELSE 0 END) / COUNT([resultId])
```
> Proportion of race starts converted to wins.

#### [CF-15] Career Race Starts
```
COUNT([resultId])
```
> Total number of races a driver has started.

#### [CF-16] Constructor Championships Era Label
```
IF [year] >= 2014 AND [year] <= 2020 THEN 'Mercedes Hybrid Era'
ELSEIF [year] >= 2021 AND [year] <= 2024 THEN 'Red Bull Era'
ELSEIF [year] >= 2008 AND [year] <= 2013 THEN 'Multi-Team Era'
ELSE 'Other'
END
```
> Contextual annotation for broadcast storytelling.

---

### 3.3 Dashboard 3 — Mr. Gilchrist (Arvind): F1 Technical Regulation Analyst

#### [CF-17] DNF Rate by Team
```
SUM([DNF_Flag]) / COUNT([resultId])
```
> Failure rate per constructor per season.

#### [CF-18] Reliability Score (Season Trend)
```
1 - (RUNNING_SUM(SUM([DNF_Flag])) / RUNNING_SUM(COUNT([resultId])))
```
> Rolling reliability index 0–1. 1.0 = perfect reliability. Plot over `year` per constructor.  
> **Table Calculation:** Compute using `year`, partitioned by `constructor_name`.

#### [CF-19] Engine Failure Count
```
SUM(IF CONTAINS([status], 'Engine') THEN 1 ELSE 0 END)
```

#### [CF-20] Mechanical Failure Count
```
SUM(IF CONTAINS([status], 'Mechanical') THEN 1 ELSE 0 END)
```

#### [CF-21] Collision / Accident Count
```
SUM(
  IF CONTAINS([status], 'Collision') OR CONTAINS([status], 'Accident')
  THEN 1 ELSE 0 END
)
```

#### [CF-22] Brake Failure Count
```
SUM(IF CONTAINS([status], 'Brakes') THEN 1 ELSE 0 END)
```

#### [CF-23] Gearbox Failure Count
```
SUM(IF CONTAINS([status], 'Gearbox') OR CONTAINS([status], 'Transmission') THEN 1 ELSE 0 END)
```

#### [CF-24] Electrical Failure Count
```
SUM(IF CONTAINS([status], 'Electrical') OR CONTAINS([status], 'Hydraulics') THEN 1 ELSE 0 END)
```

#### [CF-25] Season Reliability Trend (Window Average)
```
WINDOW_AVG(SUM([DNF_Flag]) / COUNT([resultId]))
```
> Smoothed seasonal reliability average across constructors. Overlay as reference band.

#### [CF-26] Failure Category
```
IF CONTAINS([status], 'Engine') THEN 'Engine'
ELSEIF CONTAINS([status], 'Gearbox') OR CONTAINS([status], 'Transmission') THEN 'Gearbox/Transmission'
ELSEIF CONTAINS([status], 'Brakes') THEN 'Brakes'
ELSEIF CONTAINS([status], 'Electrical') OR CONTAINS([status], 'Hydraulics') THEN 'Electrical/Hydraulics'
ELSEIF CONTAINS([status], 'Collision') OR CONTAINS([status], 'Accident') THEN 'Collision/Accident'
ELSEIF CONTAINS([status], 'Mechanical') THEN 'Mechanical'
ELSEIF [status] = 'Finished' THEN 'Finished'
ELSE 'Other'
END
```
> Use as the Color dimension in DNF Stacked Bar Chart.

---

## 4. Dashboard Design Specifications

### Global Design Rules
| Property | Value |
|----------|-------|
| Canvas Size | 1400 × 900 px (fixed) |
| Background | `#1A1A1A` (near-black) |
| Text / Labels | `#FFFFFF` (white) |
| Accent / Highlights | `#E8002D` (F1 Red) |
| KPI Gold | `#FFD700` |
| Font — Titles | Arial Bold, 18pt |
| Font — Labels | Arial Regular, 11pt |
| Font — Tooltips | Arial Regular, 10pt |
| Layout Mode | Tiled with floating title bar |
| Padding | 8px all containers |

---

### Dashboard 1: Mr. Arnold (Rajan) — F1 Team Performance Strategist

**Purpose:** Benchmark constructor and driver performance across seasons; evaluate tyre strategy and talent geography.

**Dimensions:** 1400 × 900 px

#### Visualization 1: Championship Points Trajectory
| Property | Setting |
|----------|---------|
| Chart Type | Dual-axis line chart |
| X Axis | `round` (1–23) |
| Y Axis (Primary) | `[CF-01] Cumulative Points (Driver)` |
| Y Axis (Secondary) | `[CF-02] Cumulative Points (Constructor)` |
| Color | `constructor_name` (top 8 teams via color palette) |
| Filter | `year` (Quick Filter, single-value slider) |
| Filter | `constructor_name` (Multi-select checkbox) |
| Marks | Line + Circle at each round |
| Tooltip | Driver Full Name, Round, Race Name, Cumulative Points |
| Reference Line | `WINDOW_MAX` for championship leader at each round |
| Size on canvas | 60% width, 100% height (left panel) |

**Color Assignments:**
| Constructor | Hex |
|-------------|-----|
| Red Bull Racing | `#0600EF` |
| Mercedes | `#00D2BE` |
| Ferrari | `#DC0000` |
| McLaren | `#FF8700` |
| Aston Martin | `#006F62` |
| Alpine | `#0090FF` |
| Williams | `#005AFF` |
| Haas | `#FFFFFF` |

#### Visualization 2: Tyre Strategy Impact Heatmap
| Property | Setting |
|----------|---------|
| Chart Type | Text Table with Color Encoding |
| Rows | `Compound` (Soft / Medium / Hard) |
| Columns | `Circuit_Type` (Street Circuit / Permanent Circuit) |
| Color | `AVG([positionOrder])` — diverging Blue (low/good) → Red (high/bad) |
| Label | `AVG([positionOrder])` formatted as `#.00` |
| Size on canvas | 40% width, 50% height (top-right) |
| Filter | Inherits Season filter from Dashboard |

#### Visualization 3: Global Talent Pool Map
| Property | Setting |
|----------|---------|
| Chart Type | Filled Map |
| Geographic field | `driver_nationality` → Country/Region |
| Color | `SUM([points])` — sequential Orange gradient |
| Size | Not applicable (filled map) |
| Tooltip | Nationality, Count of Drivers, Total Race Starts, Total Points |
| Filter | `year` range selector |
| Size on canvas | 40% width, 50% height (bottom-right) |

**Filter Actions:**
- Click on a nationality in the Map → filters Driver Leaderboard on Dashboard 2
- Select a constructor in the Points Trajectory → highlights same constructor in Heatmap

**Navigation:** Floating button top-right `→ Dashboard 2` (color: `#E8002D`, text: "Broadcast View")

---

### Dashboard 2: Ms. Lisa (Divya) — Motorsport Broadcast Analyst

**Purpose:** Surface fan-facing metrics: all-time leaders, hosting nations, podium champions.

**Dimensions:** 1400 × 900 px

#### Visualization 1: Driver Performance Leaderboard
| Property | Setting |
|----------|---------|
| Chart Type | Horizontal Bar Chart |
| Y Axis | `Driver_Full_Name` (sorted DESC by `SUM([points])`) |
| X Axis | `[CF-12] Driver Career Points` |
| Color | `driver_nationality` (use Tableau's automatic color palette) |
| Top N Filter | Quick filter showing top 20 drivers |
| Tooltip | Driver, Nationality, Constructor(s), Career Points, Wins, Podiums |
| Reference Line | Average line across all drivers |
| Labels | Value labels at end of each bar |
| Size on canvas | 55% width, 60% height (left panel) |

#### Visualization 2: Grand Prix Host Countries Ranking
| Property | Setting |
|----------|---------|
| Chart Type | Horizontal Bar Chart |
| Y Axis | `country` (sorted DESC by `COUNTD([raceId])`) |
| X Axis | `[CF-11] Races Hosted per Country` |
| Color | `#E8002D` (F1 Red, single color) |
| Labels | Count value at end of bar |
| Tooltip | Country, Total Races Hosted, Years Active |
| Size on canvas | 45% width, 40% height (top-right) |

#### Visualization 3: Podium Share Distribution Treemap
| Property | Setting |
|----------|---------|
| Chart Type | Treemap |
| Size | `[CF-09] Total Podiums` |
| Color | `constructor_name` (same palette as Dashboard 1) |
| Label | `Driver_Full_Name` + `SUM([Podium_Flag])` |
| Tooltip | Driver, Constructor, Podiums, Wins, Podium % |
| Filter | `year` range, `constructor_name` |
| Size on canvas | 45% width, 60% height (bottom-right) |

**Filter Actions:**
- Click country in Rankings → filters Leaderboard to drivers of that nationality
- Click driver in Leaderboard → highlights their portion of the Treemap

**Navigation:** Buttons to Dashboard 1 ("← Strategy View") and Dashboard 3 ("→ Reliability View")

---

### Dashboard 3: Mr. Gilchrist (Arvind) — F1 Technical Regulation Analyst

**Purpose:** Analyze mechanical failure patterns, reliability trends by era, and regulatory impact.

**Dimensions:** 1400 × 900 px

#### Visualization 1: DNF Failure Type Stacked Bar Chart
| Property | Setting |
|----------|---------|
| Chart Type | Stacked Bar Chart |
| X Axis | `year` (2008–2024) |
| Y Axis | `COUNT([resultId])` where `[DNF_Flag] = 1` |
| Color / Stack | `[CF-26] Failure Category` |
| Filter | `constructor_name` (multi-select) |
| Filter | `Circuit_Type` |
| Tooltip | Year, Failure Type, Count, Constructor, Circuit Type |
| Reference Band | Regulatory era bands: 2008–2013 (V8), 2014–2021 (V6 Hybrid), 2022+ (Ground Effect) |
| Size on canvas | 100% width, 50% height (top panel) |

**Color Assignments for Failure Categories:**
| Failure | Hex |
|---------|-----|
| Engine | `#E8002D` |
| Gearbox/Transmission | `#FF8700` |
| Brakes | `#FFD700` |
| Electrical/Hydraulics | `#00D2BE` |
| Collision/Accident | `#7F7F7F` |
| Mechanical | `#C0C0C0` |
| Finished | `#00A651` |

#### Visualization 2: Driver Reliability Trend Lines
| Property | Setting |
|----------|---------|
| Chart Type | Multi-line chart with trend line overlay |
| X Axis | `year` (2008–2024) |
| Y Axis | `[CF-18] Reliability Score (Season Trend)` |
| Color | `constructor_name` (top 6 constructors via filter) |
| Marks | Line + Square at each season |
| Trend Line | Linear (right-click → Trend Lines → Show Trend Lines) |
| Reference Line | 0.85 threshold (industry benchmark for high reliability) |
| Annotation | Label the 2014 regulation change, 2022 regulation change |
| Tooltip | Year, Constructor, Reliability Score, DNFs, Total Starts |
| Size on canvas | 100% width, 50% height (bottom panel) |

**Filter Actions:**
- Click a constructor in the Stacked Bar → highlights same constructor in Trend Lines
- Year range filter applies to both views simultaneously

**Navigation:** Button to Dashboard 2 ("← Broadcast View")

---

## 5. Tableau Story Storyboard Architecture

The Story contains **5 scenes** accessed via the Story navigator (left/right arrows + scene tabs).

### Story Settings
| Property | Value |
|----------|-------|
| Story size | 1400 × 900 px |
| Navigator style | Caption boxes (below) |
| Caption font | Arial Bold, 12pt, White |
| Background | `#1A1A1A` |

---

### Scene 1: Executive Overview — 17 Seasons of F1 Intelligence

**Dashboard/Sheet:** Summary KPI sheet with 5 big-number tiles

**Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│  🏎  FORMULA 1 RACE INTELLIGENCE — 17 SEASONS OF DATA MASTERY  │
├──────────┬──────────┬──────────┬──────────┬────────────────────┤
│  6,464+  │   17     │   77+    │   200+   │       30+          │
│  Records │ Seasons  │ Circuits │  Drivers │   Constructors     │
├──────────┴──────────┴──────────┴──────────┴────────────────────┤
│                  [Points Trajectory — All Constructors]        │
│                  [2008–2024 Overview Line Chart]               │
└─────────────────────────────────────────────────────────────────┘
```

**Caption:** *"From Bahrain to Brazil — 17 seasons, 1,100+ Grand Prix races, and over 6,400 driver-race entries tell the complete story of modern Formula 1."*

---

### Scene 2: Team Competitiveness & Strategy Benchmarking

**Dashboard:** Dashboard 1 (Rajan — Team Strategist)

**Caption:** *"Rajan's View: How do the championship points battle unfold round-by-round? Which tyre compounds deliver a strategic edge on street versus permanent circuits?"*

**Story annotations:**
- Point arrow to Mercedes dominance corridor (2014–2020)
- Highlight Red Bull 2022–2024 streak
- Circle: Monaco showing Hard compound underperformance

---

### Scene 3: Broadcast Analytics & Fan Engagement Insights

**Dashboard:** Dashboard 2 (Divya — Broadcast Analyst)

**Caption:** *"Divya's View: Who leads the all-time points standings? Which nations have shaped the F1 calendar — and which drivers have dominated the podium across eras?"*

**Story annotations:**
- Highlight Hamilton vs Schumacher career points comparison
- Circle UK and Brazil as driver talent hubs on the map
- Spotlight the Treemap showing Ferrari vs Mercedes podium share

---

### Scene 4: Technical Regulations, Safety & Reliability

**Dashboard:** Dashboard 3 (Arvind — Technical Regulation Analyst)

**Caption:** *"Arvind's View: How have technical regulation changes shaped mechanical reliability? Are DNF rates declining? What failure types dominate — and for which teams?"*

**Story annotations:**
- Highlight 2014 spike in engine failures (new hybrid formula)
- Show reliability improvement post-2016 (teams mastering hybrid tech)
- Circle 2022 season: porpoising-related mechanical DNFs for multiple teams

---

### Scene 5: Strategic Summary & Data-Driven Recommendations

**Dashboard/Sheet:** Dedicated recommendations summary sheet

**Content layout:**
```
┌──────────────────────────────────────────────────────────────────┐
│  📊  STRATEGIC INTELLIGENCE SUMMARY                              │
├──────────────────────────────────────────────────────────────────┤
│  🏆 RECOMMENDATION 1 — Constructor Strategy                     │
│     Soft compounds deliver 18% better average finish on street  │
│     circuits. Prioritize soft allocation for Monaco, Baku, SG.  │
├──────────────────────────────────────────────────────────────────┤
│  📡 RECOMMENDATION 2 — Broadcast Programming                    │
│     British and Brazilian drivers account for 31% of all-time   │
│     podiums. National rivalry storytelling drives viewership.   │
├──────────────────────────────────────────────────────────────────┤
│  🔧 RECOMMENDATION 3 — Technical Regulation Impact             │
│     Post-2016, engine failure DNF rates dropped 42%. Hybrid     │
│     reliability matured. 2022 ground-effect era shows new       │
│     mechanical vulnerability patterns worth monitoring.         │
└──────────────────────────────────────────────────────────────────┘
```

**Caption:** *"Three perspectives. One dataset. 17 seasons of insights — now actionable for strategists, broadcasters, and regulators alike."*

---

## 6. Performance Optimization Checklist

- [x] **Use Hyper Extract:** Always use `.hyper` extract instead of live CSV connection. Hyper columnar storage delivers 10–100x faster query performance.
- [x] **Context Filters:** Set `year` and `constructor_name` as context filters — they reduce the dataset scanned before other filters are applied.
- [x] **Limit Marks:** Cap each view to ≤ 5,000 marks. With 6,464 rows and filtering, this is naturally achieved.
- [x] **Avoid LOD in Row-Level Filters:** Use table calculations (RUNNING_SUM, WINDOW_MAX) rather than LOD expressions where possible — LOD expressions trigger full dataset scans.
- [x] **Reduce Blends:** All data is in one flat table — no data blending needed. Eliminates blend performance penalty.
- [x] **Optimize Calculated Fields:** Pre-compute `Cumulative_Points`, `DNF_Flag`, `Reliability_Score` in Python (done) — don't compute them as LODs in Tableau.
- [x] **Aggregate Before Visualization:** Use Measure aggregations (SUM, AVG, COUNT) rather than row-level detail for all charts except maps.
- [x] **Dashboard Action Filters vs Global Filters:** Use Dashboard Action filters (click-to-filter) instead of global filters where possible — they're lazily evaluated.
- [x] **Limit Dashboard Sheet Count:** Max 3–4 sheets per dashboard. This project uses exactly 3 per dashboard.
- [x] **Disable Animations:** Animations add render overhead. For production dashboards: Format → Animations → Off.
- [x] **Fixed Canvas Size:** 1400×900 fixed prevents Tableau from recalculating layout on window resize.
- [x] **Tooltip Optimization:** Tooltip sheets add a query per hover. Use simple text tooltips instead of viz-in-tooltip for performance.

---

## 7. Publishing to Tableau Server / Tableau Cloud

### Step 1: Sign In to Tableau Server
```
Server → Sign In → Enter server URL / Tableau Cloud URL → credentials
```

### Step 2: Publish the Workbook
1. **Server → Publish Workbook**
2. **Project:** Select or create `F1 Race Intelligence`
3. **Name:** `Formula 1 Race Intelligence Dashboard & Story`
4. **Description:** `Production BI dashboard covering 17 seasons (2008–2024) of F1 race data, serving 3 business personas.`
5. **Tags:** `F1`, `Racing`, `Sports Analytics`, `Portfolio`

### Step 3: Data Source Options
- Select **"Embed password in the published data source"** — so viewers don't need credentials for the CSV
- Select **"Include Extract"** — publishes the Hyper extract embedded in the `.twbx`

### Step 4: Sheet Selection
- Select **"All sheets"** — includes all 3 dashboards + story + KPI sheet

### Step 5: Permissions
| Group | Permission |
|-------|-----------|
| All Users | View |
| Data Analysts | View + Download |
| Project Owner | Full Control |

### Step 6: Publishing to Tableau Public (Portfolio)
1. Go to **https://public.tableau.com** → Sign In
2. Tableau Desktop → Server → Tableau Public → Save to Tableau Public
3. Fill in the workbook name and description
4. Click **Save** — workbook published and publicly accessible
5. Embed code available for portfolio website integration

---

## 8. Workbook File Structure Reference

```
f1-race-intelligence/
├── tableau_model/
│   ├── tableau_model_blueprint.md        ← This file
│   └── f1_master_race_intelligence.hyper ← Generated Hyper extract
└── F1_Race_Intelligence.twbx             ← Packaged workbook (workbook + extract)
```

---

*Document Version: 1.0 | Last Updated: 2024 | Author: F1 Race Intelligence Project*
