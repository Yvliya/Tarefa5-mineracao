import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

PUBLIC_DATA_URL = 'https://raw.githubusercontent.com/rfordatascience/tidytuesday/master/data/2020/2020-01-21/spotify_songs.csv'

@st.cache_data
def load_data(url):
    try:
        df = pd.read_csv(url)
    except Exception as e:
        st.error(f"Erro ao carregar os dados da URL: {e}. Verifique sua conexão ou a URL do dataset.")
        st.stop()
    
    # Renomeando colunas para padronizar
    column_rename_map = {}
    if 'track_name' in df.columns:
        column_rename_map['track_name'] = 'name'
    if 'track_artist' in df.columns:
        column_rename_map['track_artist'] = 'artists'
    df = df.rename(columns=column_rename_map)

    # Criando coluna 'year'
    if 'track_album_release_date' in df.columns:
        df['year'] = df['track_album_release_date'].astype(str).str.split('-').str[0]
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
    else:
        df['year'] = np.nan

    # Colunas obrigatórias que vamos precisar
    required_cols = ['artists', 'name', 'popularity', 'year']

    # Garante que só usamos colunas que realmente existem
    existing_cols = [col for col in required_cols if col in df.columns]

    if existing_cols:
        df = df.dropna(subset=existing_cols)
    else:
        st.warning("Nenhuma das colunas obrigatórias foi encontrada no dataset!")

    # Tratamento da coluna 'year'
    if 'year' in df.columns:
        df = df[df['year'].notna()]
        df['year'] = df['year'].astype(int, errors='ignore')
        df = df[(df['year'] >= 1921) & (df['year'] <= 2020)]
        df['decade'] = (df['year'] // 10) * 10
        df['decade'] = df['decade'].astype(str) + 's'
    else:
        df['decade'] = "Desconhecida"

    return df


# ---------------------------
# APP STREAMLIT
# ---------------------------

df_original = load_data(PUBLIC_DATA_URL)

st.set_page_config(
    page_title="Dashboard Spotify (1921-2020)", 
    page_icon="🎵", 
    layout="wide"
)

st.title("🎵 Análise de Músicas do Spotify (1921-2020)")

st.markdown("""
Este painel interativo permite explorar tendências e métricas-chave (KPIs) de faixas 
musicais, abrangendo um século de história da música. **(Versão de Produção)**.  
Use os filtros laterais para personalizar sua análise.
""")

st.markdown("---")

st.sidebar.header("Filtros de Dados")

if df_original is not None:
    df_filtered = df_original.copy()

    min_year = int(df_original['year'].min())
