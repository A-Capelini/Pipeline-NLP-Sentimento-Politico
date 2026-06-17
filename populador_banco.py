import os
import json
import uuid
import random
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ---------------------------------------------------------
# 1. SETUP E CONFIGURAÇÕES
# ---------------------------------------------------------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("❌ ERRO: Chave da API do Gemini não encontrada no arquivo .env!")
    exit()

client = genai.Client(api_key=GEMINI_API_KEY)

# Modelo atual e veloz da família Gemini
GEMINI_MODEL = "gemini-2.5-flash"

def gerar_uuid():
    return str(uuid.uuid4())

def criar_conexao():
    try:
        conexao = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        return conexao
    except Error as e:
        print(f"❌ Erro ao conectar ao MySQL: {e}")
        return None

# ---------------------------------------------------------
# 2. FUNÇÕES DE BANCO DE DADOS E GERAÇÃO
# ---------------------------------------------------------
def preparar_banco_analitico(cursor):
    print("-> Criando tabela auxiliar de análise de sentimentos...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comment_analysis (
            comment_id CHAR(36) PRIMARY KEY,
            classificacao_sentimento VARCHAR(50) NOT NULL,
            analisado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_analysis_comment FOREIGN KEY (comment_id) REFERENCES comment(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)

def popular_dados_base(cursor):
    print("-> Populando dados geográficos e usuários base...")

    # Inserir País
    cursor.execute("INSERT IGNORE INTO country (id, name) VALUES (1, 'Brasil')")

    # Inserir Região
    cursor.execute("INSERT IGNORE INTO region (id, name) VALUES (1, 'Sudeste')")

    # Inserir Estado
    cursor.execute("INSERT IGNORE INTO state (id, name, acronym, region_id, country_id) VALUES (1, 'São Paulo', 'SP', 1, 1)")

    # Inserir Município
    cursor.execute("INSERT IGNORE INTO municipality (id, name, state_id) VALUES (1, 'São Paulo', 1)")

    # Inserir Categoria
    cat_id = gerar_uuid()
    cursor.execute("INSERT INTO category (id, name, description) VALUES (%s, %s, %s)",
                   (cat_id, 'Mobilidade Urbana', 'Propostas relacionadas a trânsito e transporte.'))

    # Inserir 5 Usuários Fictícios
    usuarios_ids = []
    nomes = ["Ana Silva", "Carlos Souza", "Beatriz Lima", "Fernando Costa", "Mariana Alves"]
    for nome in nomes:
        user_id = gerar_uuid()
        email = f"{nome.split()[0].lower()}@teste.com"
        cursor.execute("INSERT INTO app_user (id, email, name, verified) VALUES (%s, %s, %s, True)",
                       (user_id, email, nome))
        usuarios_ids.append(user_id)

    return cat_id, usuarios_ids

def criar_proposta(cursor, cat_id, user_id):
    print("-> Criando proposta legislativa...")
    prop_id = gerar_uuid()
    titulo = "Implementação de Pedágio Urbano no Centro"
    descricao = "Criação de uma taxa de R$ 5,00 para veículos particulares que circularem no centro comercial em horário de pico, visando reduzir o trânsito e financiar o transporte público."

    cursor.execute("""
        INSERT INTO proposal (id, title, description, category_id, user_id, municipality_id, status)
        VALUES (%s, %s, %s, %s, %s, 1, 'publicado')
    """, (prop_id, titulo, descricao, cat_id, user_id))

    return prop_id, titulo, descricao

def gerar_comentarios_gemini(titulo, descricao):
    print(f"-> Solicitando comentários sintéticos ao Google Gemini (modelo: {GEMINI_MODEL})...")
    prompt = f"""
    Você é um sistema de simulação cívica. Analise a seguinte proposta de lei:
    Título: {titulo}
    Descrição: {descricao}

    Gere exatamente 5 comentários de cidadãos fictícios. Cada comentário deve representar estritamente UMA das seguintes intenções:
    1. Apoio Total
    2. Apoio com Alteração
    3. Dúvida / Neutro
    4. Oposição com Remoção
    5. Rejeição Total

    Retorne um array JSON com os 5 objetos, cada um no formato:
    {{"intencao": "Apoio Total", "texto": "comentario aqui"}}
    """

    # Usamos response_mime_type="application/json" para forçar o Gemini a
    # retornar JSON puro, sem necessidade de remover blocos ```json manualmente.
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    texto_limpo = response.text.strip()
    return json.loads(texto_limpo)

def inserir_comentarios_e_votos(cursor, prop_id, usuarios_ids, dados_gemini):
    print("-> Inserindo comentários, classificações e simulando engajamento (Triggers)...")

    for i, item in enumerate(dados_gemini):
        comment_id = gerar_uuid()
        user_id = usuarios_ids[i]

        # Insere na tabela original comment
        cursor.execute("""
            INSERT INTO comment (id, proposal_id, user_id, body)
            VALUES (%s, %s, %s, %s)
        """, (comment_id, prop_id, user_id, item['texto']))

        # Insere a classificação na tabela auxiliar
        cursor.execute("""
            INSERT INTO comment_analysis (comment_id, classificacao_sentimento)
            VALUES (%s, %s)
        """, (comment_id, item['intencao']))

        # Simula votos (Upvotes e Downvotes aleatórios) para acionar o Trigger
        num_votos = random.randint(1, 4)
        votantes = random.sample(usuarios_ids, num_votos)
        for votante_id in votantes:
            voto_valor = random.choice([1, 1, 1, -1])  # Maior chance de upvote
            cursor.execute("""
                INSERT IGNORE INTO comment_vote (user_id, comment_id, vote_value)
                VALUES (%s, %s, %s)
            """, (votante_id, comment_id, voto_valor))

def criar_view_dashboard(cursor):
    print("-> Construindo a View Analítica (vw_dashboard_sentimento)...")
    cursor.execute("DROP VIEW IF EXISTS vw_dashboard_sentimento;")
    cursor.execute("""
        CREATE VIEW vw_dashboard_sentimento AS
        SELECT
            c.id AS id_comentario,
            p.title AS tema_proposta,
            c.body AS texto_comentario,
            ca.classificacao_sentimento,
            c.score AS score_engajamento
        FROM comment c
        INNER JOIN proposal p ON c.proposal_id = p.id
        INNER JOIN comment_analysis ca ON c.id = ca.comment_id;
    """)

# ---------------------------------------------------------
# 3. EXECUÇÃO PRINCIPAL (PIPELINE)
# ---------------------------------------------------------
if __name__ == "__main__":
    print("🚀 INICIANDO PIPELINE OPINATE...")
    conn = criar_conexao()

    if conn:
        try:
            cursor = conn.cursor()

            # 1. Preparar Banco
            preparar_banco_analitico(cursor)

            # 2. Gerar Base
            cat_id, usuarios_ids = popular_dados_base(cursor)
            prop_id, titulo, desc = criar_proposta(cursor, cat_id, usuarios_ids[0])

            # 3. IA Generativa
            comentarios_ia = gerar_comentarios_gemini(titulo, desc)

            # 4. Inserção e Triggers
            inserir_comentarios_e_votos(cursor, prop_id, usuarios_ids, comentarios_ia)

            # 5. View BI
            criar_view_dashboard(cursor)

            # Salvar tudo
            conn.commit()
            print("\n✅ SUCESSO! Banco de dados populado e preparado para o Streamlit.")

        except Exception as e:
            conn.rollback()
            print(f"\n❌ ERRO DURANTE A EXECUÇÃO: {e}")
        finally:
            cursor.close()
            conn.close()