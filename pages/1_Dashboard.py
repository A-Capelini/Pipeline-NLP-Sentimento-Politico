# pages/1_Dashboard.py
import streamlit as st
import plotly.express as px
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt

# Importa a função que criamos na pasta utils
from utils.database import carregar_dados_analiticos

st.title("📊 Painel de Sentimentos e Nuances")
st.markdown("5 níveis de opinião — Metodologia Opinate")

# 1. Carregamento dos Dados
df = carregar_dados_analiticos()

if df.empty:
    st.warning("Nenhum dado encontrado. Certifique-se de ter rodado o populador_banco.py.")
    st.stop()

# 2. Filtros Laterais
st.sidebar.header("Filtros")
temas_disponiveis = df['tema_proposta'].unique().tolist()
tema_selecionado = st.sidebar.selectbox("Filtrar por Proposta:", ["Todas"] + temas_disponiveis)

# Aplicando o filtro no DataFrame
if tema_selecionado != "Todas":
    df_filtrado = df[df['tema_proposta'] == tema_selecionado]
else:
    df_filtrado = df

# 3. Métricas (Os 5 níveis da imagem)
contagem = df_filtrado['classificacao_sentimento'].value_counts()
total = len(df_filtrado)

# Criando 5 colunas para os Cards
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    qtd = contagem.get("Apoio Total", 0)
    st.metric("✅ Apoio Total", qtd, f"{(qtd/total*100):.1f}%" if total > 0 else "0%")
with col2:
    qtd = contagem.get("Apoio com Alteração", 0)
    st.metric("🟡 Apoio com Alter.", qtd, f"{(qtd/total*100):.1f}%" if total > 0 else "0%")
with col3:
    qtd = contagem.get("Dúvida / Neutro", 0)
    st.metric("⚪ Neutro", qtd, f"{(qtd/total*100):.1f}%" if total > 0 else "0%")
with col4:
    qtd = contagem.get("Oposição com Remoção", 0)
    st.metric("🟠 Oposição Parcial", qtd, f"{(qtd/total*100):.1f}%" if total > 0 else "0%")
with col5:
    qtd = contagem.get("Rejeição Total", 0)
    st.metric("🔴 Rejeição Total", qtd, f"{(qtd/total*100):.1f}%" if total > 0 else "0%")

st.divider() # Linha de separação

# 4. Gráficos de Visualização Profunda
col_grafico, col_top = st.columns([1, 1])

with col_grafico:
    st.subheader("Distribuição Geral")
    
    # Criamos um dicionário travando cada categoria na sua respectiva cor hexadecimal
    cores_map = {
        "Apoio Total": "#00C853",        
        "Apoio com Alteração": "#FFD600", 
        "Dúvida / Neutro": "#9E9E9E",     
        "Oposição com Remoção": "#FF6D00",
        "Rejeição Total": "#D50000"       
    }

    # Atualizamos o gráfico para usar esse mapeamento
    fig = px.pie(
        df_filtrado, 
        names='classificacao_sentimento', 
        color='classificacao_sentimento', # Avisa o Plotly qual coluna define a cor
        color_discrete_map=cores_map,     # Aplica a nossa regra exata
        hole=0.4 # Isso transforma o gráfico de pizza em um gráfico de Rosca (Donut)
    )
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

with col_top:
    st.subheader("Top Sugestões (Maior Engajamento)")
    # Filtra apenas os comentários construtivos e ordena pelo maior Score
    df_sugestoes = df_filtrado[df_filtrado['classificacao_sentimento'].isin(['Apoio com Alteração', 'Oposição com Remoção'])]
    df_sugestoes = df_sugestoes.sort_values(by='score_engajamento', ascending=False)
    
    st.dataframe(
        df_sugestoes[['classificacao_sentimento', 'score_engajamento', 'texto_comentario']],
        hide_index=True,
        use_container_width=True
    )

# 5. Nuvem de Palavras
st.subheader("Nuvem de Palavras - Oposição")
textos_oposicao = " ".join(df_filtrado[df_filtrado['classificacao_sentimento'] == 'Rejeição Total']['texto_comentario'].tolist())

if textos_oposicao:
    # Criando uma lista de palavras para ignorar no português
    stopwords_pt = set(STOPWORDS)
    stopwords_pt.update(["um", "uma", "para", "é", "os", "as", "o", "a", "de", "do", "da", "em", "no", "na", "que", "se", "com", "por", "dos", "das", "não", "isso", "esse", "essa", "e", "ao", "vai", "lei"])

    wordcloud = WordCloud(
        width=800, 
        height=400, 
        background_color='#1E1E2E', 
        colormap='Reds',
        stopwords=stopwords_pt # Aplicando o filtro aqui!
    ).generate(textos_oposicao)
    
    fig_wc, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    fig_wc.patch.set_facecolor('#1E1E2E')
    st.pyplot(fig_wc)
else:
    st.info("Nenhum comentário de Rejeição Total para gerar nuvem de palavras neste tema.")