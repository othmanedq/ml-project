# prepare_curated.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prepare_curated.py
-------------------
Pour chaque saison :
1. Lit les raw (boxscores, phys)
2. Agrège match→joueur/saison
3. Fusionne mensurations + POSITION + exp
4. Ajoute min_per_game
5. Joint esv_mean et pace
6. Sauvegarde en curated
"""
import pandas as pd
from pathlib import Path

RAW     = Path("nba_rating/data/raw")
CURATED = Path("nba_rating/data/curated")
CURATED.mkdir(parents=True, exist_ok=True)
SEASONS = [f"{y}-{str(y+1)[-2:]}" for y in range(1999, 2024)]

for season in SEASONS:
    gl = pd.read_parquet(RAW/f"player_gamelog_{season}.parquet")
    phys = pd.read_parquet(RAW/f"player_phys_{season}.parquet")
    esv  = pd.read_parquet(RAW/f"player_esv_{season}.parquet")
    pace = pd.read_parquet(RAW/f"team_pace_{season}.parquet")

    # 1) stats de base
    stats = gl.groupby("PLAYER_ID").agg(
        pts_mean        = ("PTS","mean"),
        reb_mean        = ("REB","mean"),
        ast_mean        = ("AST","mean"),
        plus_minus_mean = ("PLUS_MINUS","mean"),
        gp               = ("GAME_ID","nunique"),
        min_per_game    = ("MIN","mean")
    ).reset_index()

    # 2) phys + poste + exp
    phys = phys.rename(columns={"AGE":"age","EXP":"exp"})
    keep = ["PLAYER_ID","POSITION","height_cm","weight_kg","bmi","age","exp"]
    phys = phys[[c for c in keep if c in phys.columns]]

    df = stats.merge(phys, on="PLAYER_ID", how="left")

    # 3) esv_mean
    df = df.merge(esv, on="PLAYER_ID", how="left")

    # 4) pace
    main_tm = gl.groupby(["PLAYER_ID","TEAM_ID"]).size()\
                .reset_index(name="cnt")\
                .sort_values("cnt",ascending=False)\
                .drop_duplicates("PLAYER_ID")
    df = df.merge(main_tm[["PLAYER_ID","TEAM_ID"]], on="PLAYER_ID", how="left")
    df = df.merge(pace, on="TEAM_ID", how="left")

    # 5) vérifications
    for c in ["pts_mean","reb_mean","ast_mean","plus_minus_mean","gp"]:
        assert c in df.columns

    df.to_parquet(CURATED/f"player_season_{season}.parquet", index=False)
    print(f"✅ {season} → {len(df)} joueurs")
