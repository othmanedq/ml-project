#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compute_rating_all.py
---------------------
1) Calcule score_100 pour chaque saison (merge dans player_season_{season}.parquet)
2) Construit all_seasons_scores.parquet avec (PLAYER_ID, season, score_100)
"""

import pandas as pd
import numpy as np
from scipy.stats import zscore
from pathlib import Path
import pyarrow.parquet as pq
import sys

# Répertoires
BASE    = Path(__file__).resolve().parents[1]
CURATED = BASE / "data" / "curated"

def compute_per_season(season):
    path = CURATED / f"player_season_{season}.parquet"
    df   = pd.read_parquet(path)

    # 1) Disponibilité
    df["avail"] = pd.to_numeric(df["gp"], errors="coerce") / 82

    # 2) Features à normaliser
    basic         = ["pts_mean","reb_mean","ast_mean","plus_minus_mean","avail"]
    advanced_rate = ["efg_pct","ts_pct","stl_mean","blk_mean","tov_mean"]
    per36         = ["pts36","reb36","ast36","stl36","blk36","tov36","pm36"]
    context       = ["esv_mean","pace"]
    phys          = ["height_cm","bmi","age","exp"]

    to_z = basic + advanced_rate + per36 + context + phys

    # 3) Coercition en numérique & imputation, puis z-score
    for col in to_z:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col].fillna(df[col].mean(), inplace=True)
        df[f"Z_{col}"] = zscore(df[col])

    # 4) Poids de la note brute
    weights = {
        "pts_mean": 0.25, "reb_mean": 0.10, "ast_mean": 0.10, "plus_minus_mean": 0.15,
        "avail": 0.05,
        "efg_pct": 0.10, "ts_pct": 0.10,
        "stl_mean": 0.05, "blk_mean": 0.05, "tov_mean": -0.05,
        "pts36": 0.10, "reb36": 0.05, "ast36": 0.05,
        "stl36": 0.03, "blk36": 0.03, "tov36": -0.03, "pm36": 0.05,
        "esv_mean": 0.05, "pace": 0.05,
        "height_cm": 0.02, "bmi": -0.02, "age": -0.05, "exp": 0.05
    }

    # 5) Calcul de note_raw et normalisation 0–100
    df["note_raw"] = sum(df[f"Z_{f}"] * w for f, w in weights.items())
    mn, mx = df["note_raw"].min(), df["note_raw"].max()
    df["score_100"] = 100 * (df["note_raw"] - mn) / (mx - mn)

    # 6) Nettoyage des colonnes intermédiaires
    drop_cols = [f"Z_{c}" for c in to_z] + ["note_raw"]
    df.drop(columns=drop_cols, inplace=True, errors="ignore")

    # Assurez-vous d’ajouter la saison comme colonne
    df["season"] = season

    # Sauvegarde de player_season_{season}.parquet
    df.to_parquet(path, index=False)
    print(f"✅ Saison {season} mise à jour → score_100 ajouté")

    # Retour pour l’agrégation globale
    return df[["PLAYER_ID", "season", "score_100"]]



# 1) Récupère la liste des saisons
files   = sorted(CURATED.glob("player_season_*.parquet"))
seasons = [f.stem.split("_")[-1] for f in files]

all_scores = []
for s in seasons:
    # 2) Vérifie via le schéma parquet que les colonnes avancées existent
    schema = pq.ParquetFile(CURATED / f"player_season_{s}.parquet").schema.names
    missing = [c for c in ("efg_pct", "ts_pct") if c not in schema]
    if missing:
        print(f"⚠️ Skip saison {s}: colonnes manquantes {missing}")
        continue

    # 3) Calcul pour cette saison
    all_scores.append(compute_per_season(s))

if not all_scores:
    print("❌ Aucune saison traitée : vérifie feature_engineering.py")
    sys.exit(1)

# 4) Concatène et sauvegarde le fichier global
df_all = pd.concat(all_scores, ignore_index=True)
out    = CURATED / "all_seasons_scores.parquet"
df_all.to_parquet(out, index=False)
print(f"\n🎉 all_seasons_scores.parquet généré ({len(df_all)} lignes)")