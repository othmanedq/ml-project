import streamlit as st
import pandas as pd
import altair as alt
import streamlit.components.v1 as components
import os

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
    # 1) Charger le template
    template = Image.open(template_path).convert("RGBA")
    GOLD = (212, 175, 55, 255)  # couleur or
    # 2) Récupérer la photo du joueur et appliquer un masque circulaire
    resp = requests.get(player_photo_url)
    player_img = Image.open(BytesIO(resp.content)).convert("RGBA")
    # Agrandir la photo du joueur de 40%
    size = (int(500), int(500))
    player_img = player_img.resize(size)
    # Créer un masque circulaire pour ne conserver que le visage
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
    abbrev, _ = TEAM_INFO.get(int(team_id), ("", None))
    team_text = str(abbrev)
    team_bbox = draw.textbbox((0, 0), team_text, font=font_small)
    team_w = team_bbox[2] - team_bbox[0]
    draw.text((template.width * 0.5 - team_w/2, info_y), team_text, font=font_small, fill=GOLD)

    # Score (droite)
    score_text = f"{score:.1f}"
    score_bbox = draw.textbbox((0, 0), score_text, font=font_small)
    score_w = score_bbox[2] - score_bbox[0]
    draw.text((template.width * 0.75 - score_w/2, info_y), score_text, font=font_small, fill=GOLD)
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
# Colonnes position et équipe
position_col = next((c for c in df.columns if "position" in c.lower()), None)
team_col     = next((c for c in df.columns if "team_name" in c.lower() or c.lower()=="team"), None)

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
        # récupérer position et équipe
        position  = p_df[position_col].iloc[0] if position_col else ""
        template_path    = "assets/template.png"
        player_photo_url = p_df["photo_url"].iloc[0]
        score_val        = p_df[score_col].iloc[-1]
       # Affichage du card et du logo SVG à droite
        # On alloue plus d'espace à la carte et centre le logo
        col_card, col_logo = st.columns([1, 1])

        # Carte joueur (garde width=300)
        with col_card:
            st.image(
                generate_player_card(
                    template_path,
                    player_photo_url,
                    p_df["team"].iloc[0],
                    position,
                    score_val,
                    sel_player
                ),
                width=300
            )

        # Logo SVG à droite, centré verticalement
        with col_logo:
            abbrev, logo_url = TEAM_INFO.get(int(p_df["team"].iloc[0]), ("", None))
            if logo_url:
                # Centrer verticalement le logo à côté de la carte
                st.markdown(
                    f"""
                    <div style="
                      display: flex;
                      align-items: center;
                      justify-content: center;
                      height: 400px; /* Ajuster selon la hauteur du card */
                    ">
                      <img src="{logo_url}" width="300" />
                    </div>
                    """,
                    unsafe_allow_html=True
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
