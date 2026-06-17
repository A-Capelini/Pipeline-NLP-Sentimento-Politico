# app.py
import streamlit as st

# Configuração global da página (Deve ser SEMPRE o primeiro comando)
st.set_page_config(
    page_title="Opinate | Plataforma Cívica",
    page_icon="🗣️",
    layout="wide", # Usa a tela inteira, ideal para BI
    initial_sidebar_state="expanded"
)

# Injetar o CSS
def load_css():
    with open("assets/style.css") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css()

# Conteúdo da Página Principal (Home)
st.title("Bem-vindo ao Opinate 🗣️")
st.markdown("""
    Esta é a área administrativa da Plataforma Cívica. 
    
    👈 **Utilize o menu lateral** para navegar até os painéis de Business Intelligence e analisar o sentimento das propostas de lei.
""")