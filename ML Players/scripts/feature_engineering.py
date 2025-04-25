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
   - per36_* (pts36, reb36, ast36, stl36, blk36, tov36)
"""
import pandas as pd
from pathlib import Path

RAW     = Path("nba_rating/data/raw")
CURATED = Path("nba_rating/data/curated")
SEASONS = [f"{y}-{str(y+1)[-2:]}" for y in range(1999, 2024)]

for season in SEASONS:
    # 1) charger raw gamelog
    gl = pd.read_parquet(RAW / f"player_gamelog_{season}.parquet")
    gl = gl[gl["MIN"] > 0]  # éviter division par zéro

    # 2) agrégation des compteurs totaux
    agg = gl.groupby("PLAYER_ID").agg(
        fgm_total            = ("FGM", "sum"),
        fg3m_total           = ("FG3M", "sum"),
        fga_total            = ("FGA", "sum"),
        fta_total            = ("FTA", "sum"),
        pts_total            = ("PTS", "sum"),
        stl_total            = ("STL", "sum"),
        blk_total            = ("BLK", "sum"),
        tov_total            = ("TOV", "sum"),
        reb_total            = ("REB", "sum"),
        ast_total            = ("AST", "sum"),
        plus_minus_total     = ("PLUS_MINUS", "sum"),
        min_total            = ("MIN", "sum"),
        gp                   = ("GAME_ID", "nunique")
    )

    # 3) calcul des ratios et per36
    agg["efg_pct"]  = (agg["fgm_total"] + 0.5 * agg["fg3m_total"]) / agg["fga_total"]
    agg["ts_pct"]   = agg["pts_total"] / (2 * (agg["fga_total"] + 0.44 * agg["fta_total"]))
    agg["stl_mean"] = agg["stl_total"] / agg["gp"]
    agg["blk_mean"] = agg["blk_total"] / agg["gp"]
    agg["tov_mean"] = agg["tov_total"] / agg["gp"]

    # per36 pour stats importantes
    per36_stats = [
        ("pts_total", "pts36"),
        ("reb_total", "reb36"),
        ("ast_total", "ast36"),
        ("stl_total", "stl36"),
        ("blk_total", "blk36"),
        ("tov_total", "tov36"),
        ("plus_minus_total", "pm36")
    ]
    for raw_col, new_col in per36_stats:
        agg[new_col] = agg[raw_col] * (36 / agg["min_total"])

    new_feats = agg[[
        "efg_pct","ts_pct",
        "stl_mean","blk_mean","tov_mean",
        "pts36","reb36","ast36","stl36","blk36","tov36","pm36"
    ]].reset_index()

    # 4) chargement du fichier curated existant et merge
    ps = pd.read_parquet(CURATED / f"player_season_{season}.parquet")
    df = ps.merge(new_feats, on="PLAYER_ID", how="left")

    # 5) sauvegarde
    df.to_parquet(CURATED / f"player_season_{season}.parquet", index=False)
    print(f"✅ Features avancées ajoutées pour {season}")
