import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
from sqlalchemy import text

# Importa as funções do banco de dados
from utils.database import carregar_dados_analiticos, obter_engine

st.set_page_config(page_title="Visão Geral", page_icon="📈", layout="wide")

st.title("📈 Visão Geral: Panorama Macro")
st.markdown("Análise global de engajamento da população e distribuição de sentimentos.")

# ==========================================
# 1. FUNÇÕES DE CARREGAMENTO E CACHE
# ==========================================
df = carregar_dados_analiticos()

if df.empty:
    st.warning("Nenhum dado encontrado. Certifique-se de ter executado o pipeline de ingestão no banco de dados.")
    st.stop()

# ==========================================
# 2. FILTROS LATERAIS
# ==========================================
st.sidebar.header("🎯 Filtros de Análise")
df_filtrado = df.copy()

temas_disponiveis = ["Todas"] + sorted(df_filtrado['tema_proposta'].dropna().unique().tolist())
tema_selecionado = st.sidebar.selectbox("Proposta:", temas_disponiveis)

if tema_selecionado != "Todas":
    df_filtrado = df_filtrado[df_filtrado['tema_proposta'] == tema_selecionado]

# ==========================================
# 2.1. PARLAMENTARES E PARTIDOS ENVOLVIDOS NO FILTRO ATUAL
# ==========================================
@st.cache_data(ttl=3600)  # Faz cache por 1 hora; cada proposta selecionada gera sua própria entrada de cache
def obter_totais_filtrados(tema):
    """
    Conta parlamentares e partidos distintos REALMENTE envolvidos no
    filtro atual, via proposal_parliamentarian. Quando "Todas" está
    selecionado, retorna a base completa de parlamentares/partidos
    cadastrados na plataforma; quando uma proposta específica é
    escolhida, conta só quem está vinculado a ela.
    """
    engine = obter_engine()
    try:
        with engine.connect() as conn:
            if tema == "Todas":
                tot_parl = pd.read_sql("SELECT COUNT(*) as qtd FROM parliamentarian", conn).iloc[0]['qtd']
                tot_part = pd.read_sql(
                    "SELECT COUNT(DISTINCT party) as qtd FROM parliamentarian WHERE party IS NOT NULL",
                    conn
                ).iloc[0]['qtd']
            else:
                query = text("""
                    SELECT
                        COUNT(DISTINCT parl.id) AS qtd_parl,
                        COUNT(DISTINCT parl.party) AS qtd_part
                    FROM proposal p
                    INNER JOIN proposal_parliamentarian pp ON p.id = pp.proposal_id
                    INNER JOIN parliamentarian parl ON pp.parliamentarian_id = parl.id
                    WHERE p.title = :titulo
                """)
                resultado = pd.read_sql(query, conn, params={"titulo": tema})
                tot_parl = resultado.iloc[0]['qtd_parl']
                tot_part = resultado.iloc[0]['qtd_part']
        return tot_parl, tot_part
    except Exception as e:
        st.sidebar.warning(f"Aviso de DB: {e}")
        return 0, 0

total_parlamentares_db, total_partidos_db = obter_totais_filtrados(tema_selecionado)

# ==========================================
# 3. KPIs DE ESCALA (Volume de Dados)
# ==========================================
st.markdown("#### 📊 Dimensões da Plataforma")
col_vol1, col_vol2, col_vol3, col_vol4 = st.columns(4)

total_interacoes = len(df_filtrado)
total_propostas = df_filtrado['tema_proposta'].nunique()

col_vol1.metric("Interações Filtradas", f"{total_interacoes:,}".replace(",", "."))
col_vol2.metric("Propostas Envolvidas", total_propostas)
col_vol3.metric("Total Parlamentares (Plataforma)", total_parlamentares_db)
col_vol4.metric("Total Partidos (Plataforma)", total_partidos_db)

st.divider()

# ==========================================
# 4. MÉTRICAS DE SENTIMENTO (5 Níveis)
# ==========================================
st.markdown("#### 🌡️ Termômetro de Aprovação")
contagem = df_filtrado['classificacao_sentimento'].value_counts()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    qtd = contagem.get("Apoio Total", 0)
    st.metric("✅ Apoio Total", qtd, f"{(qtd/total_interacoes*100):.1f}%" if total_interacoes > 0 else "0%")
with col2:
    qtd = contagem.get("Apoio com Alteração", 0)
    st.metric("🟡 Apoio com Alter.", qtd, f"{(qtd/total_interacoes*100):.1f}%" if total_interacoes > 0 else "0%")
with col3:
    qtd = contagem.get("Dúvida / Neutro", 0)
    st.metric("⚪ Neutro", qtd, f"{(qtd/total_interacoes*100):.1f}%" if total_interacoes > 0 else "0%")
with col4:
    qtd = contagem.get("Oposição com Remoção", 0)
    st.metric("🟠 Oposição Parcial", qtd, f"{(qtd/total_interacoes*100):.1f}%" if total_interacoes > 0 else "0%")
with col5:
    qtd = contagem.get("Rejeição Total", 0)
    st.metric("🔴 Rejeição Total", qtd, f"{(qtd/total_interacoes*100):.1f}%" if total_interacoes > 0 else "0%")

st.divider()

# ==========================================
# 5. GRÁFICOS E TABELAS DE PROFUNDIDADE
# ==========================================
col_grafico, col_top = st.columns([1, 1])

with col_grafico:
    st.subheader("Distribuição Geral")
    
    cores_map = {
        "Apoio Total": "#00C853",        
        "Apoio com Alteração": "#FFD600", 
        "Dúvida / Neutro": "#9E9E9E",     
        "Oposição com Remoção": "#FF6D00",
        "Rejeição Total": "#D50000"       
    }

    fig = px.pie(
        df_filtrado, 
        names='classificacao_sentimento', 
        color='classificacao_sentimento', 
        color_discrete_map=cores_map,     
        hole=0.4 
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=20, l=20, r=20),
        showlegend=True
    )
    st.plotly_chart(fig, use_container_width=True)

with col_top:
    st.subheader("Top Sugestões (Maior Engajamento)")
    df_sugestoes = df_filtrado[df_filtrado['classificacao_sentimento'].isin(['Apoio com Alteração', 'Oposição com Remoção'])]
    df_sugestoes = df_sugestoes.sort_values(by='score_engajamento', ascending=False)
    
    st.dataframe(
        df_sugestoes[['classificacao_sentimento', 'score_engajamento', 'texto_comentario']],
        hide_index=True,
        use_container_width=True
    )

st.divider()

# ==========================================
# 6. NUVEM DE PALAVRAS E NLP INSIGHTS
# ==========================================
st.subheader("Nuvem de Palavras - Extração de Dores (Oposição)")

col_texto_nuvem, col_img_nuvem = st.columns([1, 2])

with col_texto_nuvem:
    st.info("""
    **💡 Como interpretar este visual?**
    
    Esta Nuvem de Palavras utiliza técnicas de **Processamento de Linguagem Natural (NLP)** para extrair os termos mais frequentes exclusivamente dos comentários classificados como **"Rejeição Total"**.
    
    * **Objetivo:** Identificar rapidamente a raiz da insatisfação popular.
    * **Ação:** Termos em destaque indicam os principais focos de atrito das propostas, permitindo que a gestão prepare respostas direcionadas ou ajuste os textos legislativos.
    """)

with col_img_nuvem:
    textos_oposicao = " ".join(df_filtrado[df_filtrado['classificacao_sentimento'] == 'Rejeição Total']['texto_comentario'].dropna().tolist())

    if textos_oposicao.strip():
        stopwords_pt = set(STOPWORDS)
        stopwords_pt.update(["um", "uma", "para", "é", "os", "as", "o", "a", "de", "do", "da", "em", "no", "na", "que", "se", "com", "por", "dos", "das", "não", "isso", "esse", "essa", "e", "ao", "vai", "lei", "projeto", "sobre"])

        wordcloud = WordCloud(
            width=800, 
            height=400, 
            background_color='#1E1E2E', 
            colormap='Reds',
            stopwords=stopwords_pt 
        ).generate(textos_oposicao)
        
        fig_wc, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        fig_wc.patch.set_facecolor('#1E1E2E')
        st.pyplot(fig_wc)
    else:
        st.warning("Nenhum comentário de Rejeição Total encontrado com os filtros atuais para gerar a nuvem.")