# pages/5_Analise_Qualitativa.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import networkx as nx
from collections import Counter
import re
from utils.database import carregar_dados_qualitativos

st.set_page_config(page_title="Análise Qualitativa", page_icon="🧠", layout="wide")

st.title("🧠 Redes de Narrativa e N-Gramas")
st.markdown("Descubra os principais temas e conexões de palavras por trás dos sentimentos expressos pela população.")

# ==========================================
# 1. GUIA DE LEITURA (ONBOARDING)
# ==========================================
with st.expander("📖 Como ler esta página e interpretar os dados?", expanded=False):
    st.markdown("""
    Esta tela utiliza Inteligência Artificial (Processamento de Linguagem Natural) para transformar milhares de comentários em mapas visuais fáceis de entender.
    
    *   **O Filtro em Cascata:** Use a barra lateral para afunilar sua pesquisa. Exemplo: Escolha um *Partido*, depois um *Parlamentar* desse partido, uma *Proposta* dele e, por fim, isole apenas os comentários de *Rejeição Total*.
    *   **Grafo de Coocorrência (O Mapa de Bolhas):** Mostra quais palavras são ditas juntas na mesma frase. 
        *   🟢 **Tamanho da Bolha:** Quanto maior, mais vezes a palavra foi escrita.
        *   ➖ **Linhas (Conexões):** Quanto mais grossa a linha entre duas palavras, mais forte é a relação entre elas na mente do eleitor (ex: "imposto" fortemente ligado a "abusivo").
    *   **Ranking de Bigramas (A Tabela):** Um "Bigrama" é um par de palavras. Esta tabela lista as duplas de palavras mais repetidas. É a melhor ferramenta para descobrir **slogans, narrativas de ataque ou jargões** que o público adotou.
    """)

# ==========================================
# 2. CARREGAMENTO DOS DADOS
# ==========================================
df_qualitativo = carregar_dados_qualitativos()

if df_qualitativo.empty:
    st.warning("Nenhum texto encontrado no banco de dados para análise.")
    st.stop()

# ==========================================
# 3. FILTROS LATERAIS (CASCATA DE 4 NÍVEIS)
# ==========================================
st.sidebar.header("🎯 Filtros de Narrativa")

# Nível 1: Partido
partidos_disp = ["Todos"] + sorted(df_qualitativo['partido'].dropna().unique().tolist())
filtro_partido = st.sidebar.selectbox("1. Foco Partidário:", partidos_disp)

df_temp1 = df_qualitativo[df_qualitativo['partido'] == filtro_partido] if filtro_partido != "Todos" else df_qualitativo.copy()

# Nível 2: Parlamentar
politicos_disp = ["Todos"] + sorted(df_temp1['parlamentar'].dropna().unique().tolist())
filtro_politico = st.sidebar.selectbox("2. Isolar Parlamentar:", politicos_disp)

df_temp2 = df_temp1[df_temp1['parlamentar'] == filtro_politico] if filtro_politico != "Todos" else df_temp1.copy()

# Nível 3: Proposta
propostas_disp = ["Todas"] + sorted(df_temp2['tema_proposta'].dropna().unique().tolist())
filtro_proposta = st.sidebar.selectbox("3. Filtrar por Proposta:", propostas_disp)

df_temp3 = df_temp2[df_temp2['tema_proposta'] == filtro_proposta] if filtro_proposta != "Todas" else df_temp2.copy()

# Nível 4: Sentimento
sentimentos_disp = ["Todos"] + sorted(df_temp3['classificacao_sentimento'].dropna().unique().tolist())
filtro_sentimento = st.sidebar.selectbox("4. Isolar Sentimento:", sentimentos_disp)

# DataFrame Final após todos os filtros
df_final = df_temp3[df_temp3['classificacao_sentimento'] == filtro_sentimento] if filtro_sentimento != "Todos" else df_temp3.copy()

if df_final.empty:
    st.sidebar.warning("Nenhum comentário encontrado com essa combinação de filtros.")
    st.stop()

# Informação de volume para o usuário saber a base da amostra
st.sidebar.divider()
st.sidebar.caption(f"Analisando **{len(df_final):,}** comentários com os filtros atuais.")

# ==========================================
# 4. PROCESSAMENTO DE NLP (N-Gramas)
# ==========================================
textos = df_final['texto_comentario'].dropna().tolist()

stopwords_pt = {"um", "uma", "para", "é", "os", "as", "o", "a", "de", "do", "da", "em", "no", "na", "que", "se", "com", "por", "dos", "das", "não", "isso", "esse", "essa", "e", "ao", "vai", "lei", "como", "mas", "sua", "seu", "já", "mais", "tem", "aos"}

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

# Pega os 40 pares mais comuns
top_bigramas = Counter(bigramas).most_common(40)

if not top_bigramas:
    st.info("Volume de texto ou variedade de palavras insuficiente para gerar conexões nesta seleção específica. Tente ampliar os filtros.")
    st.stop()

# ==========================================
# 5. CONSTRUÇÃO DO GRAFO (NetworkX)
# ==========================================
G = nx.Graph()
for (w1, w2), peso in top_bigramas:
    G.add_edge(w1, w2, weight=peso)

# Layout de mola (força as conexões mais fortes para o centro)
pos = nx.spring_layout(G, k=0.8, iterations=50)

# Preparando Plotly (Arestas/Linhas)
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
    # Tamanho baseado na frequência da palavra
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

# ==========================================
# 6. RENDERIZAÇÃO FINAL
# ==========================================
st.divider()

col_grafo, col_tabela = st.columns([6, 4])

with col_grafo:
    st.subheader("Grafo de Coocorrência")
    st.plotly_chart(fig, use_container_width=True)

with col_tabela:
    st.subheader("Ranking de Bigramas")
    # Transformando os dados para um DataFrame elegante
    df_bigramas = pd.DataFrame([
        {"Termo 1": w1, "Termo 2": w2, "Frequência": peso} 
        for (w1, w2), peso in top_bigramas
    ])
    st.dataframe(df_bigramas, use_container_width=True, hide_index=True)