import os
import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from datetime import date

# ─── 1) CONFIGURATION STREAMLIT ───────────────────────────────────────────────
st.set_page_config(
    page_title="NBA Dashboard",
    layout="wide",
    page_icon="🏀"
)

# ─── 2) INJECTION DU CSS : FOND + OVERLAY + ENCADRÉS ──────────────────────────
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
</style>
""", unsafe_allow_html=True)

# ─── 3) CHARGEMENT DES DONNÉES ────────────────────────────────────────────────
@st.cache_data
def load_gamelog():
    df = pd.read_parquet("data/curated/team_gamelog_all_seasons.parquet")
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
    return pd.read_parquet("data/curated/all_pair_preds.parquet")

@st.cache_data
def load_logos():
    df = load_gamelog()
    logo_dir = "logos"
    return {
        row["TEAM_NAME"]: os.path.join(logo_dir, f"{row['TEAM_ABBREVIATION']}.svg")
        for _, row in df[["TEAM_NAME","TEAM_ABBREVIATION"]].drop_duplicates().iterrows()
    }

df       = load_gamelog()
df_preds = load_preds()
logos    = load_logos()

models = {
    "Random Forest":       "models/random_forest.pkl",
    "XGBoost":             "models/xgboost.pkl",
    "KNN":                 "models/knn.pkl",
    "Logistic Regression": "models/logistic_regression.pkl"
}

all_teams  = sorted(df["team"].unique())
all_years  = sorted(df["year"].unique())
all_models = list(models.keys())

home_color = "#C9082A"
away_color = "#17408B"

# ─── 4) STRUCTURE EN TABS ─────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["Stats Équipe", "Match Simulé"])

# — Onglet 1 : Statistiques par équipe
with tab1:
    st.title("Statistiques NBA par Équipe")
    st.sidebar.subheader("Filtres")
    y1, y2 = st.sidebar.slider(
        "Période",
        min_value=all_years[0],
        max_value=all_years[-1],
        value=(all_years[-3], all_years[-1])
    )
    team = st.sidebar.selectbox("Équipe", all_teams)

    df_team = df.query("year>=@y1 & year<=@y2 & team==@team")
    st.header(f"{team} ({y1} – {y2})")

    # Logo
    logo = logos.get(team)
    if logo and os.path.exists(logo):
        st.image(logo, width=100)

    # Metric cards
    c1, c2, c3, c4 = st.columns(4)
    for col, label, value in zip(
        (c1,c2,c3,c4),
        ["Matchs joués","% Victoires","Points Moy.","Rebonds Moy."],
        [
            len(df_team),
            f"{df_team['win'].mean()*100:.1f}%",
            f"{df_team['pts'].mean():.1f}",
            f"{df_team['reb'].mean():.1f}"
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

    l1, l2 = st.columns(2)
    for col, team_ in zip((l1,l2),(home,away)):
        logo = logos.get(team_)
        if logo and os.path.exists(logo):
            col.image(logo, width=100)
        col.markdown(
            f"<h3 style='text-align:center; color:{home_color if team_==home else away_color};'>{team_}</h3>",
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
                df.query("team==@home")
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
            def simulate_quarters(total):
                parts = np.random.dirichlet(np.ones(4), size=1)[0]
                return [int(p * total) for p in parts]

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