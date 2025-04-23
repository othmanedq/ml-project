#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
from pathlib import Path
from scipy.stats import zscore
from tqdm import tqdm

RAW     = Path(__file__).parent.parent / "data" / "raw"
CURATED = Path(__file__).parent.parent / "data" / "curated"
OUT     = CURATED / "all_seasons_scores.parquet"

seasons = [f"{y}-{str(y+1)[-2:]}" for y in range(2014, 2024)]
records = []

print("⚙️ Traitement des saisons pour calculer `score_100`…")

for season in tqdm(seasons):
    path = CURATED / f"player_season_{season}.parquet"
    if not path.exists():
        print(f"❌ {season} : fichier manquant")
        continue

    try:
        df = pd.read_parquet(path)

        # 1) Remplir et calculer la dispo
        for col in ["pts_mean","reb_mean","ast_mean","plus_minus_mean","gp"]:
            df[col] = df[col].fillna(df[col].mean())
        df["avail"] = df["gp"] / 82

        # 2) Préparer les colonnes pour z-score
        prod_cols = ["pts_mean","reb_mean","ast_mean","plus_minus_mean","avail"]
        phys_cols = [c for c in ["height_cm","bmi","AGE"] if c in df.columns]

        # 3) Z-scores
        for col in prod_cols + phys_cols:
            df[f"Z_{col}"] = zscore(df[col].fillna(df[col].mean()))

        # 4) Calcul de la note brute
        df["note_raw"] = (
              0.35 * df["Z_pts_mean"]
            + 0.15 * df["Z_reb_mean"]
            + 0.15 * df["Z_ast_mean"]
            + 0.25 * df["Z_plus_minus_mean"]
            + 0.10 * df["Z_avail"]
        )
        if "Z_height_cm" in df: df["note_raw"] += 0.10 * df["Z_height_cm"]
        if "Z_bmi"       in df: df["note_raw"] -= 0.05 * df["Z_bmi"]
        if "Z_AGE"       in df: df["note_raw"] -= 0.10 * df["Z_AGE"]

        # 5) Normalisation finale et mise à l’échelle 0–100
        df["note"] = zscore(df["note_raw"]) * 10
        mn, mx     = df["note"].min(), df["note"].max()
        df["score_100"] = 100 * (df["note"] - mn) / (mx - mn)

        # 6) Préparer l’output
        out = pd.DataFrame({
            "PLAYER_ID": df["PLAYER_ID"],
            "season":    season,
            "score_100": df["score_100"]
        })
        records.append(out)

    except Exception as e:
        print(f"❌ {season} : erreur → {e}")

# Fusion finale et ajout des noms
if records:
    all_df = pd.concat(records, ignore_index=True)

    # Récupérer les noms depuis le raw gamelog 2023-24
    gl = pd.read_parquet(RAW / "player_gamelog_2023-24.parquet",
                         columns=["PLAYER_ID","PLAYER_NAME"])
    id2name = (gl.drop_duplicates("PLAYER_ID")
                 .set_index("PLAYER_ID")["PLAYER_NAME"]
                 .to_dict())
    all_df["PLAYER_NAME"] = all_df["PLAYER_ID"].map(id2name)

    all_df.to_parquet(OUT, index=False)
    print(f"\n✅ Fichier final : {len(all_df)} lignes écrites dans `{OUT}`")
else:
    print("❌ Aucun fichier traité.")
