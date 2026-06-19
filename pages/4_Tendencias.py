# pages/4_Tendencias.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta  # <--- NOVA IMPORTAÇÃO AQUI
from utils.database import carregar_dados_temporais

st.set_page_config(page_title="Radar de Tendências", page_icon="📈", layout="wide")

st.title("📈 Radar de Tendências")
st.markdown("Acompanhe a evolução do sentimento público ao longo do tempo.")

df_temp = carregar_dados_temporais()

if df_temp.empty:
    st.info("Aguardando dados temporais...")
    st.stop()

# Filtro de data
df_temp['data'] = pd.to_datetime(df_temp['data'])
min_date = df_temp['data'].min().to_pydatetime()
max_date = df_temp['data'].max().to_pydatetime()

# --- CORREÇÃO DO ERRO DO SLIDER ---
# Se houver apenas dados de um dia, cria um intervalo artificial de segurança
if min_date == max_date:
    min_date = min_date - timedelta(days=1)
    max_date = max_date + timedelta(days=1)
# ----------------------------------

st.sidebar.header("Filtros Temporais")
data_inicio, data_fim = st.sidebar.slider(
    "Período de Análise:", 
    min_value=min_date, 
    max_value=max_date, 
    value=(min_date, max_date)
)

df_filtrado = df_temp[(df_temp['data'] >= pd.to_datetime(data_inicio)) & (df_temp['data'] <= pd.to_datetime(data_fim))]

# Gráfico de Área Empilhada (Time Series)
fig = px.area(
    df_filtrado, 
    x="data", 
    y="total", 
    color="classificacao_sentimento",
    color_discrete_map={
        "Apoio Total": "#00C853", "Apoio com Alteração": "#FFD600", 
        "Dúvida / Neutro": "#9E9E9E", "Oposição com Remoção": "#FF6D00", 
        "Rejeição Total": "#D50000"
    },
    title="Volume de Sentimento por Dia"
)

fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", hovermode="x unified")

# Renderização do gráfico atualizada para remover o warning de depreciação
st.plotly_chart(fig, width="stretch")

# Resumo rápido
st.subheader("Análise de Pico")
pico = df_filtrado.groupby('data')['total'].sum().idxmax()
st.write(f"O dia de maior engajamento registrado foi: **{pico.strftime('%d/%m/%Y')}**")