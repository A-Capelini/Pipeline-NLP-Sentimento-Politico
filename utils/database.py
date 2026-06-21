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
        port=os.getenv("DB_PORT", 3306), # ADICIONE ESTA LINHA
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
    direcionado a cada partido político e parlamentar.
    """
    try:
        engine = obter_engine()
        query = """
            SELECT 
                parl.party AS partido,
                parl.name AS parlamentar,
                p.title AS tema_proposta,
                ca.classificacao_sentimento,
                COUNT(c.id) AS total_comentarios
            FROM proposal p
            INNER JOIN proposal_parliamentarian pp ON p.id = pp.proposal_id
            INNER JOIN parliamentarian parl ON pp.parliamentarian_id = parl.id
            INNER JOIN comment c ON p.id = c.proposal_id
            INNER JOIN comment_analysis ca ON c.id = ca.comment_id
            GROUP BY parl.party, parl.name, p.title, ca.classificacao_sentimento
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
    com o partido político, o parlamentar, a proposta e o sentimento do comentário.
    """
    try:
        engine = obter_engine()
        query = """
            SELECT 
                parl.party AS partido,
                parl.name AS parlamentar,
                p.title AS tema_proposta,
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
            GROUP BY parl.party, parl.name, p.title, r.name, s.name, s.acronym, ca.classificacao_sentimento
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
    
@st.cache_data(ttl=600)
def carregar_dados_cidadao():
    """
    Traz o histórico de comentários mascarando o ID do usuário (LGPD),
    cruzando com a cidade da proposta para descobrir a 'Zona de Interesse'.
    """
    try:
        engine = obter_engine()
        query = """
            SELECT 
                UPPER(SUBSTRING(c.user_id, 1, 8)) AS cidadao_anonimo,
                p.title AS tema_proposta,
                m.name AS cidade,
                s.acronym AS uf,
                ca.classificacao_sentimento,
                c.score AS engajamento_recebido,
                c.body AS texto_comentario,
                c.created_at AS data_comentario
            FROM comment c
            INNER JOIN comment_analysis ca ON c.id = ca.comment_id
            INNER JOIN proposal p ON c.proposal_id = p.id
            INNER JOIN municipality m ON p.municipality_id = m.id
            INNER JOIN state s ON m.state_id = s.id
            ORDER BY c.created_at DESC
        """
        with engine.connect() as conn:
            return pd.read_sql(query, conn)
    except Exception as e:
        st.error(f"Erro ao carregar dados do cidadão: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def carregar_dados_cidadao_avancado():
    """
    Traz o histórico completo, mascarando o ID do usuário (LGPD),
    cruzando com a cidade, político (parliamentarian) e partido da proposta.
    """
    try:
        engine = obter_engine()
        query = """
            SELECT 
                UPPER(SUBSTRING(c.user_id, 1, 8)) AS cidadao_anonimo,
                p.title AS tema_proposta,
                m.name AS cidade,
                s.acronym AS uf,
                ca.classificacao_sentimento,
                c.score AS engajamento_recebido,
                c.body AS texto_comentario,
                c.created_at AS data_comentario,
                parl.name AS nome_politico,
                parl.party AS sigla_partido
            FROM comment c
            INNER JOIN comment_analysis ca ON c.id = ca.comment_id
            INNER JOIN proposal p ON c.proposal_id = p.id
            INNER JOIN proposal_parliamentarian pp ON p.id = pp.proposal_id
            INNER JOIN parliamentarian parl ON pp.parliamentarian_id = parl.id
            INNER JOIN municipality m ON p.municipality_id = m.id
            INNER JOIN state s ON m.state_id = s.id
            ORDER BY c.created_at DESC
        """
        with engine.connect() as conn:
            return pd.read_sql(query, conn)
    except Exception as e:
        st.error(f"Erro ao carregar dados do cidadão: {e}")
        return pd.DataFrame()
    
@st.cache_data(ttl=600)
def carregar_dados_tendencias():
    """
    Extrai a linha do tempo do sentimento cruzada com propostas e parlamentares
    para alimentar o radar de tendências.
    """
    try:
        engine = obter_engine()
        
        query = """
            SELECT 
                DATE(c.created_at) AS data,
                p.title AS tema_proposta,
                parl.party AS partido,
                parl.name AS parlamentar,
                ca.classificacao_sentimento,
                COUNT(c.id) AS total_comentarios
            FROM comment c
            INNER JOIN proposal p ON c.proposal_id = p.id
            INNER JOIN comment_analysis ca ON c.id = ca.comment_id
            INNER JOIN proposal_parliamentarian pp ON p.id = pp.proposal_id
            INNER JOIN parliamentarian parl ON pp.parliamentarian_id = parl.id
            GROUP BY DATE(c.created_at), p.title, parl.party, parl.name, ca.classificacao_sentimento
            ORDER BY data ASC
        """

        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        
        # Converte a coluna para o tipo datetime real do Pandas
        df['data'] = pd.to_datetime(df['data'])
        return df

    except Exception as e:
        st.error(f"Erro ao extrair dados de tendências: {e}")
        return pd.DataFrame()
    
@st.cache_data(ttl=600)
def carregar_dados_qualitativos():
    """
    Extrai os textos dos comentários cruzados com a hierarquia política
    para alimentar a análise de N-Gramas e Redes.
    """
    try:
        engine = obter_engine()
        
        query = """
            SELECT 
                c.body AS texto_comentario,
                p.title AS tema_proposta,
                parl.party AS partido,
                parl.name AS parlamentar,
                ca.classificacao_sentimento
            FROM comment c
            INNER JOIN proposal p ON c.proposal_id = p.id
            INNER JOIN comment_analysis ca ON c.id = ca.comment_id
            INNER JOIN proposal_parliamentarian pp ON p.id = pp.proposal_id
            INNER JOIN parliamentarian parl ON pp.parliamentarian_id = parl.id
            WHERE c.body IS NOT NULL AND c.body != ''
        """

        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
            
        return df

    except Exception as e:
        st.error(f"Erro ao extrair dados qualitativos: {e}")
        return pd.DataFrame()