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
   - per36_* (pts36,…)
   - shooting splits: fg2_pct, fg3_pct, ft_pct
   - usage_rate (approx)
   - ast_tov_ratio
"""
import pandas as pd
from pathlib import Path

RAW     = Path("nba_rating/data/raw")
CURATED = Path("nba_rating/data/curated")

files   = sorted(RAW.glob("player_gamelog_*.parquet"))
seasons = [f.stem.rsplit("_",1)[-1] for f in files]

for season in seasons:
    print(f"🔄 Traitement de la saison {season}...")

    # 1) Chargement
    df_raw = pd.read_parquet(RAW / f"player_gamelog_{season}.parquet")

    # 2) Indicateurs de tir
    df_raw["FG2M"]    = df_raw["FGM"] - df_raw["FG3M"]
    df_raw["FG2A"]    = df_raw["FGA"] - df_raw["FG3A"]
    df_raw["fg2_pct"] = df_raw["FG2M"] / df_raw["FG2A"]
    df_raw["fg3_pct"] = df_raw["FG3M"] / df_raw["FG3A"]
    df_raw["ft_pct"]  = df_raw["FTM"]  / df_raw["FTA"]

    # 3) Indicateurs avancés déjà existants
    df_raw["efg_pct"] = (df_raw["FGM"] + 0.5 * df_raw["FG3M"]) / df_raw["FGA"]
    df_raw["ts_pct"]  = df_raw["PTS"]  / (2 * (df_raw["FGA"] + 0.44 * df_raw["FTA"]))

    # 4) Estimation possessions (approximation NBA : Poss = FGA + 0.44*FTA + TOV)
    df_raw["poss"] = df_raw["FGA"] + 0.44 * df_raw["FTA"] + df_raw["TOV"]

    # 5) Agglo par joueur
    agg = df_raw.groupby("PLAYER_ID").agg(
        efg_pct        = ("efg_pct",    "mean"),
        ts_pct         = ("ts_pct",     "mean"),
        fg2_pct        = ("fg2_pct",    "mean"),
        fg3_pct        = ("fg3_pct",    "mean"),
        ft_pct         = ("ft_pct",     "mean"),
        stl_mean       = ("STL",        "mean"),
        blk_mean       = ("BLK",        "mean"),
        tov_mean       = ("TOV",        "mean"),
        ast_tov_ratio  = ("AST","sum"),  # on calculera juste après
        pts_total      = ("PTS",        "sum"),
        reb_total      = ("REB",        "sum"),
        ast_total      = ("AST",        "sum"),
        stl_total      = ("STL",        "sum"),
        blk_total      = ("BLK",        "sum"),
        tov_total      = ("TOV",        "sum"),
        min_total      = ("MIN",        "sum"),
        pm_total       = ("PLUS_MINUS", "sum"),
        poss_total     = ("poss",       "sum")
    )

    # 6) Ratios et per36
    # AST/TOV
    agg["ast_tov_ratio"] = agg["ast_total"] / agg["tov_total"].replace(0, pd.NA)
    # per36 et usage rate
    per36_map = {
        "pts_total":"pts36","reb_total":"reb36","ast_total":"ast36",
        "stl_total":"stl36","blk_total":"blk36","tov_total":"tov36",
        "pm_total":"pm36"
    }
    for raw_col,new_col in per36_map.items():
        agg[new_col] = agg[raw_col] * (36/agg["min_total"]) \
                         .replace([float("inf"), -float("inf")], pd.NA)

    # Usage rate approximé = joueur poss / équipe poss
    # Ici team poss par game ≃ 100 possessions,
    # mais on peut normaliser par GP*100 si tu veux
    agg["usage_rate"] = agg["poss_total"] / (agg["min_total"]/48)  # approx possessions/48'

    # 7) Sélection features
    new_feats = agg[[
        "efg_pct","ts_pct","fg2_pct","fg3_pct","ft_pct",
        "stl_mean","blk_mean","tov_mean","ast_tov_ratio","usage_rate",
        "pts36","reb36","ast36","stl36","blk36","tov36","pm36"
    ]].reset_index()

    # 8) Merge et sauvegarde
    ps     = pd.read_parquet(CURATED / f"player_season_{season}.parquet")
    df_out = ps.merge(new_feats, on="PLAYER_ID", how="left")
    df_out.to_parquet(CURATED / f"player_season_{season}.parquet", index=False)

    print(f"✅ Avancé features ajoutées pour {season}")
