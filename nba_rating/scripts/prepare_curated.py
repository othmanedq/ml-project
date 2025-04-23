#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
prepare_curated.py
-------------------
Pour chaque saison, ce script :
1. Lit les fichiers raw (boxscores + mensurations)
2. Agrège les statistiques match → joueur/saison
3. Fusionne avec les mensurations
4. Vérifie que les colonnes critiques sont bien présentes
5. Sauvegarde le fichier final dans data/curated/
"""

import pandas as pd
from pathlib import Path

# Dossiers
RAW     = Path("nba_rating/data/raw")
CURATED = Path("nba_rating/data/curated")
CURATED.mkdir(parents=True, exist_ok=True)

# Saisons à traiter
seasons = [f"{y}-{str(y+1)[-2:]}" for y in range(2014, 2024)]

def convert_height(ht):
    try:
        ft, inch = map(int, ht.split("-"))
        return ft * 30.48 + inch * 2.54
    except:
        return None

print("📦 Création des fichiers curated/")
for season in seasons:
    try:
        # Chargement des fichiers RAW
        gl_path = RAW / f"player_gamelog_{season}.parquet"
        ph_path = RAW / f"player_phys_{season}.parquet"
        out_path = CURATED / f"player_season_{season}.parquet"

        gl = pd.read_parquet(gl_path)

        # Agrégation des stats par joueur
        stats = gl.groupby("PLAYER_ID").agg(
            pts_mean         = ("PTS", "mean"),
            reb_mean         = ("REB", "mean"),
            ast_mean         = ("AST", "mean"),
            plus_minus_mean  = ("PLUS_MINUS", "mean"),
            gp               = ("GAME_ID", "nunique")
        ).reset_index()

        # Tentative de fusion avec les mensurations
        if ph_path.exists():
            phys = pd.read_parquet(ph_path)

            # Conversions si manquantes
            if "height_cm" not in phys.columns and "HEIGHT" in phys.columns:
                phys["height_cm"] = phys["HEIGHT"].apply(convert_height)

            if "weight_kg" not in phys.columns and "WEIGHT" in phys.columns:
                phys["weight_kg"] = pd.to_numeric(phys["WEIGHT"], errors="coerce") / 2.205

            if "bmi" not in phys.columns and {"height_cm", "weight_kg"}.issubset(phys.columns):
                phys["bmi"] = phys["weight_kg"] / (phys["height_cm"]/100)**2

            if "AGE" in phys.columns:
                phys = phys.rename(columns={"AGE": "age"})

            # Sélection des colonnes disponibles
            phys = phys[["PLAYER_ID"] + [c for c in ["height_cm", "weight_kg", "bmi", "age"] if c in phys.columns]]
        else:
            phys = pd.DataFrame(columns=["PLAYER_ID"])  # fichier vide mais sans erreur

        # Fusion
        df = stats.merge(phys, on="PLAYER_ID", how="left")

        # Vérifications
        cols_essentielles = ["pts_mean", "reb_mean", "ast_mean", "plus_minus_mean", "gp"]
        for col in cols_essentielles:
            assert col in df.columns, f"❌ Colonne manquante : {col} dans {season}"

        if not {"height_cm", "bmi", "age"}.issubset(df.columns):
            print(f"⚠️  Mensurations incomplètes pour {season} (physiques non utilisés dans cette saison)")

        df.to_parquet(out_path, index=False)
        print(f"✅ {season} : {len(df)} joueurs traités")

    except Exception as e:
        print(f"❌ {season} : erreur → {e}")
