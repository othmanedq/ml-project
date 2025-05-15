#!/usr/bin/env python3
# nba_rating/scripts/predict_future.py

import argparse
import joblib
import pandas as pd
import numpy as np
from pathlib import Path

def load_model(model_path):
    return joblib.load(model_path)

def load_dataset(dataset_path):
    return pd.read_parquet(dataset_path)

def predict_horizon(df, model, feature_cols, name_col, season_col, player_name, horizon=1):
    # Sélection du joueur et tri chronologique
    p_df     = df[df[name_col] == player_name].sort_values(season_col)
    last_row = p_df.iloc[-1]
    # Préparer un vecteur de features complet attendu par le modèle
    if hasattr(model, "feature_names_in_"):
        expected_feats = list(model.feature_names_in_)
    else:
        expected_feats = feature_cols

    # Construire une Series avec toutes les features, remplissant les manquantes par NaN
    current = pd.Series({feat: (last_row.get(feat, np.nan)) for feat in expected_feats})
    preds    = []
    for h in range(1, horizon + 1):
        raw  = model.predict(current.values.reshape(1, -1))[0]
        pred = float(np.clip(raw, 0.0, 100.0))
        preds.append(pred)
        # ---- Faire évoluer progressivement les features temporelles ----
        # On propage le score prédit pour qu'il soit pris en compte au pas suivant
        if "score_100" in expected_feats:
            current["score_100"] = pred
        # Âge / expérience / saison : +1 par horizon si présents dans les features
        if "age" in current:
            current["age"] += 1
        if "experience" in current:
            current["experience"] += 1
        # Certaines features encodent la saison sous forme d'indice numérique
        for time_col in ("season_idx", "season_index", "season_num"):
            if time_col in current:
                current[time_col] += 1
    return preds

def main(args):
    # 1) Charger modèle et data
    model   = load_model(args.model)
    df      = load_dataset(args.dataset)
    # Encode season into a numeric index if not present
    if "season_idx" not in df.columns:
        df["season_idx"] = df["season"].astype("category").cat.codes
    # 2) Déterminer colonnes
    name_col    = "player_name"
    season_col  = "season"
    # 2) Déterminer colonnes de features utilisées par le modèle
    if hasattr(model, "feature_names_in_"):
        FEATURE_COLS = list(model.feature_names_in_)
    else:
        # fallback : toutes les colonnes sauf celles exclues
        excluded = {name_col, season_col, "target_note_n1"}
        FEATURE_COLS = [c for c in df.columns if c not in excluded]
    # 3) Prédire
    results = []
    # Always process all active players (ignore --player flag)
    active = df[df["target_note_n1"].notna()][name_col].unique()
    players = sorted(active.tolist())
    for pl in players:
        preds = predict_horizon(df, model, FEATURE_COLS,
                                name_col, season_col,
                                pl, args.horizon)
        for i, val in enumerate(preds, start=1):
            results.append({
                "PLAYER_NAME": pl,
                "horizon": i,
                "pred_score": float(val)
            })
    out = pd.DataFrame(results)
    # 4) Afficher / Exporter
#    # Sauvegarde par défaut vers projections.parquet
    output_path = args.output or (Path(__file__).resolve().parents[1] / "data" / "curated" / "projections.parquet")
    output_path.parent.mkdir(exist_ok=True, parents=True)
    out.to_parquet(output_path, index=False)
    print(f"→ Projections sauvegardées dans {output_path}")

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Projeter score_100 n+1…n+H via modèle ML")
    p.add_argument("--model",   default="nba_rating/models/model_best.pkl")
    p.add_argument("--dataset", default="nba_rating/data/curated/dataset_ml.parquet")
    p.add_argument("--horizon", type=int, default=5, help="Nombre de saisons à projeter (défaut 5)")
    p.add_argument("--output",  help="Chemin pour sauvegarder le résultat (CSV)")
    name_col = "player_name"
    season_col = "season"
    main(p.parse_args())