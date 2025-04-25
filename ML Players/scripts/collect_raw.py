# collect_raw.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
collect_raw.py
--------------
Collecte les données brutes NBA :
  · player_gamelog (P)
  · player_phys + POSITION + EXP (CommonTeamRoster)
  · bulk offense → esv_mean (LeagueDashPlayerStats)
  · team pace via GameLog (T)
  · DEF_RATING désactivé pour rapidité
"""
import time, random
from pathlib import Path
import pandas as pd
from tqdm import tqdm
from nba_api.stats.static import teams
from nba_api.stats.endpoints import (
    LeagueGameLog,
    CommonTeamRoster,
    LeagueDashPlayerStats,
)

# Répertoire raw
RAW_DIR = Path("nba_rating/data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

SEASONS = [f"{y}-{str(y+1)[-2:]}" for y in range(1999, 2024)]
TEAMS   = teams.get_teams()

def convert_height(ht: str) -> float:
    try:
        ft, inch = map(int, ht.split("-"))
        return ft * 30.48 + inch * 2.54
    except:
        return None

def collect_gamelog(season: str):
    out_path = RAW_DIR / f"player_gamelog_{season}.parquet"
    if out_path.exists():
        print(f"📁 Gamelog {season} déjà présent")
        return
    df = LeagueGameLog(
        player_or_team_abbreviation="P",
        season=season,
        season_type_all_star="Regular Season",
        timeout=60
    ).get_data_frames()[0]
    df.to_parquet(out_path, index=False)
    print(f"✅ {season}: {len(df)} lignes")
    time.sleep(1)

def collect_phys(season: str):
    out_path = RAW_DIR / f"player_phys_{season}.parquet"
    if out_path.exists():
        print(f"📁 Physiques {season} déjà présent")
        return
    rows = []
    for tm in tqdm(TEAMS, desc=f"Mensurations {season}"):
        try:
            df_tm = CommonTeamRoster(tm["id"], season, timeout=30).get_data_frames()[0]
            rows.append(df_tm)
        except:
            pass
        time.sleep(random.uniform(0.3, 0.6))
    df = pd.concat(rows, ignore_index=True)
    df["height_cm"] = df["HEIGHT"].apply(convert_height)
    df["weight_kg"] = pd.to_numeric(df["WEIGHT"], errors="coerce") / 2.205
    df["bmi"]       = df["weight_kg"] / (df["height_cm"]/100)**2
    df = df.rename(columns={"AGE":"age","EXP":"exp"})
    df.to_parquet(out_path, index=False)
    print(f"✅ {season}: {len(df)} joueurs physiques")

def collect_esv(season: str):
    out_path = RAW_DIR / f"player_esv_{season}.parquet"
    if out_path.exists():
        return
    bulk = LeagueDashPlayerStats(
        season=season,
        season_type_all_star="Regular Season"
    ).get_data_frames()[0]
    bulk["esv_mean"] = ((bulk["FGM"] - bulk["FG3M"]) * 2 + bulk["FG3M"] * 3) / bulk["GP"]
    bulk[["PLAYER_ID","esv_mean"]].to_parquet(out_path, index=False)
    print(f"✅ {season}: ESV pour {len(bulk)} joueurs")

def collect_pace(season: str):
    out_path = RAW_DIR / f"team_pace_{season}.parquet"
    if out_path.exists():
        return
    tgl = LeagueGameLog(
        player_or_team_abbreviation="T",
        season=season,
        season_type_all_star="Regular Season",
        timeout=60
    ).get_data_frames()[0]
    tgl["poss"] = tgl["FGA"] + 0.4*tgl["FTA"] - tgl["OREB"] + tgl["TOV"]
    pace = tgl.groupby("TEAM_ID")["poss"].mean().reset_index().rename(columns={"poss":"pace"})
    pace.to_parquet(out_path, index=False)
    print(f"✅ {season}: Pace pour {len(pace)} équipes")

if __name__ == "__main__":
    print(f"📦 Collecte raw dans {RAW_DIR.resolve()}")
    for season in SEASONS:
        print(f"\n=== Saison {season} ===")
        collect_gamelog(season)
        collect_phys(season)
        collect_esv(season)
        collect_pace(season)
    print("\n✅ Collecte raw terminée.")
