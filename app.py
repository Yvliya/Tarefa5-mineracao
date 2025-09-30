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
    
    df = df.dropna(subset=required_cols)
    

    df['year'] = df['year'].astype(int)
    df = df[(df['year'] >= 1921) & (df['year'] <= 2020)]

    df['decade'] = (df['year'] // 10) * 10
    df['decade'] = df['decade'].astype(str) + 's'

    return df

df_original = load_data(PUBLIC_DATA_URL)

st.set_page_config(
    page_title="Dashboard Spotify (1921-2020)", 
    page_icon="🎵", 
    layout="wide"
)

st.title("🎵 Análise de Músicas do Spotify (1921-2020)")

st.markdown("""
Este painel interativo permite explorar tendências e métricas-chave (KPIs) de faixas 
musicais, abrangendo um século de história da música. **(Versão de Produção)**. Use os filtros laterais para personalizar sua análise.
""")

st.markdown("---")

st.sidebar.header("Filtros de Dados")

if df_original is not None:
    df_filtered = df_original.copy()

    min_year = int(df_original['year'].min())
    max_year = int(df_original['year'].max())
    
    year_range = st.sidebar.slider(
        "Selecione o Intervalo de Ano de Lançamento",
        min_value=min_year,
        max_value=max_year,
        value=(1990, 2020)
    )
    
    df_filtered = df_filtered[
        (df_filtered['year'] >= year_range[0]) & 
        (df_filtered['year'] <= year_range[1])
    ]

    top_artists = df_original['artists'].value_counts().nlargest(100).index.tolist()
    
    selected_artists = st.sidebar.multiselect(
        "Selecione Artistas",
        options=top_artists,
        default=[] 
    )
    
    if selected_artists:
        df_filtered = df_filtered[df_filtered['artists'].isin(selected_artists)]

    if df_filtered.empty:
        st.warning("Nenhuma música encontrada com os filtros selecionados.")
        st.stop()
        
    st.sidebar.markdown("---")
    st.sidebar.info(f"Músicas Filtradas: **{len(df_filtered):,}**")

col1, col2, col3 = st.columns(3)

total_tracks = len(df_filtered)
col1.metric("Total de Músicas Filtradas", f"{total_tracks:,}")

avg_popularity = df_filtered['popularity'].mean()
col2.metric("Média de Popularidade (0-100)", f"{avg_popularity:.1f}")

most_frequent_artist = df_filtered['artists'].mode().iloc[0] if not df_filtered['artists'].mode().empty else "N/A"
col3.metric("Artista Mais Frequente", most_frequent_artist)

st.markdown("---")

st.header("Análise Visual")
chart_col1, chart_col2 = st.columns(2)

top_10_artists = df_filtered['artists'].value_counts().nlargest(10).reset_index()
top_10_artists.columns = ['Artista', 'Contagem de Músicas']

fig_bar = px.bar(
    top_10_artists, 
    x='Contagem de Músicas', 
    y='Artista', 
    orientation='h',
    title='Top 10 Artistas por Número de Músicas',
    color='Contagem de Músicas',
    color_continuous_scale=px.colors.sequential.Teal
)
fig_bar.update_layout(
    yaxis={'categoryorder':'total ascending'}, 
    title_x=0.5,
    margin=dict(l=20, r=20, t=50, b=20)
)

chart_col1.plotly_chart(fig_bar, use_container_width=True)

decade_distribution = df_filtered['decade'].value_counts().reset_index()
decade_distribution.columns = ['Década', 'Contagem']

decade_distribution['Sort_Decade'] = decade_distribution['Década'].str.replace('s', '').astype(int)
decade_distribution = decade_distribution.sort_values(by='Sort_Decade')

fig_pie = px.pie(
    decade_distribution, 
    names='Década', 
    values='Contagem', 
    title='Distribuição de Músicas por Década',
    hole=.3, 
    color_discrete_sequence=px.colors.sequential.RdBu
)

fig_pie.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#000000', width=1)))
fig_pie.update_layout(title_x=0.5, margin=dict(l=20, r=20, t=50, b=20))

chart_col2.plotly_chart(fig_pie, use_container_width=True)

st.header("Visualização dos Dados Filtrados")

st.data_editor(
    df_filtered.drop(columns=['decade']), 
    column_order=('name', 'artists', 'year', 'popularity', 'energy', 'danceability', 'valence', 'duration_ms'),
    column_config={
        "name": st.column_config.TextColumn("Nome da Música"),
        "artists": st.column_config.TextColumn("Artista(s)"),
        "year": st.column_config.NumberColumn("Ano", help="Ano de lançamento"),
        "popularity": st.column_config.ProgressColumn("Popularidade", format="%d", min_value=0, max_value=100),
        "energy": st.column_config.ProgressColumn("Energia", format="%.2f", min_value=0, max_value=1),
        "danceability": st.column_config.ProgressColumn("Dançabilidade", format="%.2f", min_value=0, max_value=1),
        "valence": st.column_config.ProgressColumn("Felicidade (Valence)", format="%.2f", min_value=0, max_value=1),
        "duration_ms": st.column_config.NumberColumn("Duração (ms)"),
    },
    hide_index=True,
    use_container_width=True,
)
