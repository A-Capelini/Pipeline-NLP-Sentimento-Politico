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
    """
    url = URL.create(
        drivername="mysql+mysqlconnector",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
    )
    return create_engine(url)


@st.cache_data(ttl=600)  
def carregar_dados_analiticos():
    """
    Extrai a view 'vw_dashboard_sentimento' inteira em um DataFrame Pandas.
    """
    try:
        engine = obter_engine()
        query = "SELECT * FROM vw_dashboard_sentimento"

        with engine.connect() as conn:
            df = pd.read_sql(query, conn)

        return df

    except Exception as e:
        st.error(f"Erro ao conectar ou extrair dados do banco: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=600)
def carregar_dados_partidarios():
    """
    Cruza comentários, propostas e parlamentares para extrair o sentimento
    direcionado a cada partido político.
    """
    try:
        engine = obter_engine()
        # Query que faz o caminho completo: Comentário -> Proposta -> Relação Parlamentar -> Parlamentar
        query = """
            SELECT 
                parl.party AS partido,
                p.title AS tema_proposta,
                ca.classificacao_sentimento,
                COUNT(c.id) AS total_comentarios
            FROM proposal p
            INNER JOIN proposal_parliamentarian pp ON p.id = pp.proposal_id
            INNER JOIN parliamentarian parl ON pp.parliamentarian_id = parl.id
            INNER JOIN comment c ON p.id = c.proposal_id
            INNER JOIN comment_analysis ca ON c.id = ca.comment_id
            GROUP BY parl.party, p.title, ca.classificacao_sentimento
        """

        with engine.connect() as conn:
            df = pd.read_sql(query, conn)

        return df

    except Exception as e:
        st.error(f"Erro ao extrair dados partidários: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def carregar_dados_geopoliticos():
    """
    Cruza a localização geográfica da proposta (Região e Estado) 
    com o partido político e o sentimento do comentário.
    """
    try:
        engine = obter_engine()
        query = """
            SELECT 
                parl.party AS partido,
                r.name AS regiao,
                s.name AS estado,
                s.acronym AS uf,
                ca.classificacao_sentimento,
                COUNT(c.id) AS total_comentarios
            FROM comment c
            INNER JOIN comment_analysis ca ON c.id = ca.comment_id
            INNER JOIN proposal p ON c.proposal_id = p.id
            INNER JOIN proposal_parliamentarian pp ON p.id = pp.proposal_id
            INNER JOIN parliamentarian parl ON pp.parliamentarian_id = parl.id
            INNER JOIN municipality m ON p.municipality_id = m.id
            INNER JOIN state s ON m.state_id = s.id
            INNER JOIN region r ON s.region_id = r.id
            GROUP BY parl.party, r.name, s.name, s.acronym, ca.classificacao_sentimento
        """

        with engine.connect() as conn:
            df = pd.read_sql(query, conn)

        return df

    except Exception as e:
        st.error(f"Erro ao extrair dados geopolíticos: {e}")
        return pd.DataFrame()
    
@st.cache_data(ttl=600)
def carregar_dados_temporais():
    """
    Busca o volume de sentimentos por dia.
    """
    try:
        engine = obter_engine()
        # Nota: Ajuste 'created_at' se o seu campo de data tiver outro nome
        query = """
            SELECT 
                DATE(c.created_at) as data,
                ca.classificacao_sentimento,
                COUNT(c.id) as total
            FROM comment c
            INNER JOIN comment_analysis ca ON c.id = ca.comment_id
            GROUP BY DATE(c.created_at), ca.classificacao_sentimento
            ORDER BY data ASC
        """
        with engine.connect() as conn:
            return pd.read_sql(query, conn)
    except Exception as e:
        st.error(f"Erro ao carregar dados temporais: {e}")
        return pd.DataFrame()
    
@st.cache_data(ttl=600)
def carregar_dados_simulador():
    """
    Cruza dados geográficos, políticos e de propostas para alimentar 
    os filtros em cascata do simulador de cenários.
    """
    try:
        engine = obter_engine()
        query = """
            SELECT 
                r.name AS regiao,
                s.name AS estado,
                parl.party AS partido,
                parl.name AS parlamentar,
                p.title AS tema_proposta,
                ca.classificacao_sentimento,
                COUNT(c.id) AS total_comentarios
            FROM comment c
            INNER JOIN comment_analysis ca ON c.id = ca.comment_id
            INNER JOIN proposal p ON c.proposal_id = p.id
            INNER JOIN proposal_parliamentarian pp ON p.id = pp.proposal_id
            INNER JOIN parliamentarian parl ON pp.parliamentarian_id = parl.id
            INNER JOIN municipality m ON p.municipality_id = m.id
            INNER JOIN state s ON m.state_id = s.id
            INNER JOIN region r ON s.region_id = r.id
            GROUP BY r.name, s.name, parl.party, parl.name, p.title, ca.classificacao_sentimento
        """
        with engine.connect() as conn:
            return pd.read_sql(query, conn)
    except Exception as e:
        st.error(f"Erro ao carregar dados do simulador: {e}")
        return pd.DataFrame()