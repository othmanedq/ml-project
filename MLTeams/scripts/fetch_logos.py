# fetch_logos.py
import os
import requests
from nba_api.stats.static import teams
from time import sleep

# 1) Dossier de sortie
out_dir = "logos"
os.makedirs(out_dir, exist_ok=True)

# 2) Récupération des équipes NBA
teams_list = teams.get_teams()
print(f"Trouvé {len(teams_list)} équipes.")

# 3) Pour chaque équipe, télécharger son logo SVG
for t in teams_list:
    tid  = t["id"]
    abbr = t["abbreviation"]
    # URL standard du logo NBA
    url  = f"https://cdn.nba.com/logos/nba/{tid}/primary/L/logo.svg"
    resp = requests.get(url, timeout=5)
    if resp.status_code == 200:
        path = os.path.join(out_dir, f"{abbr}.svg")
        with open(path, "wb") as f:
            f.write(resp.content)
        print(f"📥 {abbr} → {path}")
    else:
        print(f"⚠️ Échec pour {abbr} ({resp.status_code})")
    sleep(0.1)  # politesse

print("Terminé !")
