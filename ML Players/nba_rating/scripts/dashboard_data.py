#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dashboard_data.py
-----------------
Fusionne automatiquement :
 - dataset_ml.parquet       (features + target_note_n1)
 - wins_shares_vorp.parquet (Win Shares & VORP)
 - player_clusters.parquet  (clusters)
 - all_player_gamelogs.parquet (pour extraire tous les player_name)

et génère `dashboard_data.parquet` prêt à être consommé par le dashboard.

Usage :
    python -m nba_rating.scripts.dashboard_data
"""

import pandas as pd
from pathlib import Path

def make_photo_url(player_id: int, size: str = "260x190") -> str:
    """
    Construit l'URL publique du headshot NBA pour un joueur donné.
    """
    return f"https://cdn.nba.com/headshots/nba/latest/{size}/{int(player_id)}.png"

# 1) Définition des chemins
BASE       = Path(__file__).resolve().parents[1] / "data"
CURATED    = BASE / "curated"
RAW        = BASE / "raw"
IN_DS      = CURATED / "dataset_ml.parquet"
IN_WS      = CURATED / "wins_shares_vorp.parquet"
IN_CL      = CURATED / "player_clusters.parquet"
IN_LOGS    = CURATED / "all_player_gamelogs.parquet"
OUT        = CURATED / "dashboard_data.parquet"

# 2) Chargement du dataset principal
print(f"🔄 Chargement      : {IN_DS.name}")
df = pd.read_parquet(IN_DS)

# 2a) Fusion du score_100 depuis all_seasons_scores.parquet
SCORES_PATH = CURATED / "all_seasons_scores.parquet"
if SCORES_PATH.exists():
    print(f"🔄 Fusion score_100 : {SCORES_PATH.name}")
    scores_df = (
        pd.read_parquet(SCORES_PATH)[["PLAYER_ID", "season", "score_100"]]
        .drop_duplicates(subset=["PLAYER_ID", "season"])
    )
    df = df.merge(scores_df, on=["PLAYER_ID", "season"], how="left")

else:
    print(f"⚠️ Fichier introuvable : {SCORES_PATH.name} (score_100 non ajouté)")

# 2b) Normalisation du score_100
# Normalisation du score_100 issu de merges multiples
if "score_100_x" in df.columns and "score_100_y" in df.columns:
    df["score_100"] = df["score_100_x"].fillna(df["score_100_y"])
    df = df.drop(columns=["score_100_x", "score_100_y"])
elif "score_100_x" in df.columns:
    df = df.rename(columns={"score_100_x": "score_100"})
elif "score_100_y" in df.columns:
    df = df.rename(columns={"score_100_y": "score_100"})
    
# 3) Extraction des noms depuis all_player_gamelogs.parquet (curated)
LOGS_ALL = CURATED / "all_player_gamelogs.parquet"
if LOGS_ALL.exists():
    print(f"🔄 Extraction des noms : {LOGS_ALL.name}")
    names = (
        pd.read_parquet(LOGS_ALL)[["PLAYER_ID", "PLAYER_NAME"]]
        .drop_duplicates(subset=["PLAYER_ID"])
        .rename(columns={"PLAYER_NAME": "player_name_new"})
    )
    # Conserver l'ancien nom si présent
    if "player_name" in df.columns:
        df = df.rename(columns={"player_name": "player_name_old"})
    # Fusionner les nouveaux noms
    df = df.merge(names, on="PLAYER_ID", how="left")
    # Combiner ancien et nouveau
    if "player_name_old" in df.columns:
        df["player_name"] = df["player_name_old"].fillna(df["player_name_new"])
    else:
        df["player_name"] = df["player_name_new"]
    # Supprimer colonnes intermédiaires
    df = df.drop(columns=[c for c in ["player_name_old","player_name_new"] if c in df.columns])

    # 4) Construire l'URL de la photo headshot
    df["photo_url"] = df["PLAYER_ID"].apply(lambda pid: make_photo_url(pid))
else:
    print(f"⚠️ Fichier introuvable : {LOGS_ALL.name} ➔ noms non ajoutés")

# 5) Fusion Win Shares / VORP
if IN_WS.exists():
    print(f"🔄 Fusion WS/VORP  : {IN_WS.name}")
    ws = pd.read_parquet(IN_WS).drop_duplicates(subset=["PLAYER_ID","season"])
    df = df.merge(ws, on=["PLAYER_ID","season"], how="left")
else:
    print(f"⚠️ Fichier introuvable : {IN_WS.name}\n   Aucun Win Shares/VORP ajouté")

# 6) Fusion Clusters
if IN_CL.exists():
    print(f"🔄 Fusion clusters : {IN_CL.name}")
    cl = pd.read_parquet(IN_CL).drop_duplicates(subset=["PLAYER_ID","season"])
    # renommer si nécessaire
    if "player_cluster" in cl.columns:
        cl = cl.rename(columns={"player_cluster": "cluster"})
    df = df.merge(
        cl[["PLAYER_ID","season","cluster"]],
        on=["PLAYER_ID","season"],
        how="left"
    )
else:
    print(f"⚠️ Fichier introuvable : {IN_CL.name}\n   Aucun cluster ajouté")

# 7) Écriture du fichier final
print(f"✅ Écriture        : {OUT.name} → {len(df)} lignes × {len(df.columns)} colonnes")
df.to_parquet(OUT, index=False)
