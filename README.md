# NBA-Rating ML – README

## 📊 Data, Methods & Sources

| Aspect | Description |
|--------|-------------|
| **Data type** | *Tabular sports data* covering every NBA season **1999 → 2023**. <br>• **Game-level box-scores** (PTS, REB, AST, ± …) <br>• **Player physiques** (height cm, weight kg, BMI, age, position) <br>• **Derived stats** per season : `min_per_game`, per-36 rates, shooting efficiency (eFG %, TS %), Estimated Shot Value `esv_mean` <br>• **Target** : `score_100`, unidimensional rating recentred to μ = 50, σ = 25 |
| **Sources & API endpoints** | [`nba_api`](https://github.com/swar/nba_api) – official NBA Stats REST  <br>• `LeagueGameLog` → box-scores  <br>• `CommonTeamRoster` → physiques & position  <br>• `LeagueDashPlayerStats` → shot profile (ESV)  <br>All calls automatised in **`scripts/collect_raw.py`**; parquet caches under `nba_rating/data/raw/`. |
| **Data preparation** | **`prepare_curated.py`** & **`feature_engineering.py`**  <br>1. Aggregate game logs → season averages per player  <br>2. Merge physiques, compute BMI & availability (`gp/82`)  <br>3. Add per-36 & efficiency features  <br>4. Output `player_season_YYYY-YY.parquet` in `data/curated/`. |
| **Purpose** | • Build a **rating reference** (`score_100`) comparable across eras  <br>• Train a model predicting **next-season score** (`note_n+1`) to flag breakout/decline trends  <br>• Feed a future Streamlit dashboard for scouting & fan analytics. |

---

## 🤖 Machine-Learning Methods & Rationale

| Modèle | Pourquoi ce choix ? |
|--------|--------------------|
| **Ridge Regression** | Baseline linéaire régularisée (L2) : interprétable, très rapide, souvent au plus proche du RMSE mini après normalisation Z-score. |
| **HistGradientBoostingRegressor** | Boosting à histogrammes (scikit-learn) : capture non-linéarités & interactions, tuning modéré, robuste aux grandes tables. |
| **LightGBM** | Implémentation GBDT ultra-rapide (CPU/GPU), gère nativement missing values & catégories, ≈ 5 % plus précis que HGB pour un coût calcul raisonnable. |
| **MLPRegressor** | Réseau feed-forward (64-128-64) : apprend des patterns non linéaires plus fins ; gagne ~0.5 % RMSE sur nos données pour un temps < 5 s. |
| **Stacking final** | Ensemble Ridge + HGB + LightGBM (+ MLP) avec meta-Ridge : combine forces linéaires & non-linéaires, ~-2 % RMSE supplémentaire en CV. |

> **Critères de sélection** : performance (RMSE / R², 5-fold CV), robustesse (variance entre folds), temps d’entraînement/prédiction (CI-friendly), interprétabilité (coeffs Ridge, permutation importance HGB/LGBM).
