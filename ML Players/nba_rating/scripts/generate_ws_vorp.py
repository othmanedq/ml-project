#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_ws_vorp.py
-------------------
Automatisation de la collecte des métriques avancées (Win Shares, VORP)
depuis Basketball-Reference pour chaque saison NBA de 1999-00 à 2023-24,
puis matching sur PLAYER_ID via all_player_gamelogs.parquet, avec
normalisation des noms, fuzzy matching, et export des noms non mappés.

Usage:
    python nba_rating/scripts/generate_ws_vorp.py
"""

import warnings
import unicodedata
import re
from pathlib import Path

import pandas as pd
from thefuzz import process


def normalize(name: str) -> str:
    if not isinstance(name, str):
        return ""
    # enlever accents
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_str = "".join(c for c in nfkd if not unicodedata.combining(c))
    # ➊ remplacer tirets/traits d’union par espace
    ascii_str = ascii_str.replace("-", " ").replace("–", " ")
    # ➋ minuscules, ne garder que alphanum & espace
    s = re.sub(r"[^a-zA-Z0-9 ]+", "", ascii_str.lower()).strip()
    # ➌ retirer suffixes
    s = re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", s)
    # ➍ compresser espaces multiples
    return re.sub(r"\s+", " ", s).strip()


def fetch_season_table(year: int) -> pd.DataFrame:
    """
    Récupère la table "Advanced" pour la saison (year-1)-year depuis B-Ref,
    extrait Player, WS, VORP, ajoute 'season' format 'YYYY-YY'.
    """
    url = f"https://www.basketball-reference.com/leagues/NBA_{year}_advanced.html"
    try:
        df = pd.read_html(url)[0]
    except Exception as e:
        warnings.warn(f"Impossible de télécharger {url}: {e}")
        return pd.DataFrame()

    # flatten header
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [
            col[1] if col[1] and not col[1].startswith("Unnamed") else col[0]
            for col in df.columns.values
        ]

    # supprimer lignes d'en-tête répétées
    if "Player" in df.columns:
        df = df[df["Player"] != "Player"]

    # vérifier colonnes
    required = {"Player", "WS", "VORP"}
    found = set(df.columns)
    if not required.issubset(found):
        warnings.warn(
            f"Saison {year-1}-{str(year)[2:]} ignorée : attendues {required}, trouvées {found}"
        )
        return pd.DataFrame()

    df = df.loc[:, ["Player", "WS", "VORP"]].copy()
    df.columns = ["PLAYER_NAME", "Win_Shares", "VORP"]
    df["season"] = f"{year-1}-{str(year)[2:]}"
    return df


BASE        = Path(__file__).resolve().parents[1] / "data"
RAW_DIR     = BASE / "raw"
CURATED_DIR = BASE / "curated"
OUT_PATH    = CURATED_DIR / "wins_shares_vorp.parquet"
LOGS_UNI    = CURATED_DIR / "all_player_gamelogs.parquet"

if not LOGS_UNI.exists():
    raise FileNotFoundError("…lance d'abord rassemble_gamelogs.py…")

# 1) Scraping → df_ws
years, dfs = range(2000,2025), []
for y in years:
    df_s = fetch_season_table(y)
    if not df_s.empty:
        dfs.append(df_s)
df_ws = pd.concat(dfs, ignore_index=True)

# 2) Normalisation
df_ws["PLAYER_NAME_NORM"] = df_ws["PLAYER_NAME"].apply(normalize)

# 3) Mapping complet
mapping = (
    pd.read_parquet(LOGS_UNI, columns=["PLAYER_ID","PLAYER_NAME"])
        .drop_duplicates("PLAYER_NAME")
)
mapping["PLAYER_NAME_NORM"] = mapping["PLAYER_NAME"].apply(normalize)

# 4) Merge norm
df_ext = df_ws.merge(mapping[["PLAYER_ID","PLAYER_NAME_NORM"]],
                        on="PLAYER_NAME_NORM", how="left")

# 5) Fuzzy matching
miss = df_ext["PLAYER_ID"].isna()
noms = df_ext.loc[miss,"PLAYER_NAME_NORM"].unique()
choices = mapping["PLAYER_NAME_NORM"].tolist()
fmap = {n: process.extractOne(n, choices, score_cutoff=90)[0]
        for n in noms if process.extractOne(n, choices, score_cutoff=90)}
df_ext["PLAYER_NAME_NORM_FUZZY"] = df_ext["PLAYER_NAME_NORM"].map(lambda x: fmap.get(x,x))
df_ext = df_ext.merge(mapping[["PLAYER_ID","PLAYER_NAME_NORM"]],
                        left_on="PLAYER_NAME_NORM_FUZZY",
                        right_on="PLAYER_NAME_NORM",
                        how="left",
                        suffixes=("","_fuzzy"))
df_ext["PLAYER_ID"] = df_ext["PLAYER_ID"].fillna(df_ext["PLAYER_ID_fuzzy"])

# 6) Manual map pour derniers cas
manual_map = {
    "league average": None,
    # ex :
    # "tre scott":       "762",
    # "jeenathan williams":"1630252",
    # …
}
df_ext["PLAYER_NAME_NORM"] = df_ext["PLAYER_NAME_NORM"].replace(manual_map)
df_ext = df_ext.merge(mapping[["PLAYER_ID","PLAYER_NAME_NORM"]],
                        on="PLAYER_NAME_NORM",
                        how="left",
                        suffixes=("","_manu"))
df_ext["PLAYER_ID"] = df_ext["PLAYER_ID"].fillna(df_ext["PLAYER_ID_manu"])

# —— DEBUG export non-mappés ——
unmatched = df_ext[df_ext["PLAYER_ID"].isna()]
if not unmatched.empty:
    to_debug = (unmatched[["PLAYER_NAME","PLAYER_NAME_NORM"]]
                .drop_duplicates())
    debug_path = CURATED_DIR / "unmatched_ws_vorp.parquet"
    to_debug.to_parquet(debug_path, index=False)
    print(f"🔍 noms non mappés → {debug_path} ({len(to_debug)} uniq)")

# 7) Export final
df_ext.loc[:,["PLAYER_ID","season","Win_Shares","VORP"]] \
        .to_parquet(OUT_PATH, index=False)
print(f"✅ wins_shares_vorp.parquet ({len(df_ext)}) → {OUT_PATH}")