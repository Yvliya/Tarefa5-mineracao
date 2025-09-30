import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- 1. Carregamento e Preparação dos Dados (Usando cache para performance) ---

# Define a função de carregamento e pré-processamento
@st.cache_data
def load_data(file_path):
    """Carrega o dataset, extrai o ano e calcula a década, e trata NaN/inconsistências."""
    try:
        # Carrega o CSV. Assumindo que o arquivo se chama 'spotify_tracks.csv'
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        st.error(f"Erro: Arquivo '{file_path}' não encontrado. Por favor, baixe o dataset e coloque-o na mesma pasta.")
        st.stop()
    
    # 1.1. Tratar valores ausentes: Removendo linhas com NaN em colunas críticas
    df = df.dropna(subset=['artists', 'name', 'popularity', 'year'])
    
    # Garantir que 'year' seja um inteiro e está dentro do intervalo esperado
    df['year'] = df['year'].astype(int)
    df = df[(df['year'] >= 1921) & (df['year'] <= 2020)]

    # 1.2. Criação da coluna 'decade' para o Gráfico de Pizza
    df['decade'] = (df['year'] // 10) * 10
    df['decade'] = df['decade'].astype(str) + 's'
    
    # Limpeza da coluna 'artists' (removendo colchetes e aspas se estiver como lista de string)
    # Por exemplo: transforma '["Ed Sheeran"]' em 'Ed Sheeran'
    df['artists'] = df['artists'].str.replace(r"[\[\]']", '', regex=True).str.strip()

    return df

# Define o nome do arquivo do dataset
DATA_FILE = 'spotify_tracks.csv'
df_original = load_data(DATA_FILE)

# --- 2. Configuração do Dashboard ---

st.set_page_config(
    page_title="Dashboard Spotify (1921-2020)", 
    page_icon="🎵", 
    layout="wide"
)

# Título Principal
st.title("🎵 Análise de Músicas do Spotify (1921-2020)")

# Descrição Inicial
st.markdown("""
Este painel interativo permite explorar tendências e métricas-chave (KPIs) de mais de 160 mil faixas 
musicais, abrangendo um século de história da música. Use os filtros laterais para personalizar sua análise.
""")

st.markdown("---")

# --- 3. Filtros na Barra Lateral ---

st.sidebar.header("Filtros de Dados")

if df_original is not None:
    df_filtered = df_original.copy()

    # 3.1. Filtro de Ano de Lançamento (Intervalo)
    min_year = int(df_original['year'].min())
    max_year = int(df_original['year'].max())
    
    year_range = st.sidebar.slider(
        "Selecione o Intervalo de Ano de Lançamento",
        min_value=min_year,
        max_value=max_year,
        value=(1990, 2020)
    )
    
    # Aplica o filtro de ano
    df_filtered = df_filtered[
        (df_filtered['year'] >= year_range[0]) & 
        (df_filtered['year'] <= year_range[1])
    ]

    # 3.2. Filtro de Artista (Seleção Múltipla)
    
    # Para evitar um seletor com 30k+ artistas, pegamos os 100 artistas mais frequentes
    top_artists = df_original['artists'].value_counts().nlargest(100).index.tolist()
    
    selected_artists = st.sidebar.multiselect(
        "Selecione Artistas",
        options=top_artists,
        default=[] # Deixa vazio por padrão para não carregar todos os dados
    )
    
    if selected_artists:
        # Aplica o filtro de artista
        df_filtered = df_filtered[df_filtered['artists'].isin(selected_artists)]

    # Se o DataFrame filtrado estiver vazio, mostramos uma mensagem e paramos
    if df_filtered.empty:
        st.warning("Nenhuma música encontrada com os filtros selecionados.")
        st.stop()
        
    st.sidebar.markdown("---")
    st.sidebar.info(f"Músicas Filtradas: **{len(df_filtered):,}**")

# --- 4. Métricas Principais (KPIs) ---

# Layout para KPIs
col1, col2, col3 = st.columns(3)

# 4.1. Total de Músicas Selecionadas
total_tracks = len(df_filtered)
col1.metric("Total de Músicas Filtradas", f"{total_tracks:,}")

# 4.2. Média de Popularidade das Músicas
avg_popularity = df_filtered['popularity'].mean()
col2.metric("Média de Popularidade (0-100)", f"{avg_popularity:.1f}")

# 4.3. Artista Mais Frequente (no conjunto filtrado)
most_frequent_artist = df_filtered['artists'].mode().iloc[0] if not df_filtered['artists'].mode().empty else "N/A"
col3.metric("Artista Mais Frequente", most_frequent_artist)

st.markdown("---")

# --- 5. Gráficos Interativos (Plotly) ---

st.header("Análise Visual")
chart_col1, chart_col2 = st.columns(2)

# 5.1. Gráfico de Barras: Top 10 Artistas com Mais Músicas

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
# Ajuste do layout para melhor visualização
fig_bar.update_layout(
    yaxis={'categoryorder':'total ascending'}, 
    title_x=0.5,
    margin=dict(l=20, r=20, t=50, b=20)
)

chart_col1.plotly_chart(fig_bar, use_container_width=True)

# 5.2. Gráfico de Pizza: Distribuição das Músicas por Década de Lançamento

decade_distribution = df_filtered['decade'].value_counts().reset_index()
decade_distribution.columns = ['Década', 'Contagem']

# Ordena as décadas antes de plotar
# Garante que as décadas sejam tratadas como inteiros temporariamente para ordenação correta
decade_distribution['Sort_Decade'] = decade_distribution['Década'].str.replace('s', '').astype(int)
decade_distribution = decade_distribution.sort_values(by='Sort_Decade')

fig_pie = px.pie(
    decade_distribution, 
    names='Década', 
    values='Contagem', 
    title='Distribuição de Músicas por Década',
    hole=.3, # Cria um gráfico de donut
    color_discrete_sequence=px.colors.sequential.RdBu
)

fig_pie.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#000000', width=1)))
fig_pie.update_layout(title_x=0.5, margin=dict(l=20, r=20, t=50, b=20))

chart_col2.plotly_chart(fig_pie, use_container_width=True)

# --- 6. Tabela Dinâmica ---

st.header("Visualização dos Dados Filtrados")

# Mostra os dados filtrados em formato de tabela interativa (st.data_editor)
st.data_editor(
    df_filtered.drop(columns=['decade']), # Remove a coluna auxiliar 'decade' da visualização
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
