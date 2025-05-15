# ML Players

> ⚠️ Projet – Système de notation et prédiction des performances NBA.

Lien de la présentation : https://bit.ly/NBAmlproject

## Table des matières

1. [Objectif du projet](#objectif-du-projet)  
2. [Description des données](#description-des-données)  
3. [Méthodologie & pipeline](#méthodologie--pipeline)  
4. [Modèles & choix algorithmiques](#modèles--choix-algorithmiques)  
5. [Validation & évaluation](#validation--évaluation)  
6. [Dashboard & visualisation](#dashboard--visualisation)  
7. [Installation & premiers tests](#installation--premiers-tests)  
8. [Automatisation](#automatisation)  
9. [Contribution](#contribution)  
10. [Licence](#licence)  


---

## Objectif du projet

ML Players a pour vocation de :
- **Mesurer** la performance d’un joueur NBA sur une saison via un **score unifié** (`score_100`).  
- **Prédire** ce `score_100` pour la saison suivante à partir des statistiques et features avancées.  
- **Valider** la qualité de la prédiction par back-tests temporels et corrélations externes (Win Shares, VORP).  
- **Fournir** un outil interactif (dashboard Streamlit) pour explorer scores, clusters et comparaisons.

## Description des données

- **Box-scores bruts** : récupérés via l’API NBA et/ou fichiers CSV de Basketball-Reference, sauvegardés en Parquet (`nba_rating/data/raw/player_gamelog_YYYY-YY.parquet`).  
- **Métriques externes** : Win Shares & VORP scrapés depuis Basketball-Reference, normalisés et matchés par fuzzy matching (`wins_shares_vorp.parquet`).  
- **Bio & contexte** : hauteur, poids, poste, ESV (estimate strength value), pace de l’équipe, extraits de l’API et de sources officielles.  
- **Dataset final** : multi-saisons contenant pour chaque joueur-saison _n_ les features d’entrée et la cible `score_100` de la saison _n+1` (`dataset_ml.parquet`).

## Méthodologie & pipeline

1. **Collecte & nettoyage**  
   - `collect_raw.py` : requêtes API ou lecture CSV → Parquet bruts.  
   - `fix_phys.py` : nettoyage et standardisation de la taille, poids, poste.  
2. **Préparation “curated”**  
   - `prepare_curated.py` : agrégation match→joueur, jointures bio/ESV/pace.  
3. **Calcul du score unifié**  
   - `compute_rating_all.py` : calcul de Z‑scores par variable, conversion en `score_100` (moyenne = 50, écart-type = 10).  
4. **Feature engineering avancé**  
   - `feature_engineering.py` :  
     - Efficacité : eFG %, TS %  
     - Production normalisée : per36 (pts36, reb36…)  
     - Splits : fg2_pct, fg3_pct, ft_pct  
     - Ratios : AST/TO, usage_rate  
     - Potentiel d’impact : plus-minus ajusté  
5. **Clustering des profils**  
   - `cluster_players.py` : K‑Means sur features standardisées + t‑SNE pour visualisation.  
6. **Construction du dataset multi-saisons**  
   - `build_dataset_ml.py` : fusion scores, features, clusters → `dataset_ml.parquet`.  
7. **Validation externe & back-tests**  
   - `validation_backtests.ipynb` : corrélations vs Win Shares/VORP, back-tests RMSE & R² par saison, analyse des résidus.  

## Modèles & choix algorithmiques

- **Baseline** : prédiction constante (moyenne mobile du `score_100`) pour évaluer le gain minimal.  
- **Régression linéaire** : modèle simple pour interprétabilité et comparaison.  
- **LightGBM** :  
  - **Avantages** : gestion des interactions complexes, robustesse aux features hétérogènes, rapidité d’entraînement.  
  - **Hyper-tuning** : Optuna / RandomizedSearchCV pour optimiser `num_leaves`, `learning_rate`, `n_estimators`.  
- **Importance des features** :  
  - Calcul via gain LightGBM et **SHAP** pour expliquer les contributions des variables.  

## Validation & évaluation

- **Cross-validation temporelle** (`TimeSeriesSplit`) : évaluer RMSE & R² en simulation « train sur saisons < N → test sur N ».  
- **Back-tests** : calcul de RMSE cible ≤ 10 et R² ≥ 0.6 sur la majorité des saisons.  
- **Corrélations externes** :  
  - Pearson entre `score_100` et Win Shares / VORP (objectif ≥ 0.7).  
- **Analyse des résidus** : identification des joueurs/outliers pour affiner features ou modèle.  

## Dashboard & visualisation

- **Streamlit** : exploration interactive des scores par saison, clusters, comparaisons score_100 vs Win Shares/VORP.  
- **Altair** : graphiques dynamiques (heatmaps, time series, scatter).  
- **Extensions** possibles : photos, logos des équipes, stats situational splits (clutch, PBP).  

## Installation & premiers tests

```bash
git clone https://github.com/othmanedq/ml-players.git
cd ml-players
pip install -r requirements.txt

# Pipeline complet
make all

# Lancer uniquement le dashboard (données déjà préparées)
make dashboard
```

## Automatisation

Toutes les étapes clés du pipeline sont regroupées dans le **Makefile** :

| Cible | Description |
|-------|-------------|
| `make collect_raw`          | Récupération des box‑scores bruts via l’API | 
| `make fix_phys`             | Nettoyage & standardisation des attributs physiques |
| `make prepare_curated`      | Agrégation match ➜ joueur & enrichment bio/pace |
| `make feature_engineering`  | Calcul des features avancées (per36, eFG %, TS %, etc.) |
| `make compute_rating`       | Calcul du `score_100` unifié |
| `make cluster_players`      | Clustering K‑means des profils |
| `make build_dataset_ml`     | Construction du dataset multi‑saisons ML |
| `make generate_ws_vorp`     | Scraping & fusion Win Shares / VORP |
| `make dashboard_data`       | Préparation des données finales pour le dashboard |
| `make predict_future`       | Projections horizon 1 → 5 saisons à l’avance |
| `make all`                  | Chaîne complète (collecte ➜ projections) |

> *Astuce :* chaque cible peut être lancée indépendamment pour du développement incrémental.

## Contribution

Les PR sont les bienvenues !  
1. Forkez le repo et créez votre branche (`git checkout -b feat/ma-feature`).  
2. Commitez vos changements (`git commit -m "Ajoute ma feature"`).  
3. Poussez la branche (`git push origin feat/ma-feature`) et ouvrez une *pull‑request*.

Merci de vous assurer que la commande `make all` s’exécute sans erreur avant d’ouvrir une pull‑request.

## Licence

Projet distribué sous licence **MIT**.  
Voir le fichier [`LICENSE`](LICENSE) pour plus de détails.


- Merci à [Basketball‑Reference](https://www.basketball-reference.com/) et à la [NBA Stats API](https://www.nba.com/stats) pour la mise à disposition des données.
- Icônes par [Feather](https://feathericons.com/) – licence MIT.

---
