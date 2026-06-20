import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.database import carregar_dados_tendencias

st.set_page_config(page_title="Radar de Tendências", page_icon="📈", layout="wide")

st.title("📈 Radar de Tendências")
st.markdown("Acompanhe a evolução do sentimento público, identifique dias críticos e descubra os estopins das crises.")

# ==========================================
# 1. CARREGAMENTO E PREPARAÇÃO DOS DADOS
# ==========================================
df_tendencias = carregar_dados_tendencias()

if df_tendencias.empty:
    st.warning("Nenhum dado temporal processado ainda.")
    st.stop()

min_date = df_tendencias['data'].min().date()
max_date = df_tendencias['data'].max().date()

# ==========================================
# 2. FILTROS LATERAIS (CASCATA + TEMPORAL)
# ==========================================
st.sidebar.header("🎯 Filtros de Análise")

datas_selecionadas = st.sidebar.date_input(
    "Período de Análise:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(datas_selecionadas) == 2:
    start_date, end_date = datas_selecionadas
else:
    start_date = end_date = datas_selecionadas[0]

df_filtrado_data = df_tendencias[
    (df_tendencias['data'].dt.date >= start_date) & 
    (df_tendencias['data'].dt.date <= end_date)
].copy()

# Cascata: Partido -> Parlamentar -> Proposta
partidos_disp = ["Todos"] + sorted(df_filtrado_data['partido'].dropna().unique().tolist())
filtro_partido = st.sidebar.selectbox("Foco Partidário:", partidos_disp)

if filtro_partido != "Todos":
    df_temp_partido = df_filtrado_data[df_filtrado_data['partido'] == filtro_partido]
else:
    df_temp_partido = df_filtrado_data.copy()

politicos_disp = ["Todos"] + sorted(df_temp_partido['parlamentar'].dropna().unique().tolist())
filtro_politico = st.sidebar.selectbox("Isolar Parlamentar:", politicos_disp)

if filtro_politico != "Todos":
    df_temp_parlamentar = df_temp_partido[df_temp_partido['parlamentar'] == filtro_politico]
else:
    df_temp_parlamentar = df_temp_partido.copy()

propostas_disp = ["Todas"] + sorted(df_temp_parlamentar['tema_proposta'].dropna().unique().tolist())
filtro_proposta = st.sidebar.selectbox("Foco em Proposta:", propostas_disp)

df_filtrado = df_temp_parlamentar.copy()
if filtro_proposta != "Todas":
    df_filtrado = df_filtrado[df_filtrado['tema_proposta'] == filtro_proposta]

if df_filtrado.empty:
    st.sidebar.warning("Nenhuma interação no período/filtros selecionados.")
    st.stop()

# ==========================================
# 3. MOTOR ANALÍTICO (Simplificação e Picos)
# ==========================================
def macro_sentimento(sentimento):
    if sentimento in ["Apoio Total", "Apoio com Alteração"]: return "Aprovação"
    if sentimento in ["Rejeição Total", "Oposição com Remoção"]: return "Rejeição"
    return "Neutro"

df_filtrado['Sentimento Macro'] = df_filtrado['classificacao_sentimento'].apply(macro_sentimento)
df_linha = df_filtrado.groupby(['data', 'Sentimento Macro'])['total_comentarios'].sum().reset_index()
df_pivot = df_linha.pivot(index='data', columns='Sentimento Macro', values='total_comentarios').fillna(0)

for col in ['Aprovação', 'Rejeição', 'Neutro']:
    if col not in df_pivot.columns: df_pivot[col] = 0

# ==========================================
# 4. KPIs E RESUMO EXECUTIVO (MOVIDO PARA O TOPO)
# ==========================================
st.markdown("### 📊 Resumo do Período Selecionado")
col1, col2, col3 = st.columns(3)

# KPI 1: Total
total_interacoes = int(df_filtrado['total_comentarios'].sum())
col1.metric("Volume Total de Interações", f"{total_interacoes:,}".replace(',', '.'))

# KPI 2: Pico
dia_mais_barulhento = df_pivot.sum(axis=1).idxmax()
volume_dia_barulhento = int(df_pivot.sum(axis=1).max())
col2.metric(
    "Maior Pico de Engajamento (Dia)", 
    f"{volume_dia_barulhento:,}".replace(',', '.'), 
    f"Ocorrido em {dia_mais_barulhento.strftime('%d/%m/%Y')}", 
    delta_color="off"
)

# KPI 3: Saldo
total_aprovacao = int(df_pivot['Aprovação'].sum())
total_rejeicao = int(df_pivot['Rejeição'].sum())
saldo_periodo = total_aprovacao - total_rejeicao

cor_saldo = "normal" if saldo_periodo >= 0 else "inverse"
sinal = "+" if saldo_periodo > 0 else ""

col3.metric(
    "Saldo de Imagem (Aprovações vs Rejeições)", 
    f"{sinal}{saldo_periodo:,}".replace(',', '.'), 
    f"{total_aprovacao:,} Apoios | {total_rejeicao:,} Rejeições".replace(',', '.'), 
    delta_color=cor_saldo
)

st.divider()

# ==========================================
# 5. GRÁFICO: O RADAR COM ANOTAÇÕES
# ==========================================
# Identificação dos picos para o gráfico
dia_pico_rejeicao = df_pivot['Rejeição'].idxmax() if not df_pivot['Rejeição'].empty and df_pivot['Rejeição'].max() > 0 else None
dia_pico_aprovacao = df_pivot['Aprovação'].idxmax() if not df_pivot['Aprovação'].empty and df_pivot['Aprovação'].max() > 0 else None

def descobrir_estopim(df_base, dia_alvo, sentimento_alvo):
    if dia_alvo is None: return ""
    dados_dia = df_base[(df_base['data'] == dia_alvo) & (df_base['Sentimento Macro'] == sentimento_alvo)]
    if dados_dia.empty: return "Múltiplos pequenos temas"
    tema_principal = dados_dia.groupby('tema_proposta')['total_comentarios'].sum().idxmax()
    return f"Foco em: {tema_principal[:30]}..."

estopim_rejeicao = descobrir_estopim(df_filtrado, dia_pico_rejeicao, "Rejeição")
estopim_aprovacao = descobrir_estopim(df_filtrado, dia_pico_aprovacao, "Aprovação")

st.subheader("Linha do Tempo de Interações e Estopins")

cores_macro = {"Aprovação": "#00C853", "Rejeição": "#D50000", "Neutro": "#9E9E9E"}

fig = px.line(
    df_linha,
    x="data",
    y="total_comentarios",
    color="Sentimento Macro",
    color_discrete_map=cores_macro,
    markers=True,
    labels={"data": "Data", "total_comentarios": "Volume Diário", "Sentimento Macro": "Viés"}
)

if dia_pico_rejeicao and df_pivot.loc[dia_pico_rejeicao, 'Rejeição'] > 0:
    fig.add_annotation(
        x=dia_pico_rejeicao,
        y=df_pivot.loc[dia_pico_rejeicao, 'Rejeição'],
        text=f"🚨 <b>Pico de Crise</b><br>{estopim_rejeicao}",
        showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor="#D50000",
        ax=-20, ay=-50, bgcolor="rgba(255, 255, 255, 0.8)", bordercolor="#D50000",
        font=dict(size=11, color="#D50000")
    )

if dia_pico_aprovacao and df_pivot.loc[dia_pico_aprovacao, 'Aprovação'] > 0:
    fig.add_annotation(
        x=dia_pico_aprovacao,
        y=df_pivot.loc[dia_pico_aprovacao, 'Aprovação'],
        text=f"🌟 <b>Pico de Apoio</b><br>{estopim_aprovacao}",
        showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor="#00C853",
        ax=20, ay=-50, bgcolor="rgba(255, 255, 255, 0.8)", bordercolor="#00C853",
        font=dict(size=11, color="#00C853")
    )

fig.update_traces(line_shape='spline')
fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    hovermode="x unified",
    xaxis_title="",
    yaxis_title="Volume Diário",
    margin=dict(t=10, b=10) # Reduz as margens para encaixar melhor abaixo dos KPIs
)

st.plotly_chart(fig, use_container_width=True)