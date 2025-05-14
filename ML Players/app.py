import streamlit as st
import pandas as pd
import altair as alt
import streamlit.components.v1 as components

# --- Ajout helper carte joueur ---
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

def generate_player_card(template_path, player_photo_url, team_logo_url, position, team_name, score, player_name):
    # 1) Charger le template
    template = Image.open(template_path).convert("RGBA")
    # 2) Récupérer et masquer la photo du joueur
    resp = requests.get(player_photo_url)
    player_img = Image.open(BytesIO(resp.content)).convert("RGBA")
    size = (300, 300)
    player_img = player_img.resize(size)
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + size, fill=255)
    player_img.putalpha(mask)
    template.paste(player_img, (int((template.width-size[0])/2), 80), player_img)
    # 3) Récupérer le logo et coller en haut à droite
    resp = requests.get(team_logo_url)
    logo_img = Image.open(BytesIO(resp.content)).convert("RGBA")
    logo_size = (80, 80)
    logo_img = logo_img.resize(logo_size)
    template.paste(logo_img, (template.width-logo_size[0]-30, 30), logo_img)
    # 4) Dessiner le texte
    draw = ImageDraw.Draw(template)
    try:
        font_large = ImageFont.truetype("arial.ttf", 36)
        font_small = ImageFont.truetype("arial.ttf", 24)
    except IOError:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    # Nom du joueur
    w, h = draw.textsize(player_name, font=font_large)
    draw.text(((template.width-w)/2, 400), player_name, font=font_large, fill="white")
    # Position & équipe
    pt = f"{position} - {team_name}"
    w2, h2 = draw.textsize(pt, font=font_small)
    draw.text(((template.width-w2)/2, 440), pt, font=font_small, fill="white")
    # Score
    sc = f"Score: {score:.1f}"
    w3, h3 = draw.textsize(sc, font=font_small)
    draw.text(((template.width-w3)/2, template.height-60), sc, font=font_small, fill="gold")
    return template

# 1) Chargement des données (en cache)
@st.cache_data
def load_data():
    df = pd.read_parquet("nba_rating/data/curated/dashboard_data.parquet")
    return df

df = load_data()

# 2) Détection dynamique des colonnes clefs
season_col  = next((c for c in df.columns if c.lower() == "season"), None)
player_col  = next((c for c in df.columns if c.lower() == "player_id"), None)
name_col    = next((c for c in df.columns if "name" in c.lower()), None)
cluster_col = next((c for c in df.columns if "cluster" in c.lower()), None)
score_col   = next((c for c in df.columns if c.lower() == "score_100"), None)

# On stoppe si colonnes manquantes
if season_col is None or player_col is None or score_col is None:
    st.error(f"❌ Colonnes requises manquantes : season_col={season_col}, player_col={player_col}, score_col={score_col}")
    st.stop()

st.title("🏀 ML Players – Mode Carrière")
st.markdown("### Tableau de bord interactif des joueurs NBA")
st.markdown("---")

# 3) Onglets principaux
tabs = st.tabs(["📊 Stats Joueur", "🆕 Rookie Scout", "🔮 Projection Futur"])

# ---- Onglet 1 : Stats Joueur ----
with tabs[0]:
    # Création de deux sous-onglets
    sub_tabs = st.tabs(["Overview", "Individual"])

    # ---- Sub-tab Overview ----
    with sub_tabs[0]:
        st.header("Profil & Carrière - Vue d'ensemble")

        # A. Top 10 joueurs par score moyen
        st.subheader("🏆 Top 10 (score_100 moyen sur carrière)")
        overall = (
            df.groupby(name_col)
              .agg(mean_score=(score_col, "mean"), seasons_played=(season_col, "nunique"))
              .reset_index()
        )
        top10 = overall.sort_values("mean_score", ascending=False).head(10)

        # Metrics globaux
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Score Moyen Global", f"{overall['mean_score'].mean():.1f}")
        m2.metric("Joueurs Total", overall.shape[0])
        m3.metric("Clusters", df[cluster_col].nunique() if cluster_col else "–")
        m4.metric("Saisons Max", df[season_col].nunique())
        st.markdown("---")

        # Top 10 table and bar chart side by side
        t1, t2 = st.columns([1,1])
        with t1:
            st.subheader("Top 10 Joueurs")
            top10_df = top10.rename(columns={
                name_col: "Joueur",
                "mean_score": "Score Moyen",
                "seasons_played": "Saisons Jouées"
            })[["Joueur", "Score Moyen", "Saisons Jouées"]].reset_index(drop=True)
            st.markdown(top10_df.to_html(index=False), unsafe_allow_html=True)
        with t2:
            st.subheader("Visualisation")
            bar_top10 = (
                alt.Chart(top10)
                   .mark_bar()
                   .encode(
                       x=alt.X("mean_score:Q", title="Score Moyen"),
                       y=alt.Y(f"{name_col}:N", sort="-x", title="Joueur")
                   )
                   .properties(height=300)
            )
            st.altair_chart(bar_top10, use_container_width=True)
        st.markdown("---")

        # Distribution des scores
        st.subheader("📊 Distribution des score_100")
        hist_score = (
            alt.Chart(df)
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
        if "usage_rate" in df.columns:
            st.subheader("🔄 Usage Rate vs score_100")
            scatter_ur = (
                alt.Chart(df)
                   .mark_circle(size=50, opacity=0.6)
                   .encode(
                       x=alt.X("usage_rate:Q", title="Usage Rate"),
                       y=alt.Y(f"{score_col}:Q", title="score_100"),
                       color=alt.Color("cluster:N", title="Cluster"),
                       tooltip=[alt.Tooltip(name_col, title="Joueur"), alt.Tooltip("usage_rate:Q"), alt.Tooltip(f"{score_col}:Q")]
                   )
                   .properties(height=300)
                   .interactive()
            )
            st.altair_chart(scatter_ur, use_container_width=True)
            st.markdown("---")

        # B. Répartition par cluster
        if cluster_col:
            st.subheader("🎭 Répartition par cluster")
            cl_counts = (
                df.groupby(cluster_col)[player_col]
                  .nunique()
                  .reset_index(name="Nb Joueurs")
            )
            bar_cl = (
                alt.Chart(cl_counts)
                   .mark_bar()
                   .encode(
                       x=alt.X("Nb Joueurs:Q", title="Nombre de joueurs"),
                       y=alt.Y(f"{cluster_col}:N", sort="-x", title="Cluster")
                   )
                   .properties(height=250)
            )
            st.altair_chart(bar_cl, use_container_width=True)
            st.markdown("---")

        # C. Distribution des âges
        if "age" in df.columns:
            st.subheader("👶 Distribution des âges")
            hist_age = (
                alt.Chart(df)
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
                alt.Chart(df)
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
        template_path = "assets/template.png"  # chemin vers votre fond de carte
        player_photo_url = p_df["photo_url"].iloc[0]
        team_logo_url = p_df["team_logo_url"].iloc[0] if "team_logo_url" in p_df.columns else ""
        score_val = p_df[score_col].iloc[-1]
        st.image(
            generate_player_card(
                template_path,
                player_photo_url,
                team_logo_url,
                p_df["position"].iloc[0] if "position" in p_df.columns else "",
                p_df["team"].iloc[0] if "team" in p_df.columns else "",
                score_val,
                sel_player
            ),
            use_column_width=False
        )

        # Vidéo de highlights
        if "yt_clip_url" in p_df.columns and pd.notna(p_df["yt_clip_url"].iloc[0]):
            components.iframe(p_df["yt_clip_url"].iloc[0], height=315)
            st.markdown("---")

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
        # Tableau saisonnel sans index via HTML
        season_df = p_df[[season_col] + existing].reset_index(drop=True)
        st.markdown(season_df.to_html(index=False), unsafe_allow_html=True)

# ---- Onglet 2 : Rookie Scout ----
with tabs[1]:
    st.header("Scouting du Rookie")
    st.markdown("Entrez les caractéristiques pour estimer son potentiel (score_100).")

    col1, col2 = st.columns(2)
    with col1:
        height = st.number_input("Taille (cm)", 150, 250, 200)
        weight = st.number_input("Poids (kg)", 60, 150, 90)
        age    = st.number_input("Âge", 18, 25, 19)
    with col2:
        position   = st.selectbox("Poste", ["PG", "SG", "SF", "PF", "C"])
        teams      = df["team"].unique().tolist() if "team" in df.columns else ["–"]
        draft_team = st.selectbox("Équipe draftee", teams)

    if st.button("Estimer potentiel rookie"):
        potential = 50 + (height-200)*0.1 + (age-20)*0.3
        st.metric("Potentiel estimé (score_100)", f"{potential:.1f}")
        st.info("🔧 Modèle rookie à intégrer ultérieurement")

# ---- Onglet 3 : Projection Futur ----
with tabs[2]:
    st.header("Projection future")
    players_proj = sorted(df[name_col].unique())
    sel_p = st.selectbox("Joueur", players_proj, key="proj")
    horizon = st.slider("Horizon (saisons)", 1, 5, 1)

    if st.button("Prédire"):
        last = df[df[name_col] == sel_p].sort_values(season_col).iloc[-1]
        pred = last[score_col] + 2*horizon
        st.write(f"**Score_100 prédit pour +{horizon} saison(s)** : {pred:.1f}")
        st.info("🔧 Modèle multi-horizon à développer")

# Footer
st.markdown("---")
st.markdown(
    "ℹ️ Dashboard prototype – cluster et filtres automatiques si dispo. "
    "À enrichir (CI/CD, docker, PBP, tracking…)."
)
