import streamlit as st

# Configuração da Página
st.set_page_config(page_title="Civic Data Analytics", page_icon="📊", layout="wide")

# ==========================================
# 1. CABEÇALHO E BRANDING
# ==========================================
col1, col2 = st.columns([3, 1])
with col1:
    st.title("📊 Civic Data Analytics")
    st.markdown("#### Pipeline de NLP e Análise de Sentimento Político")
with col2:
    st.write("") # Espaçamento para alinhar
    st.markdown(
        "[![GitHub](https://img.shields.io/badge/GitHub-Acessar_Repositório-181717?style=for-the-badge&logo=github)](https://github.com/A-Capelini/Pipeline-NLP-Sentimento-Politico)"
    )

st.divider()

# ==========================================
# 2. SOBRE O PROJETO (ARQUITETURA)
# ==========================================
st.header("⚙️ Sobre o Projeto")
st.markdown("""
Este projeto é um portfólio completo de Engenharia e Ciência de Dados, demonstrando a construção de um pipeline analítico (ELT) de ponta a ponta. 

* **Geração de Dados:** Simulação de um ambiente cívico com milhares de interações, propostas legislativas e usuários.
* **Integração com IA (Google Gemini):** Utilização de Modelos de Linguagem Grande (LLM) para processamento de linguagem natural (NLP), classificando o sentimento e a intenção política de cada comentário.
* **Modelagem Relacional:** Ingestão estruturada dos dados tratados em um banco de dados MySQL, mantendo integridade referencial.
* **Data Visualization:** Este aplicativo consome views de Business Intelligence diretamente do banco, garantindo análises dinâmicas e interativas.
""")

st.markdown("#### 🛠️ Tech Stack")
st.markdown("`Python 3.10+` | `Streamlit` | `MySQL` | `Google Gemini API` | `Pandas` | `Plotly` | `SQLAlchemy`")

st.divider()

# ==========================================
# 3. GUIA DE NAVEGAÇÃO
# ==========================================
st.header("🧭 Guia de Navegação (O Funil Analítico)")
st.markdown("""
Navegue pelo menu lateral para explorar os dados, descendo do panorama macro até a análise individual de cada cidadão:

1. **Visão Geral:** KPIs globais da plataforma, distribuição de sentimentos e nuvem de palavras de oposição.
2. **Termômetro Partidário:** Cruzamento do sentimento dos eleitores direcionado a cada partido político.
3. **Geopolítica:** Mapa de calor e análise regional (como cada estado reage às propostas).
4. **Tendências:** Análise de série temporal (volume de interações ao longo do tempo).
5. **Análise Qualitativa:** Mergulho profundo nos textos dos comentários e suas respectivas classificações de IA.
6. **Simulador:** Motor de cruzamento de filtros múltiplos (Região > Estado > Partido > Parlamentar).
7. **Raio-X do Cidadão:** O nível micro. Ferramenta de CRM Cívico para perfilar cidadãos, gerar alertas de comportamento e obter sugestões prescritivas.
""")

st.divider()

# ==========================================
# 4. STATUS DO SISTEMA
# ==========================================
try:
    from utils.database import obter_engine
    engine = obter_engine()
    with engine.connect() as conn:
        st.success("✅ Conexão com o Banco de Dados (MySQL) e Views de BI operantes.")
except Exception as e:
    st.error(f"❌ Erro ao conectar com o banco de dados: {e}")