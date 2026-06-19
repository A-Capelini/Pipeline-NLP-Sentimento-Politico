# pages/5_Analise_Qualitativa.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import networkx as nx
from collections import Counter
import re
from utils.database import carregar_dados_analiticos

st.set_page_config(page_title="Análise Qualitativa", page_icon="🧠", layout="wide")

st.title("🧠 Redes de Narrativa e N-Gramas")
st.markdown("Descubra os principais temas e conexões de palavras por trás dos sentimentos.")

# 1. Carregamento dos Dados
df = carregar_dados_analiticos()

if df.empty:
    st.warning("Nenhum dado encontrado.")
    st.stop()

st.divider()

# 2. Filtros Laterais
st.sidebar.header("Filtros de Narrativa")
temas_disponiveis = df['tema_proposta'].unique().tolist()
tema_selecionado = st.sidebar.selectbox("Filtrar por Proposta:", ["Todas"] + temas_disponiveis)

sentimentos_disponiveis = df['classificacao_sentimento'].unique().tolist()
sentimento_selecionado = st.sidebar.selectbox("Isolar Sentimento:", ["Todos"] + sentimentos_disponiveis)

# Aplicando Filtros
df_filtrado = df.copy()
if tema_selecionado != "Todas":
    df_filtrado = df_filtrado[df_filtrado['tema_proposta'] == tema_selecionado]
if sentimento_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['classificacao_sentimento'] == sentimento_selecionado]

textos = df_filtrado['texto_comentario'].dropna().tolist()

# 3. Processamento de Linguagem Natural (NLP) - Extração de Bigramas
stopwords_pt = {"um", "uma", "para", "é", "os", "as", "o", "a", "de", "do", "da", "em", "no", "na", "que", "se", "com", "por", "dos", "das", "não", "isso", "esse", "essa", "e", "ao", "vai", "lei", "como", "mas", "sua", "seu", "já", "mais"}

bigramas = []
frequencia_palavras = Counter()

for texto in textos:
    # Limpeza: minúsculas e apenas letras
    palavras = re.findall(r'\b[a-zà-ú]+\b', str(texto).lower())
    # Remove stopwords e palavras muito curtas
    palavras_limpas = [p for p in palavras if p not in stopwords_pt and len(p) > 2]
    
    # Contagem para o tamanho dos nós
    frequencia_palavras.update(palavras_limpas)
    
    # Criação dos pares (Bigramas)
    for i in range(len(palavras_limpas) - 1):
        # Ordena o par alfabeticamente para evitar duplicação (A-B ser diferente de B-A)
        par = tuple(sorted([palavras_limpas[i], palavras_limpas[i+1]]))
        bigramas.append(par)

# Pega os 40 pares mais comuns para não virar um emaranhado ilegível
top_bigramas = Counter(bigramas).most_common(40)

if not top_bigramas:
    st.info("Volume de texto insuficiente para gerar conexões nesta seleção.")
    st.stop()

# 4. Construção do Grafo (NetworkX)
G = nx.Graph()
for (w1, w2), peso in top_bigramas:
    G.add_edge(w1, w2, weight=peso)

# Layout de mola (força as conexões mais fortes para o centro)
pos = nx.spring_layout(G, k=0.8, iterations=50)

# 5. Preparando Plotly (Arestas/Linhas)
edge_x = []
edge_y = []
for edge in G.edges():
    x0, y0 = pos[edge[0]]
    x1, y1 = pos[edge[1]]
    edge_x.extend([x0, x1, None])
    edge_y.extend([y0, y1, None])

edge_trace = go.Scatter(
    x=edge_x, y=edge_y,
    line=dict(width=1.5, color='#888'),
    hoverinfo='none',
    mode='lines')

# Preparando Plotly (Nós/Bolinhas)
node_x = []
node_y = []
node_text = []
node_size = []

for node in G.nodes():
    x, y = pos[node]
    node_x.append(x)
    node_y.append(y)
    node_text.append(node)
    # Tamanho baseado na frequência da palavra (com um limite mínimo/máximo)
    tamanho = frequencia_palavras.get(node, 1) * 2
    node_size.append(min(max(tamanho, 15), 50)) 

node_trace = go.Scatter(
    x=node_x, y=node_y,
    mode='markers+text',
    text=node_text,
    textposition="top center",
    hoverinfo='text',
    marker=dict(
        showscale=False,
        colorscale='YlGnBu',
        reversescale=True,
        color=node_size,
        size=node_size,
        line_width=2))

fig = go.Figure(data=[edge_trace, node_trace],
             layout=go.Layout(
                showlegend=False,
                hovermode='closest',
                margin=dict(b=0,l=0,r=0,t=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                )

# 6. Renderização Final no Streamlit
col_grafo, col_tabela = st.columns([2, 1])

with col_grafo:
    st.subheader("Grafo de Coocorrência")
    st.plotly_chart(fig, use_container_width=True)

with col_tabela:
    st.subheader("Ranking de Bigramas")
    # Transformando os dados para um DataFrame bonito
    df_bigramas = pd.DataFrame([
        {"Termo 1": w1, "Termo 2": w2, "Frequência": peso} 
        for (w1, w2), peso in top_bigramas
    ])
    st.dataframe(df_bigramas, use_container_width=True, hide_index=True)