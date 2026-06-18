# utils/database.py
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

load_dotenv()


@st.cache_resource
def obter_engine():
    """
    Cria a engine SQLAlchemy de conexão com o MySQL.

    Usamos URL.create() em vez de montar a string de conexão manualmente
    (ex: f"mysql+mysqlconnector://{user}:{senha}@{host}/{db}") porque essa
    abordagem manual quebra silenciosamente se a senha tiver caracteres
    especiais como @, : ou / — URL.create() escapa tudo corretamente.

    Cacheada com @st.cache_resource (e não @st.cache_data) porque a engine
    não é um objeto serializável: ela representa um pool de conexões vivo,
    não um dado.
    """
    url = URL.create(
        drivername="mysql+mysqlconnector",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
    )
    return create_engine(url)


@st.cache_data(ttl=600)  # Evita reconectar/reconsultar o banco a cada interação do usuário
def carregar_dados_analiticos():
    """
    Extrai a view 'vw_dashboard_sentimento' inteira em um DataFrame Pandas,
    pronto para o dashboard.
    """
    try:
        engine = obter_engine()
        query = "SELECT * FROM vw_dashboard_sentimento"

        # pd.read_sql com uma engine SQLAlchemy é o caminho oficialmente
        # suportado pelo pandas - não gera mais o UserWarning que tínhamos
        # com mysql.connector puro, então não precisamos suprimir nada.
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)

        return df

    except Exception as e:
        st.error(f"Erro ao conectar ou extrair dados do banco: {e}")
        return pd.DataFrame()
