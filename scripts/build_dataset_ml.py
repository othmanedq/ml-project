#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_dataset_ml.py
---------------------
Construit un dataset X/y multi-saisons pour entraîner un modèle de prédiction
du score_100 futur (note_n+1).
Basé sur : all_seasons_scores.parquet + player_season_YYYY-YY.parquet
"""
import pandas as pd
from pathlib import Path

# Répertoire des données
CURATED = Path("nba_rating/data/curated")
SEASONS = [f"{y}-{str(y+1)[-2:]}" for y in range(1999, 2024)]

# 1. Charger les scores
scores = pd.read_parquet(CURATED / "all_seasons_scores.parquet")

# 2. Charger et concaténer toutes les saisons de features
dfs = []
for season in SEASONS:
    p = CURATED / f"player_season_{season}.parquet"
    if not p.exists():
        continue
    df = pd.read_parquet(p)
    df["season"] = season
    dfs.append(df)
if not dfs:
    raise RuntimeError("Aucune saison chargée dans player_season_*.parquet")
features = pd.concat(dfs, ignore_index=True)

# 3. Fusion scores + features
df_all = pd.merge(scores, features, on=["PLAYER_ID", "season"], how="left")

# 4. Recalcul de la dispo si besoin
if "gp" in df_all.columns:
    df_all["avail"] = df_all["gp"] / 82

# 5. Création des colonnes note_n, note_n1 et delta_score
df_all["note_n"]     = df_all["score_100"]
df_all["note_n1"]    = df_all.groupby("PLAYER_ID")["score_100"].shift(-1)
df_all["delta_score"] = df_all.groupby("PLAYER_ID")["score_100"].diff()

# 6. Conversion de l'expérience en numérique
df_all["exp"] = pd.to_numeric(df_all.get("exp", 0), errors="coerce").fillna(0).astype(int)

# 7. Intégration des clusters (optionnel)
cluster_file = CURATED / "player_clusters.parquet"
if cluster_file.exists():
    clusters = pd.read_parquet(cluster_file)
    df_all = pd.merge(
        df_all,
        clusters[["PLAYER_ID", "season", "player_cluster", "profile_name"]],
        on=["PLAYER_ID", "season"],
        how="left"
    )
    print("✅ Clusters intégrés au dataset ML")
else:
    print("⚠️ Aucun cluster trouvé, passe cluster integration")

# 8. Filtrer les lignes valides (note_n1 connue)
df_ml = df_all.dropna(subset=["note_n1"]).reset_index(drop=True)

# 9. Sélection des features pour l’apprentissage
features_used = [
    "pts_mean", "reb_mean", "ast_mean", "plus_minus_mean",
    "min_per_game", "avail", "esv_mean", "pace",
    "height_cm", "bmi", "age", "exp", "delta_score"
]

# Vérifier qu’aucune feature n’est manquante
missing = [f for f in features_used if f not in df_ml.columns]
if missing:
    raise KeyError(f"Features manquantes dans df_ml : {missing}")

X = df_ml[features_used]
y = df_ml["note_n1"]

# 10. Export du dataset final
df_out = X.copy()
df_out["target_note_n1"] = y
out_path = CURATED / "dataset_ml.parquet"
df_out.to_parquet(out_path, index=False)
print(f"✅ Dataset ML enregistré ({df_out.shape[0]} lignes, {len(features_used)} features + cible)")
