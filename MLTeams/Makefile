# Makefile - Automatisation du pipeline NBA Teams

# Dossiers
CURATED_DIR = data/curated
RAW_DIR = data/raw
SCRIPTS_DIR = scripts
NOTEBOOKS_DIR = notebooks

# Commandes

collect_data:
	python $(SCRIPTS_DIR)/collect_team_data.py

prepare_curated:
	python $(SCRIPTS_DIR)/prepare_curated.py

explore_teams:
	jupyter nbconvert --to notebook --execute $(NOTEBOOKS_DIR)/explore_team_data.ipynb --inplace

model_v1:
	jupyter nbconvert --to notebook --execute $(NOTEBOOKS_DIR)/Modele.ipynb --inplace

model_final:
	jupyter nbconvert --to notebook --execute $(NOTEBOOKS_DIR)/Modele\ 2.0.ipynb --inplace

clean_curated:
	rm -f $(CURATED_DIR)/*.parquet

all: collect_data prepare_curated explore_teams
	@echo "All tasks completed successfully!"
	@echo "You can now run the model notebooks."
	@echo "To clean the curated data, run 'make clean_curated'."