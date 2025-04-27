#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
collect_team_data.py
--------------------
Collecte des données brutes NBA pour les équipes :
  · GameLog des équipes (TEAM)
  · Calcul des stats moyennes par équipe et par saison
"""

import time
from pathlib import Path
import pandas as pd
from nba_api.stats.endpoints import LeagueGameLog

# Définir le dossier de sauvegarde
RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Définir les saisons souhaitées
SEASONS = [f"{year}-{str(year+1)[-2:]}" for year in range(2018, 2024)]  # 2018-2019 à 2023-2024

def collect_team_gamelog(season: str):
    """
    Récupère les GameLogs d'une saison et sauvegarde en Parquet.
    """
    out_path = RAW_DIR / f"team_gamelog_{season}.parquet"
    
    if out_path.exists():
        print(f"📁 Données déjà présentes pour {season}")
        return

    print(f"⏳ Récupération des GameLogs pour la saison {season}…")
    
    try:
        # Appel API
        df = LeagueGameLog(
            player_or_team_abbreviation="T",  # "T" pour Team
            season=season,
            season_type_all_star="Regular Season",
            timeout=60
        ).get_data_frames()[0]

        # Sauvegarde brute sans transformation
        df.to_parquet(out_path, index=False)
        print(f"✅ Données sauvegardées : {out_path.name}")

    except Exception as e:
        print(f"❌ Erreur lors de la récupération pour {season} : {e}")

if __name__ == "__main__":
    print(f"🚀 Lancement de la collecte dans {RAW_DIR.resolve()}")
    
    for season in SEASONS:
        collect_team_gamelog(season)
        time.sleep(1)  # Petite pause pour éviter d'être bloqué par l'API
    
    print("\n🏁 Collecte des données équipes terminée.")

    
