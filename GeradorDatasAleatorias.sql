-- atualizar_datas_comentarios.sql
--
-- Distribui aleatoriamente a data de criação dos comentários já existentes
-- dentro dos últimos 30 dias, para que a página de Tendências (que usa
-- carregar_dados_temporais() em utils/database.py) tenha uma série
-- temporal real para analisar, em vez de todos os comentários concentrados
-- no mesmo instante em que o 1_gerador_massa.py rodou o INSERT em massa.
--
-- Rode este script direto no MySQL Workbench, conectado ao banco "dond".

USE dond;

-- -----------------------------------------------------------------
-- Passo 1 (opcional): conferir o estado atual antes de alterar nada.
-- -----------------------------------------------------------------
SELECT
    COUNT(*) AS total_comentarios,
    MIN(created_at) AS data_mais_antiga,
    MAX(created_at) AS data_mais_recente
FROM comment;

-- -----------------------------------------------------------------
-- Passo 2: aplica a randomização (últimos 30 dias, distribuição uniforme).
-- -----------------------------------------------------------------
-- Cada comentário recebe uma data/hora aleatória entre agora e até 30 dias
-- atrás. updated_at é setado para o MESMO valor de created_at dentro da
-- própria instrução (MySQL avalia o SET da esquerda para a direita, então
-- "updated_at = created_at" já pega o valor recém-calculado) — sem isso,
-- a cláusula ON UPDATE CURRENT_TIMESTAMP(6) da coluna updated_at faria ela
-- ficar travada no momento em que este script foi executado, em vez de
-- acompanhar a data simulada do comentário.
--
-- O MySQL Workbench, por padrão, bloqueia UPDATE/DELETE sem WHERE numa
-- coluna indexada (Safe Updates Mode / erro 1175) — como aqui é proposital
-- atualizar TODAS as linhas, desligamos essa proteção só para este
-- comando e religamos imediatamente depois.
SET SQL_SAFE_UPDATES = 0;

UPDATE comment
SET
    created_at = NOW(6)
        - INTERVAL FLOOR(RAND() * 30) DAY
        - INTERVAL FLOOR(RAND() * 24) HOUR
        - INTERVAL FLOOR(RAND() * 60) MINUTE
        - INTERVAL FLOOR(RAND() * 60) SECOND,
    updated_at = created_at;

SET SQL_SAFE_UPDATES = 1;

-- -----------------------------------------------------------------
-- Passo 3 (opcional): confirmar o resultado.
-- -----------------------------------------------------------------
SELECT
    COUNT(*) AS total_comentarios,
    MIN(created_at) AS data_mais_antiga,
    MAX(created_at) AS data_mais_recente
FROM comment;