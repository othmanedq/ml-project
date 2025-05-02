# NBA-Rating Machine Learning Project — Players

## 📊 Data, Methods & Sources (Players)

| Aspect | Description |
|--------|-------------|
| **Data type** | *Tabular sports data* sur tous les joueurs NBA, saisons **1999 → 2023**.  
• **Box-scores par match** (PTS, REB, AST, ± …)  
• **Caractéristiques physiques** (taille, poids, BMI, âge, poste)  
• **Stats dérivées** par saison : `min_per_game`, per-36, efficacité au tir (eFG %, TS %), Estimated Shot Value `esv_mean`  
• **Cible** : `score_100`, rating unidimensionnel recentré (μ = 50, σ = 25) |
| **Sources & API endpoints** | [`nba_api`](https://github.com/swar/nba_api) – NBA Stats REST  
• `LeagueGameLog` → box-scores  
• `CommonTeamRoster` → physiques & position  
• `LeagueDashPlayerStats` → shot profile (ESV)  
Automatisation dans **`scripts/collect_raw.py`** ; caches parquet sous `nba_rating/data/raw/`. |
| **Data preparation** | **`prepare_curated.py`** & **`feature_engineering.py`**  
1. Agrégation logs → moyennes saison/joueur  
2. Fusion physiques, calcul BMI & disponibilité (`gp/82`)  
3. Ajout per-36 & features d’efficacité  
4. Sortie `player_season_YYYY-YY.parquet` dans `data/curated/`. |
| **Purpose** | • Construire une **référence de rating** (`score_100`) comparable entre époques  
• Entraîner un modèle prédisant le **score saison suivante** (`note_n+1`) pour détecter breakout/decline  
• Alimenter un futur dashboard Streamlit pour scouting & analytics fans. |

---

## 🤖 Machine-Learning Methods & Rationale (Players)

| Modèle | Pourquoi ce choix ? |
|--------|---------------------|
| **Ridge Regression** | Baseline linéaire régularisée (L2) : interprétable, très rapide, souvent proche du RMSE mini après normalisation Z-score. |
| **HistGradientBoostingRegressor** | Boosting à histogrammes (scikit-learn) : capture non-linéarités & interactions, tuning modéré, robuste sur grandes tables. |
| **LightGBM** | GBDT ultra-rapide (CPU/GPU), gère nativement missing values & catégories, ≈ 5 % plus précis que HGB pour un coût calcul raisonnable. |
| **MLPRegressor** | Réseau feed-forward (64-128-64) : apprend des patterns non linéaires fins ; gagne ~0.5 % RMSE sur nos données pour un temps < 5 s. |
| **Stacking final** | Ensemble Ridge + HGB + LightGBM (+ MLP) avec meta-Ridge : combine linéaire & non-linéaire, ~-2 % RMSE supplémentaire en CV. |

> **Critères de sélection** : performance (RMSE / R², 5-fold CV), robustesse (variance entre folds), temps d’entraînement/prédiction (CI-friendly), interprétabilité (coeffs Ridge, permutation importance HGB/LGBM).


Nom des participants : Louis ALLIO — Noa KASSABI — Othmane EDDAQQAQ