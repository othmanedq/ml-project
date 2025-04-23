#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
from pathlib import Path

RAW     = Path(__file__).parent.parent / "data" / "raw"
CURATED = Path(__file__).parent.parent / "data" / "curated"
CURATED.mkdir(parents=True, exist_ok=True)

def height_to_cm(ht: str) -> float:
    feet, inches = map(int, ht.split('-'))
    return feet * 30.48 + inches * 2.54

print("📦 Création des fichiers `player_season_YYYY-YY.parquet` dans `data/curated/`")

seasons = [f"{y}-{str(y+1)[-2:]}" for y in range(2014, 2024)]
for season in seasons:
    gl_path   = RAW     / f"player_gamelog_{season}.parquet"
    phys_path = RAW     / f"player_phys_{season}.parquet"
    out_path  = CURATED / f"player_season_{season}.parquet"

    try:
        # 1) Charger et agréger les statistiques par joueur --------------------------------
        gl = pd.read_parquet(gl_path)
        season_stats = (
            gl.groupby("PLAYER_ID")
              .agg(
                  pts_mean         = ("PTS",         "mean"),
                  reb_mean         = ("REB",         "mean"),
                  ast_mean         = ("AST",         "mean"),
                  plus_minus_mean  = ("PLUS_MINUS",  "mean"),
                  gp               = ("GAME_ID",     "nunique"),
              )
              .reset_index()
        )

        # 2) Charger les mensurations si elles existent -------------------------------
        if phys_path.exists():
            phys = pd.read_parquet(phys_path)

            # conversions HEIGHT→height_cm, WEIGHT→weight_kg, BMI
            if "HEIGHT" in phys.columns and "height_cm" not in phys.columns:
                phys["height_cm"] = phys["HEIGHT"].map(height_to_cm)
            if "WEIGHT" in phys.columns and "weight_kg" not in phys.columns:
                phys["weight_kg"] = phys["WEIGHT"].astype(float) / 2.205
            if {"height_cm","weight_kg"}.issubset(phys.columns) and "bmi" not in phys.columns:
                phys["bmi"] = phys["weight_kg"] / (phys["height_cm"]/100)**2

            # garantir AGE
            if "AGE" not in phys.columns and "age" in phys.columns:
                phys["AGE"] = phys["age"]

            phys_sel = phys[["PLAYER_ID","height_cm","weight_kg","bmi","AGE"]]
        else:
            phys_sel = pd.DataFrame(columns=["PLAYER_ID","height_cm","weight_kg","bmi","AGE"])

        # 3) Fusionner et écrire ------------------------------------------------------
        merged = season_stats.merge(phys_sel, on="PLAYER_ID", how="left")
        merged.to_parquet(out_path, index=False)
        print(f"✅ {season} : {len(merged)} lignes")
    except Exception as e:
        print(f"❌ {season} : erreur → {e}")
