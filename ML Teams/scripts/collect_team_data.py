#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
collect_team_data.py
--------------------
Collecte les GameLogs NBA pour les équipes :
  · GameLog des équipes (T)
  · Sauvegarde en Parquet dans data/raw/
"""

import time
from pathlib import Path
import pandas as pd
from nba_api.stats.endpoints import LeagueGameLog

# Définir le chemin de base
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"

# Créer les dossiers data/ et data/raw/ s'ils n'existent pas
if not DATA_DIR.exists():
    DATA_DIR.mkdir(parents=True)
if not RAW_DIR.exists():
    RAW_DIR.mkdir(parents=True)

# Définir les saisons à télécharger
SEASONS = [f"{year}-{str(year+1)[-2:]}" for year in range(1999, 2024)]  # 2018-2019 à 2023-2024

def collect_team_gamelog(season: str):
    """
    Récupère les GameLogs d'une saison et sauvegarde en Parquet.
    """
    out_path = RAW_DIR / f"team_gamelog_{season}.parquet"
    
    if out_path.exists():
        print(f"📁 GameLog {season} déjà présent")
        return

    try:
        df = LeagueGameLog(
            player_or_team_abbreviation="T",  # "T" pour Team
            season=season,
            season_type_all_star="Regular Season",
            timeout=60
        ).get_data_frames()[0]

        df.to_parquet(out_path, index=False)
        print(f"✅ {season}: {len(df)} matchs collectés")

    except Exception as e:
        print(f"❌ Erreur pour {season} : {e}")

    time.sleep(1)  # Petite pause pour éviter d'être bloqué par l'APIpwd

if __name__ == "__main__":
    print(f"📦 Collecte des GameLogs dans {RAW_DIR.resolve()}")
    for season in SEASONS:
        print(f"\n=== Saison {season} ===")
        collect_team_gamelog(season)
    print("\n✅ Collecte des GameLogs terminée.")

    

