#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dashboard_data.py
──────────────────
Assemble toutes les sources de données nécessaires au dashboard
MLPlayers **sans lancer Streamlit** et produit un unique
`dashboard_data.parquet` dans `data/curated/`.

Sources fusionnées
------------------
• dataset_ml.parquet         → features & score normalisé  
• all_seasons_scores.parquet → score_100 par saison  
• wins_shares_vorp.parquet   → Win Shares & VORP  
• player_clusters.parquet    → cluster K‑means / rôle  
• all_player_gamelogs.parquet→ noms officiels des joueurs  
• projections.parquet        → prévisions de score à horizon 1 à 5  

Usage
-----
```bash
python -m nba_rating.scripts.dashboard_data
```
"""

from __future__ import annotations
import pandas as pd
from pathlib import Path
import pyarrow.parquet as pq

# ────────────────────────────────
#  1. Chemins de base
# ────────────────────────────────
BASE = Path(__file__).resolve().parents[1] / "data"
CURATED = BASE / "curated"

IN_DS   = CURATED / "dataset_ml.parquet"
IN_S100 = CURATED / "all_seasons_scores.parquet"
IN_WS   = CURATED / "wins_shares_vorp.parquet"
IN_CL   = CURATED / "player_clusters.parquet"
IN_LOGS = CURATED / "all_player_gamelogs.parquet"
IN_PROJ = CURATED / "projections.parquet"

OUTFILE = CURATED / "dashboard_data.parquet"


def make_photo_url(player_id: int, size: str = "260x190") -> str:
    """Renvoie l’URL CDN NBA du head‑shot du joueur."""
    return f"https://cdn.nba.com/headshots/nba/latest/{size}/{int(player_id)}.png"


# ────────────────────────────────
#  2. Dataset principal
# ────────────────────────────────
print(f"🔄  Chargement      : {IN_DS.name}")
df = pd.read_parquet(IN_DS)  # contient PLAYER_ID, season, score, etc.

# Pour les joins ultérieurs
id_name_map = (
    df[["PLAYER_ID", "player_name"]].drop_duplicates()
    if "player_name" in df.columns
    else pd.DataFrame(columns=["PLAYER_ID", "player_name"])
)

# ────────────────────────────────
#  3. Ajout score_100
# ────────────────────────────────
if IN_S100.exists():
    print(f"🔄  Fusion score_100 : {IN_S100.name}")
    s100 = (
        pd.read_parquet(IN_S100)[["PLAYER_ID", "season", "score_100"]]
        .drop_duplicates()
    )
    df = df.merge(s100, on=["PLAYER_ID", "season"], how="left")
else:
    print(f"⚠️  {IN_S100.name} manquant – score_100 non ajouté")

# ────────────────────────────────
#  4. Extraction noms officiels
# ────────────────────────────────
if IN_LOGS.exists():
    print(f"🔄  Extraction noms  : {IN_LOGS.name}")
    names = (
        pd.read_parquet(IN_LOGS, columns=["PLAYER_ID", "PLAYER_NAME"])
        .drop_duplicates()
        .rename(columns={"PLAYER_NAME": "player_name_official"})
    )
    df = df.merge(names, on="PLAYER_ID", how="left")
    # Préférence ordre : officiel > existant
    if "player_name" in df.columns:
        df["player_name"] = df["player_name_official"].fillna(df["player_name"])
    else:
        df = df.rename(columns={"player_name_official": "player_name"})
else:
    print(f"⚠️  {IN_LOGS.name} manquant – noms non mis à jour")

# URL photo
df["photo_url"] = df["PLAYER_ID"].apply(make_photo_url)

# ────────────────────────────────
#  5. Win Shares / VORP
# ────────────────────────────────
if IN_WS.exists():
    print(f"🔄  Fusion WS/VORP   : {IN_WS.name}")
    ws = pd.read_parquet(IN_WS).drop_duplicates(subset=["PLAYER_ID", "season"])
    df = df.merge(ws, on=["PLAYER_ID", "season"], how="left")
else:
    print(f"⚠️  {IN_WS.name} manquant – WS/VORP non ajoutés")

# ────────────────────────────────
#  6. Clusters
# ────────────────────────────────
if IN_CL.exists():
    print(f"🔄  Fusion clusters  : {IN_CL.name}")
    cl = pd.read_parquet(IN_CL).drop_duplicates(subset=["PLAYER_ID", "season"])
    cl = cl.rename(columns={"player_cluster": "cluster"}) if "player_cluster" in cl.columns else cl
    df = df.merge(cl[["PLAYER_ID", "season", "cluster"]], on=["PLAYER_ID", "season"], how="left")
else:
    print(f"⚠️  {IN_CL.name} manquant – clusters non ajoutés")

# ────────────────────────────────
#  7. Projections multi‑horizon
# ────────────────────────────────
if IN_PROJ.exists():
    print(f"🔄  Fusion projections: {IN_PROJ.name}")
    proj = pd.read_parquet(IN_PROJ)

    # Harmoniser les noms de colonnes
    proj = proj.rename(columns=str.lower)  # player_id, player_name, horizon, pred_score…

    # Si player_id absent, l’ajouter via le mapping nom ↔ id
    if "player_id" not in proj.columns:
        if not id_name_map.empty:
            proj = proj.merge(
                id_name_map.rename(columns={"PLAYER_ID": "player_id"}),
                left_on="player_name",
                right_on="player_name",
                how="left",
            )
        missing = proj["player_id"].isna().sum()
        if missing:
            print(f"⚠️  {missing} projections sans PLAYER_ID (nom non trouvé)")

    # Pivot : 1 colonne par horizon (proj_1 … proj_5)
    proj_wide = (
        proj.pivot_table(
            index="player_id",
            columns="horizon",
            values="pred_score",
            aggfunc="first",
        )
        .add_prefix("proj_")
        .reset_index()
    )

    df = df.merge(proj_wide, left_on="PLAYER_ID", right_on="player_id", how="left")
    df = df.drop(columns=["player_id"])
else:
    print(f"⚠️  {IN_PROJ.name} manquant – projections non ajoutées")

# ────────────────────────────────
#  7.b Équipe principale (team_id)
# ────────────────────────────────
if IN_LOGS.exists():
    print(f"🔄  Attribution équipe principale : {IN_LOGS.name}")
    # On choisit l’équipe la plus fréquente jouée par le joueur sur la saison
    # ‑ Détection du nom de colonne saison dans les gamelogs : "SEASON" ou "SEASON_ID"
    # Lecture ultra‑légère du schéma (0 I/O) pour détecter les noms de colonnes
    sample_cols = pq.ParquetFile(IN_LOGS).schema.names

    season_src  = "SEASON" if "SEASON" in sample_cols else "SEASON_ID"

    logs_min = pd.read_parquet(
        IN_LOGS,
        columns=["PLAYER_ID", "TEAM_ID", season_src]
    )

    team_lookup = (
        logs_min
          .groupby(["PLAYER_ID", season_src])["TEAM_ID"]
          .agg(lambda x: x.value_counts().idxmax())
          .reset_index()
          .rename(columns={season_src: "season", "TEAM_ID": "team_id"})
    )
    df = df.merge(team_lookup, on=["PLAYER_ID", "season"], how="left")
else:
    print(f"⚠️  {IN_LOGS.name} manquant – team_id non ajouté")

# ────────────────────────────────
#  8. Sauvegarde
# ────────────────────────────────
print(f"✅  Écriture         : {OUTFILE.name}  ({len(df):,} lignes, {df.shape[1]} colonnes)")
df.to_parquet(OUTFILE, index=False)
