# pages/6_Simulador.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.database import carregar_dados_simulador

st.set_page_config(page_title="Simulador de Cenários", page_icon="🎯", layout="wide")

st.title("🎯 Simulador de Cenários e Impacto")
st.markdown("Filtre o seu alvo e simule o impacto de ações de comunicação e marketing.")

# ==========================================
# 1. GUIA DE USO (ONBOARDING)
# ==========================================
with st.expander("💡 Como utilizar o Simulador de Campanhas?", expanded=False):
    st.markdown("""
    Este simulador permite prever o Retorno sobre o Investimento (ROI) de campanhas de comunicação.
    
    1. **Segmentação (Alvo):** Use o primeiro bloco da barra lateral para isolar o público que você deseja atingir (ex: Eleitores de um estado específico reagindo a uma proposta específica).
    2. **Parâmetros de Campanha (Esforço):** Use os controles deslizantes para definir a meta de conversão da sua campanha de marketing. Exemplo: *"Se eu investir na quebra de objeções, quantos % da Oposição eu consigo transformar em Neutros?"*
    3. **Análise de Impacto (Resultado):** Observe os KPIs no topo da tela para ver o ganho real em números de apoiadores e redução de rejeição. O gráfico ilustra de onde os eleitores saíram e para onde foram.
    """)

# ==========================================
# 2. CARREGAMENTO DOS DADOS
# ==========================================
df = carregar_dados_simulador() #[cite: 2]

if df.empty:
    st.warning("Nenhum dado encontrado para simulação.")
    st.stop()

# ==========================================
# 3. FILTROS EM CASCATA (MOTOR ORIGINAL)
# ==========================================
st.sidebar.header("🎯 Segmentação do Alvo")

# Nível 1: Região[cite: 2]
regioes = ["Todas"] + sorted(df['regiao'].dropna().unique().tolist())
regiao_sel = st.sidebar.selectbox("1. Região:", regioes)
df_f1 = df if regiao_sel == "Todas" else df[df['regiao'] == regiao_sel]

# Nível 2: Estado[cite: 2]
estados = ["Todos"] + sorted(df_f1['estado'].dropna().unique().tolist())
estado_sel = st.sidebar.selectbox("2. Estado:", estados)
df_f2 = df_f1 if estado_sel == "Todos" else df_f1[df_f1['estado'] == estado_sel]

# Nível 3: Partido[cite: 2]
partidos = ["Todos"] + sorted(df_f2['partido'].dropna().unique().tolist())
partido_sel = st.sidebar.selectbox("3. Partido:", partidos)
df_f3 = df_f2 if partido_sel == "Todos" else df_f2[df_f2['partido'] == partido_sel]

# Nível 4: Parlamentar[cite: 2]
parlamentares = ["Todos"] + sorted(df_f3['parlamentar'].dropna().unique().tolist())
parl_sel = st.sidebar.selectbox("4. Parlamentar:", parlamentares)
df_f4 = df_f3 if parl_sel == "Todos" else df_f3[df_f3['parlamentar'] == parl_sel]

# Nível 5: Proposta[cite: 2]
propostas = ["Todas"] + sorted(df_f4['tema_proposta'].dropna().unique().tolist())
prop_sel = st.sidebar.selectbox("5. Proposta:", propostas)
df_filtrado = df_f4 if prop_sel == "Todas" else df_f4[df_f4['tema_proposta'] == prop_sel]

st.sidebar.divider()

# ==========================================
# 4. AGRUPAMENTO E CONTROLES (MOTOR ORIGINAL)
# ==========================================
categorias = [
    "Rejeição Total", 
    "Oposição com Remoção", 
    "Dúvida / Neutro", 
    "Apoio com Alteração", 
    "Apoio Total"
] #[cite: 2]

# Soma os totais agrupados pelo filtro final[cite: 2]
contagem_bruta = df_filtrado.groupby('classificacao_sentimento')['total_comentarios'].sum()
# Garante que todas as categorias existam, mesmo com zero votos[cite: 2]
contagem_real = pd.Series([contagem_bruta.get(c, 0) for c in categorias], index=categorias)

st.sidebar.header("📊 Parâmetros de Campanha")

conv_rej_op = st.sidebar.slider("Converter 'Rejeição' para 'Oposição Parcial' (%)", 0, 100, 0, 5) #[cite: 2]
conv_op_neu = st.sidebar.slider("Converter 'Oposição' para 'Neutro' (%)", 0, 100, 0, 5) #[cite: 2]
conv_neu_ap = st.sidebar.slider("Converter 'Neutro' para 'Apoio Parcial' (%)", 0, 100, 0, 5) #[cite: 2]
conv_ap_tot = st.sidebar.slider("Converter 'Apoio Parcial' para 'Apoio Total' (%)", 0, 100, 0, 5) #[cite: 2]

# ==========================================
# 5. MATEMÁTICA DA SIMULAÇÃO
# ==========================================
simulacao = contagem_real.copy().astype(float) #[cite: 2]

transf_rej_op = simulacao["Rejeição Total"] * (conv_rej_op / 100.0) #[cite: 2]
simulacao["Rejeição Total"] -= transf_rej_op #[cite: 2]
simulacao["Oposição com Remoção"] += transf_rej_op #[cite: 2]

transf_op_neu = simulacao["Oposição com Remoção"] * (conv_op_neu / 100.0) #[cite: 2]
simulacao["Oposição com Remoção"] -= transf_op_neu #[cite: 2]
simulacao["Dúvida / Neutro"] += transf_op_neu #[cite: 2]

transf_neu_ap = simulacao["Dúvida / Neutro"] * (conv_neu_ap / 100.0) #[cite: 2]
simulacao["Dúvida / Neutro"] -= transf_neu_ap #[cite: 2]
simulacao["Apoio com Alteração"] += transf_neu_ap #[cite: 2]

transf_ap_tot = simulacao["Apoio com Alteração"] * (conv_ap_tot / 100.0) #[cite: 2]
simulacao["Apoio com Alteração"] -= transf_ap_tot #[cite: 2]
simulacao["Apoio Total"] += transf_ap_tot #[cite: 2]

# ==========================================
# 6. KPIs DE IMPACTO (MOVIDOS PARA O TOPO)
# ==========================================
st.markdown("### 📈 Métricas de Impacto Projetado")
col1, col2, col3 = st.columns(3)

# Base[cite: 2]
aprovacao_real = contagem_real["Apoio com Alteração"] + contagem_real["Apoio Total"] 
rejeicao_real = contagem_real["Rejeição Total"] + contagem_real["Oposição com Remoção"]

# Simulação[cite: 2]
aprovacao_simulada = simulacao["Apoio com Alteração"] + simulacao["Apoio Total"]
rejeicao_simulada = simulacao["Rejeição Total"] + simulacao["Oposição com Remoção"]

# Deltas
delta_aprovacao = int(aprovacao_simulada - aprovacao_real)
delta_rejeicao = int(rejeicao_simulada - rejeicao_real)
delta_indecisos = int(simulacao['Dúvida / Neutro'] - contagem_real['Dúvida / Neutro'])

col1.metric(
    "Aprovação Projetada (Total + Parcial)", 
    f"{int(aprovacao_simulada):,}".replace(',', '.'), 
    f"{'+' if delta_aprovacao > 0 else ''}{delta_aprovacao:,} novos apoiadores".replace(',', '.'),
    delta_color="normal"
)

col2.metric(
    "Indecisos / Neutros Restantes", 
    f"{int(simulacao['Dúvida / Neutro']):,}".replace(',', '.'), 
    f"{'+' if delta_indecisos > 0 else ''}{delta_indecisos:,} pessoas convertidas".replace(',', '.'),
    delta_color="off" 
)

col3.metric(
    "Rejeição Projetada (Total + Oposição)", 
    f"{int(rejeicao_simulada):,}".replace(',', '.'), 
    f"{delta_rejeicao:,} pessoas reduzidas na rejeição".replace(',', '.'),
    delta_color="inverse"
)

st.divider()

# ==========================================
# 7. GRÁFICO DE STORYTELLING: BARRAS SOBREPOSTAS
# ==========================================
st.subheader("Comparativo de Sentimento Público: Real vs. Simulado")

# Invertendo a ordem para "Apoio Total" ficar no topo do gráfico horizontal
ordem_sentimentos = categorias[::-1] 
cores_projetadas = ['#00C853', '#FFD600', '#9E9E9E', '#FF6D00', '#D50000']

# Extraindo os valores ordenados para o gráfico
valores_reais_grafico = [contagem_real[c] for c in ordem_sentimentos]
valores_simulados_grafico = [simulacao[c] for c in ordem_sentimentos]

fig = go.Figure()

# Barra 1: Cenário Atual (Barra Larga e Cinza Claro ao fundo)
fig.add_trace(go.Bar(
    y=ordem_sentimentos,
    x=valores_reais_grafico,
    name='Cenário Atual (Base)',
    orientation='h',
    marker=dict(color='#E0E0E0', line=dict(color='#BDBDBD', width=1)),
    width=0.7,
    hoverinfo='x+name'
))

# Barra 2: Cenário Projetado (Barra Fina e Colorida à frente)
fig.add_trace(go.Bar(
    y=ordem_sentimentos,
    x=valores_simulados_grafico,
    name='Cenário Projetado',
    orientation='h',
    marker=dict(color=cores_projetadas), 
    width=0.4,
    text=[f"{int(v)}" for v in valores_simulados_grafico],
    textposition='outside',
    textfont=dict(color='black', size=12),
    hoverinfo='x+name'
))

fig.update_layout(
    barmode='overlay', # MÁGICA ACONTECE AQUI: Sobrepõe as barras em vez de agrupá-las
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(title='Volume de Impactos', showgrid=True, gridcolor='#F5F5F5'),
    yaxis=dict(categoryorder='array', categoryarray=ordem_sentimentos),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=0, r=0, t=30, b=0),
    height=450
)

st.plotly_chart(fig, use_container_width=True)