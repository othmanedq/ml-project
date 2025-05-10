#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
feature_engineering.py
----------------------
À partir de raw/player_gamelog_{season}.parquet et
   curated/player_season_{season}.parquet,
   calcule et ajoute :
   - efg_pct, ts_pct
   - stl_mean, blk_mean, tov_mean
   - per36_* (pts36, reb36, ast36, stl36, blk36, tov36, pm36)
"""
import pandas as pd
from pathlib import Path

# Chemins relatifs au projet
RAW     = Path("nba_rating/data/raw")
CURATED = Path("nba_rating/data/curated")

# 1) Détection des saisons disponibles
files   = sorted(RAW.glob("player_gamelog_*.parquet"))
seasons = [f.stem.split("_")[-1] for f in files]

for season in seasons:
    print(f"🔄 Traitement de la saison {season}...")

    # 2) Chargement des logs bruts
    df_raw = pd.read_parquet(RAW / f"player_gamelog_{season}.parquet")

    # 3) Calcul des indicateurs avancés
    # Effective FG%
    df_raw["efg_pct"] = (df_raw["FGM"] + 0.5 * df_raw["FG3M"]) / df_raw["FGA"]
    # True Shooting%
    df_raw["ts_pct"]  = df_raw["PTS"] / (2 * (df_raw["FGA"] + 0.44 * df_raw["FTA"]))

    # Agrégation par joueur
    agg = df_raw.groupby("PLAYER_ID").agg(
        efg_pct    = ("efg_pct", "mean"),
        ts_pct     = ("ts_pct",  "mean"),
        stl_mean   = ("STL",     "mean"),
        blk_mean   = ("BLK",     "mean"),
        tov_mean   = ("TOV",     "mean"),
        pts_total  = ("PTS",     "sum" ),
        reb_total  = ("REB",     "sum" ),
        ast_total  = ("AST",     "sum" ),
        stl_total  = ("STL",     "sum" ),
        blk_total  = ("BLK",     "sum" ),
        tov_total  = ("TOV",     "sum" ),
        min_total  = ("MIN",     "sum" ),
        pm_total   = ("PLUS_MINUS", "sum")
    )

    # 4) Calcul des per36 (incluant pm)
    per36_map = {
        "pts_total": "pts36", "reb_total": "reb36", "ast_total": "ast36",
        "stl_total": "stl36", "blk_total": "blk36", "tov_total": "tov36",
        "pm_total":  "pm36"
    }
    # Évite la division par zéro
    for raw_col, new_col in per36_map.items():
        agg[new_col] = agg[raw_col] * (36 / agg["min_total"]) \
                        .replace([float('inf'), -float('inf')], pd.NA)

    # 5) Sélection des nouvelles features
    new_feats = agg[[
        "efg_pct","ts_pct",
        "stl_mean","blk_mean","tov_mean",
        "pts36","reb36","ast36","stl36","blk36","tov36","pm36"
    ]].reset_index()

    # 6) Merge avec le fichier season déjà curé
    ps     = pd.read_parquet(CURATED / f"player_season_{season}.parquet")
    df_out = ps.merge(new_feats, on="PLAYER_ID", how="left")

    # 7) Sauvegarde
    df_out.to_parquet(CURATED / f"player_season_{season}.parquet", index=False)
    print(f"✅ Features avancées ajoutées pour {season}")
