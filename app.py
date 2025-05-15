# Mapping des postes acronyme → nom complet
POS_MAPPING = {
    "PG": "Point Guard",
    "SG": "Shooting Guard",
    "SF": "Small Forward",
    "PF": "Power Forward",
    "C":  "Center",
    "G": "Guard",
    "F": "Forward"
}
import streamlit as st
import pandas as pd
import altair as alt
import streamlit.components.v1 as components
import re, urllib.parse
from functools import lru_cache
import os
import numpy as np
from datetime import date

# ─── CSS GLOBAL DE FOND & OVERLAY ──────────────────────────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Anton&display=swap" rel="stylesheet">

<style>
  /* --- On annule tout background sur l'app --- */
  .stApp {
    position: relative !important;
    background: none !important;
  }

  /* --- Pseudo-élément pour l'image + overlay semi-opaque --- */
  .stApp::before {
    content: "";
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background:
      /* Overlay semi-opaque (noir à 50%) */
      linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.5)),
      /* Image de fond */
      url("https://m.media-amazon.com/images/I/71vnTbuSmNL.jpg") center/cover no-repeat;
    filter: blur(3px);  /* Optionnel : léger flou */
    z-index: -1;
  }

  /* --- On remet le contenu au-dessus --- */
  .stApp > * {
    position: relative;
    z-index: 1;
  }

  /* --- Encadrés transparents pour chaque bloc de contenu --- */
  .stApp .main .block-container .element-container {
    background-color: rgba(255,255,255,0.85) !important;
    padding: 1rem !important;
    border-radius: 12px !important;
    margin-bottom: 1rem !important;
  }
  .stApp .main .block-container .element-container > * {
    position: relative;
    z-index: 1;
  }

  /* --- Metric Cards --- */
  .metric-card {
    background: rgba(255,255,255,0.9);
    border-radius: 12px;
    padding: 1.2rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    text-align: center;
    margin-bottom: 1rem;
  }
  .metric-card h4 {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 300;
    color: #C9082A;
  }
  .metric-card p {
    margin: 0.5rem 0 0;
    font-size: 1.8rem;
    font-weight: 700;
    color: #333;
  }

  /* --- Sidebar semi-transparente --- */
  .sidebar .sidebar-content {
    background-color: rgba(30, 30, 30, 0.8);
    color: #FFF;
  }
  .sidebar .sidebar-content select, 
  .sidebar .sidebar-content input {
    color: #000;
  }

  /* --- Titres --- */
  h1,h2,h3,h4 {
    font-family: 'Anton', sans-serif;
    color: #FFFFFF;
    font-weight: 300;
    margin-bottom: 0.3em;
  }

  /* --- Boutons primaires --- */
  button[kind="primary"] {
    background-color: #C9082A !important;
    color: #fff !important;
    border-radius: 8px !important;
    padding: 0.5em 1.5em !important;
    font-weight: bold !important;
  }
  button[kind="primary"]:hover {
    background-color: #8A0C19 !important;
  }
</style>
""", unsafe_allow_html=True)

# Descriptions des profils de cluster
CLUSTER_DESCRIPTIONS = {
    'Playmaker': 'Maîtrise du jeu, distribution et vision du terrain',
    'All-Around': 'Polyvalent dans toutes les facettes du jeu',
    'Scoring Guard': 'Principalement axé sur la création et la finition au scoring',
    'Big Man': 'Présence dans la raquette et rebonds',
    'Sharpshooter': 'Excellence au tir extérieur'
}
# --- Ajout TEAM_INFO pour logos et abréviations ---
TEAM_INFO = {
    1610612737: ('ATL', 'https://cdn.nba.com/logos/nba/1610612737/global/L/logo.svg'),
    1610612738: ('BOS', 'https://cdn.nba.com/logos/nba/1610612738/global/L/logo.svg'),
    1610612739: ('CLE', 'https://cdn.nba.com/logos/nba/1610612739/global/L/logo.svg'),
    1610612740: ('NOP', 'https://cdn.nba.com/logos/nba/1610612740/global/L/logo.svg'),
    1610612741: ('CHI', 'https://cdn.nba.com/logos/nba/1610612741/global/L/logo.svg'),
    1610612742: ('DAL', 'https://cdn.nba.com/logos/nba/1610612742/global/L/logo.svg'),
    1610612743: ('DEN', 'https://cdn.nba.com/logos/nba/1610612743/global/L/logo.svg'),
    1610612744: ('GSW', 'https://cdn.nba.com/logos/nba/1610612744/global/L/logo.svg'),
    1610612745: ('HOU', 'https://cdn.nba.com/logos/nba/1610612745/global/L/logo.svg'),
    1610612746: ('LAC', 'https://cdn.nba.com/logos/nba/1610612746/global/L/logo.svg'),
    1610612747: ('LAL', 'https://cdn.nba.com/logos/nba/1610612747/global/L/logo.svg'),
    1610612748: ('MIA', 'https://cdn.nba.com/logos/nba/1610612748/global/L/logo.svg'),
    1610612749: ('MIL', 'https://cdn.nba.com/logos/nba/1610612749/global/L/logo.svg'),
    1610612750: ('MIN', 'https://cdn.nba.com/logos/nba/1610612750/global/L/logo.svg'),
    1610612751: ('BKN', 'https://cdn.nba.com/logos/nba/1610612751/global/L/logo.svg'),
    1610612752: ('NYK', 'https://cdn.nba.com/logos/nba/1610612752/global/L/logo.svg'),
    1610612753: ('ORL', 'https://cdn.nba.com/logos/nba/1610612753/global/L/logo.svg'),
    1610612754: ('IND', 'https://cdn.nba.com/logos/nba/1610612754/global/L/logo.svg'),
    1610612755: ('PHI', 'https://cdn.nba.com/logos/nba/1610612755/global/L/logo.svg'),
    1610612756: ('PHX', 'https://cdn.nba.com/logos/nba/1610612756/global/L/logo.svg'),
    1610612757: ('POR', 'https://cdn.nba.com/logos/nba/1610612757/global/L/logo.svg'),
    1610612758: ('SAC', 'https://cdn.nba.com/logos/nba/1610612758/global/L/logo.svg'),
    1610612759: ('SAS', 'https://cdn.nba.com/logos/nba/1610612759/global/L/logo.svg'),
    1610612760: ('OKC', 'https://cdn.nba.com/logos/nba/1610612760/global/L/logo.svg'),
    1610612761: ('TOR', 'https://cdn.nba.com/logos/nba/1610612761/global/L/logo.svg'),
    1610612762: ('UTA', 'https://cdn.nba.com/logos/nba/1610612762/global/L/logo.svg'),
    1610612763: ('MEM', 'https://cdn.nba.com/logos/nba/1610612763/global/L/logo.svg'),
    1610612764: ('WAS', 'https://cdn.nba.com/logos/nba/1610612764/global/L/logo.svg'),
    1610612765: ('DET', 'https://cdn.nba.com/logos/nba/1610612765/global/L/logo.svg'),
    1610612766: ('CHA', 'https://cdn.nba.com/logos/nba/1610612766/global/L/logo.svg'),
}

# --- Ajout helper carte joueur ---
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

def generate_player_card(template_path, player_photo_url, team_id, position, score, player_name):
    # Initialize abbrev to avoid UnboundLocalError
    abbrev = ""
    # 1) Charger le template
    template = Image.open(template_path).convert("RGBA")
    GOLD = (212, 175, 55, 255)  # couleur or
    # 2) Récupérer la photo du joueur et appliquer un masque circulaire
    resp = requests.get(player_photo_url)
    player_img = Image.open(BytesIO(resp.content)).convert("RGBA")
    # Agrandir la photo du joueur de 40%
    size = (int(500), int(500))
    player_img = player_img.resize(size)

    mask = Image.new("L", size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0) + size, fill=255)
    player_img.putalpha(mask)
    # Calcul des coordonnées centrées sur le template
    x_pos = (template.width - size[0]) // 2
    y_pos = int(template.height * 0.27)
    # Effacer le fond à l'intérieur du cercle (rendre transparent)
    draw_template = ImageDraw.Draw(template)
    circle_bbox = (x_pos, y_pos, x_pos + size[0], y_pos + size[1])
    draw_template.ellipse(circle_bbox, fill=(0, 0, 0, 0))
    # Coller ensuite la photo du joueur masquée
    template.paste(player_img, (x_pos, y_pos), player_img)
    # 3) (Suppression du collage du logo sur le template)
    # 4) Dessiner le texte
    draw = ImageDraw.Draw(template)
    # Chargement des polices avec plusieurs fallback pour garantir une taille lisible
    try:
        font_large = ImageFont.truetype("arial.ttf", 36)
        font_small = ImageFont.truetype("arial.ttf", 24)
    except IOError:
        try:
            # macOS system font
            font_large = ImageFont.truetype("/Library/Fonts/Arial.ttf", 70)
            font_small = ImageFont.truetype("/Library/Fonts/Arial.ttf", 60)
        except IOError:
            try:
                # common Linux fallback
                font_large = ImageFont.truetype("DejaVuSans.ttf", 36)
                font_small = ImageFont.truetype("DejaVuSans.ttf", 24)
            except IOError:
                # dernier recours : police par défaut (mais petite)
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
    # Nom du joueur au-dessus du trait
    name_y = template.height * 0.65
    bbox = draw.textbbox((0, 0), player_name, font=font_large)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((template.width - w) / 2, name_y), player_name, font=font_large, fill=GOLD)

    # Afficher poste, équipe et note sous la ligne en or
    info_y = name_y + h + 150

    # Position (gauche)
    pos_text = str(position)
    pos_bbox = draw.textbbox((0, 0), pos_text, font=font_small)
    pos_w = pos_bbox[2] - pos_bbox[0]
    draw.text((template.width * 0.24 - pos_w/2, info_y), pos_text, font=font_small, fill=GOLD)

    # Team abbreviation (centre)
        # --- Fallback : si team_id est déjà une abréviation texte (ex : "DEN") ----
    if abbrev == "":
        team_str = str(team_id)
        if len(team_str) == 3 and team_str.isalpha():
            abbrev = team_str.upper()
    team_text = str(abbrev) if abbrev else ""
    team_bbox = draw.textbbox((0, 0), team_text, font=font_small)
    team_w = team_bbox[2] - team_bbox[0]
    draw.text((template.width * 0.5 - team_w/2, info_y), team_text, font=font_small, fill=GOLD)

    # Score (droite)
    score_text = f"{score:.1f}"
    score_bbox = draw.textbbox((0, 0), score_text, font=font_small)
    score_w = score_bbox[2] - score_bbox[0]
    draw.text((template.width * 0.75 - score_w/2, info_y), score_text, font=font_small, fill=GOLD)
    return template

# Helper: fetch first YouTube highlight for a player (scraping, no API)
@lru_cache(maxsize=256)
def fetch_highlight_url(player: str) -> str | None:
    """
    Retourne l’URL du premier résultat YouTube pour « {player} highlights »  
    (scraping HTML – pas d’API officielle).
    """
    query = urllib.parse.quote_plus(f"{player} highlights")
    resp  = requests.get(
        f"https://www.youtube.com/results?search_query={query}",
        headers={"User-Agent": "Mozilla/5.0"}
    )
    if resp.status_code != 200:
        return None

    # Les IDs vidéo (11 caractères) sont dans le JSON initial de la page
    ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', resp.text)
    return f"https://www.youtube.com/watch?v={ids[0]}" if ids else None

# 1) Chargement des données (en cache)
@st.cache_data
def load_data():
    df = pd.read_parquet("MLPlayers/nba_rating/data/curated/dashboard_data.parquet")
    return df

df = load_data()


# 2) Détection dynamique des colonnes clefs
season_col  = next((c for c in df.columns if c.lower() == "season"), None)
player_col  = next((c for c in df.columns if c.lower() == "player_id"), None)
name_col    = next((c for c in df.columns if "name" in c.lower()), None)
cluster_col = next((c for c in df.columns if "cluster" in c.lower()), None)
# Recherche flexible de la colonne score
score_col = next((c for c in df.columns if c.lower() == "score_100"), None)
if score_col is None:
    # Fallback : chercher la première colonne qui contient l'un des mots‑clés
    keywords = ["score", "rating", "overall", "index"]
    score_candidates = [c for c in df.columns if any(k in c.lower() for k in keywords)]
    score_col = score_candidates[0] if score_candidates else None

# Aide au debug : si toujours introuvable, afficher la liste des colonnes
if score_col is None:
    st.warning(f"Colonne de score introuvable. Colonnes disponibles : {list(df.columns)}")
# Colonnes position et équipe
position_col = next(
    (c for c in df.columns
     if c.lower() in ("position", "pos", "player_pos", "player_position")
     or "position" in c.lower()),
    None
)
 # Column holding numeric team ID (preferred). Fallback to team name text column.
team_col = next((c for c in df.columns if "team_id" in c.lower()), None)
if team_col is None:
    team_col = next((c for c in df.columns if "team_name" in c.lower() or c.lower() == "team"), None)
# Détection colonne des profils (noms de clusters)
profile_col = next((c for c in df.columns if "profile_name" in c.lower()), None)

# Ajouter une colonne position_full avec le nom complet si position existe
if position_col and position_col in df.columns:
    df["position_full"] = df[position_col].map(POS_MAPPING).fillna(df[position_col])
else:
    df["position_full"] = None

# On stoppe si colonnes manquantes
if season_col is None or player_col is None or score_col is None:
    st.error(f"❌ Colonnes requises manquantes : season_col={season_col}, player_col={player_col}, score_col={score_col}")
    st.stop()

st.title("🏀 NBA Career Dashboard")
st.markdown("### Explorez les statistiques et la carrière des joueurs NBA grâce à ce tableau de bord interactif")
st.markdown("---")

# ─── Teams Tab: Data Loading and Utilities (Top-level) ─────────────────────────────
@st.cache_data
def load_gamelog():
    df = pd.read_parquet("MLTeams/data/curated/team_gamelog_all_seasons.parquet")
    df["date"] = pd.to_datetime(df["GAME_DATE"])
    df["year"] = df["date"].dt.year
    df["team"] = df["TEAM_NAME"]
    df["win"]  = df["WL"].map({"W":1,"L":0})
    df["pts"]  = df["PTS"]
    df["ast"]  = df["AST"]
    df["reb"]  = df["REB"]
    df["stl"]  = df["STL"]
    df["blk"]  = df["BLK"]
    return df

@st.cache_data
def load_preds():
    return pd.read_parquet("MLTeams/data/curated/all_pair_preds.parquet")

@st.cache_data
def load_logos():
    df = load_gamelog()
    logo_dir = "MLTeams/logos"
    logos = {
        row["TEAM_NAME"]: os.path.join(logo_dir, f"{row['TEAM_ABBREVIATION']}.svg")
        for _, row in df[["TEAM_NAME","TEAM_ABBREVIATION"]].drop_duplicates().iterrows()
    }
    return logos

# Inject CSS for .metric-card (for use in this file)
st.markdown("""
<style>
.metric-card {
  background: rgba(255,255,255,0.9);
  border-radius: 12px;
  padding: 1.2rem;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  text-align: center;
  margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

def simulate_quarters(total):
    parts = np.random.dirichlet(np.ones(4), size=1)[0]
    return [int(p * total) for p in parts]

df_teamlog       = load_gamelog()
df_preds = load_preds()
logos    = load_logos()

models = {
    "Random Forest":       "MLTeams/models/random_forest.pkl",
    "XGBoost":             "MLTeams/models/xgboost.pkl",
    "KNN":                 "MLTeams/models/knn.pkl",
    "Logistic Regression": "MLTeams/models/logistic_regression.pkl"
}

all_teams  = sorted(df_teamlog["team"].unique())
all_years  = sorted(df_teamlog["year"].unique())
all_models = list(models.keys())

home_color = "#C9082A"
away_color = "#17408B"

# 3) Onglets principaux
tabs = st.tabs(["Players", "Teams"])

# ---- Teams Tab ----
with tabs[1]:
    # ─── 4) STRUCTURE EN TABS ─────────────────────────────────────────────────────
    tab1, tab2 = st.tabs(["Stats Équipe", "Match Simulé"])

    # — Onglet 1 : Statistiques par équipe
    with tab1:
        st.title("Statistiques NBA par Équipe")
        st.subheader("Filtres")
        y1, y2 = st.slider(
            "Période",
            min_value=all_years[0],
            max_value=all_years[-1],
            value=(all_years[-3], all_years[-1])
        )
        team = st.selectbox("Équipe", all_teams)

        df_team = df_teamlog.query("year>=@y1 & year<=@y2 & team==@team")
        st.header(f"{team} ({y1} – {y2})")

        # Afficher le logo SVG basé sur TEAM_INFO mapping
        abbr = next((abbr for tid, (abbr, url) in TEAM_INFO.items() if "TEAM_ID" in df_team.columns and tid == df_team["TEAM_ID"].iloc[0]), None)
        logo_url = TEAM_INFO.get(next((tid for tid, (abbr2, url) in TEAM_INFO.items() if abbr2 == abbr), None), (None, None))[1] if abbr else None
        if logo_url:
            st.image(logo_url, width=100, use_container_width=False)

        # Metric cards
        c1, c2, c3, c4 = st.columns([1,1,1,1], gap="large")
        for col, label, value in zip(
            (c1,c2,c3,c4),
            ["Matchs joués","% Victoires","Points Moy.","Rebonds Moy."],
            [
                len(df_team),
                f"{df_team['win'].mean()*100:.1f}%" if len(df_team) > 0 else "–",
                f"{df_team['pts'].mean():.1f}" if len(df_team) > 0 else "–",
                f"{df_team['reb'].mean():.1f}" if len(df_team) > 0 else "–"
            ]
        ):
            col.markdown(f"""
            <div class="metric-card">
            <h4>{label}</h4>
            <p>{value}</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        g1, g2 = st.columns(2, gap="large")
        with g1:
            st.subheader("Distribution des points")
            hist = (
                alt.Chart(df_team)
                .mark_bar(color=home_color)
                .encode(
                    alt.X("pts:Q", bin=alt.Bin(maxbins=25), title="Points"),
                    y="count()", tooltip=["count()"]
                )
                .properties(height=300)
            )
            st.altair_chart(hist, use_container_width=True)

        with g2:
            st.subheader("Évolution des points par saison")
            avg = df_team.groupby("year", as_index=False)["pts"].mean()
            line = (
                alt.Chart(avg)
                .mark_line(point=True, color=home_color)
                .encode(
                    x=alt.X("year:O", title="Année"),
                    y=alt.Y("pts:Q", title="Points moyens"),
                    tooltip=["year","pts"]
                )
                .properties(height=300)
            )
            st.altair_chart(line, use_container_width=True)

    # — Onglet 2 : Simulation de match
    with tab2:
        st.title("Affiche Officielle du Match NBA")
        model_name = st.selectbox("Modèle", all_models)

        c1, c2 = st.columns(2)
        with c1:
            home = st.selectbox("🏠 Équipe à domicile", all_teams)
        with c2:
            away = st.selectbox("🚩 Équipe extérieure", [t for t in all_teams if t!=home])

        l1, l2 = st.columns(2, gap="large")
        for col, team_ in zip((l1,l2),(home,away)):
            # Affichage du logo
            logo = logos.get(team_)
            if logo and os.path.exists(logo):
                col.image(logo, width=120, use_container_width=False)
            # Nom de l'équipe
            col.markdown(
                f"<h3 style='text-align:center; color:{home_color if team_==home else away_color}; margin-top:0.5em'>{team_}</h3>",
                unsafe_allow_html=True
            )

        if st.button("Lancer la prédiction"):
            sel = df_preds.query(
                "model==@model_name & team_A==@home & team_B==@away"
            )
            if sel.empty:
                st.warning("❓ Aucune prédiction disponible pour ce matchup.")
            else:
                row    = sel.iloc[0]
                p      = row["proba"]
                pred   = row["pred"]
                winner = home if pred==1 else away
                conf   = (p if pred==1 else 1-p)*100

                score_home = int(100 + (conf if pred==1 else 100-conf)/5)
                score_away = score_home - int(5 + conf/20)

                st.markdown("### 📍 Résultat & Analyse")
                st.success(f"✅ {winner} devrait gagner ({conf:.1f}% de confiance)")
                st.markdown(
                    f"<div style='text-align:center;'><h2 style='color:{home_color if pred==1 else away_color};'>{home} {score_home} – {score_away} {away}</h2></div>",
                    unsafe_allow_html=True
                )
                st.markdown(f"**Marge attendue** : **{abs(score_home-score_away)}** points")

                # Forme récente
                df_last5 = (
                    df_teamlog.query("team==@home")
                    .sort_values("date", ascending=False)
                    .head(5)
                    .sort_values("date")
                )
                st.markdown("### 🏃‍♂️ Forme récente (5 derniers matchs)")
                form = (
                    alt.Chart(df_last5)
                    .mark_line(point=True, color=home_color)
                    .encode(
                        x=alt.X("date:T", title="Date", axis=alt.Axis(format="%d %b")),
                        y=alt.Y("pts:Q", title="Points")
                    )
                    .properties(height=250)
                )
                st.altair_chart(form, use_container_width=True)

                # Timeline quart-temps
                qh = simulate_quarters(score_home)
                qa = simulate_quarters(score_away)
                df_q = pd.DataFrame({
                    "Quart-temps": ["Q1","Q2","Q3","Q4"] * 2,
                    "Points":       qh + qa,
                    "Équipe":       [home]*4 + [away]*4
                })
                st.markdown("### 📊 Timeline du match (par quart-temps)")
                timeline = (
                    alt.Chart(df_q)
                    .mark_bar()
                    .encode(
                        x=alt.X("Quart-temps:O", title="Quart-temps"),
                        y=alt.Y("Points:Q", title="Pts"),
                        color=alt.Color(
                            "Équipe:N",
                            scale=alt.Scale(domain=[home, away], range=[home_color, away_color]),
                            legend=alt.Legend(title="Équipe")
                        ),
                        tooltip=["Équipe","Points"]
                    )
                    .properties(height=300)
                )
                st.altair_chart(timeline, use_container_width=True)

                # Résumé officiel
                st.markdown("### 📅 Résumé Officiel")
                today = date.today().strftime("%d %B %Y")
                st.markdown(f"**{home} vs {away}** – *{today}*")
                st.markdown(f"#### 🎯 Score simulé : **{score_home} – {score_away}**")

# ---- Players Tab ----
with tabs[0]:

    # Création de quatre sous-onglets
    sub_tabs = st.tabs(["Overview", "Individual", "Rookie Scout", "Projection Future"])

    # ---- Sub-tab Overview ----
    with sub_tabs[0]:
        st.header("Profil & Carrière - Vue d'ensemble")

        # Filtre par position (utilise position_full)
        if "position_full" in df.columns and df["position_full"].notna().any():
            positions = sorted(df["position_full"].dropna().unique())
            sel_positions = st.multiselect("Filtrer par poste", positions, default=positions)
            df_filtered = df[df["position_full"].isin(sel_positions)]
        else:
            # Pas de colonne position valide : on désactive le filtre
            sel_positions = []
            df_filtered = df.copy()

        # A. Top 10 joueurs par score moyen
        st.subheader("🏆 Top 10 (score_100 moyen sur carrière)")
        overall = (
            df_filtered.groupby(name_col)
                .agg(
                    mean_score=(score_col, "mean"),
                    seasons_played=(season_col, "nunique"),
                    score_std=(score_col, "std"),
                    score_peak=(score_col, "max")
                )
                .reset_index()
        )
        overall["peak_to_avg"] = overall["score_peak"] / overall["mean_score"]
        top10 = overall.sort_values("mean_score", ascending=False).head(10)

        # Metrics globaux
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Score Moyen Global", f"{overall['mean_score'].mean():.1f}")
        m2.metric("Joueurs Total", overall.shape[0])
        # Nombre de profils uniques
        if profile_col:
            m3.metric("Profils", df_filtered[profile_col].nunique())
        else:
            m3.metric("Clusters", df_filtered[cluster_col].nunique() if cluster_col else "–")
        m4.metric("Saisons Max", df_filtered[season_col].nunique())
        st.markdown("---")

        # Top 10 table and bar chart side by side
        t1, t2 = st.columns([2,1], gap="large")
        with t1:
            st.subheader("Top 10 Joueurs")
            top10_df = top10.rename(columns={
                name_col: "Joueur",
                "mean_score": "Score Moyen",
                "seasons_played": "Saisons Jouées",
                "score_std": "Volatilité",
                "peak_to_avg": "Peak/Avg"
            })[["Joueur", "Score Moyen", "Saisons Jouées", "Volatilité", "Peak/Avg"]].reset_index(drop=True)
            # Display Top10 as styled HTML table
            styled_table = (
                top10_df.style
                    .hide(axis="index")
                    .set_table_styles([
                        {'selector': 'th', 'props': [('background-color', '#e8dcca')]},
                        {'selector': 'td', 'props': [('background-color', '#e8dcca')]}
                    ])
                    .set_properties(**{'border': '1px solid #ddd'})
            )
            html = styled_table.to_html()
            components.html(html, height=400, scrolling=True)

            
        with t2:
            st.subheader("Visualisation")
            # Bar chart for Top 10 players
            bar_top10 = (
                alt.Chart(top10)
                   .mark_bar()
                   .encode(
                       x=alt.X("mean_score:Q", title="Score Moyen"),
                       y=alt.Y(f"{name_col}:N", sort="-x", title="Joueur")
                   )
                   .properties(height=300, width=400)
            )
            st.altair_chart(bar_top10.properties(width=400), use_container_width=False)
        st.markdown("---")

        # Distribution des scores
        st.subheader("📊 Distribution des score_100")
        hist_score = (
            alt.Chart(df_filtered)
               .mark_bar()
               .encode(
                   x=alt.X(f"{score_col}:Q", bin=alt.Bin(maxbins=30), title="score_100"),
                   y=alt.Y("count()", title="Nombre de joueurs")
               )
               .properties(height=200)
        )
        st.altair_chart(hist_score, use_container_width=True)
        st.markdown("---")

        # Scatter Usage vs Score
        if "usage_rate" in df_filtered.columns:
            st.subheader("🔄 Usage Rate vs score_100")
            scatter_ur = (
                alt.Chart(df_filtered)
                   .mark_circle(size=50, opacity=0.6)
                   .encode(
                       x=alt.X("usage_rate:Q", title="Usage Rate"),
                       y=alt.Y(f"{score_col}:Q", title="score_100"),
                       color=alt.Color(f"{profile_col}:N", title="Profil joueur") if profile_col else alt.Color("cluster:N", title="Cluster"),
                       tooltip=[alt.Tooltip(name_col, title="Joueur"), alt.Tooltip("usage_rate:Q"), alt.Tooltip(f"{score_col}:Q")]
                   )
                   .properties(height=300)
                   .interactive()
            )
            # Place the legend at the bottom if possible
            if profile_col:
                st.altair_chart(scatter_ur.configure_legend(orient="bottom"), use_container_width=True)
            else:
                st.altair_chart(scatter_ur, use_container_width=True)
            st.markdown("---")

        # B. Répartition par cluster (utilise cluster_label pour affichage)
        if cluster_col:
            st.subheader("🎭 Répartition par profil de joueur")
            # create cluster_label for display
            if profile_col:
                df_filtered["cluster_label"] = df_filtered[profile_col]
            else:
                df_filtered["cluster_label"] = df_filtered[cluster_col].map({
                    0: "Playmaker", 1: "All-Around", 2: "Scoring Guard",
                    3: "Big Man", 4: "Sharpshooter"
                })
            cl_counts = (
                df_filtered.groupby("cluster_label")[player_col]
                  .nunique()
                  .reset_index(name="Nb Joueurs")
            )
            bar_cl = (
                alt.Chart(cl_counts)
                   .mark_bar()
                   .encode(
                       x=alt.X("Nb Joueurs:Q", title="Nombre de joueurs"),
                       y=alt.Y("cluster_label:N", sort="-x", title="Profil")
                   )
                   .properties(height=250)
            )
            st.altair_chart(bar_cl, use_container_width=True)
            # Afficher descriptions sous le graphique
            for prof, desc in CLUSTER_DESCRIPTIONS.items():
                st.markdown(f"**{prof}** : {desc}")
            st.markdown("---")

        # C. Distribution des âges
        if "age" in df_filtered.columns:
            st.subheader("👶 Distribution des âges")
            hist_age = (
                alt.Chart(df_filtered)
                   .mark_bar()
                   .encode(
                       x=alt.X("age:Q", bin=alt.Bin(maxbins=20), title="Âge"),
                       y=alt.Y("count()", title="Nombre de joueurs")
                   )
                   .properties(height=200)
            )
            st.altair_chart(hist_age, use_container_width=True)
            st.markdown("---")

            # D. Score vs Âge
            st.subheader("📈 Score vs Âge")
            scatter = (
                alt.Chart(df_filtered)
                   .mark_circle(size=60, opacity=0.5)
                   .encode(
                       x=alt.X("age:Q", title="Âge"),
                       y=alt.Y(f"{score_col}:Q", title="score_100"),
                       tooltip=[
                           alt.Tooltip(name_col, title="Joueur"),
                           alt.Tooltip("age:Q", title="Âge"),
                           alt.Tooltip(f"{score_col}:Q", title="Score")
                       ]
                   )
                   .interactive()
                   .properties(height=300)
            )
            st.altair_chart(scatter, use_container_width=True)
            st.markdown("---")

        # --- Résumé narratif automatique ---
        st.subheader("📝 Résumé Clé")
        if not top10.empty:
            leader = top10.iloc[0]
            leader_name = leader[name_col]
            leader_score = leader["mean_score"]
            st.markdown(f"**Leader** : {leader_name} avec un score moyen de **{leader_score:.1f}** sur sa carrière.")
        else:
            st.markdown("Aucun joueur à afficher.")

        st.markdown("---")
        # --- Métriques avancées moyennes ---
        st.subheader("📊 Métriques avancées moyennes")
        adv_metrics = ['efg_pct', 'ts_pct', 'ast_tov_ratio', 'usage_rate']
        # Filter metrics present
        adv_metrics = [m for m in adv_metrics if m in df_filtered.columns]
        if adv_metrics:
            avg_adv = df_filtered[adv_metrics].mean().reset_index()
            avg_adv.columns = ['Métrique', 'Valeur Moyenne']
            bar_adv = (
                alt.Chart(avg_adv)
                   .mark_bar(color="#C9082A")
                   .encode(
                       x=alt.X("Valeur Moyenne:Q", title="Valeur Moyenne"),
                       y=alt.Y("Métrique:N", sort='-x', title="Métrique")
                   )
                   .properties(height=200)
            )
            st.altair_chart(bar_adv, use_container_width=True)
        else:
            st.markdown("Pas de métriques avancées disponibles pour ce filtre.")

 
    # ---- Sub-tab Individual ----
    with sub_tabs[1]:
        # Sélecteur de saison local
        seasons = sorted(df[season_col].unique())
        sel_season = st.selectbox("Saison", seasons, index=len(seasons)-1)

        st.header("Profil & Carrière - Joueur Individuel")
        st.subheader("Filtrer Joueurs")


        actif_only = st.checkbox("Afficher uniquement les joueurs en activité", value=True)

        latest_season = sorted(df[season_col].unique())[-1]
        active_ids = df[df[season_col] == latest_season][player_col].unique()

        if actif_only:
            df_season = df[(df[season_col] == sel_season) & (df[player_col].isin(active_ids))]
        else:
            df_season = df[df[season_col] == sel_season]

        df_season = df_season.sort_values(score_col, ascending=False)
        players = df_season[name_col].tolist()
        sel_player = st.selectbox("Choisir un joueur", players, index=0) if players else None
        if not sel_player:
            st.warning("Aucun joueur pour ce filtre.")
            p_df = pd.DataFrame(columns=df.columns)
        else:
            p_df = df[df[name_col] == sel_player].sort_values(season_col)

        # Affichage sous forme de carte
        # récupérer position et équipe (utilise position_full si dispo)
                # --- Position : plusieurs fallbacks ------------------------------------
        position = None
        # 1) Position « full » déjà préparée
        if "position_full" in p_df.columns and pd.notna(p_df["position_full"].iloc[0]):
            position = p_df["position_full"].iloc[0]
        # 2) Colonne brute (PG, C…) puis mapping vers nom complet
        elif position_col and position_col in p_df.columns and pd.notna(p_df[position_col].iloc[0]):
            raw_pos  = p_df[position_col].iloc[0]
            position = POS_MAPPING.get(str(raw_pos).upper(), raw_pos)
        # 3) Sinon chaîne vide pour ne rien afficher
        else:
            position = ""

        template_path    = "MLPlayers/assets/template.png"
        player_photo_url = p_df["photo_url"].iloc[0]
        score_val        = p_df[score_col].iloc[-1]

        # ─── Détermination robuste de l’équipe ──────────────────────────────
        team_raw = None
        if team_col and team_col in p_df.columns:
            team_raw = p_df[team_col].iloc[0]
        elif "team" in p_df.columns:                # fallback colonne 'team'
            team_raw = p_df["team"].iloc[0]

        # 1) Essayer de convertir en ID numérique
        try:
            team_id_int = int(team_raw)
            abbrev, _   = TEAM_INFO.get(team_id_int, ("", None))
        except (TypeError, ValueError):
            team_id_int = None
            # 2) Si texte : chercher l’abréviation ou le nom complet
            team_str = str(team_raw) if team_raw is not None else ""
            # Si déjà une abréviation de 3 lettres
            if len(team_str) == 3 and team_str.isalpha():
                abbrev = team_str.upper()
            else:
                # Cherche l’abréviation dans le nom complet
                match = next(
                    (abbr for abbr, name in
                     [(v[0], k) for k, v in TEAM_INFO.items()]
                     if abbr.lower() in team_str.lower() or name.lower() in team_str.lower()),
                    ""
                )
                abbrev = match

        # Passe soit l’ID, soit l’abréviation (fonction gère les deux)
        card_team_param = team_id_int if team_id_int is not None else abbrev

        # Affichage du card et du logo SVG à droite
        col_card, col_logo = st.columns([1, 1])

        # Carte joueur (garde width=300)
        with col_card:
            st.image(
                generate_player_card(
                    template_path,
                    player_photo_url,
                    card_team_param,
                    position,
                    score_val,
                    sel_player
                ),
                width=300
            )

        # Logo SVG à droite, centré verticalement et biographie
        with col_logo:
            abbrev = ""
            # Récupère (abbrev, logo_url) à partir de l’ID numérique OU de l’abréviation
            if team_id_int is not None:
                abbrev, logo_url = TEAM_INFO.get(team_id_int, ("", None))
            else:
                # cherche via l’abréviation texte
                team_id_int = next(
                    (tid for tid, (abbr, _) in TEAM_INFO.items() if abbr == abbrev),
                    None
                )
                _, logo_url = TEAM_INFO.get(team_id_int, ("", None))
            if logo_url:
                # Centrer verticalement le logo à côté de la carte
                st.markdown(
                    f"""
                    <div style="
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        height: 350px;  /* adjust as needed */
                    ">
                        <img src="{logo_url}" width="300" />
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # --- Biographie & données physiques ---
            bio_cols = {
                "Taille (cm)": "height_cm",
                "Poids (kg)": "weight_kg" if "weight_kg" in p_df.columns else None,
                "Âge": "age",
                "Expérience (années)": "exp",
                "Poste": "position_full" if "position_full" in p_df.columns else (position_col or None),
            }
            bio_data = {}
            for label, col in bio_cols.items():
                # Ignore undefined mappings
                if not col:
                    continue

                # Primary source: value from the dataframe
                if col in p_df.columns:
                    value = p_df[col].iloc[-1]
                    if pd.notna(value):
                        bio_data[label] = value
                        continue  # value found, move to next label

                # ── Fallbacks ──────────────────────────────────────────────
                # For "Poste", fall back to the already‑computed `position`
                if label == "Poste" and position:
                    bio_data[label] = position
            if bio_data:
                bio_df = pd.DataFrame.from_dict(bio_data, orient="index", columns=["Valeur"])
                styled_bio = (
                    bio_df.style
                        .set_table_styles([
                            {'selector': 'tbody td', 'props': [('background-color', '#e8dcca')]},
                            {'selector': 'thead th', 'props': [('background-color', '#e8dcca')]},
                            {'selector': 'tbody th', 'props': [('background-color', '#e8dcca')]}  # This styles the index
                        ])
                )
                html_bio = styled_bio.to_html()
                components.html(html_bio, height=200, scrolling=False)
            else:
                                st.info("Données physiques indisponibles.")
            st.markdown("---")


        # Vidéo de highlights — scrap automatique si colonne absente
        yt_url = None
        if "yt_clip_url" in p_df.columns and pd.notna(p_df["yt_clip_url"].iloc[0]):
            yt_url = p_df["yt_clip_url"].iloc[0]
        else:
            yt_url = fetch_highlight_url(sel_player)

        if yt_url:
            embed = yt_url.replace("watch?v=", "embed/")
            components.iframe(embed, height=315)
            st.markdown("---")
        else:
            st.info("Aucun highlight trouvé automatiquement.")

        # Évolution des métriques clés vs moyenne générale
        st.subheader("Évolution des métriques clés vs moyenne générale")
        metrics = [score_col, "pts_mean", "reb_mean", "ast_mean", "win_shares", "vorp"]
        existing = [m for m in metrics if m in p_df.columns]

        # Préparer les données du joueur
        player_df = p_df[[season_col] + existing].copy().assign(Type="Player")
        player_melt = player_df.melt(
            id_vars=[season_col, "Type"],
            value_vars=existing,
            var_name="Metric",
            value_name="Value"
        )

        # Préparer les données globales pour les mêmes saisons que le joueur
        player_seasons = p_df[season_col].unique().tolist()
        global_df = (
            df[df[season_col].isin(player_seasons)]
              .groupby(season_col)[existing]
              .mean()
              .reset_index()
              .assign(Type="Global")
        )
        global_melt = global_df.melt(
            id_vars=[season_col, "Type"],
            value_vars=existing,
            var_name="Metric",
            value_name="Value"
        )

        # Concaténation pour tracer ensemble
        evo_df = pd.concat([player_melt, global_melt], ignore_index=True)

        chart = (
            alt.Chart(evo_df)
               .mark_line(point=True)
               .encode(
                   x=alt.X(f"{season_col}:N", title="Saison"),
                   y=alt.Y("Value:Q", title="Valeur"),
                   color=alt.Color("Metric:N", legend=alt.Legend(title="Métrique")),
                   strokeDash=alt.StrokeDash(
                       'Type:N',
                       scale=alt.Scale(
                           domain=['Global','Player'],
                           range=[[4,2],[1,0]]
                       ),
                       legend=alt.Legend(title='Type')
                   ),
                   size=alt.Size(
                       'Type:N',
                       scale=alt.Scale(domain=['Global','Player'], range=[1,3]),
                       legend=None
                   ),
                   opacity=alt.condition(
                       alt.datum.Type == 'Player',
                       alt.value(1.0),
                       alt.value(0.4)
                   ),
                   tooltip=[
                       alt.Tooltip(f"{season_col}:N", title="Saison"),
                       alt.Tooltip("Metric:N", title="Métrique"),
                       alt.Tooltip("Type:N", title="Type"),
                       alt.Tooltip("Value:Q", title="Valeur")
                   ]
               )
               .properties(width=700, height=350)
        )
        st.altair_chart(chart, use_container_width=True)

        # Stats par saison
        st.subheader("Stats par saison")
        season_df = p_df[[season_col] + existing].reset_index(drop=True)
        # Display as a styled HTML table
        styled_table = (
            season_df.style
            .hide(axis="index")
            .set_table_styles([
            {'selector': 'th', 'props': [('background-color', '#e8dcca')]},
            {'selector': 'td', 'props': [('background-color', '#e8dcca')]}
            ])
            .set_properties(**{'border': '1px solid #ddd'})
        )
        html = styled_table.to_html()
        components.html(html, height=250, scrolling=True)


        # 2) Disponibilité par saison
        st.subheader("🏥 Disponibilité par saison")
        if "avail" in p_df.columns:
            avail_df = p_df[[season_col, "avail"]].copy()
            avail_df["pct"] = avail_df["avail"] * 100
            avail_bar = (
                alt.Chart(avail_df)
                  .mark_bar(color="#C9082A")
                  .encode(
                    x=alt.X(f"{season_col}:O", title="Saison"),
                    y=alt.Y("pct:Q", title="% Matchs Joués"),
                    tooltip=[season_col, alt.Tooltip("pct:Q", format=".1f", title="Pct")]
                  )
                  .properties(height=200)
            )
            st.altair_chart(avail_bar, use_container_width=True)
        else:
            st.info("Aucune donnée de disponibilité disponible.")
        st.markdown("---")

        # 3) Comparaison à un All‑Star du même poste
        st.subheader("🤝 Comparaison à un All‑Star")

        # Helper pour récupérer le meilleur joueur (score moyen carrière le plus élevé)
        def top_reference(filter_df):
            return (
                filter_df
                    .groupby(name_col)
                    .agg(mean_score=(score_col, "mean"))
                    .reset_index()
                    .query(f"{name_col} != @sel_player")
                    .sort_values("mean_score", ascending=False)
                    .head(1)
            )

        # --- Étape 0 : recherche d'un All‑Star du même cluster/profil ---
        player_cluster = None
        # ─── Limiter le pool de référence aux saisons antérieures au début du joueur ──
        debut_season = p_df[season_col].min()
        base_df = df[df[season_col] < debut_season]           # seulement saisons < début
        # Si aucune saison antérieure n'existe (cas extrême), on garde tout le dataset
        if base_df.empty:
            base_df = df.copy()

        if profile_col and profile_col in p_df.columns:
            player_cluster = p_df[profile_col].iloc[0]
        elif cluster_col and cluster_col in p_df.columns:
            player_cluster = p_df[cluster_col].iloc[0]

        ref = pd.DataFrame()  # initialisation
        if player_cluster is not None:
            # On cible en priorité les joueurs du même cluster/profil
            ref_filter = (
                base_df[base_df[cluster_col] == player_cluster]
                if cluster_col and player_cluster is not None
                else base_df[base_df[profile_col] == player_cluster]
            )
            ref = top_reference(ref_filter)

        # Poste exact (nom complet ex : "Point Guard")
        pos_full = position            # ex: "Point Guard"
        # Étape 1 : même poste complet
        if ref.empty:
            ref = top_reference(base_df[base_df["position_full"] == pos_full])

        # Fallback 1 : même acronyme (PG / SG / SF / PF / C / G / F)
        if ref.empty and position_col and position_col in p_df.columns:
            pos_acro = p_df[position_col].iloc[0]
            ref = top_reference(base_df[base_df[position_col] == pos_acro])

        # Fallback 2 : poste large (Guard / Forward / Center)
        if ref.empty and isinstance(pos_full, str):
            broad_keywords = ["Guard", "Forward", "Center"]
            broad = next((k for k in broad_keywords if k.lower() in pos_full.lower()), None)
            if broad:
                ref = top_reference(base_df[base_df["position_full"].str.contains(broad, case=False, na=False)])

        # Fallback 3 : meilleur score global (hors joueur sélectionné)
        if ref.empty:
            ref = top_reference(base_df)

        # --- Affichage du graphique comparatif ou message si encore vide ---
        if not ref.empty:
            ref_name = ref[name_col].iloc[0]

            # Données saisonnières pour le joueur sélectionné
            comp_df = p_df[[season_col, score_col]].assign(Player=sel_player)

            # Données saisonnières pour la référence
            ref_df = df[df[name_col] == ref_name][[season_col, score_col]].assign(Player=ref_name)

            comp_all = pd.concat([comp_df, ref_df], ignore_index=True)

            comp_chart = (
                alt.Chart(comp_all)
                   .mark_line(point=True)
                   .encode(
                       x=alt.X(f"{season_col}:O", title="Saison"),
                       y=alt.Y(f"{score_col}:Q", title="Score_100"),
                       color=alt.Color("Player:N", title="Joueur"),
                       tooltip=[season_col, alt.Tooltip(score_col, title="Score"), "Player"]
                   )
                   .properties(height=300)
            )
            st.altair_chart(comp_chart, use_container_width=True)
            st.markdown(f"Référence All‑Star sélectionnée : **{ref_name}** (moyenne {ref['mean_score'].iloc[0]:.1f})")
        else:
            st.info("Pas d'All‑Star trouvé pour ce poste (même après fallback).")

    # ---- Rookie Scout ----
    with sub_tabs[2]:
        st.header("Scouting du Rookie")
        st.markdown("Entrez les caractéristiques pour estimer sa potentielle note.")

        col1, col2 = st.columns(2)
        with col1:
            height = st.number_input("Taille (cm)", 150, 250, 200)
            weight = st.number_input("Poids (kg)", 60, 150, 90)
            age    = st.number_input("Âge", 18, 25, 19)
        with col2:
            position   = st.selectbox("Poste", list(POS_MAPPING.values()))
            # Build list of full team names for draft selection
            # Use the game log dataframe to map abbreviations to full names
            abbr_to_name = dict(
                df_teamlog[["TEAM_ABBREVIATION","TEAM_NAME"]]
                    .drop_duplicates()
                    .values
            )
            name_to_abbr = {v: k for k, v in abbr_to_name.items()}
            team_names = sorted(abbr_to_name.values())
            draft_team = st.selectbox("Équipe draftee", team_names)

        if st.button("Estimer potentiel rookie"):
            potential = 50 + (height-200)*0.1 + (age-20)*0.3

            # Map full name back to abbreviation then to ID
            selected_abbr = name_to_abbr.get(draft_team)
            team_id = next((tid for tid, (abbr, _) in TEAM_INFO.items() if abbr == selected_abbr), None)

            # Afficher les résultats
            st.metric("Potentiel estimé (score_100)", f"{potential:.1f}")
            if team_id:
                st.markdown(f"**Équipe**: {draft_team} (ID: {team_id})")
                # Afficher le logo de l'équipe si disponible
                logo_url = TEAM_INFO.get(team_id, (None, None))[1]
                if logo_url:
                    st.image(logo_url, width=100)

        # --- Explication du modèle rookie ---
        st.markdown("#### ❓ Qu'est-ce que le modèle Rookie ?")
        st.markdown(
            "C'est un point de départ heuristique : on part d'une note de 50/100, "
            "puis on la module en fonction de la taille (gain de 0.1 pt/cm au-dessus de 200cm) "
            "et de l'âge (perte de 0.3 pt/an en dessous de 20 ans)."
        )

 # ─── Projection Futur (remplace le bloc actuel) ─────────────────────────
with sub_tabs[3]:
    st.header("Projection future")

    players_proj = sorted(df[name_col].unique())
    sel_p = st.selectbox("Joueur", players_proj, key="proj")

    max_horizon = 5                       # ←  proj_1 … proj_5 disponibles
    horizon     = st.slider("Horizon (saisons)", 1, max_horizon, 1)

    if st.button("Prédire"):
        row = df[df[name_col] == sel_p].sort_values(season_col).iloc[-1]

        # Nom de la colonne à aller chercher
        proj_col = f"proj_{horizon}"
        if proj_col not in row:
            st.error(f"Colonne {proj_col} absente du parquet.")
        else:
            pred = row[proj_col]
            st.metric(f"Score_100 projeté à +{horizon}", f"{pred:.1f}")

        # Afficher la trajectoire 0-5 saisons
        traj = row[[f"proj_{i}" for i in range(1, max_horizon+1)]].T.reset_index()
        traj.columns = ["Horizon", "Projection"]
        traj["Horizon"] = traj["Horizon"].str.extract("(\d)").astype(int)

        line = (
            alt.Chart(traj)
               .mark_line(point=True, color="#C9082A")
               .encode(
                   x=alt.X("Horizon:O", title="Saisons dans le futur"),
                   y=alt.Y("Projection:Q", title="Score_100 projeté")
               )
               .properties(height=300)
        )
        st.altair_chart(line, use_container_width=True)
    # Footer
    st.markdown("---")
 

