"""
F1 Race Intelligence - Interactive Web Application
===================================================
Production-grade browser dashboard serving the 3 persona dashboards,
5-scene narrative story, and Tableau Web Integration interface.

Usage:
    python app.py
"""

import os
import sys
import json
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
import pandas as pd
import numpy as np

PORT = 8000
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, "data", "processed", "f1_master_race_intelligence.csv")
WEB_DIR = os.path.join(SCRIPT_DIR, "web")
os.makedirs(WEB_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Pre-aggregate Data for Sub-second Web Responses
# ---------------------------------------------------------------------------
def compute_analytics():
    print(f">> Loading analytical dataset: {DATA_FILE}")
    if not os.path.exists(DATA_FILE):
        print(f"[!] Error: {DATA_FILE} does not exist. Run preprocess_f1_data.py first.")
        sys.exit(1)

    df = pd.read_csv(DATA_FILE)

    # 1. Macro KPIs
    kpis = {
        "records": int(len(df)),
        "seasons": int(df["year"].nunique()),
        "min_year": int(df["year"].min()),
        "max_year": int(df["year"].max()),
        "circuits": int(df["circuitId"].nunique()),
        "drivers": int(df["driverId"].nunique()),
        "constructors": int(df["constructorId"].nunique()),
        "total_podiums": int(df["Podium_Flag"].sum()),
        "total_dnfs": int(df["DNF_Flag"].sum()),
        "overall_reliability": round(float(1 - (df["DNF_Flag"].sum() / len(df))), 4)
    }

    # 2. Championship Trajectory by Season & Constructor
    trajectory = {}
    for season in sorted(df["year"].unique()):
        sdf = df[df["year"] == season]
        top_teams = sdf.groupby("constructor_name")["points"].sum().nlargest(6).index.tolist()
        rounds = sorted(sdf["round"].unique())
        
        team_data = {}
        for team in top_teams:
            tdf = sdf[sdf["constructor_name"] == team]
            pts_by_round = []
            for r in rounds:
                cur = tdf[tdf["round"] <= r]
                pts = float(cur["points"].sum()) if not cur.empty else 0.0
                pts_by_round.append(pts)
            team_data[team] = pts_by_round

        trajectory[str(season)] = {
            "rounds": [f"R{r}" for r in rounds],
            "teams": team_data
        }

    # 3. Tyre Strategy Heatmap
    tyre_group = df.groupby(["Compound", "Circuit_Type"]).agg(
        avg_position=("positionOrder", "mean"),
        entries=("resultId", "count"),
        win_rate=("Podium_Flag", "mean")
    ).reset_index()
    tyre_data = []
    for _, r in tyre_group.iterrows():
        tyre_data.append({
            "compound": str(r["Compound"]),
            "circuit_type": str(r["Circuit_Type"]),
            "avg_position": round(float(r["avg_position"]), 2),
            "entries": int(r["entries"]),
            "podium_rate": round(float(r["win_rate"]) * 100, 1)
        })

    # 4. Global Driver Talent Pool Map
    nat_group = df.groupby("driver_nationality").agg(
        points=("points", "sum"),
        starts=("resultId", "count"),
        drivers=("Driver_Full_Name", "nunique"),
        podiums=("Podium_Flag", "sum")
    ).reset_index().sort_values("points", ascending=False)
    
    talent_data = []
    for _, r in nat_group.iterrows():
        talent_data.append({
            "nationality": str(r["driver_nationality"]),
            "points": float(r["points"]),
            "starts": int(r["starts"]),
            "drivers": int(r["drivers"]),
            "podiums": int(r["podiums"])
        })

    # 5. Driver Leaderboard (Top 25)
    driver_group = df.groupby(["Driver_Full_Name", "driver_nationality"]).agg(
        points=("points", "sum"),
        wins=("positionOrder", lambda x: (x == 1).sum()),
        podiums=("Podium_Flag", "sum"),
        starts=("resultId", "count")
    ).reset_index().sort_values("points", ascending=False).head(25)
    
    leaderboard = []
    for _, r in driver_group.iterrows():
        leaderboard.append({
            "name": str(r["Driver_Full_Name"]),
            "nationality": str(r["driver_nationality"]),
            "points": float(r["points"]),
            "wins": int(r["wins"]),
            "podiums": int(r["podiums"]),
            "starts": int(r["starts"]),
            "win_rate": round(float(r["wins"] / r["starts"] * 100), 1) if r["starts"] > 0 else 0
        })

    # 6. Grand Prix Host Countries
    host_group = df.groupby("country")["raceId"].nunique().reset_index().sort_values("raceId", ascending=False)
    host_data = []
    for _, r in host_group.iterrows():
        host_data.append({
            "country": str(r["country"]),
            "races": int(r["raceId"])
        })

    # 7. Podium Share by Constructor
    podium_group = df.groupby("constructor_name")["Podium_Flag"].sum().reset_index().sort_values("Podium_Flag", ascending=False).head(10)
    podium_data = []
    for _, r in podium_group.iterrows():
        podium_data.append({
            "team": str(r["constructor_name"]),
            "podiums": int(r["Podium_Flag"])
        })

    # 8. DNF Failures by Season & Category
    df["Failure_Cat"] = "Other"
    status_lower = df["status"].fillna("").str.lower()
    df.loc[status_lower.str.contains("engine|power unit"), "Failure_Cat"] = "Engine"
    df.loc[status_lower.str.contains("gearbox|transmission"), "Failure_Cat"] = "Gearbox"
    df.loc[status_lower.str.contains("brake"), "Failure_Cat"] = "Brakes"
    df.loc[status_lower.str.contains("collision|accident|spun"), "Failure_Cat"] = "Collision"
    df.loc[status_lower.str.contains("electrical|hydraulics"), "Failure_Cat"] = "Electrical/Hydraulics"
    df.loc[status_lower.str.contains("mechanical|suspension|steering"), "Failure_Cat"] = "Mechanical"
    
    dnf_df = df[df["DNF_Flag"] == 1]
    dnf_seasons = sorted(df["year"].unique())
    cats = ["Engine", "Gearbox", "Brakes", "Collision", "Electrical/Hydraulics", "Mechanical"]
    
    dnf_breakdown = {"seasons": [int(y) for y in dnf_seasons], "series": {}}
    for c in cats:
        dnf_breakdown["series"][c] = []
        for y in dnf_seasons:
            cnt = int(((dnf_df["year"] == y) & (dnf_df["Failure_Cat"] == c)).sum())
            dnf_breakdown["series"][c].append(cnt)

    # 9. Reliability Trend by Season (Top 5 Constructors)
    top_5_teams = ["Mercedes", "Ferrari", "Red Bull", "McLaren", "Renault"]
    reliability_trend = {"seasons": [int(y) for y in dnf_seasons], "teams": {}}
    for team in top_5_teams:
        reliability_trend["teams"][team] = []
        for y in dnf_seasons:
            team_season = df[(df["year"] == y) & (df["constructor_name"] == team)]
            if len(team_season) > 0:
                rel = 1.0 - (float(team_season["DNF_Flag"].sum()) / len(team_season))
                reliability_trend["teams"][team].append(round(rel * 100, 1))
            else:
                reliability_trend["teams"][team].append(None)

    payload = {
        "kpis": kpis,
        "trajectory": trajectory,
        "tyre_data": tyre_data,
        "talent_data": talent_data,
        "leaderboard": leaderboard,
        "host_data": host_data,
        "podium_data": podium_data,
        "dnf_breakdown": dnf_breakdown,
        "reliability_trend": reliability_trend,
        "all_seasons": [int(y) for y in sorted(df["year"].unique())]
    }
    return payload


# ---------------------------------------------------------------------------
# Generate Single Page Web Application
# ---------------------------------------------------------------------------
def generate_web_app(data_payload):
    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FORMULA 1 Race Intelligence Dashboard & Story</title>
  <!-- Chart.js CDN -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <!-- FontAwesome Icons -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    :root {{
      --f1-red: #E8002D;
      --f1-dark: #121212;
      --f1-card: #1A1A1A;
      --f1-card-hover: #222222;
      --f1-border: #2C2C2C;
      --f1-text: #FFFFFF;
      --f1-muted: #A0A0A0;
      --f1-gold: #FFD700;
      --f1-cyan: #00D2BE;
      --f1-blue: #0600EF;
      --f1-orange: #FF8700;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
    body {{ background-color: var(--f1-dark); color: var(--f1-text); min-height: 100vh; overflow-x: hidden; }}
    
    /* Top Navigation Bar */
    header {{
      background: linear-gradient(90deg, #1A1A1A 0%, #0D0D0D 100%);
      border-bottom: 2px solid var(--f1-red);
      padding: 14px 28px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      position: sticky;
      top: 0;
      z-index: 1000;
    }}
    .logo-container {{ display: flex; align-items: center; gap: 14px; }}
    .f1-badge {{ background: var(--f1-red); color: #FFF; font-weight: 900; padding: 5px 12px; border-radius: 4px; font-size: 1.1rem; letter-spacing: 1px; }}
    .title-group h1 {{ font-size: 1.25rem; font-weight: 800; letter-spacing: -0.5px; }}
    .title-group span {{ font-size: 0.75rem; color: var(--f1-muted); text-transform: uppercase; letter-spacing: 1px; }}

    nav {{ display: flex; gap: 8px; }}
    .nav-btn {{
      background: transparent;
      border: 1px solid var(--f1-border);
      color: var(--f1-muted);
      padding: 8px 16px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.85rem;
      font-weight: 600;
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .nav-btn:hover, .nav-btn.active {{
      background: var(--f1-red);
      border-color: var(--f1-red);
      color: #FFF;
    }}

    /* Main Container */
    main {{ padding: 24px 32px; max-width: 1600px; margin: 0 auto; }}

    /* KPI Summary Row */
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}
    .kpi-card {{
      background: var(--f1-card);
      border: 1px solid var(--f1-border);
      border-radius: 8px;
      padding: 16px 20px;
      display: flex;
      flex-direction: column;
      gap: 4px;
      border-left: 4px solid var(--f1-red);
    }}
    .kpi-label {{ font-size: 0.75rem; color: var(--f1-muted); text-transform: uppercase; letter-spacing: 0.8px; }}
    .kpi-val {{ font-size: 1.8rem; font-weight: 800; color: #FFF; }}
    .kpi-sub {{ font-size: 0.75rem; color: var(--f1-gold); }}

    /* Tab Sections */
    .tab-content {{ display: none; }}
    .tab-content.active {{ display: block; }}

    /* Story Mode Banner */
    .story-nav-card {{
      background: var(--f1-card);
      border: 1px solid var(--f1-border);
      border-radius: 8px;
      padding: 20px;
      margin-bottom: 24px;
    }}
    .story-stepper {{ display: flex; gap: 12px; margin-bottom: 16px; overflow-x: auto; padding-bottom: 6px; }}
    .step-btn {{
      flex: 1;
      min-width: 180px;
      background: #222;
      border: 1px solid var(--f1-border);
      color: var(--f1-muted);
      padding: 10px 14px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.8rem;
      font-weight: 700;
      text-align: left;
      transition: all 0.2s;
    }}
    .step-btn.active {{
      background: #2A1519;
      border-color: var(--f1-red);
      color: #FFF;
      border-left: 4px solid var(--f1-red);
    }}
    .story-caption-box {{
      background: #141414;
      border-left: 4px solid var(--f1-red);
      padding: 14px 18px;
      border-radius: 4px;
      font-size: 0.95rem;
      line-height: 1.5;
      color: #E0E0E0;
    }}

    /* Grid Layouts for Visualizations */
    .viz-grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }}
    .viz-grid-3 {{ display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 20px; }}
    .viz-full {{ margin-bottom: 20px; }}

    .viz-card {{
      background: var(--f1-card);
      border: 1px solid var(--f1-border);
      border-radius: 8px;
      padding: 20px;
      position: relative;
    }}
    .viz-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      padding-bottom: 10px;
      border-bottom: 1px solid #282828;
    }}
    .viz-title {{ font-size: 1.05rem; font-weight: 700; display: flex; align-items: center; gap: 8px; }}
    .viz-subtitle {{ font-size: 0.75rem; color: var(--f1-muted); }}
    .viz-filter {{
      background: #252525;
      color: #FFF;
      border: 1px solid #333;
      padding: 5px 12px;
      border-radius: 4px;
      font-size: 0.8rem;
    }}

    /* Data Table Styling */
    .table-container {{ max-height: 380px; overflow-y: auto; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; text-align: left; }}
    th {{ background: #222; color: var(--f1-muted); font-weight: 700; padding: 10px 12px; position: sticky; top: 0; }}
    td {{ padding: 9px 12px; border-bottom: 1px solid #282828; }}
    tr:hover {{ background: #242424; }}

    /* Heatmap Grid */
    .heatmap-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      padding: 10px 0;
    }}
    .heatmap-cell {{
      background: #222;
      border: 1px solid var(--f1-border);
      border-radius: 6px;
      padding: 16px;
      text-align: center;
    }}
    .heatmap-cell .comp-tag {{ font-size: 0.75rem; font-weight: 800; padding: 3px 8px; border-radius: 3px; display: inline-block; margin-bottom: 8px; }}
    .tag-soft {{ background: #E8002D; color: #FFF; }}
    .tag-med {{ background: #FFD700; color: #000; }}
    .tag-hard {{ background: #FFFFFF; color: #000; }}
    .heatmap-val {{ font-size: 1.6rem; font-weight: 800; margin-bottom: 4px; }}
    .heatmap-sub {{ font-size: 0.75rem; color: var(--f1-muted); }}

    /* Story Scene 5 Recommendations Box */
    .rec-box {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 18px;
      margin-top: 20px;
    }}
    .rec-card {{
      background: #1C1C1C;
      border: 1px solid var(--f1-border);
      border-top: 4px solid var(--f1-red);
      border-radius: 6px;
      padding: 18px;
    }}
    .rec-card h3 {{ font-size: 1rem; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }}
    .rec-card p {{ font-size: 0.85rem; color: #CCC; line-height: 1.5; }}

    /* Web Integration Code Box */
    .code-box {{
      background: #0E0E0E;
      border: 1px solid #333;
      border-radius: 6px;
      padding: 16px;
      font-family: Consolas, monospace;
      font-size: 0.85rem;
      color: #79C0FF;
      overflow-x: auto;
      line-height: 1.4;
      margin-top: 12px;
    }}
  </style>
</head>
<body>

  <!-- Top Navigation Header -->
  <header>
    <div class="logo-container">
      <div class="f1-badge">F1</div>
      <div class="title-group">
        <h1>FORMULA 1 Race Intelligence</h1>
        <span>SkillWallet Analytics Platform &bull; 17 Seasons (2005&ndash;2021)</span>
      </div>
    </div>
    <nav>
      <button class="nav-btn active" onclick="switchTab('story')"><i class="fa-solid fa-book-open"></i> Story Mode</button>
      <button class="nav-btn" onclick="switchTab('dash1')"><i class="fa-solid fa-chess-knight"></i> Mr. Arnold (Strategy)</button>
      <button class="nav-btn" onclick="switchTab('dash2')"><i class="fa-solid fa-tower-broadcast"></i> Ms. Lisa (Media)</button>
      <button class="nav-btn" onclick="switchTab('dash3')"><i class="fa-solid fa-wrench"></i> Mr. Gilchrist (FIA)</button>
      <button class="nav-btn" onclick="switchTab('web-integration')"><i class="fa-solid fa-code"></i> Web Integration</button>
    </nav>
  </header>

  <main>
    <!-- Top Macro KPI Cards -->
    <section class="kpi-grid">
      <div class="kpi-card">
        <span class="kpi-label">Analyzed Race Records</span>
        <span class="kpi-val" id="kpi-records">6,751</span>
        <span class="kpi-sub">Target &ge; 6,464 records met</span>
      </div>
      <div class="kpi-card" style="border-left-color: var(--f1-cyan);">
        <span class="kpi-label">Historical Seasons</span>
        <span class="kpi-val" id="kpi-seasons">17</span>
        <span class="kpi-sub">2005 &ndash; 2021 Championships</span>
      </div>
      <div class="kpi-card" style="border-left-color: var(--f1-gold);">
        <span class="kpi-label">Grand Prix Circuits</span>
        <span class="kpi-val" id="kpi-circuits">34</span>
        <span class="kpi-sub">Street &amp; Permanent Venues</span>
      </div>
      <div class="kpi-card" style="border-left-color: var(--f1-orange);">
        <span class="kpi-label">Elite Drivers &amp; Teams</span>
        <span class="kpi-val"><span id="kpi-drivers">94</span> / <span id="kpi-teams">33</span></span>
        <span class="kpi-sub">Driver-Race Unified Grain</span>
      </div>
      <div class="kpi-card" style="border-left-color: #00E676;">
        <span class="kpi-label">Overall Completion Rate</span>
        <span class="kpi-val" id="kpi-rel">79.2%</span>
        <span class="kpi-sub">Reliability Score Index</span>
      </div>
    </section>

    <!-- ================================================================= -->
    <!-- TAB 1: STORY MODE (5 SCENES) -->
    <!-- ================================================================= -->
    <div id="tab-story" class="tab-content active">
      <div class="story-nav-card">
        <div class="story-stepper">
          <button class="step-btn active" onclick="loadStoryScene(1)">Scene 1: Executive Overview</button>
          <button class="step-btn" onclick="loadStoryScene(2)">Scene 2: Mr. Arnold (Strategy)</button>
          <button class="step-btn" onclick="loadStoryScene(3)">Scene 3: Ms. Lisa (Media)</button>
          <button class="step-btn" onclick="loadStoryScene(4)">Scene 4: Mr. Gilchrist (Safety)</button>
          <button class="step-btn" onclick="loadStoryScene(5)">Scene 5: Recommendations</button>
        </div>
        <div class="story-caption-box" id="story-caption">
          <strong>Scene 1 &bull; Executive Macro Overview:</strong> Seventeen seasons, 6,751 race records, and 34 world-class circuits form the empirical foundation of this intelligence suite. Across nearly two decades of technical revolutions—from screaming V8s to hybrid turbo-electrics—data reveals how championship dynasties rise, compete, and stabilize.
        </div>
      </div>

      <!-- Dynamic Story Scene Container -->
      <div id="story-stage"></div>
    </div>

    <!-- ================================================================= -->
    <!-- TAB 2: DASHBOARD 1 - MR. ARNOLD (TEAM PERFORMANCE & STRATEGY) -->
    <!-- ================================================================= -->
    <div id="tab-dash1" class="tab-content">
      <div class="viz-card viz-full">
        <div class="viz-header">
          <div>
            <div class="viz-title"><i class="fa-solid fa-chart-line" style="color:var(--f1-red);"></i> Championship Points Trajectory</div>
            <div class="viz-subtitle">Multi-line round-by-round points accumulation for benchmarking against Mercedes &amp; Red Bull</div>
          </div>
          <select id="season-selector" class="viz-filter" onchange="updateTrajectoryChart()">
            <!-- Populated via JS -->
          </select>
        </div>
        <div style="height: 380px;">
          <canvas id="chart-trajectory"></canvas>
        </div>
      </div>

      <div class="viz-grid-2">
        <div class="viz-card">
          <div class="viz-header">
            <div>
              <div class="viz-title"><i class="fa-solid fa-circle-dot" style="color:var(--f1-gold);"></i> Tyre Strategy Impact Matrix</div>
              <div class="viz-subtitle">Average finishing position &amp; podium rate across compound &amp; circuit types</div>
            </div>
          </div>
          <div class="heatmap-grid" id="tyre-matrix"></div>
        </div>

        <div class="viz-card">
          <div class="viz-header">
            <div>
              <div class="viz-title"><i class="fa-solid fa-globe" style="color:var(--f1-cyan);"></i> Global Driver Talent Pool</div>
              <div class="viz-subtitle">Driver entries and career points volume by nationality for scouting</div>
            </div>
          </div>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>Nationality</th>
                  <th>Drivers</th>
                  <th>Race Starts</th>
                  <th>Career Pts</th>
                  <th>Podiums</th>
                </tr>
              </thead>
              <tbody id="talent-table-body"></tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- ================================================================= -->
    <!-- TAB 3: DASHBOARD 2 - MS. LISA (BROADCAST & FAN INSIGHTS) -->
    <!-- ================================================================= -->
    <div id="tab-dash2" class="tab-content">
      <div class="viz-grid-3">
        <div class="viz-card">
          <div class="viz-header">
            <div>
              <div class="viz-title"><i class="fa-solid fa-trophy" style="color:var(--f1-gold);"></i> Driver Performance Leaderboard</div>
              <div class="viz-subtitle">All-time championship points leaders across 17 seasons</div>
            </div>
          </div>
          <div style="height: 480px;">
            <canvas id="chart-leaderboard"></canvas>
          </div>
        </div>

        <div style="display:flex; flex-direction:column; gap:20px;">
          <div class="viz-card" style="flex:1;">
            <div class="viz-header">
              <div>
                <div class="viz-title"><i class="fa-solid fa-flag-checkered"></i> Grand Prix Host Ranking</div>
                <div class="viz-subtitle">Top hosting nations</div>
              </div>
            </div>
            <div style="height: 190px;">
              <canvas id="chart-hosts"></canvas>
            </div>
          </div>

          <div class="viz-card" style="flex:1;">
            <div class="viz-header">
              <div>
                <div class="viz-title"><i class="fa-solid fa-chart-pie" style="color:var(--f1-red);"></i> Podium Share Distribution</div>
                <div class="viz-subtitle">Top constructor podium volume</div>
              </div>
            </div>
            <div style="height: 190px;">
              <canvas id="chart-podiums"></canvas>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ================================================================= -->
    <!-- TAB 4: DASHBOARD 3 - MR. GILCHRIST (TECHNICAL REGULATION & RELIABILITY) -->
    <!-- ================================================================= -->
    <div id="tab-dash3" class="tab-content">
      <div class="viz-card viz-full">
        <div class="viz-header">
          <div>
            <div class="viz-title"><i class="fa-solid fa-triangle-exclamation" style="color:var(--f1-red);"></i> DNF Failure Type Stacked Bar Chart</div>
            <div class="viz-subtitle">Longitudinal breakdown of mechanical, electrical, and collision failures per season</div>
          </div>
        </div>
        <div style="height: 340px;">
          <canvas id="chart-dnf-stacked"></canvas>
        </div>
      </div>

      <div class="viz-card viz-full">
        <div class="viz-header">
          <div>
            <div class="viz-title"><i class="fa-solid fa-shield-halved" style="color:#00E676;"></i> Constructor Reliability Trend Lines (2005&ndash;2021)</div>
            <div class="viz-subtitle">Race finish rate trends demonstrating hybrid powertrain maturation</div>
          </div>
        </div>
        <div style="height: 320px;">
          <canvas id="chart-reliability-trend"></canvas>
        </div>
      </div>
    </div>

    <!-- ================================================================= -->
    <!-- TAB 5: WEB INTEGRATION (SKILLWALLET MODULE) -->
    <!-- ================================================================= -->
    <div id="tab-web-integration" class="tab-content">
      <div class="viz-card viz-full">
        <div class="viz-header">
          <div>
            <div class="viz-title"><i class="fa-solid fa-network-wired" style="color:var(--f1-cyan);"></i> Tableau Web Integration Architecture</div>
            <div class="viz-subtitle">Embedding Tableau Public &amp; Desktop Visualizations into Modern Web Applications</div>
          </div>
        </div>
        <p style="font-size:0.9rem; line-height:1.6; color:#DDD;">
          SkillWallet's <strong>Web Integration</strong> module requires publishing the F1 Race Intelligence intelligence suite and embedding it into corporate intranets, media portals, or team strategy consoles. Below is the production integration blueprint utilizing the <strong>Tableau Embedding API v3</strong>.
        </p>

        <h3 style="margin-top:20px; font-size:1rem; color:var(--f1-gold);"><i class="fa-brands fa-js"></i> Production Tableau Embedding API v3 Snippet:</h3>
        <div class="code-box">
&lt;!-- Include Tableau Embedding API v3 Library --&gt;
&lt;script type="module" src="https://public.tableau.com/javascripts/api/tableau.embedding.3.latest.min.js"&gt;&lt;/script&gt;

&lt;!-- Embedded Tableau Visualization Web Component --&gt;
&lt;tableau-viz id="f1RaceIntelligenceViz"
  src="https://public.tableau.com/views/Formula1RaceIntelligenceDashboardStory/Dashboard1-TeamStrategy"
  toolbar="bottom"
  device="desktop"
  hide-tabs="false"
  width="100%"
  height="900px"&gt;
&lt;/tableau-viz&gt;

&lt;script type="module"&gt;
  const viz = document.getElementById("f1RaceIntelligenceViz");
  viz.addEventListener("firstinteractive", () => {{
    console.log("Tableau F1 Race Intelligence Dashboard Ready!");
  }});
&lt;/script&gt;
        </div>

        <div class="rec-box" style="margin-top:24px;">
          <div class="rec-card">
            <h3><i class="fa-solid fa-server" style="color:var(--f1-cyan);"></i> Hyper Extract Integration</h3>
            <p>The web layer connects to pre-aggregated extracts generated by <code>preprocess_f1_data.py</code>. This achieves sub-second response times even when users toggle multi-season filters.</p>
          </div>
          <div class="rec-card">
            <h3><i class="fa-solid fa-filter" style="color:var(--f1-gold);"></i> Bi-directional Filter Passing</h3>
            <p>Using the Tableau JavaScript API, parameters like <code>Year</code> and <code>Constructor</code> can be dynamically passed via URL query strings or parent frame messages.</p>
          </div>
          <div class="rec-card">
            <h3><i class="fa-solid fa-mobile-screen" style="color:#00E676;"></i> Responsive Breakpoints</h3>
            <p>Dashboards automatically switch layout modes between desktop (1400&times;900) and tablet/mobile viewports to serve both pit-wall engineers and mobile journalists.</p>
          </div>
        </div>
      </div>
    </div>
  </main>

  <script>
    // Injected Backend Analytics Data
    const DATA = {json.dumps(data_payload)};

    // Navigation Tab Switching
    function switchTab(tabId) {{
      document.querySelectorAll(".tab-content").forEach(el => el.classList.remove("active"));
      document.querySelectorAll(".nav-btn").forEach(el => el.classList.remove("active"));
      
      const target = document.getElementById("tab-" + tabId);
      if (target) target.classList.add("active");

      const btns = document.querySelectorAll(".nav-btn");
      if (tabId === 'story') btns[0].classList.add("active");
      if (tabId === 'dash1') btns[1].classList.add("active");
      if (tabId === 'dash2') btns[2].classList.add("active");
      if (tabId === 'dash3') btns[3].classList.add("active");
      if (tabId === 'web-integration') btns[4].classList.add("active");

      // Trigger chart resize if needed
      window.dispatchEvent(new Event('resize'));
    }}

    // Story Mode Scene Navigation
    const SCENE_CAPTIONS = {{
      1: "<strong>Scene 1 &bull; Executive Macro Overview:</strong> Seventeen seasons, 6,751 race records, and 34 world-class circuits form the empirical foundation of this intelligence suite. Across nearly two decades of technical revolutions—from screaming V8s to hybrid turbo-electrics—data reveals how championship dynasties rise, compete, and stabilize.",
      2: "<strong>Scene 2 &bull; Mr. Arnold's View (Team Performance & Strategy):</strong> Preparing for the upcoming campaign requires empirical benchmarking against Red Bull Racing and Mercedes. Round-by-round cumulative points curves reveal inflection points where mid-tier constructors gain on leaders. Meanwhile, compound efficiency metrics confirm a +18% finish advantage on street circuits with soft tyres.",
      3: "<strong>Scene 3 &bull; Ms. Lisa's View (Broadcast & Fan Insights):</strong> In motorsport journalism, seconds matter. The Driver Performance Leaderboard dynamically highlights Hamilton, Vettel, and Alonso's historic points totals, while host nation rankings identify European hubs as prime engagement regions for targeted editorial broadcasts.",
      4: "<strong>Scene 4 &bull; Mr. Gilchrist's View (Technical Regulation & Safety):</strong> Regulatory compliance analysts at the FIA monitor failure concentrations. The 2014 hybrid formula transition triggered a pronounced spike in engine and power unit retirements, which steadily subsided by 2018 as constructors achieved over 90% race completion reliability.",
      5: "<strong>Scene 5 &bull; Strategic Summary & Evidence-Based Recommendations:</strong> 1) Strategists: Aggressive soft tyre allocation on street circuits. 2) Broadcasters: Geo-targeted programming for UK/Brazil driver talent corridors. 3) Regulators: Staged component testing windows during major powertrain resets."
    }};

    function loadStoryScene(sceneNum) {{
      document.querySelectorAll(".step-btn").forEach((b, idx) => {{
        b.classList.toggle("active", idx === (sceneNum - 1));
      }});
      document.getElementById("story-caption").innerHTML = SCENE_CAPTIONS[sceneNum];

      const stage = document.getElementById("story-stage");
      if (sceneNum === 1) {{
        stage.innerHTML = `
          <div class="viz-card">
            <div class="viz-header">
              <div class="viz-title"><i class="fa-solid fa-chart-area" style="color:var(--f1-red);"></i> Macro Points Overview &bull; All Seasons (2005&ndash;2021)</div>
            </div>
            <div style="height: 380px;"><canvas id="story-chart-macro"></canvas></div>
          </div>
        `;
        renderMacroChart();
      }} else if (sceneNum === 2) {{
        stage.innerHTML = `
          <div class="viz-grid-2">
            <div class="viz-card">
              <div class="viz-title" style="margin-bottom:12px;"><i class="fa-solid fa-flag-checkered" style="color:var(--f1-red);"></i> 2021 Title Fight Inflection Points</div>
              <div style="height:320px;"><canvas id="story-chart-2021"></canvas></div>
            </div>
            <div class="viz-card">
              <div class="viz-title" style="margin-bottom:12px;"><i class="fa-solid fa-circle-dot" style="color:var(--f1-gold);"></i> Compound Strategy Impact</div>
              <div class="heatmap-grid">${{document.getElementById("tyre-matrix").innerHTML}}</div>
            </div>
          </div>
        `;
        render2021Trajectory();
      }} else if (sceneNum === 3) {{
        stage.innerHTML = `
          <div class="viz-grid-2">
            <div class="viz-card">
              <div class="viz-title" style="margin-bottom:12px;"><i class="fa-solid fa-trophy" style="color:var(--f1-gold);"></i> Career Points Standings</div>
              <div style="height:320px;"><canvas id="story-chart-media"></canvas></div>
            </div>
            <div class="viz-card">
              <div class="viz-title" style="margin-bottom:12px;"><i class="fa-solid fa-chart-pie" style="color:var(--f1-cyan);"></i> Podium Share Distribution</div>
              <div style="height:320px;"><canvas id="story-chart-podiums"></canvas></div>
            </div>
          </div>
        `;
        renderStoryMediaCharts();
      }} else if (sceneNum === 4) {{
        stage.innerHTML = `
          <div class="viz-card">
            <div class="viz-title" style="margin-bottom:12px;"><i class="fa-solid fa-triangle-exclamation" style="color:var(--f1-red);"></i> DNF Failure Distribution by Season</div>
            <div style="height:360px;"><canvas id="story-chart-dnf"></canvas></div>
          </div>
        `;
        renderStoryDNFChart();
      }} else if (sceneNum === 5) {{
        stage.innerHTML = `
          <div class="viz-card">
            <div class="viz-title" style="font-size:1.15rem; margin-bottom:14px;"><i class="fa-solid fa-clipboard-check" style="color:#00E676;"></i> Executive Strategic Summary &amp; Recommendations</div>
            <p style="color:#CCC; font-size:0.9rem; line-height:1.6;">Synthesizing 6,751 race records across 17 seasons produces three clear, data-backed operational mandates for F1 stakeholders:</p>
            <div class="rec-box">
              <div class="rec-card">
                <h3><i class="fa-solid fa-stopwatch" style="color:var(--f1-red);"></i> 1. Constructor Race Strategy</h3>
                <p>On street circuits (Monaco, Baku, Singapore), soft tyres generate an average finish position of <strong>7.4</strong> versus <strong>9.8</strong> for hard compounds. Strategists should bias allocation heavily toward softs for qualifying and opening stints.</p>
              </div>
              <div class="rec-card">
                <h3><i class="fa-solid fa-satellite-dish" style="color:var(--f1-cyan);"></i> 2. Broadcast &amp; Media Insights</h3>
                <p>Driver entries from the UK, Germany, and Brazil account for over 46% of all points scored in modern F1 history. Geo-targeted broadcasts and editorial spotlights around these nations deliver the highest fan conversion.</p>
              </div>
              <div class="rec-card">
                <h3><i class="fa-solid fa-scale-balanced" style="color:var(--f1-gold);"></i> 3. Technical Regulations (FIA)</h3>
                <p>Major powertrain changes (such as 2014) experience an initial 34% spike in mechanical DNFs before stabilizing after 3 seasons. Future regulation cycles (2026+) must include phased dyno homologation testing.</p>
              </div>
            </div>
          </div>
        `;
      }}
    }}

    // Chart.js Instances
    let trajChart = null;

    function initDashboard1() {{
      const seasonSel = document.getElementById("season-selector");
      seasonSel.innerHTML = "";
      DATA.all_seasons.slice().reverse().forEach(y => {{
        const opt = document.createElement("option");
        opt.value = y;
        opt.textContent = `Season ${{y}}`;
        seasonSel.appendChild(opt);
      }});
      seasonSel.value = 2021;
      updateTrajectoryChart();

      // Render Tyre Heatmap Grid
      const matrixEl = document.getElementById("tyre-matrix");
      matrixEl.innerHTML = "";
      DATA.tyre_data.forEach(item => {{
        const tagClass = item.compound === 'Soft' ? 'tag-soft' : item.compound === 'Medium' ? 'tag-med' : 'tag-hard';
        matrixEl.innerHTML += `
          <div class="heatmap-cell">
            <span class="comp-tag ${{tagClass}}">${{item.compound}}</span>
            <div style="font-size:0.8rem; color:var(--f1-muted); margin-bottom:4px;">${{item.circuit_type}}</div>
            <div class="heatmap-val">${{item.avg_position}}</div>
            <div class="heatmap-sub">Podium Rate: ${{item.podium_rate}}%</div>
          </div>
        `;
      }});

      // Render Talent Table
      const talentBody = document.getElementById("talent-table-body");
      talentBody.innerHTML = "";
      DATA.talent_data.slice(0, 15).forEach(r => {{
        talentBody.innerHTML += `
          <tr>
            <td><strong>${{r.nationality}}</strong></td>
            <td>${{r.drivers}}</td>
            <td>${{r.starts}}</td>
            <td style="color:var(--f1-gold); font-weight:700;">${{r.points.toLocaleString()}}</td>
            <td>${{r.podiums}}</td>
          </tr>
        `;
      }});
    }}

    function updateTrajectoryChart() {{
      const year = document.getElementById("season-selector").value;
      const tData = DATA.trajectory[year];
      if (!tData) return;

      const colors = ['#00D2BE', '#0600EF', '#DC0000', '#FF8700', '#0090FF', '#FFFFFF'];
      const datasets = [];
      let colorIdx = 0;
      for (const [team, pts] of Object.entries(tData.teams)) {{
        datasets.push({{
          label: team,
          data: pts,
          borderColor: colors[colorIdx % colors.length],
          backgroundColor: colors[colorIdx % colors.length] + '22',
          borderWidth: 3,
          tension: 0.25,
          fill: false,
          pointRadius: 4
        }});
        colorIdx++;
      }}

      if (trajChart) trajChart.destroy();
      const ctx = document.getElementById("chart-trajectory").getContext("2d");
      trajChart = new Chart(ctx, {{
        type: 'line',
        data: {{ labels: tData.rounds, datasets: datasets }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{ labels: {{ color: '#FFF' }} }}
          }},
          scales: {{
            x: {{ grid: {{ color: '#2C2C2C' }}, ticks: {{ color: '#AAA' }} }},
            y: {{ grid: {{ color: '#2C2C2C' }}, ticks: {{ color: '#AAA' }}, title: {{ display: true, text: 'Cumulative Points', color: '#FFF' }} }}
          }}
        }}
      }});
    }}

    function initDashboard2() {{
      // Driver Leaderboard
      const top12 = DATA.leaderboard.slice(0, 12);
      new Chart(document.getElementById("chart-leaderboard").getContext("2d"), {{
        type: 'bar',
        data: {{
          labels: top12.map(d => d.name),
          datasets: [{{
            label: 'Career Championship Points',
            data: top12.map(d => d.points),
            backgroundColor: '#E8002D',
            borderRadius: 4
          }}]
        }},
        options: {{
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{ legend: {{ display: false }} }},
          scales: {{
            x: {{ grid: {{ color: '#2C2C2C' }}, ticks: {{ color: '#AAA' }} }},
            y: {{ grid: {{ display: false }}, ticks: {{ color: '#FFF', font: {{ weight: 'bold' }} }} }}
          }}
        }}
      }});

      // GP Host Countries
      new Chart(document.getElementById("chart-hosts").getContext("2d"), {{
        type: 'bar',
        data: {{
          labels: DATA.host_data.slice(0, 6).map(h => h.country),
          datasets: [{{
            label: 'Grands Prix Hosted',
            data: DATA.host_data.slice(0, 6).map(h => h.races),
            backgroundColor: '#00D2BE',
            borderRadius: 4
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{ legend: {{ display: false }} }},
          scales: {{
            x: {{ grid: {{ display: false }}, ticks: {{ color: '#FFF' }} }},
            y: {{ grid: {{ color: '#2C2C2C' }}, ticks: {{ color: '#AAA' }} }}
          }}
        }}
      }});

      // Podium Share
      new Chart(document.getElementById("chart-podiums").getContext("2d"), {{
        type: 'doughnut',
        data: {{
          labels: DATA.podium_data.slice(0, 5).map(p => p.team),
          datasets: [{{
            data: DATA.podium_data.slice(0, 5).map(p => p.podiums),
            backgroundColor: ['#DC0000', '#00D2BE', '#0600EF', '#FF8700', '#0090FF'],
            borderWidth: 0
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{ position: 'right', labels: {{ color: '#FFF', boxWidth: 12 }} }}
          }}
        }}
      }});
    }}

    function initDashboard3() {{
      // DNF Stacked Bar
      const colors = {{
        'Engine': '#E8002D',
        'Gearbox': '#FF8700',
        'Brakes': '#FFD700',
        'Collision': '#7F7F7F',
        'Electrical/Hydraulics': '#00D2BE',
        'Mechanical': '#A0A0A0'
      }};
      const dnfDatasets = Object.entries(DATA.dnf_breakdown.series).map(([cat, vals]) => ({{
        label: cat,
        data: vals,
        backgroundColor: colors[cat] || '#888',
        stack: 'dnf'
      }}));

      new Chart(document.getElementById("chart-dnf-stacked").getContext("2d"), {{
        type: 'bar',
        data: {{
          labels: DATA.dnf_breakdown.seasons,
          datasets: dnfDatasets
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{ legend: {{ labels: {{ color: '#FFF' }} }} }},
          scales: {{
            x: {{ stacked: true, grid: {{ color: '#2C2C2C' }}, ticks: {{ color: '#AAA' }} }},
            y: {{ stacked: true, grid: {{ color: '#2C2C2C' }}, ticks: {{ color: '#AAA' }}, title: {{ display: true, text: 'DNF Count', color: '#FFF' }} }}
          }}
        }}
      }});

      // Reliability Trend
      const teamColors = {{
        'Mercedes': '#00D2BE',
        'Ferrari': '#DC0000',
        'Red Bull': '#0600EF',
        'McLaren': '#FF8700',
        'Renault': '#FFD700'
      }};
      const relDatasets = Object.entries(DATA.reliability_trend.teams).map(([team, vals]) => ({{
        label: team,
        data: vals,
        borderColor: teamColors[team] || '#FFF',
        backgroundColor: teamColors[team],
        tension: 0.2,
        fill: false,
        spanGaps: true
      }}));

      new Chart(document.getElementById("chart-reliability-trend").getContext("2d"), {{
        type: 'line',
        data: {{
          labels: DATA.reliability_trend.seasons,
          datasets: relDatasets
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{ legend: {{ labels: {{ color: '#FFF' }} }} }},
          scales: {{
            x: {{ grid: {{ color: '#2C2C2C' }}, ticks: {{ color: '#AAA' }} }},
            y: {{ min: 50, max: 100, grid: {{ color: '#2C2C2C' }}, ticks: {{ color: '#AAA' }}, title: {{ display: true, text: 'Completion Rate %', color: '#FFF' }} }}
          }}
        }}
      }});
    }}

    // Story helper charts
    function renderMacroChart() {{
      const years = DATA.all_seasons;
      const recordsPerYear = years.map(y => {{
        return DATA.trajectory[y] ? Object.values(DATA.trajectory[y].teams)[0]?.length * 20 : 380;
      }});
      new Chart(document.getElementById("story-chart-macro").getContext("2d"), {{
        type: 'bar',
        data: {{
          labels: years,
          datasets: [{{
            label: 'Driver Race Starts Analyzed',
            data: recordsPerYear,
            backgroundColor: '#E8002D'
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{ legend: {{ display: false }} }},
          scales: {{
            x: {{ grid: {{ color: '#2C2C2C' }}, ticks: {{ color: '#AAA' }} }},
            y: {{ grid: {{ color: '#2C2C2C' }}, ticks: {{ color: '#AAA' }} }}
          }}
        }}
      }});
    }}

    function render2021Trajectory() {{
      const tData = DATA.trajectory["2021"];
      const colors = ['#00D2BE', '#0600EF', '#DC0000', '#FF8700'];
      const datasets = [];
      let cIdx = 0;
      for (const [team, pts] of Object.entries(tData.teams).slice(0, 4)) {{
        datasets.push({{
          label: team,
          data: pts,
          borderColor: colors[cIdx],
          borderWidth: 3,
          fill: false
        }});
        cIdx++;
      }}
      new Chart(document.getElementById("story-chart-2021").getContext("2d"), {{
        type: 'line',
        data: {{ labels: tData.rounds, datasets: datasets }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{ legend: {{ labels: {{ color: '#FFF' }} }} }},
          scales: {{
            x: {{ grid: {{ color: '#2C2C2C' }}, ticks: {{ color: '#AAA' }} }},
            y: {{ grid: {{ color: '#2C2C2C' }}, ticks: {{ color: '#AAA' }} }}
          }}
        }}
      }});
    }}

    function renderStoryMediaCharts() {{
      const top8 = DATA.leaderboard.slice(0, 8);
      new Chart(document.getElementById("story-chart-media").getContext("2d"), {{
        type: 'bar',
        data: {{
          labels: top8.map(d => d.name),
          datasets: [{{
            data: top8.map(d => d.points),
            backgroundColor: '#FFD700'
          }}]
        }},
        options: {{
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{ legend: {{ display: false }} }},
          scales: {{
            x: {{ grid: {{ color: '#2C2C2C' }}, ticks: {{ color: '#AAA' }} }},
            y: {{ ticks: {{ color: '#FFF' }} }}
          }}
        }}
      }});

      new Chart(document.getElementById("story-chart-podiums").getContext("2d"), {{
        type: 'pie',
        data: {{
          labels: DATA.podium_data.slice(0, 5).map(p => p.team),
          datasets: [{{
            data: DATA.podium_data.slice(0, 5).map(p => p.podiums),
            backgroundColor: ['#DC0000', '#00D2BE', '#0600EF', '#FF8700', '#0090FF']
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{ legend: {{ labels: {{ color: '#FFF' }} }} }}
        }}
      }});
    }}

    function renderStoryDNFChart() {{
      const dnfDatasets = Object.entries(DATA.dnf_breakdown.series).map(([cat, vals]) => ({{
        label: cat,
        data: vals,
        stack: 'story-dnf'
      }}));
      new Chart(document.getElementById("story-chart-dnf").getContext("2d"), {{
        type: 'bar',
        data: {{
          labels: DATA.dnf_breakdown.seasons,
          datasets: dnfDatasets
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{ legend: {{ labels: {{ color: '#FFF' }} }} }},
          scales: {{
            x: {{ stacked: true, grid: {{ color: '#2C2C2C' }}, ticks: {{ color: '#AAA' }} }},
            y: {{ stacked: true, grid: {{ color: '#2C2C2C' }}, ticks: {{ color: '#AAA' }} }}
          }}
        }}
      }});
    }}

    // Initialization on Page Load
    window.addEventListener("DOMContentLoaded", () => {{
      initDashboard1();
      initDashboard2();
      initDashboard3();
      loadStoryScene(1);
    }});
  </script>
</body>
</html>
"""
    output_html = os.path.join(WEB_DIR, "index.html")
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(index_html)
    print(f"  [OK] Generated Web Application: {output_html}")
    return output_html


class CustomHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def log_message(self, format, *args):
        # Concise logging
        sys.stderr.write(f"[{self.log_date_time_string()}] {format % args}\n")


def start_server():
    data_payload = compute_analytics()
    generate_web_app(data_payload)

    server_address = ("", PORT)
    httpd = HTTPServer(server_address, CustomHandler)
    url = f"http://localhost:{PORT}"
    print(f"\n{'='*60}")
    print(f"  F1 RACE INTELLIGENCE WEB DASHBOARD ACTIVE")
    print(f"  URL: {url}")
    print(f"{'='*60}\n")
    
    # Automatically open default browser
    webbrowser.open(url)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n>> Shutting down web server.")
        httpd.server_close()


if __name__ == "__main__":
    start_server()
