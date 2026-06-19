# pages/3_Geopolitica.py
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.database import carregar_dados_geopoliticos

st.set_page_config(page_title="Geopolítica", page_icon="🗺️", layout="wide")

st.title("🗺️ Mapa Geopolítico e Aceitação Regional")

# 1. Carrega os dados
df_geo = carregar_dados_geopoliticos()
if df_geo.empty:
    st.warning("Nenhum dado geográfico processado ainda.")
    st.stop()

# 2. Filtro Interativo
partidos_disponiveis = df_geo['partido'].unique().tolist()
partido_selecionado = st.sidebar.selectbox("Filtrar por Partido:", ["Visão Nacional (Todos)"] + partidos_disponiveis)
df_filtrado = df_geo[df_geo['partido'] == partido_selecionado].copy() if partido_selecionado != "Visão Nacional (Todos)" else df_geo.copy()

# 3. Linha de KPIs (Cards no topo)
col_k1, col_k2, col_k3 = st.columns(3)
total_coments = df_filtrado['total_comentarios'].sum()
regiao_lider = df_filtrado.groupby('regiao')['total_comentarios'].sum().idxmax() if not df_filtrado.empty else "N/A"
col_k1.metric("Volume de Engajamento", f"{total_coments:,}")
col_k2.metric("Região Mais Ativa", regiao_lider)
col_k3.metric("UFs Cobertas", df_filtrado['uf'].nunique())

st.divider()

# 4. Mapa do Brasil (Ocupando toda a largura)
st.subheader("Densidade de Engajamento por Estado")
df_mapa_base = pd.DataFrame({'uf': ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']})
df_agrupado_uf = df_filtrado.groupby('uf')['total_comentarios'].sum().reset_index()
df_final_mapa = pd.merge(df_mapa_base, df_agrupado_uf, on='uf', how='left').fillna(0)

fig_map = px.choropleth(
    df_final_mapa, 
    geojson="https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson", 
    locations='uf', featureidkey='properties.sigla',
    color='total_comentarios',
    color_continuous_scale=[[0, '#1E1E2E'], [0.01, '#81d4fa'], [1, '#0277bd']],
    hover_name='uf'
)
fig_map.update_geos(fitbounds="locations", visible=False)
fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor="rgba(0,0,0,0)", height=500)
st.plotly_chart(fig_map, use_container_width=True)

st.divider()

# 5. Gráficos Analíticos (Linha inferior)
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.markdown("**Taxa de Intenção por Região (%)**")
    df_regiao = df_filtrado.groupby(['regiao', 'classificacao_sentimento'])['total_comentarios'].sum().reset_index()
    total_regiao = df_regiao.groupby('regiao')['total_comentarios'].transform('sum')
    df_regiao['percentual'] = (df_regiao['total_comentarios'] / total_regiao) * 100
    df_regiao['texto'] = df_regiao['percentual'].apply(lambda x: f"{x:.1f}%")
    
    fig_bar = px.bar(df_regiao, x="regiao", y="percentual", color="classificacao_sentimento",
                     color_discrete_map={"Apoio Total": "#00C853", "Apoio com Alteração": "#FFD600", 
                                         "Dúvida / Neutro": "#9E9E9E", "Oposição com Remoção": "#FF6D00", 
                                         "Rejeição Total": "#D50000"},
                     text="texto")
    fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", barmode="stack")
    st.plotly_chart(fig_bar, use_container_width=True)

with col_g2:
    st.markdown("**Top 5 Estados mais Engajados**")
    df_top = df_filtrado.groupby('estado')['total_comentarios'].sum().nlargest(5).reset_index()
    fig_top = px.bar(df_top, x='total_comentarios', y='estado', orientation='h', color='total_comentarios', color_continuous_scale='Blues')
    fig_top.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_top, use_container_width=True)