import streamlit as st
import pandas as pd
import plotly.express as px
from utils.database import carregar_dados_partidarios

st.set_page_config(page_title="Termômetro Partidário", page_icon="🏛️", layout="wide")

st.title("🏛️ Termômetro Partidário e Risco Político")
st.markdown("Analise o saldo de aceitação, volume de engajamento e risco de imagem de legendas e parlamentares.")

# ==========================================
# 1. CARREGAMENTO DOS DADOS
# ==========================================
df_partidos = carregar_dados_partidarios()

if df_partidos.empty:
    st.warning("Nenhum dado partidário processado ainda. Aguarde o classificador finalizar alguns lotes.")
    st.stop()

# ==========================================
# 2. FILTROS LATERAIS EM CASCATA
# ==========================================
st.sidebar.header("🎯 Filtros de Análise")
df_filtrado = df_partidos.copy()

# Filtro 1: Proposta
propostas_disponiveis = ["Todas"] + sorted(df_filtrado['tema_proposta'].dropna().unique().tolist())
filtro_proposta = st.sidebar.selectbox("Foco em Proposta:", propostas_disponiveis)

if filtro_proposta != "Todas":
    df_filtrado = df_filtrado[df_filtrado['tema_proposta'] == filtro_proposta]

# Filtro 2: Partido
partidos_disponiveis = ["Todos"] + sorted(df_filtrado['partido'].dropna().unique().tolist())
filtro_partido = st.sidebar.selectbox("Foco Partidário:", partidos_disponiveis)
st.sidebar.caption("💡 Dica: Filtrar um partido altera a visão dos gráficos para seus Parlamentares.")

if filtro_partido != "Todos":
    df_filtrado = df_filtrado[df_filtrado['partido'] == filtro_partido]

# Filtro 3: Parlamentar 
politicos_disponiveis = ["Todos"] + sorted(df_filtrado['parlamentar'].dropna().unique().tolist())
filtro_politico = st.sidebar.selectbox("Isolar Parlamentar:", politicos_disponiveis)

if filtro_politico != "Todos":
    df_filtrado = df_filtrado[df_filtrado['parlamentar'] == filtro_politico]

if df_filtrado.empty:
    st.sidebar.warning("Nenhum dado encontrado para os filtros selecionados.")
    st.stop()

# ==========================================
# 3. MOTOR DE CÁLCULO E LÓGICA DE DRILL-DOWN
# ==========================================
# Dinâmica inteligente: Se filtrou Partido, compara Parlamentares. Se não, compara Partidos.
if filtro_partido != "Todos" and filtro_politico == "Todos":
    entidade_alvo = "parlamentar"
    nome_entidade = "Parlamentar"
else:
    entidade_alvo = "partido"
    nome_entidade = "Legenda"

# Agrupa e Pivotar os dados
df_agrupado = df_filtrado.groupby([entidade_alvo, 'classificacao_sentimento'])['total_comentarios'].sum().reset_index()
df_pivot = df_agrupado.pivot(index=entidade_alvo, columns='classificacao_sentimento', values='total_comentarios').fillna(0).reset_index()

# Garante que todas as colunas existem
colunas_sentimento = ["Apoio Total", "Apoio com Alteração", "Dúvida / Neutro", "Oposição com Remoção", "Rejeição Total"]
for col in colunas_sentimento:
    if col not in df_pivot.columns:
        df_pivot[col] = 0

# Calcula Volume Absoluto e Saldo
df_pivot['Volume Apoio'] = df_pivot['Apoio Total'] + df_pivot['Apoio com Alteração']
df_pivot['Volume Rejeição'] = df_pivot['Rejeição Total'] + df_pivot['Oposição com Remoção']
df_pivot['Volume Total'] = df_pivot[colunas_sentimento].sum(axis=1)

# Formula do Saldo de Imagem: Varia de -100 (Rejeição Total) a +100 (Apoio Total)
df_pivot['Saldo de Imagem'] = ((df_pivot['Volume Apoio'] - df_pivot['Volume Rejeição']) / df_pivot['Volume Total']) * 100

# ==========================================
# 4. KPIs ESTRATÉGICOS
# ==========================================
st.markdown(f"#### 📊 Diagnóstico de Risco e Aprovação ({nome_entidade}s)")
col_k1, col_k2, col_k3 = st.columns(3)

total_coments = df_pivot['Volume Total'].sum()
col_k1.metric("Volume de Impacto", f"{total_coments:,.0f}")

if not df_pivot.empty and total_coments > 0:
    # Remove entidades com volume quase nulo para não distorcer o destaque
    df_valido = df_pivot[df_pivot['Volume Total'] > (df_pivot['Volume Total'].max() * 0.05)]
    if df_valido.empty: 
        df_valido = df_pivot
        
    destaque = df_valido.loc[df_valido['Saldo de Imagem'].idxmax()]
    alerta = df_valido.loc[df_valido['Saldo de Imagem'].idxmin()]
    
    col_k2.metric(f"🌟 Destaque ({nome_entidade})", destaque[entidade_alvo], f"{destaque['Saldo de Imagem']:.1f} Pts de Saldo")
    col_k3.metric(f"⚠️ Alerta Crítico ({nome_entidade})", alerta[entidade_alvo], f"{alerta['Saldo de Imagem']:.1f} Pts de Saldo", delta_color="inverse")
else:
    col_k2.metric("🌟 Destaque Positivo", "N/A")
    col_k3.metric("⚠️ Alerta Crítico", "N/A")

st.divider()

# ==========================================
# 5. MATRIZ DE RISCO E RELEVÂNCIA (QUADRANTES)
# ==========================================
st.subheader(f"🎯 Matriz de Risco vs. Relevância por {nome_entidade}")
st.markdown("O Eixo X mostra o **Volume de Discussão**, enquanto o Eixo Y mostra o **Saldo de Imagem**. Atenção ao **Quadrante Inferior Direito**: alta visibilidade com saldo negativo.")

media_volume = df_pivot['Volume Total'].mean() if len(df_pivot) > 1 else df_pivot['Volume Total'].mean() * 0.5

fig_matriz = px.scatter(
    df_pivot, 
    x="Volume Total", 
    y="Saldo de Imagem", 
    text=entidade_alvo,
    size="Volume Total", # O tamanho da bolha reflete o volume
    color="Saldo de Imagem",
    color_continuous_scale="RdYlGn", # Escala Vermelho -> Verde
    range_y=[-105, 105], # Força o eixo Y de -100 a 100
    labels={"Volume Total": "Volume de Interações (Relevância)", "Saldo de Imagem": "Saldo de Aprovação (+/-)"},
    hover_data={entidade_alvo: True, 'Volume Apoio': True, 'Volume Rejeição': True}
)

# Adicionando as linhas cruzadas (Quadrantes)
fig_matriz.add_hline(y=0, line_dash="dash", line_color="#888888", annotation_text="Divisa Neutra")
if len(df_pivot) > 1:
    fig_matriz.add_vline(x=media_volume, line_dash="dash", line_color="#888888", annotation_text="Volume Médio")

fig_matriz.update_traces(textposition='top center', marker=dict(line=dict(width=1, color='Black')))
fig_matriz.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=500)

st.plotly_chart(fig_matriz, use_container_width=True)

st.divider()

# ==========================================
# 6. GRÁFICO DIVERGENTE (TORNADO CHART)
# ==========================================
st.subheader(f"🌪️ Polarização de Sentimento por {nome_entidade}")
st.markdown("Exibe o volume absoluto em eixos divergentes. Barras à direita (Verde) representam Apoio; à esquerda (Vermelho/Laranja/Cinza) representam Rejeição e Dúvida.")

df_tornado = df_agrupado.copy()

# Truque do Tornado: Multiplicar categorias negativas por -1
def ajustar_direcao(row):
    if row['classificacao_sentimento'] in ['Rejeição Total', 'Oposição com Remoção', 'Dúvida / Neutro']:
        return -row['total_comentarios']
    return row['total_comentarios']

df_tornado['impacto_direcional'] = df_tornado.apply(ajustar_direcao, axis=1)
df_tornado['volume_real'] = abs(df_tornado['impacto_direcional']) # Guarda o valor real para o tooltip

cores_map = {
    "Apoio Total": "#00C853",        
    "Apoio com Alteração": "#FFD600", 
    "Dúvida / Neutro": "#9E9E9E",     
    "Oposição com Remoção": "#FF6D00",
    "Rejeição Total": "#D50000"       
}

# Ordena o Eixo Y do Tornado baseado no Volume Total da tabela Pivot
ordem_y = df_pivot.sort_values(by='Volume Total', ascending=True)[entidade_alvo].tolist()

fig_tornado = px.bar(
    df_tornado, 
    x="impacto_direcional", 
    y=entidade_alvo, 
    color="classificacao_sentimento",
    color_discrete_map=cores_map,
    orientation='h',
    category_orders={entidade_alvo: ordem_y},
    hover_data={'volume_real': True, 'impacto_direcional': False},
    labels={'impacto_direcional': '← Rejeição | Apoio →', 'volume_real': 'Interações', entidade_alvo: ''}
)

fig_tornado.update_layout(
    barmode='relative', # Crucial: empilha mantendo a divergência no zero
    paper_bgcolor="rgba(0,0,0,0)", 
    plot_bgcolor="rgba(0,0,0,0)",
    hovermode="y unified"
)

# Adiciona a linha zero sólida
fig_tornado.add_vline(x=0, line_width=2, line_color="black")

st.plotly_chart(fig_tornado, use_container_width=True)

# 7. Tabela Auditoria Oculta
with st.expander("Ver Tabela Bruta (Auditoria)"):
    st.dataframe(df_pivot, use_container_width=True, hide_index=True)