# Makefile - Automatisation du pipeline NBA Rating

# Dossiers
CURATED_DIR = nba_rating/data/curated

# Commandes

collect_raw:
	python scripts/collect_raw.py

fix_phys:
	python scripts/fix_phys.py

prepare_curated:
	python scripts/prepare_curated.py

compute_rating:
	python scripts/compute_rating_all.py

build_dataset_ml:
	python scripts/build_dataset_ml.py

train_model:
	jupyter nbconvert --to notebook --execute nba_rating/notebooks/train_model.ipynb --inplace

compare_models:
	jupyter nbconvert --to notebook --execute nba_rating/notebooks/compare_models.ipynb --inplace

predict_future:
	python scripts/predict_future.py

clean_curated:
	rm -f $(CURATED_DIR)/player_season_*.parquet

all: collect_raw fix_phys prepare_curated compute_rating build_dataset_ml train_model
