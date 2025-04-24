#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_phys.py
------------
Ce script corrige les fichiers `player_phys_YYYY-YY.parquet` dans le dossier `data/raw/`
en ajoutant les colonnes physiques manquantes : 
- `height_cm` : conversion de la colonne `HEIGHT` (ex. "6-8") en cm
- `weight_kg` : conversion de la colonne `WEIGHT` (en livres) en kg
- `bmi`       : calcul de l'indice de masse corporelle = poids / (taille en m)^2

Il est destiné à rendre les fichiers compatibles avec `prepare_curated.py` pour les saisons < 2023-24.

Usage :  
    python nba_rating/scripts/fix_phys.py
"""

import pandas as pd
from pathlib import Path

RAW = Path("nba_rating/data/raw")
seasons = [f"{y}-{str(y+1)[-2:]}" for y in range(2014, 2024)]

def convert_height(ht):
    try:
        ft, inch = map(int, ht.split("-"))
        return ft * 30.48 + inch * 2.54
    except:
        return None

for season in seasons:
    path = RAW / f"player_phys_{season}.parquet"
    if not path.exists():
        print(f"⏭️  {season} : fichier manquant")
        continue

    try:
        df = pd.read_parquet(path)

        updated = False

        if "HEIGHT" in df.columns and "height_cm" not in df.columns:
            df["height_cm"] = df["HEIGHT"].apply(convert_height)
            updated = True

        if "WEIGHT" in df.columns and "weight_kg" not in df.columns:
            df["weight_kg"] = pd.to_numeric(df["WEIGHT"], errors="coerce") / 2.205
            updated = True

        if {"height_cm", "weight_kg"}.issubset(df.columns) and "bmi" not in df.columns:
            df["bmi"] = df["weight_kg"] / (df["height_cm"] / 100) ** 2
            updated = True

        if updated:
            df.to_parquet(path, index=False)
            print(f"✅ {season} : colonnes physiques mises à jour")
        else:
            print(f"✔️  {season} : déjà complet")

    except Exception as e:
        print(f"❌ {season} : erreur → {e}")
