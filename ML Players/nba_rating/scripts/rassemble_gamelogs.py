#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rassemble_gamelogs.py
----------------------
Concatène tous les raw/player_gamelog_*.parquet en un seul fichier
nba_rating/data/curated/all_player_gamelogs.parquet pour usage ultérieur.
"""

import pandas as pd
from pathlib import Path

RAW      = Path(__file__).resolve().parents[1] / "data" / "raw"
OUT      = Path(__file__).resolve().parents[1] / "data" / "curated" / "all_player_gamelogs.parquet"

# 1) Liste et chargement
files = sorted(RAW.glob("player_gamelog_*.parquet"))
if not files:
    raise RuntimeError(f"Aucun fichier raw/player_gamelog_*.parquet dans {RAW}")

dfs = []
for f in files:
    print(f"🔄 Chargement de {f.name}")
    dfs.append(pd.read_parquet(f))
all_logs = pd.concat(dfs, ignore_index=True)

# 2) Écriture
all_logs.to_parquet(OUT, index=False)
print(f"✅ Fichier unifié écrit : {OUT} ({len(all_logs)} lignes)")
