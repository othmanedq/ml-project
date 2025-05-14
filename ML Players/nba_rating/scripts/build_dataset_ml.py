#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_dataset_ml.py
-------------------
Construit `dataset_ml.parquet` en fusionnant :
 1. `all_seasons_scores.parquet`   (score_100)
 2. Tous les `player_season_YYYY-YY.parquet`   (features avancées)
 3. `player_clusters.parquet`      (cluster)
 4. `all_player_gamelogs.parquet`  (player_name)

Puis génère :
 - X = toutes les features + score_100 + delta_score
 - y = note de la saison suivante (target_note_n1)

Usage :
    python -m nba_rating.scripts.build_dataset_ml
"""

import pandas as pd
from pathlib import Path

# Répertoires & fichiers
CURATED   = Path(__file__).resolve().parents[1] / "data" / "curated"
SEASONS   = [f"{y}-{str(y+1)[2:]}" for y in range(1999, 2024)]
OUT       = CURATED / "dataset_ml.parquet"
SCORES_IN = CURATED / "all_seasons_scores.parquet"
CL_IN     = CURATED / "player_clusters.parquet"
NAMES_IN  = CURATED / "all_player_gamelogs.parquet"

def _strip_suffix(col: str) -> str:
    # retire _x ou _y si présent, sinon renvoie tel quel
    return col[:-2] if col.endswith(("_x","_y")) else col

# 1) Charger score_100
print(f"🔄 Chargement scores : {SCORES_IN.name}")
scores_df = pd.read_parquet(SCORES_IN)[["PLAYER_ID","season","score_100"]]

# 2) Charger & concat features par saison
print(f"🔄 Chargement features saisons : {len(SEASONS)} fichiers")
dfs = []
for season in SEASONS:
    path = CURATED / f"player_season_{season}.parquet"
    if not path.exists():
        continue
    tmp = pd.read_parquet(path)
    tmp["season"] = season
    dfs.append(tmp)
if not dfs:
    raise RuntimeError("Aucun fichier player_season_*.parquet trouvé")
features = pd.concat(dfs, ignore_index=True)
# nettoyer suffixes doublons
features.columns = [_strip_suffix(c) for c in features.columns]
features = features.loc[:, ~features.columns.duplicated()]

# 3) Fusion scores + features
print("🔄 Fusion scores + features")
df_all = scores_df.merge(features, on=["PLAYER_ID","season"], how="left")

# 3a) Normalisation de score_100 si présent en double
if "score_100" not in df_all.columns:
    if "score_100_x" in df_all.columns:
        df_all = df_all.rename(columns={"score_100_x": "score_100"})
        if "score_100_y" in df_all.columns:
            df_all = df_all.drop(columns=["score_100_y"])
    elif "score_100_y" in df_all.columns:
        df_all = df_all.rename(columns={"score_100_y": "score_100"})
    else:
        raise KeyError("❌ score_100 manquant après fusion scores + features")

# 4) Calcul de availability si gp existe
if "gp" in df_all.columns:
    df_all["avail"] = df_all["gp"] / 82

# 5) Création des cibles temporelles
print("🔄 Création cibles temporelles")
df_all["note_n"]      = df_all["score_100"]
df_all["note_n1"]     = df_all.groupby("PLAYER_ID")["score_100"].shift(-1)
# delta_score = progression d'une saison sur l'autre
df_all["delta_score"] = df_all["note_n1"] - df_all["note_n"]

# 6) Expérience en int
if "exp" in df_all.columns:
    df_all["exp"] = (
        pd.to_numeric(df_all["exp"], errors="coerce")
            .fillna(0)
            .astype(int)
    )

# 7) Fusion clusters
if CL_IN.exists():
    print(f"🔄 Fusion clusters : {CL_IN.name}")
    cl = (
        pd.read_parquet(CL_IN)
            .drop_duplicates(subset=["PLAYER_ID","season"])
            .rename(columns={"player_cluster":"cluster"})
    )
    df_all = df_all.merge(
        cl[["PLAYER_ID","season","cluster"]],
        on=["PLAYER_ID","season"],
        how="left"
    )
else:
    print(f"⚠️ {CL_IN.name} introuvable → pas de cluster")

# 8) Extraction des noms
if NAMES_IN.exists():
    print(f"🔄 Extraction noms   : {NAMES_IN.name}")
    names = (
        pd.read_parquet(NAMES_IN)[["PLAYER_ID","PLAYER_NAME"]]
            .drop_duplicates(subset=["PLAYER_ID"])
            .rename(columns={"PLAYER_NAME":"player_name"})
    )
    df_all = df_all.merge(names, on="PLAYER_ID", how="left")
else:
    print(f"⚠️ {NAMES_IN.name} introuvable → pas de player_name")

# 9) Filtrer les lignes où la cible existe
df_ml = df_all.dropna(subset=["note_n1"]).reset_index(drop=True)

# 10) Sélection des features d'entrée
features_used = [
    "score_100",
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

# 11) Construction finale
X = df_ml[features_used]
y = df_ml["note_n1"]
out = (
    df_ml[["PLAYER_ID","season","player_name"] + features_used]
        .copy()
)
out["target_note_n1"] = y

# 12) Écriture
print(f"✅ Écriture dataset ML : {OUT.name} → {len(out)} lignes, {len(features_used)} features + cible")
out.to_parquet(OUT, index=False)
