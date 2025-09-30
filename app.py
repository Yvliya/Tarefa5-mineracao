import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Dashboard Spotify", page_icon="🎵", layout="wide")

st.title("Dashboard Spotify (1921–2020)")
st.markdown("Explore músicas do Spotify entre 1921 e 2020. Utilize os filtros à esquerda para refinar sua análise.")

PUBLIC_DATA_URL = "https://raw.githubusercontent.com/rfordatascience/tidytuesday/master/data/2020/2020-01-21/spotify_songs.csv"

@st.cache_data
def load_data(url):
    df = pd.read_csv(url)
    column_rename_map = {}
    if 'track_name' in df.columns:
        column_rename_map['track_name'] = 'name'
    if 'track_artist' in df.columns:
        column_rename_map['track_artist'] = 'artists'
    df = df.rename(columns=column_rename_map)

    if 'track_album_release_date' in df.columns:
        df['year'] = df['track_album_release_date'].str.split('-').str[0].astype(int)
    else:
        df['year'] = np.nan

    required_cols = ['artists', 'name', 'popularity', 'year']
    df = df.dropna(subset=[col for col in required_cols if col in df.columns])
    df['year'] = df['year'].astype(int)
    df = df[(df['year'] >= 1921) & (df['year'] <= 2020)]
    df['decade'] = (df['year'] // 10) * 10
    df['decade'] = df['decade'].astype(str) + 's'
    return df

df = load_data(PUBLIC_DATA_URL)

st.sidebar.header("Filtros")
anos_disponiveis = sorted(df['year'].unique())
anos_selecionados = st.sidebar.slider("Ano de lançamento", int(df['year'].min()), int(df['year'].max()), (1990, 2020))
artistas_disponiveis = sorted(df['artists'].unique())
artistas_selecionados = st.sidebar.multiselect("Artistas", artistas_disponiveis)

df_filtrado = df[(df['year'] >= anos_selecionados[0]) & (df['year'] <= anos_selecionados[1])]
if artistas_selecionados:
    df_filtrado = df_filtrado[df_filtrado['artists'].isin(artistas_selecionados)]

st.subheader("Métricas Principais")
col1, col2, col3 = st.columns(3)
col1.metric("Total de músicas", df_filtrado.shape[0])
if not df_filtrado.empty:
    col2.metric("Artista mais frequente", df_filtrado["artists"].mode()[0])
    col3.metric("Média de popularidade", round(df_filtrado["popularity"].mean(), 2))
else:
    col2.metric("Artista mais frequente", "N/A")
    col3.metric("Média de popularidade", "0")

st.subheader("Gráficos")
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    if not df_filtrado.empty:
        top_artistas = df_filtrado['artists'].value_counts().head(10).reset_index()
        top_artistas.columns = ['Artista', 'Quantidade']
        grafico_artistas = px.bar(top_artistas, x='Artista', y='Quantidade', title="Top 10 artistas com mais músicas")
        grafico_artistas.update_layout(title_x=0.5, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(grafico_artistas, use_container_width=True)
    else:
        st.warning("Nenhum dado para exibir no gráfico de artistas.")

with col_graf2:
    if not df_filtrado.empty:
        decade_counts = df_filtrado['decade'].value_counts().reset_index()
        decade_counts.columns = ['Década', 'Quantidade']
        grafico_decada = px.pie(decade_counts, values='Quantidade', names='Década', title="Distribuição das músicas por década")
        grafico_decada.update_layout(title_x=0.5)
        st.plotly_chart(grafico_decada, use_container_width=True)
    else:
        st.warning("Nenhum dado para exibir no gráfico de décadas.")

st.subheader("Tabela de Dados")
st.dataframe(df_filtrado)
