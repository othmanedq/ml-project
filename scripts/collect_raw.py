import time, random
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from nba_api.stats.endpoints import LeagueGameLog, CommonTeamRoster
from nba_api.stats.static import teams

# Répertoires
RAW_DIR = Path("nba_rating/data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Saisons à traiter
seasons = [f"{y}-{str(y+1)[-2:]}" for y in range(1999, 2024)]
team_list = teams.get_teams()

def convert_height(h: str):
    try:
        ft, inch = map(int, h.split("-"))
        return ft * 30.48 + inch * 2.54
    except:
        return None

def collect_gamelog(season: str):
    out_path = RAW_DIR / f"player_gamelog_{season}.parquet"
    if out_path.exists():
        print(f"📁 Gamelog {season} déjà présent ({out_path.name})")
        return

    try:
        lg = LeagueGameLog(
            player_or_team_abbreviation="P",
            season=season,
            season_type_all_star="Regular Season",
            timeout=60
        )
        df = lg.get_data_frames()[0]
        df.to_parquet(out_path, index=False)
        print(f"✅ {season}: {len(df):,} lignes")
    except Exception as e:
        print(f"❌ Erreur Gamelog {season}: {e}")
    time.sleep(1)

def collect_phys(season: str):
    out_path = RAW_DIR / f"player_phys_{season}.parquet"
    if out_path.exists():
        print(f"📁 Physiques {season} déjà présent ({out_path.name})")
        return

    rows = []
    for team in tqdm(team_list, desc=f"🔍 Roster {season}"):
        try:
            cr = CommonTeamRoster(team_id=team["id"], season=season, timeout=30)
            rows.append(cr.common_team_roster.get_data_frame())
            time.sleep(random.uniform(0.3, 0.6))
        except Exception as e:
            print(f"⚠️ {team['full_name']}: {e}")

    df_all = pd.concat(rows, ignore_index=True)
    df_all["height_cm"] = df_all["HEIGHT"].apply(convert_height)
    df_all["weight_kg"] = pd.to_numeric(df_all["WEIGHT"], errors="coerce") / 2.205
    df_all["bmi"] = df_all["weight_kg"] / (df_all["height_cm"] / 100) ** 2
    df_all.to_parquet(out_path, index=False)
    print(f"✅ {season}: {len(df_all)} joueurs physiques")

# Lancement global
if __name__ == "__main__":
    print(f"📦 Sauvegarde dans : {RAW_DIR.absolute()}\n")
    for season in seasons:
        print(f"\n=== 📅 Saison {season} ===")
        collect_gamelog(season)
        collect_phys(season)


