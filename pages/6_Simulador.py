# pages/6_Simulador.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.database import carregar_dados_simulador

st.set_page_config(page_title="Simulador de Cenários", page_icon="🎯", layout="wide")

st.title("🎯 Simulador de Cenários e Impacto")
st.markdown("Filtre o seu alvo e simule o impacto de ações de comunicação e marketing.")

# 1. Carregamento dos Dados
df = carregar_dados_simulador()

if df.empty:
    st.warning("Nenhum dado encontrado para simulação.")
    st.stop()

# 2. Filtros em Cascata (O Funil Estratégico)
st.sidebar.header("🎯 Segmentação do Alvo")

# Nível 1: Região
regioes = ["Todas"] + sorted(df['regiao'].unique().tolist())
regiao_sel = st.sidebar.selectbox("1. Região:", regioes)
df_f1 = df if regiao_sel == "Todas" else df[df['regiao'] == regiao_sel]

# Nível 2: Estado
estados = ["Todos"] + sorted(df_f1['estado'].unique().tolist())
estado_sel = st.sidebar.selectbox("2. Estado:", estados)
df_f2 = df_f1 if estado_sel == "Todos" else df_f1[df_f1['estado'] == estado_sel]

# Nível 3: Partido
partidos = ["Todos"] + sorted(df_f2['partido'].unique().tolist())
partido_sel = st.sidebar.selectbox("3. Partido:", partidos)
df_f3 = df_f2 if partido_sel == "Todos" else df_f2[df_f2['partido'] == partido_sel]

# Nível 4: Parlamentar
parlamentares = ["Todos"] + sorted(df_f3['parlamentar'].unique().tolist())
parl_sel = st.sidebar.selectbox("4. Parlamentar:", parlamentares)
df_f4 = df_f3 if parl_sel == "Todos" else df_f3[df_f3['parlamentar'] == parl_sel]

# Nível 5: Proposta
propostas = ["Todas"] + sorted(df_f4['tema_proposta'].unique().tolist())
prop_sel = st.sidebar.selectbox("5. Proposta:", propostas)
df_filtrado = df_f4 if prop_sel == "Todas" else df_f4[df_f4['tema_proposta'] == prop_sel]

st.divider()

# 3. Processamento In-Memory
categorias = [
    "Rejeição Total", 
    "Oposição com Remoção", 
    "Dúvida / Neutro", 
    "Apoio com Alteração", 
    "Apoio Total"
]

# Soma os totais agrupados pelo filtro final
contagem_bruta = df_filtrado.groupby('classificacao_sentimento')['total_comentarios'].sum()
# Garante que todas as categorias existam, mesmo com zero votos
contagem_real = pd.Series([contagem_bruta.get(c, 0) for c in categorias], index=categorias)

# 4. Controles de Simulação
st.sidebar.header("📊 Parâmetros de Campanha")

conv_rej_op = st.sidebar.slider("Converter 'Rejeição' para 'Oposição Parcial' (%)", 0, 100, 0, 5)
conv_op_neu = st.sidebar.slider("Converter 'Oposição' para 'Neutro' (%)", 0, 100, 0, 5)
conv_neu_ap = st.sidebar.slider("Converter 'Neutro' para 'Apoio Parcial' (%)", 0, 100, 0, 5)
conv_ap_tot = st.sidebar.slider("Converter 'Apoio Parcial' para 'Apoio Total' (%)", 0, 100, 0, 5)

# 5. Matemática da Simulação
simulacao = contagem_real.copy().astype(float)

transf_rej_op = simulacao["Rejeição Total"] * (conv_rej_op / 100.0)
simulacao["Rejeição Total"] -= transf_rej_op
simulacao["Oposição com Remoção"] += transf_rej_op

transf_op_neu = simulacao["Oposição com Remoção"] * (conv_op_neu / 100.0)
simulacao["Oposição com Remoção"] -= transf_op_neu
simulacao["Dúvida / Neutro"] += transf_op_neu

transf_neu_ap = simulacao["Dúvida / Neutro"] * (conv_neu_ap / 100.0)
simulacao["Dúvida / Neutro"] -= transf_neu_ap
simulacao["Apoio com Alteração"] += transf_neu_ap

transf_ap_tot = simulacao["Apoio com Alteração"] * (conv_ap_tot / 100.0)
simulacao["Apoio com Alteração"] -= transf_ap_tot
simulacao["Apoio Total"] += transf_ap_tot

# 6. Visualização do Gráfico
fig = go.Figure()

fig.add_trace(go.Bar(
    x=categorias, y=contagem_real.values,
    name='Cenário Atual', marker_color='#5c636a', opacity=0.6
))

cores_simulacao = ['#D50000', '#FF6D00', '#9E9E9E', '#FFD600', '#00C853']
fig.add_trace(go.Bar(
    x=categorias, y=simulacao.values,
    name='Cenário Projetado', marker_color=cores_simulacao,
    text=[f"+{int(simulacao[c] - contagem_real[c])}" if simulacao[c] > contagem_real[c] 
          else f"{int(simulacao[c] - contagem_real[c])}" for c in categorias],
    textposition='auto'
))

fig.update_layout(
    barmode='group',
    title_text='Comparativo de Sentimento Público: Real vs. Simulado',
    xaxis_title='', yaxis_title='Volume de Impactos',
    legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.8)'),
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", hovermode='x unified'
)

st.plotly_chart(fig, use_container_width=True)

# 7. Cartões de Resumo (KPIs)
st.subheader("Métricas de Impacto Projetado")
col1, col2, col3 = st.columns(3)

aprovacao_real = contagem_real["Apoio com Alteração"] + contagem_real["Apoio Total"]
rejeicao_real = contagem_real["Rejeição Total"] + contagem_real["Oposição com Remoção"]

aprovacao_simulada = simulacao["Apoio com Alteração"] + simulacao["Apoio Total"]
rejeicao_simulada = simulacao["Rejeição Total"] + simulacao["Oposição com Remoção"]

with col1:
    st.metric("Aprovação Total (Base vs. Projetado)", f"{int(aprovacao_simulada)}", delta=f"{int(aprovacao_simulada - aprovacao_real)} conversões")
with col2:
    st.metric("Rejeição Total (Base vs. Projetado)", f"{int(rejeicao_simulada)}", delta=f"{int(rejeicao_simulada - rejeicao_real)} conversões", delta_color="inverse")
with col3:
    st.metric("Indecisos Restantes", f"{int(simulacao['Dúvida / Neutro'])}", delta=f"{int(simulacao['Dúvida / Neutro'] - contagem_real['Dúvida / Neutro'])} conversões", delta_color="off")