#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cluster_players.py
------------------
1) Charge toutes les saisons curées (player_season_YYYY-YY.parquet)
2) Sélectionne les features clés pour le clustering
3) Standardise puis applique K-Means (n_clusters=5)
4) Nomme les clusters (Playmaker, Big Man, etc.)
5) Sauvegarde player_clusters.parquet avec PLAYER_ID, season, player_cluster, profile_name
"""

import pandas as pd
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# Répertoire des données curées
BASE    = Path(__file__).resolve().parents[1] / "data" / "curated"
SEASONS = [f"{y}-{str(y+1)[-2:]}" for y in range(1999, 2024)]
OUT     = BASE / "player_clusters.parquet"

# 1) Charger et concaténer toutes les saisons
dfs = []
for season in SEASONS:
    p = BASE / f"player_season_{season}.parquet"
    if not p.exists():
        continue
    df = pd.read_parquet(p)
    df["season"] = season
    dfs.append(df)
if not dfs:
    raise RuntimeError("Aucune saison trouvée dans data/curated")

df_all = pd.concat(dfs, ignore_index=True)

# 2) Calcul de avail si jamais absent
if "avail" not in df_all.columns and "gp" in df_all.columns:
    df_all["avail"] = df_all["gp"] / 82

# 3) Sélection des variables pour le clustering
features = [
    "pts_mean", "reb_mean", "ast_mean", "plus_minus_mean",
    "avail", "height_cm", "bmi", "age"
]
df_cluster = df_all.dropna(subset=features).copy()

# 4) Standardisation
scaler = StandardScaler()
X = scaler.fit_transform(df_cluster[features])

# 5) K-Means
kmeans = KMeans(n_clusters=5, random_state=42)
df_cluster["player_cluster"] = kmeans.fit_predict(X)

# 6) Attribution de noms d’archétypes
cluster_names = {
    0: "Playmaker",
    1: "Big Man",
    2: "Young Buck",
    3: "All-Around",
    4: "Scoring Guard"
}
df_cluster["profile_name"] = df_cluster["player_cluster"].map(cluster_names)

# 7) Sélection et sauvegarde
out = df_cluster[["PLAYER_ID", "season", "player_cluster", "profile_name"]]
out.to_parquet(OUT, index=False)
print(f"✅ Clustering terminé : {len(out)} lignes écrites dans {OUT}")