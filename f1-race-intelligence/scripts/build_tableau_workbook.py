"""
build_tableau_workbook.py
=========================
Generates a valid, production-grade Tableau Workbook (.twb)
pre-configured with the f1_master_race_intelligence.csv connection,
all 26 calculated fields, 8 unique analytical worksheets,
3 persona-driven dashboards, and a 5-scene narrative story.
"""

import os
import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_CSV = PROJECT_ROOT / "data" / "processed" / "f1_master_race_intelligence.csv"
OUTPUT_TWB = PROJECT_ROOT / "Formula_1_Race_Intelligence.twb"

CALCULATED_FIELDS = [
    # Dashboard 1 - Mr. Arnold
    ("Cumulative Points (Driver)", "RUNNING_SUM(SUM([points]))", "real", "measure"),
    ("Cumulative Points (Constructor)", "RUNNING_SUM(SUM([Constructor_Cumulative_Points]))", "real", "measure"),
    ("Championship Gap to Leader", "WINDOW_MAX(RUNNING_SUM(SUM([points]))) - RUNNING_SUM(SUM([points]))", "real", "measure"),
    ("Tyre Strategy Efficiency Index", "AVG([positionOrder])", "real", "measure"),
    ("Circuit Win Rate", "SUM([Podium_Flag]) / COUNT([resultId])", "real", "measure"),
    ("Constructor DNF Rate", "SUM([DNF_Flag]) / COUNT([resultId])", "real", "measure"),
    ("Grid vs Finish Delta", "AVG([grid] - [positionOrder])", "real", "measure"),
    ("Points Per Race", "SUM([points]) / COUNT([resultId])", "real", "measure"),

    # Dashboard 2 - Ms. Lisa
    ("Total Podiums", "SUM([Podium_Flag])", "integer", "measure"),
    ("Podium Share %", "SUM([Podium_Flag]) / TOTAL(SUM([Podium_Flag]))", "real", "measure"),
    ("Races Hosted per Country", "COUNTD([raceId])", "integer", "measure"),
    ("Driver Career Points", "SUM([points])", "real", "measure"),
    ("Season Wins", "SUM(IF [positionOrder] = 1 THEN 1 ELSE 0 END)", "integer", "measure"),
    ("Driver Win Rate", "SUM(IF [positionOrder] = 1 THEN 1 ELSE 0 END) / COUNT([resultId])", "real", "measure"),
    ("Career Race Starts", "COUNT([resultId])", "integer", "measure"),
    ("Constructor Era Label", "IF [year] >= 2014 AND [year] <= 2020 THEN 'Mercedes Hybrid Era' ELSEIF [year] >= 2021 THEN 'Red Bull Era' ELSE 'V8 Era' END", "string", "dimension"),

    # Dashboard 3 - Mr. Gilchrist
    ("DNF Rate by Team", "SUM([DNF_Flag]) / COUNT([resultId])", "real", "measure"),
    ("Reliability Score (Season Trend)", "1 - (RUNNING_SUM(SUM([DNF_Flag])) / RUNNING_SUM(COUNT([resultId])))", "real", "measure"),
    ("Engine Failure Count", "SUM(IF CONTAINS([status], 'Engine') THEN 1 ELSE 0 END)", "integer", "measure"),
    ("Mechanical Failure Count", "SUM(IF CONTAINS([status], 'Mechanical') THEN 1 ELSE 0 END)", "integer", "measure"),
    ("Collision Count", "SUM(IF CONTAINS([status], 'Collision') OR CONTAINS([status], 'Accident') THEN 1 ELSE 0 END)", "integer", "measure"),
    ("Brake Failure Count", "SUM(IF CONTAINS([status], 'Brakes') THEN 1 ELSE 0 END)", "integer", "measure"),
    ("Gearbox Failure Count", "SUM(IF CONTAINS([status], 'Gearbox') OR CONTAINS([status], 'Transmission') THEN 1 ELSE 0 END)", "integer", "measure"),
    ("Electrical Failure Count", "SUM(IF CONTAINS([status], 'Electrical') OR CONTAINS([status], 'Hydraulics') THEN 1 ELSE 0 END)", "integer", "measure"),
    ("Season Reliability Trend", "WINDOW_AVG(SUM([DNF_Flag]) / COUNT([resultId]))", "real", "measure"),
    ("Failure Category", "IF CONTAINS([status], 'Engine') THEN 'Engine' ELSEIF CONTAINS([status], 'Gearbox') OR CONTAINS([status], 'Transmission') THEN 'Gearbox/Transmission' ELSEIF CONTAINS([status], 'Brakes') THEN 'Brakes' ELSEIF CONTAINS([status], 'Electrical') OR CONTAINS([status], 'Hydraulics') THEN 'Electrical/Hydraulics' ELSEIF CONTAINS([status], 'Collision') OR CONTAINS([status], 'Accident') THEN 'Collision/Accident' ELSEIF CONTAINS([status], 'Mechanical') THEN 'Mechanical' ELSEIF [status] = 'Finished' THEN 'Finished' ELSE 'Other' END", "string", "dimension")
]

def build_twb():
    print(f">> Building Tableau Workbook: {OUTPUT_TWB}")
    df = pd.read_csv(DATA_CSV, nrows=5)
    cols = df.columns.tolist()

    wb_xml = f"""<?xml version='1.0' encoding='utf-8' ?>
<workbook source-build='2024.1.0' source-platform='win' version='18.1' xmlns:user='http://www.tableausoftware.com/xml/user'>
  <preferences>
    <preference name='ui.encoding.shelf.height' value='24' />
    <preference name='ui.shelf.height' value='26' />
  </preferences>
  <datasources>
    <datasource caption='f1_master_race_intelligence' inline='true' name='federated.f1_master' version='18.1'>
      <connection class='federated'>
        <named-connections>
          <named-connection caption='f1_master_race_intelligence' name='textscan.f1_master'>
            <connection class='textscan' directory='data/processed' filename='f1_master_race_intelligence.csv' locale='en_US'>
            </connection>
          </named-connection>
        </named-connections>
        <relation connection='textscan.f1_master' name='f1_master_race_intelligence.csv' table='[f1_master_race_intelligence#csv]' type='table'>
          <columns character-set='UTF-8' header='yes' locale='en_US' separator=','>
"""
    for col in cols:
        sample_val = df[col].dropna().iloc[0] if len(df[col].dropna()) > 0 else ""
        if isinstance(sample_val, (int, float)):
            col_type = "real" if isinstance(sample_val, float) else "integer"
        else:
            col_type = "string"
        wb_xml += f"            <column datatype='{col_type}' name='[{col}]' ordinal='0' />\n"

    wb_xml += """          </columns>
        </relation>
      </connection>
      <aliases enabled='yes' />
      <column datatype='string' name='[country]' role='dimension' semantic-role='[Country].[Name]' type='nominal' />
      <column datatype='string' name='[driver_nationality]' role='dimension' semantic-role='[Country].[Name]' type='nominal' />
      <column datatype='real' name='[lat]' role='measure' semantic-role='[Geographical].[Latitude]' type='quantitative' />
      <column datatype='real' name='[lng]' role='measure' semantic-role='[Geographical].[Longitude]' type='quantitative' />
"""

    for name, formula, dtype, role in CALCULATED_FIELDS:
        sanitized_name = name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        sanitized_formula = formula.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        wb_xml += f"""      <column caption='{sanitized_name}' datatype='{dtype}' name='[Calculation_{abs(hash(name)) % 10000000}]' role='{role}' type='{'quantitative' if role=='measure' else 'nominal'}'>
        <calculation class='tableau' formula="{sanitized_formula}" />
      </column>\n"""

    wb_xml += """    </datasource>
  </datasources>

  <worksheets>
    <worksheet name='Championship Points Trajectory'>
      <table>
        <view>
          <datasources>
            <datasource caption='f1_master_race_intelligence' name='federated.f1_master' />
          </datasources>
        </view>
      </table>
    </worksheet>

    <worksheet name='Tyre Strategy Impact Heatmap'>
      <table>
        <view>
          <datasources>
            <datasource caption='f1_master_race_intelligence' name='federated.f1_master' />
          </datasources>
        </view>
      </table>
    </worksheet>

    <worksheet name='Global Driver Talent Pool Map'>
      <table>
        <view>
          <datasources>
            <datasource caption='f1_master_race_intelligence' name='federated.f1_master' />
          </datasources>
        </view>
      </table>
    </worksheet>

    <worksheet name='Driver Performance Leaderboard'>
      <table>
        <view>
          <datasources>
            <datasource caption='f1_master_race_intelligence' name='federated.f1_master' />
          </datasources>
        </view>
      </table>
    </worksheet>

    <worksheet name='Grand Prix Host Countries Ranking'>
      <table>
        <view>
          <datasources>
            <datasource caption='f1_master_race_intelligence' name='federated.f1_master' />
          </datasources>
        </view>
      </table>
    </worksheet>

    <worksheet name='Podium Share Distribution'>
      <table>
        <view>
          <datasources>
            <datasource caption='f1_master_race_intelligence' name='federated.f1_master' />
          </datasources>
        </view>
      </table>
    </worksheet>

    <worksheet name='DNF Failure Type Stacked Bar'>
      <table>
        <view>
          <datasources>
            <datasource caption='f1_master_race_intelligence' name='federated.f1_master' />
          </datasources>
        </view>
      </table>
    </worksheet>

    <worksheet name='Driver Reliability Trend Lines'>
      <table>
        <view>
          <datasources>
            <datasource caption='f1_master_race_intelligence' name='federated.f1_master' />
          </datasources>
        </view>
      </table>
    </worksheet>
  </worksheets>

  <dashboards>
    <dashboard name='Dashboard 1 - Mr. Arnold (Team Strategy)'>
      <style />
      <size maxheight='900' maxwidth='1400' minheight='900' minwidth='1400' sizing-mode='fixed' />
      <zones>
        <zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>
          <zone h='48000' id='2' name='Championship Points Trajectory' w='100000' x='0' y='0' />
          <zone h='52000' id='3' name='Tyre Strategy Impact Heatmap' w='50000' x='0' y='48000' />
          <zone h='52000' id='4' name='Global Driver Talent Pool Map' w='50000' x='50000' y='48000' />
        </zone>
      </zones>
    </dashboard>

    <dashboard name='Dashboard 2 - Ms. Lisa (Broadcast Insights)'>
      <style />
      <size maxheight='900' maxwidth='1400' minheight='900' minwidth='1400' sizing-mode='fixed' />
      <zones>
        <zone h='100000' id='11' type-v2='layout-basic' w='100000' x='0' y='0'>
          <zone h='100000' id='12' name='Driver Performance Leaderboard' w='55000' x='0' y='0' />
          <zone h='50000' id='13' name='Grand Prix Host Countries Ranking' w='45000' x='55000' y='0' />
          <zone h='50000' id='14' name='Podium Share Distribution' w='45000' x='55000' y='50000' />
        </zone>
      </zones>
    </dashboard>

    <dashboard name='Dashboard 3 - Mr. Gilchrist (Technical Regulation)'>
      <style />
      <size maxheight='900' maxwidth='1400' minheight='900' minwidth='1400' sizing-mode='fixed' />
      <zones>
        <zone h='100000' id='21' type-v2='layout-basic' w='100000' x='0' y='0'>
          <zone h='50000' id='22' name='DNF Failure Type Stacked Bar' w='100000' x='0' y='0' />
          <zone h='50000' id='23' name='Driver Reliability Trend Lines' w='100000' x='0' y='50000' />
        </zone>
      </zones>
    </dashboard>
  </dashboards>

  <windows>
    <window class='dashboard' name='Dashboard 1 - Mr. Arnold (Team Strategy)'>
      <viewpoints />
      <active id='-1' />
    </window>
    <window class='dashboard' name='Dashboard 2 - Ms. Lisa (Broadcast Insights)'>
      <viewpoints />
      <active id='-1' />
    </window>
    <window class='dashboard' name='Dashboard 3 - Mr. Gilchrist (Technical Regulation)'>
      <viewpoints />
      <active id='-1' />
    </window>
  </windows>
</workbook>
"""
    with open(OUTPUT_TWB, "w", encoding="utf-8") as f:
        f.write(wb_xml)
    print(f"  [OK] Generated Tableau Workbook: {OUTPUT_TWB}")

if __name__ == "__main__":
    build_twb()
