# build_dataset_ml.py
# ---------------------
# Construit un dataset X/y multi-saisons pour entraîner un modèle de prédiction du score_100 futur (note_n+1)
# Basé sur les fichiers : all_seasons_scores.parquet + player_season_YYYY-YY.parquet

import pandas as pd
from pathlib import Path

# Répertoires
curated = Path("nba_rating/data/curated/")
seasons = [f"{y}-{str(y+1)[-2:]}" for y in range(2014, 2024)]

# 1. Charger le fichier des scores
scores = pd.read_parquet(curated / "all_seasons_scores.parquet")

# 2. Charger toutes les saisons de features
dfs = []
for s in seasons:
    df = pd.read_parquet(curated / f"player_season_{s}.parquet")
    df["season"] = s
    dfs.append(df)

features = pd.concat(dfs, ignore_index=True)

# 3. Fusion score_100 + features
df_all = pd.merge(scores, features, on=["PLAYER_ID", "season"], how="left")
df_all = df_all.sort_values(["PLAYER_ID", "season"])
df_all["avail"] = df_all["gp"] / 82  # recalculer si manquant

# 4. Créer note_n et note_n+1
df_all["note_n"] = df_all["score_100"]
df_all["note_n1"] = df_all.groupby("PLAYER_ID")["score_100"].shift(-1)

# 5. Filtrer les lignes valides (note_n1 connue)
df_ml = df_all.dropna(subset=["note_n1"])

# 6. Sélection des features et cible
features_used = [
    "pts_mean", "reb_mean", "ast_mean", "plus_minus_mean",
    "avail", "height_cm", "bmi", "age"
]

X = df_ml[features_used]
y = df_ml["note_n1"]

# 7. Export du dataset final
df_ml_final = X.copy()
df_ml_final["target_note_n1"] = y
df_ml_final.to_parquet(curated / "dataset_ml.parquet", index=False)

print("✅ Dataset ML enregistré dans: data/curated/dataset_ml.parquet")
