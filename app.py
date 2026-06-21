import streamlit as st

# ==========================================
# CONFIGURAÇÃO GERAL DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Civic Data Analytics", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# BARRA LATERAL (SIDEBAR) - CONTEXTO ACADÊMICO
# ==========================================
with st.sidebar:
    st.markdown("### 🎓 Contexto Acadêmico")
    st.markdown("**Instituição:** Fatec Cotia")
    st.markdown("**Curso:** Ciência de Dados")
    st.markdown("**Disciplina:** Projeto Integrado III")
    st.markdown("**Professor:** Rômulo Francisco de Souza Maia")
    
    st.divider()
    
    # ---------------------------------------------------------
    # ATENÇÃO: APAGAR ESTE BLOCO APÓS A APRESENTAÇÃO 
    # PARA DEIXAR COMO PORTFÓLIO INDIVIDUAL
    st.markdown("### 👥 Equipe do Projeto")
    st.markdown("""
    * Anderson Capelini Andrade
    * Marcelo Ramos
    * Moisés Germano Leite
    * Victor Henrique
    * Vitor Hugo Santos
    """)
    # ---------------------------------------------------------
    
    st.divider()
    st.info("ℹ️ Este painel consome dados em tempo real do banco de dados em nuvem.")

# ==========================================
# 1. CABEÇALHO E BRANDING
# ==========================================
col1, col2 = st.columns([3, 1])
with col1:
    st.title("📊 Civic Data Analytics")
    st.markdown("#### Pipeline Completo de Engenharia de Dados, NLP e BI")
with col2:
    st.write("") # Espaçamento para alinhar
    st.markdown(
        "[![GitHub](https://img.shields.io/badge/GitHub-Acessar_Repositório-181717?style=for-the-badge&logo=github)](https://github.com/A-Capelini/Pipeline-NLP-Sentimento-Politico)"
    )
    st.markdown(
        "[![Streamlit](https://img.shields.io/badge/Streamlit-App_Online-FF4B4B?style=for-the-badge&logo=streamlit)](https://sentimento-politico.streamlit.app/)"
    )

st.divider()

# ==========================================
# 2. SOBRE O PROJETO (ARQUITETURA DE NEGÓCIO)
# ==========================================
st.header("⚙️ Visão Geral do Sistema")
st.markdown("""
Este projeto é um portfólio avançado de Ciência de Dados que demonstra a construção de um pipeline analítico (ELT) de ponta a ponta. O objetivo é simular um ambiente cívico e capturar o sentimento da população em relação a propostas políticas.

* **Geração e Simulação de Dados:** Criação de um ecossistema com milhares de interações, propostas legislativas e cidadãos com perfis variados.
* **Inteligência Artificial (Google Gemini):** Utilização de Modelos de Linguagem Grande (LLMs) para Processamento de Linguagem Natural (NLP) em modo *Zero-Shot*, classificando o sentimento (Positivo, Negativo, Neutro) e a intenção de cada texto.
* **Modelagem Relacional (Views de BI):** O aplicativo consome os dados diretamente através de *views* especializadas criadas no banco de dados, garantindo performance e integridade na camada de Business Intelligence.
""")

# ==========================================
# 3. INFRAESTRUTURA CLOUD & CI/CD (NOVIDADE)
# ==========================================
st.header("☁️ Infraestrutura e Deploy")
st.markdown("""
O ciclo de vida dos dados foi estruturado com foco em escalabilidade, migrando de um ambiente de desenvolvimento local para uma arquitetura em nuvem:

* **Ambiente de Desenvolvimento:** Modelagem e testes iniciais realizados via **MySQL Local** (`localhost`).
* **Banco de Dados em Produção (Aiven):** O schema e os dados processados foram migrados para um servidor em nuvem gerenciado pela **Aiven.io**.
    * **Cloud Provider:** DigitalOcean (Região SFO - California, EUA).
    * **Instância:** Virtual Machine com 1 vCPU, 1 GB de RAM e 1 GB de Storage.
* **Integração e Entrega Contínuas (CI/CD):** Deploy do frontend interativo realizado no **Streamlit Cloud**, com integração direta à branch `main` do repositório no GitHub para atualizações automáticas.
""")

# ==========================================
# 4. TECH STACK (CATEGORIZADO)
# ==========================================
st.header("🛠️ Stack Tecnológico")
col_t1, col_t2, col_t3 = st.columns(3)

with col_t1:
    st.markdown("**Engenharia de Dados & BD**")
    st.markdown("`MySQL` `SQLAlchemy` `PyMySQL`")

with col_t2:
    st.markdown("**Inteligência Artificial & NLP**")
    st.markdown("`Google Gemini API` `N-Gramas`")

with col_t3:
    st.markdown("**Visualização & Frontend**")
    st.markdown("`Streamlit` `Pandas` `Plotly` `WordCloud`")

st.divider()

# ==========================================
# 5. GUIA DE NAVEGAÇÃO
# ==========================================
st.header("🧭 O Funil Analítico")
st.markdown("""
Utilize o menu lateral para explorar os dados, navegando do panorama macro até a análise individual de cada cidadão:

1. **Visão Geral:** KPIs globais da plataforma e nuvens de palavras de oposição/apoio.
2. **Termômetro Partidário:** Cruzamento do sentimento dos eleitores direcionado aos partidos.
3. **Geopolítica:** Mapa de calor indicando como cada estado reage às propostas.
4. **Tendências:** Série temporal demonstrando o volume e sentimento das interações ao longo do tempo.
5. **Análise Qualitativa:** Mergulho profundo nos comentários e auditoria das classificações da IA.
6. **Simulador:** Motor de busca e cruzamento de filtros múltiplos.
7. **Raio-X do Cidadão:** Ferramenta de CRM Cívico para perfilar usuários e gerar alertas de comportamento.
""")

st.divider()

# ==========================================
# 6. STATUS DO SISTEMA E CONEXÃO
# ==========================================
try:
    from utils.database import obter_engine
    engine = obter_engine()
    with engine.connect() as conn:
        st.success("✅ Sistema Operacional. Conexão com o Banco de Dados Nuvem (Aiven/MySQL) e Views de BI estabelecida com sucesso.")
except Exception as e:
    st.error(f"❌ Erro crítico de infraestrutura. Não foi possível conectar ao banco de dados: {e}")