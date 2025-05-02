# Prédiction de victoire en NBA à partir des statistiques d’équipes

Ce projet a pour objectif de prédire l’issue d’un match NBA entre deux équipes, uniquement à partir de leurs statistiques collectives moyennes.  
Nous n’utilisons aucune donnée individuelle de joueurs, aucun calendrier ou score direct.  
Tout repose sur l’analyse et l’exploitation des performances historiques moyennes des équipes NBA.

## Objectif

Pour chaque confrontation (équipe A vs équipe B), nous construisons un modèle de machine learning capable de prédire si l’équipe A va gagner.  
Le modèle s’appuie uniquement sur les moyennes statistiques calculées à partir de toutes les performances passées à partir de 1999 de chaque franchise.

## Collecte et préparation des données

Les données sont récupérées depuis l’API officielle de la NBA, via la librairie Python `nba_api`.  
Un script de collecte (`collect_team_data.py`) interroge l’API pour chaque saison et stocke, pour chaque match, les performances individuelles des équipes.  
Chaque ligne correspond à une équipe dans un match donné, avec :

- Identifiants : `TEAM_NAME`, `GAME_ID`, `MATCHUP`, `GAME_DATE`
- Résultat : `WL` (win/loss)
- Statistiques brutes : `PTS`, `REB`, `AST`, `STL`, `BLK`, `TOV`, `FG3M`, etc.

Une fois collectées, les données sont nettoyées et consolidées dans un fichier `team_gamelog_all_seasons.parquet` via le script `prepare_curated.py`.  
Ce format `.parquet` permet un chargement rapide, un traitement plus fluide et évite de relancer l’appel à l’API à chaque exécution.

## Calcul des statistiques moyennes

À partir des données consolidées, nous regroupons les matchs par équipe pour en extraire des statistiques moyennes sur l’ensemble de leur historique.

En plus des moyennes classiques (points, rebonds, passes...), nous calculons des ratios avancés :
- `AST_TOV_ratio` : efficacité à faire circuler la balle sans la perdre
- `OREB_ratio` : agressivité au rebond offensif
- `Three_Point_Rate` : dépendance au tir à 3 points

Ces ratios enrichissent le profil de chaque équipe et permettent de mieux différencier les styles de jeu.

## Analyse des styles d’équipe

Nous avons ensuite construit deux scores synthétiques pour caractériser chaque équipe :
- Un score offensif basé sur `PTS`, `AST`, `FG3M`, `OREB`
- Un score défensif basé sur `REB`, `STL`, `BLK`, et les pertes de balle

Ces scores sont normalisés pour pouvoir comparer toutes les franchises.  
Chaque équipe est ensuite classée dans un style de jeu : offensif, défensif ou équilibré.

Nous utilisons également l’algorithme de clustering KMeans pour regrouper automatiquement les équipes par profil statistique, et t-SNE pour projeter les données dans un espace 2D et visualiser la diversité des styles NBA.

## Construction du dataset A vs B

Pour entraîner un modèle de prédiction, nous avons recréé chaque match NBA comme une confrontation entre :
- les statistiques moyennes de l’équipe A (domicile)
- les statistiques moyennes de l’équipe B (extérieur)

Ces données sont fusionnées dans un seul tableau avec deux blocs de colonnes (`_Aavg` et `_Bavg`), et une colonne cible `WIN_A` (1 si l’équipe A a gagné, 0 sinon).

Les colonnes non numériques comme `style` ou `cluster` sont exclues afin de conserver un jeu de données propre pour le machine learning.

## Entraînement des modèles

Nous avons testé plusieurs modèles de classification :
- Random Forest
- XGBoost
- K-Nearest Neighbors (KNN)
- Régression logistique

Le jeu de données a été séparé en un ensemble d’entraînement (80 %) et de test (20 %).  
Les modèles sont évalués avec plusieurs métriques :
- Accuracy
- Précision, rappel, f1-score
- Matrices de confusion

Nous comparons les résultats pour identifier le modèle le plus robuste.

## Prédictions manuelles

Une fois le modèle entraîné, il est possible de simuler une confrontation entre deux équipes :
- Le système récupère les statistiques moyennes de chaque équipe
- Il construit automatiquement le format attendu
- Le modèle prédit si l’équipe A a des chances de gagner et affiche la probabilité de victoire

Cela permet de simuler n’importe quel duel NBA avec un score de confiance.

## Résultats

- Le modèle Random Forest est celui qui offre les meilleures performances (jusqu’à 60 % de précision)
- Les matrices de confusion montrent que les prédictions sont bien équilibrées
- Les projections t-SNE permettent de visualiser les styles proches et les profils atypiques
- Le système de prédiction manuelle fonctionne très bien avec une réponse rapide et interprétable

## Améliorations futures

Plusieurs pistes peuvent améliorer la performance du modèle :
- Ajouter la forme récente via des moyennes glissantes (derniers matchs)
- Intégrer des variables de contexte comme la saison, le type de match (playoffs ou non), ou l’avantage du terrain
- Calculer des différences statistiques entre A et B plutôt que de concaténer uniquement leurs profils
- Fusionner avec les données joueur-par-joueur pour une approche mixte

