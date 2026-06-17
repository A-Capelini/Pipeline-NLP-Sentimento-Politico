# utils/database.py
import os
import pandas as pd
import mysql.connector
import streamlit as st
from dotenv import load_dotenv

# Carrega as variáveis se não estiverem na memória
load_dotenv()

@st.cache_data(ttl=600) # Mantém os dados em cache por 10 minutos
def carregar_dados_analiticos():
    """
    Conecta ao MySQL e extrai a View 'vw_dashboard_sentimento' inteira em um DataFrame Pandas.
    """
    try:
        conexao = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        
        query = "SELECT * FROM vw_dashboard_sentimento"
        # Usamos o Pandas para já trazer tudo formatado e pronto para o BI
        df = pd.read_sql(query, conexao)
        
        conexao.close()
        return df

    except Exception as e:
        st.error(f"Erro ao conectar ou extrair dados do Banco: {e}")
        return pd.DataFrame() # Retorna vazio em caso de falha