import streamlit as st
import pandas as pd
import altair as alt

# 1) Chargement des données (en cache)
@st.cache_data
def load_data():
    scores = pd.read_parquet("nba_rating/data/curated/all_seasons_scores.parquet")
    ws = (
        pd.read_parquet("nba_rating/data/curated/wins_shares_vorp.parquet")
        .rename(columns={"Win_Shares":"win_shares", "VORP":"vorp"})
    )
    clusters = pd.read_parquet("nba_rating/data/curated/player_clusters.parquet")
    df = (
        scores
        .merge(ws,       on=["PLAYER_ID","season"], how="left")
        .merge(clusters, on=["PLAYER_ID","season"], how="left")
    )
    return df

df = load_data()

# 2) Debug rapide des colonnes
st.sidebar.write("⚙️ Colonnes dispo dans df:", df.columns.tolist())

# 3) Détection dynamique des colonnes clefs
season_col  = next((c for c in df.columns if c.lower()=="season"),         None)
cluster_col = next((c for c in df.columns if "cluster" in c.lower()),      None)
name_col    = next((c for c in df.columns if "profile_name" in c.lower()), None)

if not season_col:
    st.sidebar.error(f"Aucune colonne 'season' trouvée dans {df.columns.tolist()}")
    st.stop()
if not cluster_col:
    st.sidebar.error(f"Aucune colonne 'cluster' trouvée dans {df.columns.tolist()}")
    st.stop()
if not name_col:
    st.sidebar.error(f"Aucune colonne de nom de joueur trouvée dans {df.columns.tolist()}")
    st.stop()

# 4) Sidebar – filtres
st.sidebar.title("Filtres")
season_list  = sorted(df[season_col].unique())
sel_season   = st.sidebar.selectbox("Saison", season_list)
cluster_list = sorted(df[cluster_col].unique())
sel_clusters = st.sidebar.multiselect("Clusters", cluster_list, default=cluster_list)

# 5) Filtrage principal
df_season = df[
    (df[season_col] == sel_season) &
    (df[cluster_col].isin(sel_clusters))
]

# 6) Titre & résumé
st.title("🏀 Dashboard NBA Ratings")
st.markdown(
    f"**Saison sélectionnée :** {sel_season}  \n"
    f"Nombre de joueurs : {df_season.shape[0]}"
)

# 7) Top 10 joueurs par score_100
st.subheader("Top 10 joueurs par score_100")
top10 = (
    df_season
    .sort_values("score_100", ascending=False)
    .head(10)
)
st.dataframe(
    top10[[
        "PLAYER_ID", name_col, "score_100", "win_shares", "vorp", cluster_col
    ]],
    use_container_width=True
)

# 8) Historique individuel
st.sidebar.markdown("---")
sel_player = st.sidebar.selectbox(
    f"Historique d’un joueur ({name_col})",
    df_season[name_col].unique()
)
df_player = df[df[name_col] == sel_player].sort_values(season_col)

st.subheader(f"Évolution de {sel_player}")
chart = (
    alt.Chart(df_player)
       .transform_fold(
           fold=["score_100","win_shares","vorp"],
           as_=["metric","value"]
       )
       .mark_line(point=True)
       .encode(
           x=alt.X(f"{season_col}:N", axis=alt.Axis(title="Saison")),
           y=alt.Y("value:Q",       axis=alt.Axis(title="Valeur")),
           color=alt.Color("metric:N", legend=alt.Legend(title="Métrique")),
           tooltip=[
               alt.Tooltip(f"{season_col}:N", title="Saison"),
               alt.Tooltip("metric:N",       title="Métrique"),
               alt.Tooltip("value:Q",        title="Valeur"),
           ]
       )
       .properties(width=700, height=300)
)
st.altair_chart(chart, use_container_width=True)


# 9) Nuage score_100 vs Win Shares
st.subheader(f"Score_100 vs Win Shares — {sel_season}")
scatter = (
    alt.Chart(df_season)
       .mark_circle(size=60, opacity=0.7)
       .encode(
           x="win_shares:Q",
           y="score_100:Q",
           color=alt.Color(f"{cluster_col}:N", legend=alt.Legend(title="Cluster")),
           tooltip=["PLAYER_ID", name_col, "score_100", "win_shares"]
       )
       .interactive()
       .properties(width=700, height=400)
)
st.altair_chart(scatter, use_container_width=True)

# 10) Footer
st.markdown("---")
st.markdown("ℹ️ Prototype de dashboard – à enrichir avec logos, équipes, stats avancées…")
