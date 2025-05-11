import os
import streamlit as st
import pandas as pd
import altair as alt
import joblib

# ─── 0) CONFIG & STYLE ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Équipe NBA",
    layout="wide",
    page_icon="🏀"
)
st.markdown("""
<style>
  .stApp { background-color: #F5F5F5; }
  .sidebar .sidebar-content { background-color: #FFFFFF; }
  h1, h2, h3, h4 { color: #17408B; }
</style>
""", unsafe_allow_html=True)

# ─── 1) CHARGEMENT DES DONNÉES ─────────────────────────────────────────────────
@st.cache_data
def load_gamelog():
    for p in [
        "data/curated/team_gamelog_all_seasons.parquet",
        "notebooks/data/curated/team_gamelog_all_seasons.parquet"
    ]:
        if os.path.exists(p):
            df = pd.read_parquet(p)
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
    raise FileNotFoundError("team_gamelog_all_seasons.parquet introuvable.")

@st.cache_data
def load_pair_preds():
    for p in [
        "data/curated/all_pair_preds.parquet",
        "notebooks/data/curated/all_pair_preds.parquet"
    ]:
        if os.path.exists(p):
            return pd.read_parquet(p)
    raise FileNotFoundError("all_pair_preds.parquet introuvable.")

try:
    df = load_gamelog()
except Exception as e:
    st.error(f"Erreur gamelog : {e}")
    st.stop()

try:
    df_preds = load_pair_preds()
except Exception as e:
    st.error(f"Erreur prédictions : {e}")
    st.stop()

# ─── 2) DICT DES MODÈLES (noms → chemins .pkl) ──────────────────────────────────
models_dict = {
    "Random Forest":       "models/random_forest.pkl",
    "XGBoost":             "models/xgboost.pkl",
    "KNN":                 "models/knn.pkl",
    "Logistic Regression": "models/logistic_regression.pkl"
}

# ─── 3) MAPPING TEAM → LOGO ─────────────────────────────────────────────────────
logo_dir = "logos"
team_logos = {
    row["TEAM_NAME"]: os.path.join(logo_dir, f"{row['TEAM_ABBREVIATION']}.svg")
    for _, row in df[["TEAM_NAME","TEAM_ABBREVIATION"]].drop_duplicates().iterrows()
}

# ─── 4) LISTES GLOBALES ────────────────────────────────────────────────────────
all_years  = sorted(df["year"].unique())
all_teams  = sorted(df["team"].unique())
all_models = list(models_dict.keys())

# ─── 5) NAVIGATION PAGES ────────────────────────────────────────────────────────
tab_stats, tab_modele = st.tabs(["📊 Stats Équipe", "🤖 Modèle"])

# ─── 6) PAGE STATS ÉQUIPE ───────────────────────────────────────────────────────
with tab_stats:
    st.title("📊 Stats par Équipe")
    st.sidebar.header("Filtres Équipe")

    start_year, end_year = st.sidebar.slider(
        "Période (années)",
        all_years[0], all_years[-1],
        (all_years[-3], all_years[-1])
    )
    sel_team = st.sidebar.selectbox("Équipe", all_teams)

    df_team = df[
        (df["year"]>=start_year)&
        (df["year"]<=end_year)&
        (df["team"]==sel_team)
    ]

    st.header(f"Stats {sel_team} de {start_year} à {end_year}")
    logo_path = team_logos.get(sel_team)
    if logo_path and os.path.exists(logo_path):
        st.image(logo_path, width=120)

    if df_team.empty:
        st.warning("Pas de données pour cette sélection.")
        st.stop()

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Matchs joués", len(df_team))
    c2.metric("Win %", f"{df_team['win'].mean()*100:.1f}%")
    c3.metric("Pts Moy.", f"{df_team['pts'].mean():.1f}")
    c4.metric("Reb Moy.", f"{df_team['reb'].mean():.1f}")

    st.markdown("---")
    g1,g2 = st.columns(2, gap="large")
    with g1:
        st.subheader("Distribution des points")
        hist = (
            alt.Chart(df_team)
            .mark_bar(color="#17408B")
            .encode(
                alt.X("pts:Q", bin=alt.Bin(maxbins=25), title="Pts"),
                y="count()", tooltip=["count()"]
            ).properties(height=300)
        )
        st.altair_chart(hist, use_container_width=True)
    with g2:
        num_years = end_year - start_year + 1
        if num_years <= 2:
            st.subheader("Évolution des pts par match")
            line = (
                alt.Chart(df_team)
                .mark_line(point=True, color="#CE1141")
                .encode(
                    x="date:T", y="pts:Q",
                    tooltip=["date","pts"]
                ).properties(height=300)
            )
            st.altair_chart(line, use_container_width=True)
        else:
            st.subheader("Moyenne pts par saison")
            avg_szn = df_team.groupby("year",as_index=False)["pts"].mean()
            line2 = (
                alt.Chart(avg_szn)
                .mark_line(point=True, color="#CE1141")
                .encode(
                    x="year:O", y="pts:Q",
                    tooltip=["year","pts"]
                ).properties(height=300)
            )
            st.altair_chart(line2, use_container_width=True)

    st.markdown("### 🔢 Moyennes supplémentaires")
    extras = {
        "AST": df_team["ast"].mean(),
        "STL": df_team["stl"].mean(),
        "BLK": df_team["blk"].mean(),
        "TOV": df_team["pts"].mean()  # remplacez si autre stat
    }
    st.write(pd.DataFrame.from_dict(extras, orient="index", columns=["Moyenne"]))

# ─── 7) PAGE MODÈLE ───────────────────────────────────────────────────────────────
with tab_modele:
    st.header("🤖 Modèle de Prédiction")
    st.info("Choisissez un modèle, deux équipes et validez.")

    model_name = st.selectbox("🔧 Modèle", all_models)
    c1,c2 = st.columns(2)
    with c1:
        home = st.selectbox("🏠 Domicile", all_teams)
    with c2:
        away = st.selectbox("🚩 Extérieur", [t for t in all_teams if t!=home])

    lc1,lc2 = st.columns(2)
    for col,team in zip((lc1,lc2),(home,away)):
        logo = team_logos.get(team)
        if logo and os.path.exists(logo):
            col.image(logo, width=100)

    if st.button("Prédire le vainqueur"):
        sel = df_preds.query(
            "model==@model_name and team_A==@home and team_B==@away"
        )
        if sel.empty:
            st.warning("❓ Pas de pré-calcul pour cet ordre d’équipes.")
        else:
            row = sel.iloc[0]
            p, pred = row["proba"], row["pred"]
            if pred==1:
                st.success(f"✅ {home} devrait gagner ({p*100:.1f}% de confiance)")
            else:
                st.error(f"❌ {away} devrait gagner ({(1-p)*100:.1f}% de confiance)")

            comp = (
                df.groupby("team")[["pts","reb","ast","stl","blk"]]
                  .mean().loc[[home,away]]
            )
            st.table(comp)