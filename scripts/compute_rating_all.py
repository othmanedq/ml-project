# compute_rating_all.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compute_rating_all.py
---------------------
Calcule score_100 via Z-scores + ajustements âge & expérience
"""
import pandas as pd
from scipy.stats import zscore
from pathlib import Path

CURATED = Path("nba_rating/data/curated")
SEASONS = [f"{y}-{str(y+1)[-2:]}" for y in range(1999, 2024)]
out = []

for season in SEASONS:
    df = pd.read_parquet(CURATED/f"player_season_{season}.parquet")
    # s'assurer qu'exp est numérique (CommonTeamRoster peut renvoyer 'R' pour rookie)
    if 'exp' in df.columns:
        df['exp'] = pd.to_numeric(df['exp'], errors='coerce').fillna(0)
    else:
        df['exp'] = 0    
    
    df["avail"] = df["gp"] / 82

    # 1) Z-scores
    to_z = ["pts_mean","reb_mean","ast_mean","plus_minus_mean","avail",
            "height_cm","bmi","age","exp"]
    for c in to_z:
        df[f"Z_{c}"] = zscore(df[c].fillna(df[c].mean()))

    # 2) note_raw enrichie
    df["note_raw"] = (
          0.30 * df["Z_pts_mean"]
        + 0.10 * df["Z_reb_mean"]
        + 0.10 * df["Z_ast_mean"]
        + 0.20 * df["Z_plus_minus_mean"]
        + 0.05 * df["Z_avail"]
        + 0.05 * df["Z_height_cm"]
        - 0.05 * df["Z_bmi"]
        - 0.10 * df["Z_age"]
        + 0.10 * df["Z_exp"]
    )

    # 3) normalisation 0–100
    df["note"] = zscore(df["note_raw"]) * 10
    mn, mx    = df["note"].min(), df["note"].max()
    df["score_100"] = 100 * (df["note"] - mn) / (mx - mn)

    out.append(df[["PLAYER_ID","score_100"]].assign(season=season))

all_scores = pd.concat(out, ignore_index=True)
all_scores.to_parquet(CURATED/"all_seasons_scores.parquet", index=False)
print("✅ all_seasons_scores.parquet généré")