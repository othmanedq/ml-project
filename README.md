# Statistiques des Joueurs NBA

Ce dépôt contient des données de statistiques des joueurs NBA collectées via l'API officielle de la NBA. Il a été conçu pour récupérer et stocker des données en temps réel tout en minimisant les risques de perte d'information.

## Description

Les statistiques des joueurs de la NBA sont extraites grâce à l'API officielle. Pendant le processus de collecte, des fichiers intermédiaires nommés `nba_players_data_temp_*.csv` sont générés. Ces fichiers servent de sauvegarde temporaire afin de garantir que les données ne soient pas perdues en cas d'interruption de l'API.

## Structure du Dépôt

- **nba_players_data_temp_*.csv**  https://drive.google.com/drive/folders/1SLVqHJXH8_d5Z0FPvkCtuz4K37L9ZvKo?usp=sharing
  Fichiers intermédiaires générés lors de la collecte des données. Chaque fichier contient une partie des statistiques collectées pour assurer la continuité de la collecte en cas d'interruption.

## Utilisation

1. **Collecte des Données**  
   Les données sont collectées directement à partir de l'API officielle de la NBA. En cas d'interruption, les fichiers temporaires permettent de reprendre le processus de collecte sans perte de données.

2. **Analyse des Données**  
   Les fichiers CSV peuvent être importés dans des outils d'analyse de données (comme Python, R, Excel, etc.) pour effectuer des traitements ou visualiser les statistiques.  
   Pour fusionner plusieurs fichiers CSV et analyser l'ensemble des données, vous pouvez utiliser des scripts Python ou tout autre outil adapté.

3. **Mise à Jour**  
   Pour relancer ou mettre à jour la collecte des données, exécutez le processus de collecte. Les fichiers temporaires continueront d'être générés et pourront être consolidés pour obtenir les données complètes.

## Installation

Pour cloner ce dépôt, utilisez la commande suivante :

```bash
git clone https://github.com/othmanedq/ml-project.git
cd ml-project
