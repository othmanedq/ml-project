#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
compute_rating_all.py
---------------------
Calcule un score global `score_100` pour chaque joueur/saison à partir des
statistiques agrégées et mensurations (si disponibles), puis concatène toutes
les saisons dans un seul fichier `all_seasons_scores.parquet`.
"""

import pandas as pd
from pathlib import Path
from scipy.stats import zscore
from tqdm import tqdm

# Chemins
BASE     = Path("nba_rating/data")
CURATED  = BASE / "curated"
RAW      = BASE / "raw"
OUT_PATH = CURATED / "all_seasons_scores.parquet"

# Liste des saisons à traiter
seasons = [f"{y}-{str(y+1)[-2:]}" for y in range(2014, 2024)]
records = []

print("⚙️ Calcul de score_100 par joueur/saison...\n")

for season in tqdm(seasons):
    try:
        path = CURATED / f"player_season_{season}.parquet"
        df = pd.read_parquet(path)

        # Vérification minimale
        needed_cols = ["pts_mean", "reb_mean", "ast_mean", "plus_minus_mean", "gp"]
        for col in needed_cols:
            if col not in df.columns:
                raise ValueError(f"Colonne manquante : {col} dans {season}")

        # Calcul disponibilité
        df["avail"] = df["gp"] / 82

        # Colonnes utilisées
        prod_cols = ["pts_mean", "reb_mean", "ast_mean", "plus_minus_mean", "avail"]
        phys_cols = [c for c in ["height_cm", "bmi", "age"] if c in df.columns]

        # Z-scores pour chaque colonne dispo
        for col in prod_cols + phys_cols:
            df[f"Z_{col}"] = zscore(df[col].fillna(df[col].mean()))

        # Note brute production
        df["note_raw"] = (
              0.35 * df["Z_pts_mean"]
            + 0.15 * df["Z_reb_mean"]
            + 0.15 * df["Z_ast_mean"]
            + 0.25 * df["Z_plus_minus_mean"]
            + 0.10 * df["Z_avail"]
        )

        # Note physique (bonus/malus si colonnes présentes)
        if "Z_height_cm" in df: df["note_raw"] += 0.10 * df["Z_height_cm"]
        if "Z_bmi"       in df: df["note_raw"] -= 0.05 * df["Z_bmi"]
        if "Z_age"       in df: df["note_raw"] -= 0.10 * df["Z_age"]

        # Normalisation µ=0, σ=10
        df["note"] = zscore(df["note_raw"]) * 10

        # Conversion 0–100
        mn, mx = df["note"].min(), df["note"].max()
        df["score_100"] = 100 * (df["note"] - mn) / (mx - mn)

        # Export partiel
        out = df[["PLAYER_ID", "score_100"]].copy()
        out["season"] = season
        records.append(out)

    except Exception as e:
        print(f"❌ {season} : erreur → {e}")

# Fusion finale
if records:
    df_all = pd.concat(records, ignore_index=True)

    # Ajout des noms depuis le raw 2023-24
    try:
        names = pd.read_parquet(RAW / "player_gamelog_2023-24.parquet")[["PLAYER_ID", "PLAYER_NAME"]]
        id2name = names.drop_duplicates("PLAYER_ID").set_index("PLAYER_ID")["PLAYER_NAME"].to_dict()
        df_all["PLAYER_NAME"] = df_all["PLAYER_ID"].map(id2name)
    except Exception as e:
        print("⚠️  Impossible de récupérer les noms :", e)
        df_all["PLAYER_NAME"] = "Inconnu"

    # Export final
    df_all.to_parquet(OUT_PATH, index=False)
    print(f"\n✅ Fichier complet enregistré → {OUT_PATH} ({len(df_all)} lignes)")
else:
    print("❌ Aucun score n'a pu être calculé.")
