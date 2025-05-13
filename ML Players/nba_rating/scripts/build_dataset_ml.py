#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_dataset_ml.py
---------------------
Construit dataset_ml.parquet :
 - Fusion de all_seasons_scores.parquet + player_season_{season}.parquet
 - Nettoyage des colonnes _x/_y
 - Consolidation de score_100_x / score_100_y → score_100
 - Création de note_n, note_n1, delta_score
 - Export final X + target_note_n1
"""

import pandas as pd
from pathlib import Path

# --- Paramètres ---
CURATED = Path(__file__).resolve().parents[1] / "data" / "curated"
SEASONS = [f"{y}-{str(y+1)[-2:]}" for y in range(1999, 2024)]
OUT     = CURATED / "dataset_ml.parquet"

# 1) Charger les scores globaux
scores = pd.read_parquet(CURATED / "all_seasons_scores.parquet")

# 2) Charger et concaténer les features par saison
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

# 3) Dé-duplication des suffixes _x / _y
def _strip(col):
    return col[:-2] if col.endswith(("_x","_y")) else col

features.columns = [_strip(c) for c in features.columns]
features = features.loc[:, ~features.columns.duplicated()]

# 4) Fusion scores + features
df_all = scores.merge(features, on=["PLAYER_ID","season"], how="left")

# 5) Consolidation du score_100 issu de la fusion
df_all["score_100"] = (
    df_all.get("score_100_x")
         .fillna(df_all.get("score_100_y"))
)
df_all.drop(columns=["score_100_x","score_100_y"], inplace=True, errors="ignore")

# 6) Recalcul disponibilité
if "gp" in df_all.columns:
    df_all["avail"] = df_all["gp"] / 82

# 7) Création des cibles temporelles
df_all["note_n"]      = df_all["score_100"]
df_all["note_n1"]     = df_all.groupby("PLAYER_ID")["score_100"].shift(-1)
df_all["delta_score"] = df_all.groupby("PLAYER_ID")["score_100"].diff()

# 8) Expérience en int
df_all["exp"] = (
    pd.to_numeric(df_all.get("exp",0), errors="coerce")
      .fillna(0).astype(int)
)

# 9) Intégration clusters si dispo
clusters = CURATED / "player_clusters.parquet"
if clusters.exists():
    cl = pd.read_parquet(clusters)
    df_all = df_all.merge(
        cl[["PLAYER_ID","season","player_cluster","profile_name"]],
        on=["PLAYER_ID","season"], how="left"
    )
    print("✅ Clusters intégrés")
else:
    print("⚠️ Pas de player_clusters.parquet, skipping clusters")

 # 10) Ajout de la colonne player_name

from pathlib import Path
RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
# On lit le gamelog de la dernière saison pour récupérer les noms
glog = pd.read_parquet(RAW / "player_gamelog_2023-24.parquet",
                       columns=["PLAYER_ID","PLAYER_NAME"])
glog = glog.drop_duplicates(subset="PLAYER_ID")
df_all = df_all.merge(glog, on="PLAYER_ID", how="left")

# Renommer PLAYER_NAME → player_name
if "PLAYER_NAME" in df_all.columns:
    df_all = df_all.rename(columns={"PLAYER_NAME": "player_name"})


# 10) Filtrer note_n1 présentes
df_ml = df_all.dropna(subset=["note_n1"]).reset_index(drop=True)

# 11) Sélection des features
features_used = [
    "pts_mean","reb_mean","ast_mean","plus_minus_mean",
    "efg_pct","ts_pct","stl_mean","blk_mean","tov_mean",
    "pts36","reb36","ast36","stl36","blk36","tov36","pm36",
    "min_per_game","avail",
    "esv_mean","pace",
    "height_cm","bmi","age","exp",
    "delta_score"
]

missing = [f for f in features_used if f not in df_ml.columns]
if missing:
    raise KeyError(f"Features manquantes : {missing}")

X = df_ml[features_used]
y = df_ml["note_n1"]

# 12) Export final : on réintègre PLAYER_ID, season et player_name
out = df_ml[["PLAYER_ID","season","player_name"] + features_used].copy()
out["target_note_n1"] = y
out.to_parquet(OUT, index=False)
print(f"✅ Dataset ML écrit : {OUT} ({len(out)} lignes, {len(features_used)} features + cible)")
