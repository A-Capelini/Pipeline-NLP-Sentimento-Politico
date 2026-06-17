import os
import json
import time
from collections import deque

import mysql.connector
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ---------------------------------------------------------
# SETUP
# ---------------------------------------------------------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)
GEMINI_MODEL = "gemini-2.5-flash"

CATEGORIAS_VALIDAS = {
    "Apoio Total",
    "Apoio com Alteração",
    "Dúvida / Neutro",
    "Oposição com Remoção",
    "Rejeição Total",
}

TAMANHO_LOTE = 50          # quantos comentários enviamos por chamada ao Gemini
TAMANHO_PAGINA = 500       # quantos comentários buscamos do banco por vez (controle de memória)

# Limite de requisições por minuto do tier gratuito do Gemini 2.5 Flash.
# O valor publicado pelo Google costuma ser 10 RPM, mas ele muda sem aviso
# (já houve cortes de cota) e varia por projeto/região. Deixamos uma margem
# de segurança aqui (8 em vez de 10) e o ideal é confirmar o valor atual no
# painel do Google AI Studio antes de rodar em produção.
GEMINI_RPM_LIMITE = 8


class RateLimiter:
    """
    Garante que não excedemos um número máximo de requisições dentro de
    qualquer janela de 60 segundos (janela deslizante, não só "1 por minuto
    fixo"). Toda chamada à API — incluindo retries — deve passar por aqui
    antes de ser disparada, já que cada retry também consome cota de RPM.
    """

    def __init__(self, max_requisicoes_por_minuto):
        self.max_requisicoes = max_requisicoes_por_minuto
        self.timestamps = deque()

    def aguardar_se_necessario(self):
        agora = time.time()

        # Descarta da janela qualquer timestamp com mais de 60s
        while self.timestamps and agora - self.timestamps[0] > 60:
            self.timestamps.popleft()

        if len(self.timestamps) >= self.max_requisicoes:
            tempo_espera = 60 - (agora - self.timestamps[0]) + 0.5  # margem de segurança
            if tempo_espera > 0:
                print(f"   ⏱️ Limite de {self.max_requisicoes} requisições/minuto atingido. "
                      f"Aguardando {tempo_espera:.1f}s...")
                time.sleep(tempo_espera)

        self.timestamps.append(time.time())


rate_limiter = RateLimiter(GEMINI_RPM_LIMITE)


def criar_conexao():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )


def buscar_pendentes(conn, limite):
    """
    Busca comentários ainda não analisados.

    Usamos LEFT JOIN + IS NULL em vez de NOT IN (SELECT ...): se a coluna
    comment_analysis.comment_id tiver algum valor NULL, o NOT IN passaria a
    retornar zero linhas para a query inteira, travando o pipeline
    silenciosamente. O anti-join não tem esse problema.
    """
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT c.id, c.body AS texto
        FROM comment c
        LEFT JOIN comment_analysis ca ON ca.comment_id = c.id
        WHERE ca.comment_id IS NULL
        LIMIT %s
        """,
        (limite,),
    )
    resultado = cursor.fetchall()
    cursor.close()
    return resultado


def classificar_lote(comentarios, max_tentativas=3):
    prompt = f"""
    Classifique a intenção política dos seguintes comentários.
    Categorias permitidas EXATAMENTE como escritas:
    1. Apoio Total
    2. Apoio com Alteração
    3. Dúvida / Neutro
    4. Oposição com Remoção
    5. Rejeição Total

    Comentários (em formato JSON):
    {json.dumps(comentarios, ensure_ascii=False)}

    Retorne APENAS um array JSON com objetos contendo 'id' (o mesmo uuid recebido) e 'intencao'.
    """

    for tentativa in range(max_tentativas):
        # Respeita o RPM antes de QUALQUER chamada, inclusive retries —
        # um retry também é uma requisição nova e conta para a cota.
        rate_limiter.aguardar_se_necessario()

        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            return json.loads(response.text.strip())

        except json.JSONDecodeError as e:
            tempo_espera = (tentativa + 1) * 5
            print(f"   ⚠️ Resposta da IA não veio em JSON válido ({e}). "
                  f"Tentativa {tentativa + 1} de {max_tentativas}. Aguardando {tempo_espera}s...")
            time.sleep(tempo_espera)

        except Exception as e:
            erro_str = str(e)
            # Imprime o erro real para facilitar diagnóstico (429 de cota
            # esgotada vs 503 de instabilidade momentânea são causas
            # diferentes e merecem soluções diferentes).
            print(f"   🔍 Erro retornado pela API: {erro_str}")

            if "503" in erro_str or "UNAVAILABLE" in erro_str or "429" in erro_str:
                tempo_espera = (tentativa + 1) * 5
                print(f"   ⚠️ Servidor ocupado ou cota momentaneamente excedida. "
                      f"Tentativa {tentativa + 1} de {max_tentativas}. Aguardando {tempo_espera}s...")
                time.sleep(tempo_espera)
            else:
                # Erro não-transitório (ex: credencial inválida): aborta de vez
                raise e

    raise Exception("Falha ao classificar o lote após múltiplas tentativas.")


def validar_resultados(lote, resultados):
    """
    Garante que cada item devolvido pela IA:
    - é um dict com 'id' e 'intencao'
    - o 'id' realmente pertence ao lote enviado
    - a 'intencao' é uma das categorias permitidas
    """
    ids_lote = {c["id"] for c in lote}
    validos = []

    if not isinstance(resultados, list):
        print(f"   ⚠️ Resposta da IA não é uma lista, lote descartado: {resultados!r}")
        return validos

    for res in resultados:
        if not isinstance(res, dict):
            print(f"   ⚠️ Item ignorado (formato inesperado): {res!r}")
            continue

        id_item = res.get("id")
        intencao = res.get("intencao")

        if id_item not in ids_lote:
            print(f"   ⚠️ Item ignorado (id fora do lote): {res!r}")
            continue

        if intencao not in CATEGORIAS_VALIDAS:
            print(f"   ⚠️ Item ignorado (categoria inválida): {res!r}")
            continue

        validos.append((id_item, intencao))

    ids_recebidos = {item[0] for item in validos}
    faltantes = ids_lote - ids_recebidos
    if faltantes:
        print(f"   ⚠️ {len(faltantes)} comentário(s) do lote não vieram na resposta da IA "
              f"e ficarão pendentes para a próxima execução.")

    return validos


def salvar_resultados(conn, cursor, dados_validos):
    if not dados_validos:
        return

    cursor.executemany(
        """
        INSERT INTO comment_analysis (comment_id, classificacao_sentimento)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE classificacao_sentimento = VALUES(classificacao_sentimento)
        """,
        dados_validos,
    )
    conn.commit()


# ---------------------------------------------------------
# EXECUÇÃO DA FASE 2
# ---------------------------------------------------------
if __name__ == "__main__":
    print("🧠 INICIANDO FASE 2: MOTOR DE INTELIGÊNCIA ARTIFICIAL...")
    print(f"   (limite de RPM configurado: {GEMINI_RPM_LIMITE} requisições/minuto)")
    conn = criar_conexao()
    cursor = None
    lotes_com_falha = 0

    try:
        cursor = conn.cursor()
        numero_lote_global = 0

        while True:
            pagina = buscar_pendentes(conn, TAMANHO_PAGINA)
            if not pagina:
                break

            print(f"-> Página com {len(pagina)} comentário(s) pendente(s) carregada.")

            for i in range(0, len(pagina), TAMANHO_LOTE):
                lote = pagina[i:i + TAMANHO_LOTE]
                numero_lote_global += 1
                print(f"⏳ Processando lote {numero_lote_global} ({len(lote)} comentários)...")

                try:
                    resultados = classificar_lote(lote)
                    dados_validos = validar_resultados(lote, resultados)
                    salvar_resultados(conn, cursor, dados_validos)
                    print(f"   ✅ {len(dados_validos)} de {len(lote)} comentários salvos.")
                except Exception as e:
                    conn.rollback()
                    lotes_com_falha += 1
                    print(f"   ❌ Lote {numero_lote_global} falhou e será reprocessado em outra execução: {e}")
                    # Sem time.sleep(1) fixo aqui: o RateLimiter já garante o
                    # espaçamento correto entre requisições.

        if lotes_com_falha:
            print(f"\n⚠️ FASE 2 CONCLUÍDA COM RESSALVAS: {lotes_com_falha} lote(s) falharam "
                  f"e permanecem pendentes para uma nova execução.")
        else:
            print("\n✅ FASE 2 CONCLUÍDA! Todos os comentários foram classificados com sucesso.")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERRO FATAL DURANTE A CLASSIFICAÇÃO: {e}")

    finally:
        if cursor is not None:
            cursor.close()
        conn.close()