#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
assemble_curated.py
-------------------
Assemble tous les fichiers par saison en un seul dataset global.
"""

import pandas as pd
from pathlib import Path

# Chemins des dossiers
BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
CURATED_DIR = BASE_DIR / "data" / "curated"
CURATED_DIR.mkdir(parents=True, exist_ok=True)

# Liste des saisons à assembler
SEASONS = [f"{year}-{str(year+1)[-2:]}" for year in range(1999, 2024)]  # 2018-2019 à 2023-2024

dfs = []
for season in SEASONS:
    file_path = RAW_DIR / f"team_gamelog_{season}.parquet"
    if file_path.exists():
        df = pd.read_parquet(file_path)
        df["season"] = season  # Ajoute la saison comme colonne
        dfs.append(df)
    else:
        print(f"⚠ Fichier manquant pour la saison {season}")

if dfs:
    df_all = pd.concat(dfs, ignore_index=True)
    output_path = CURATED_DIR / "team_gamelog_all_seasons.parquet"
    df_all.to_parquet(output_path, index=False)
    print(f"✅ Dataset global sauvegardé dans : {output_path}")
    print(f"Forme du DataFrame final : {df_all.shape}")
else:
    print("❌ Aucun fichier à assembler.")
