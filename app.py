# app.py
from pathlib import Path
import streamlit as st

# ---------------------------------------------------------
# 1. CONFIGURAÇÃO GLOBAL (Sempre o primeiro comando)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Opinate | Plataforma Cívica",
    page_icon="🗣️",
    layout="wide",  # Usa a tela inteira, ideal para BI
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# 2. CARREGAMENTO DE ESTILOS (CSS)
# ---------------------------------------------------------
CSS_PATH = Path(__file__).parent / "assets" / "style.css"

def load_css():
    try:
        # encoding="utf-8" evita problemas de caracteres no Windows
        css = CSS_PATH.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(
            f"Arquivo de estilo não encontrado em '{CSS_PATH}'. "
            "O app vai continuar com o tema padrão do Streamlit."
        )

load_css()

# ---------------------------------------------------------
# 3. CONTEÚDO PRINCIPAL (Home)
# ---------------------------------------------------------
st.title("Bem-vindo ao Opinate 🗣️")
st.markdown(
    """
    Esta é a área administrativa da **Plataforma Cívica**.
    
    Aqui você acompanha em tempo real o engajamento da população e a análise de 
    sentimento aplicada a milhares de comentários sobre propostas legislativas.
    """
)

st.divider() # Linha de separação visual

# ---------------------------------------------------------
# 4. HEALTH CHECK DO BANCO E NAVEGAÇÃO
# ---------------------------------------------------------
st.subheader("Status do Sistema")

# Testa a conexão com o banco de forma silenciosa
banco_online = False
try:
    from utils.database import carregar_dados_analiticos
    # Testa se a query funciona puxando apenas a primeira linha
    df_teste = carregar_dados_analiticos().head(1)
    banco_online = True
    st.success("✅ Banco de Dados conectado e operante! View carregada com sucesso.")
except Exception as e:
    st.error(f"❌ Erro ao conectar ao banco de dados. Verifique o seu arquivo .env ou o status do MySQL. Erro: {e}")

st.markdown("<br>", unsafe_allow_html=True) # Espaçamento

# Botões de navegação rápida
col1, col2 = st.columns(2)

with col1:
    st.info("📊 **Business Intelligence**")
    st.markdown("Visualize gráficos de sentimento, engajamento e nuvens de palavras baseadas em NLP.")
    
    # O botão só fica disponível se o banco estiver online
    if st.button("Acessar Dashboard", use_container_width=True, disabled=not banco_online):
        st.switch_page("pages/1_Dashboard.py")

with col2:
    st.warning("⚙️ **Pipeline de Dados**")
    st.markdown("A ingestão de novos dados (ELT) e a classificação via API do Gemini são feitas diretamente via terminal.")
    st.code("python 1_gerador_massa.py\npython 2_classificador_ia.py", language="bash")