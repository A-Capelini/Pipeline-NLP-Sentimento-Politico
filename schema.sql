-- schema.sql
-- Versão para MySQL 8+
-- Encoding: UTF8MB4
--
-- Schema consolidado do projeto Opinate / Civic Data Analytics.
-- Inclui o schema relacional original (Database Opinate.sql) mais a
-- tabela comment_analysis e a view vw_dashboard_sentimento, que antes
-- só eram criadas pelo script legado populador_banco.py.

CREATE DATABASE IF NOT EXISTS dond CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
USE dond;

-- -----------------------
-- ENUMs (MySQL columns will use ENUM)
-- -----------------------
-- (Declared inline nas colunas)

-- -----------------------
-- 1) Países
-- -----------------------
CREATE TABLE IF NOT EXISTS country (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------
-- 2) Regiões
-- -----------------------
CREATE TABLE IF NOT EXISTS region (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------
-- 3) Estados
-- -----------------------
CREATE TABLE IF NOT EXISTS state (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  acronym CHAR(2) NOT NULL,
  region_id INT NOT NULL,
  country_id INT DEFAULT NULL,
  CONSTRAINT fk_state_region FOREIGN KEY (region_id) REFERENCES region(id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_state_country FOREIGN KEY (country_id) REFERENCES country(id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------
-- 4) Municípios
-- -----------------------
CREATE TABLE IF NOT EXISTS municipality (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  state_id INT NOT NULL,
  CONSTRAINT fk_municipality_state FOREIGN KEY (state_id) REFERENCES state(id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------
-- 5) Usuários
-- -----------------------
CREATE TABLE IF NOT EXISTS app_user (
  id CHAR(36) PRIMARY KEY NOT NULL DEFAULT (UUID()),
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  avatar_url TEXT,
  bio TEXT,
  created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP(6)),
  updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP(6)) ON UPDATE CURRENT_TIMESTAMP(6),
  auth_provider VARCHAR(50) NOT NULL DEFAULT 'local',
  verified BOOLEAN NOT NULL DEFAULT FALSE,
  verification_level INT NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------
-- 6) Autenticação externa
-- -----------------------
CREATE TABLE IF NOT EXISTS user_auth_provider (
  id CHAR(36) PRIMARY KEY NOT NULL DEFAULT (UUID()),
  user_id CHAR(36) NOT NULL,
  provider VARCHAR(50) NOT NULL,
  provider_user_id VARCHAR(255) NOT NULL,
  access_token TEXT,
  refresh_token TEXT,
  created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP(6)),
  UNIQUE KEY uq_user_provider (user_id, provider),
  CONSTRAINT fk_uap_user FOREIGN KEY (user_id) REFERENCES app_user(id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------
-- 8) Categoria de propostas
-- -----------------------
CREATE TABLE IF NOT EXISTS category (
  id CHAR(36) PRIMARY KEY NOT NULL DEFAULT (UUID()),
  name VARCHAR(100) NOT NULL,
  description TEXT,
  icon VARCHAR(100),
  color VARCHAR(20),
  created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP(6))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------
-- 19) Comunidades
-- -----------------------
CREATE TABLE IF NOT EXISTS community (
  id CHAR(36) PRIMARY KEY NOT NULL DEFAULT (UUID()),
  user_id CHAR(36) NOT NULL,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  password VARCHAR(255),
  created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP(6)),
  updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP(6)) ON UPDATE CURRENT_TIMESTAMP(6),
  CONSTRAINT fk_community_user FOREIGN KEY (user_id) REFERENCES app_user(id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------
-- 7) Parlamentares
-- -----------------------
CREATE TABLE IF NOT EXISTS parliamentarian (
  id CHAR(36) PRIMARY KEY NOT NULL DEFAULT (UUID()),
  user_id CHAR(36) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  political_level ENUM('federal','estadual','municipal') NOT NULL,
  position VARCHAR(100) NOT NULL,
  party VARCHAR(100),
  region_id INT DEFAULT NULL,
  state_id INT DEFAULT NULL,
  municipality_id INT DEFAULT NULL,
  term_start DATE NOT NULL,
  term_end DATE DEFAULT NULL,
  photo_url TEXT,
  official_page_url TEXT,
  contact_email VARCHAR(255),
  contact_phone VARCHAR(50),
  biography TEXT,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP(6)),
  updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP(6)) ON UPDATE CURRENT_TIMESTAMP(6),
  CONSTRAINT fk_parl_user FOREIGN KEY (user_id) REFERENCES app_user(id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_parl_region FOREIGN KEY (region_id) REFERENCES region(id) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT fk_parl_state FOREIGN KEY (state_id) REFERENCES state(id) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT fk_parl_municipality FOREIGN KEY (municipality_id) REFERENCES municipality(id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------
-- 9) Propostas
-- -----------------------
CREATE TABLE IF NOT EXISTS proposal (
  id CHAR(36) PRIMARY KEY NOT NULL DEFAULT (UUID()),
  title VARCHAR(255) NOT NULL,
  description TEXT NOT NULL,
  category_id CHAR(36) DEFAULT NULL,
  user_id CHAR(36) DEFAULT NULL,
  municipality_id INT NOT NULL,
  community_id CHAR(36) DEFAULT NULL,
  status ENUM('rascunho','publicado','arquivado') NOT NULL DEFAULT 'rascunho',
  visibility ENUM('público','privado') NOT NULL DEFAULT 'público',
  tags JSON DEFAULT NULL,
  goal_supporters INT DEFAULT NULL,
  views_count INT NOT NULL DEFAULT 0,
  upvotes_count INT NOT NULL DEFAULT 0,
  downvotes_count INT NOT NULL DEFAULT 0,
  score INT AS (upvotes_count - downvotes_count) STORED,
  created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP(6)),
  updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP(6)) ON UPDATE CURRENT_TIMESTAMP(6),
  published_at DATETIME(6) DEFAULT NULL,
  expires_at DATETIME(6) DEFAULT NULL,
  allow_anonymous BOOLEAN NOT NULL DEFAULT FALSE,
  CONSTRAINT fk_proposal_category FOREIGN KEY (category_id) REFERENCES category(id) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT fk_proposal_user FOREIGN KEY (user_id) REFERENCES app_user(id) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT fk_proposal_municipality FOREIGN KEY (municipality_id) REFERENCES municipality(id) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_proposal_community FOREIGN KEY (community_id) REFERENCES community(id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Observação: tags como array em Postgres -> usei JSON para maior flexibilidade em MySQL.

-- -----------------------
-- 10) Histórico de status
-- -----------------------
CREATE TABLE IF NOT EXISTS proposal_status_history (
  id CHAR(36) PRIMARY KEY NOT NULL DEFAULT (UUID()),
  proposal_id CHAR(36) NOT NULL,
  old_status ENUM('rascunho','publicado','arquivado'),
  new_status ENUM('rascunho','publicado','arquivado'),
  changed_by CHAR(36) DEFAULT NULL,
  changed_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP(6)),
  CONSTRAINT fk_psh_proposal FOREIGN KEY (proposal_id) REFERENCES proposal(id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_psh_user FOREIGN KEY (changed_by) REFERENCES app_user(id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------
-- 11) Comentários
-- -----------------------
CREATE TABLE IF NOT EXISTS comment (
  id CHAR(36) PRIMARY KEY NOT NULL DEFAULT (UUID()),
  proposal_id CHAR(36) NOT NULL,
  parent_comment_id CHAR(36) DEFAULT NULL,
  user_id CHAR(36) NOT NULL,
  body TEXT NOT NULL,
  upvotes_count INT NOT NULL DEFAULT 0,
  downvotes_count INT NOT NULL DEFAULT 0,
  score INT AS (upvotes_count - downvotes_count) STORED,
  created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP(6)),
  updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP(6)) ON UPDATE CURRENT_TIMESTAMP(6),
  deleted_at DATETIME(6) DEFAULT NULL,
  CONSTRAINT fk_comment_proposal FOREIGN KEY (proposal_id) REFERENCES proposal(id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_comment_parent FOREIGN KEY (parent_comment_id) REFERENCES comment(id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_comment_user FOREIGN KEY (user_id) REFERENCES app_user(id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------
-- 11.1) Análise de Sentimento (NLP / Gemini)
-- -----------------------
-- Armazena a classificação de intenção política gerada pela Fase 2
-- (2_classificador_ia.py) para cada comentário. Separada da tabela
-- comment para manter a tabela bruta intacta e permitir reclassificação
-- sem perder o texto original.
CREATE TABLE IF NOT EXISTS comment_analysis (
  comment_id CHAR(36) PRIMARY KEY,
  classificacao_sentimento VARCHAR(50) NOT NULL,
  analisado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_analysis_comment FOREIGN KEY (comment_id) REFERENCES comment(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------
-- 12) Anexos
-- -----------------------
CREATE TABLE IF NOT EXISTS attachment (
  id CHAR(36) PRIMARY KEY NOT NULL DEFAULT (UUID()),
  proposal_id CHAR(36) DEFAULT NULL,
  comment_id CHAR(36) DEFAULT NULL,
  file_url TEXT NOT NULL,
  file_type VARCHAR(50),
  uploaded_by CHAR(36) DEFAULT NULL,
  uploaded_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP(6)),
  CONSTRAINT fk_attachment_proposal FOREIGN KEY (proposal_id) REFERENCES proposal(id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_attachment_comment FOREIGN KEY (comment_id) REFERENCES comment(id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_attachment_user FOREIGN KEY (uploaded_by) REFERENCES app_user(id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------
-- 13) Apoios
-- -----------------------
CREATE TABLE IF NOT EXISTS proposal_support (
  id CHAR(36) PRIMARY KEY NOT NULL DEFAULT (UUID()),
  proposal_id CHAR(36) NOT NULL,
  user_id CHAR(36) NOT NULL,
  supported_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP(6)),
  CONSTRAINT uq_support UNIQUE (proposal_id, user_id),
  CONSTRAINT fk_support_proposal FOREIGN KEY (proposal_id) REFERENCES proposal(id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_support_user FOREIGN KEY (user_id) REFERENCES app_user(id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------
-- 14) Compartilhamentos
-- -----------------------
CREATE TABLE IF NOT EXISTS proposal_share (
  id CHAR(36) PRIMARY KEY NOT NULL DEFAULT (UUID()),
  proposal_id CHAR(36) NOT NULL,
  shared_by CHAR(36) DEFAULT NULL,
  shared_with_email VARCHAR(255) DEFAULT NULL,
  shared_with_representative_id CHAR(36) DEFAULT NULL,
  method VARCHAR(50) NOT NULL,
  message TEXT,
  shared_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP(6)),
  CONSTRAINT fk_share_proposal FOREIGN KEY (proposal_id) REFERENCES proposal(id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_share_by FOREIGN KEY (shared_by) REFERENCES app_user(id) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT fk_share_rep FOREIGN KEY (shared_with_representative_id) REFERENCES parliamentarian(id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------
-- 15) Atividades parlamentares
-- -----------------------
CREATE TABLE IF NOT EXISTS parliamentary_activity (
  id CHAR(36) PRIMARY KEY NOT NULL DEFAULT (UUID()),
  representative_id CHAR(36) NOT NULL,
  activity_type VARCHAR(100) NOT NULL,
  description TEXT,
  date_occurred DATETIME(6) NOT NULL,
  related_url TEXT,
  created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP(6)),
  CONSTRAINT fk_pa_rep FOREIGN KEY (representative_id) REFERENCES parliamentarian(id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------
-- 16) Votos oficiais
-- -----------------------
CREATE TABLE IF NOT EXISTS vote (
  id CHAR(36) PRIMARY KEY NOT NULL DEFAULT (UUID()),
  activity_id CHAR(36) NOT NULL,
  representative_id CHAR(36) NOT NULL,
  vote_choice ENUM('sim','não','abstenção') NOT NULL,
  voted_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP(6)),
  CONSTRAINT fk_vote_activity FOREIGN KEY (activity_id) REFERENCES parliamentary_activity(id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_vote_rep FOREIGN KEY (representative_id) REFERENCES parliamentarian(id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------
-- 17) Votos em propostas
-- -----------------------
CREATE TABLE IF NOT EXISTS proposal_vote (
  user_id CHAR(36) NOT NULL,
  proposal_id CHAR(36) NOT NULL,
  vote_value SMALLINT NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP(6)),
  updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP(6)) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (user_id, proposal_id),
  CONSTRAINT chk_proposal_vote CHECK (vote_value IN (-1, 1)),
  CONSTRAINT fk_pv_user FOREIGN KEY (user_id) REFERENCES app_user(id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_pv_proposal FOREIGN KEY (proposal_id) REFERENCES proposal(id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------
-- 18) Votos em comentários
-- -----------------------
CREATE TABLE IF NOT EXISTS comment_vote (
  user_id CHAR(36) NOT NULL,
  comment_id CHAR(36) NOT NULL,
  vote_value SMALLINT NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP(6)),
  updated_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP(6)) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (user_id, comment_id),
  CONSTRAINT chk_comment_vote CHECK (vote_value IN (-1, 1)),
  CONSTRAINT fk_cv_user FOREIGN KEY (user_id) REFERENCES app_user(id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_cv_comment FOREIGN KEY (comment_id) REFERENCES comment(id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------
-- 20) Tabela de Junção Proposal-Parliamentarian
-- -----------------------
CREATE TABLE IF NOT EXISTS proposal_parliamentarian (
  proposal_id CHAR(36) NOT NULL,
  parliamentarian_id CHAR(36) NOT NULL,
  assigned_at DATETIME(6) NOT NULL DEFAULT (CURRENT_TIMESTAMP(6)),
  PRIMARY KEY (proposal_id, parliamentarian_id),
  CONSTRAINT fk_pp_proposal FOREIGN KEY (proposal_id) REFERENCES proposal(id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_pp_parliamentarian FOREIGN KEY (parliamentarian_id) REFERENCES parliamentarian(id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- -----------------------
-- Triggers (ajustados para MySQL)
-- -----------------------
DELIMITER $$

-- proposal_vote AFTER INSERT
CREATE TRIGGER trg_proposal_vote_after_insert
AFTER INSERT ON proposal_vote
FOR EACH ROW
BEGIN
  IF NEW.vote_value = 1 THEN
    UPDATE proposal SET upvotes_count = upvotes_count + 1 WHERE id = NEW.proposal_id;
  ELSE
    UPDATE proposal SET downvotes_count = downvotes_count + 1 WHERE id = NEW.proposal_id;
  END IF;
END$$

-- proposal_vote AFTER UPDATE
CREATE TRIGGER trg_proposal_vote_after_update
AFTER UPDATE ON proposal_vote
FOR EACH ROW
BEGIN
  -- decrement old
  IF OLD.vote_value = 1 THEN
    UPDATE proposal SET upvotes_count = upvotes_count - 1 WHERE id = OLD.proposal_id;
  ELSE
    UPDATE proposal SET downvotes_count = downvotes_count - 1 WHERE id = OLD.proposal_id;
  END IF;
  -- increment new
  IF NEW.vote_value = 1 THEN
    UPDATE proposal SET upvotes_count = upvotes_count + 1 WHERE id = NEW.proposal_id;
  ELSE
    UPDATE proposal SET downvotes_count = downvotes_count + 1 WHERE id = NEW.proposal_id;
  END IF;
END$$

-- proposal_vote AFTER DELETE
CREATE TRIGGER trg_proposal_vote_after_delete
AFTER DELETE ON proposal_vote
FOR EACH ROW
BEGIN
  IF OLD.vote_value = 1 THEN
    UPDATE proposal SET upvotes_count = upvotes_count - 1 WHERE id = OLD.proposal_id;
  ELSE
    UPDATE proposal SET downvotes_count = downvotes_count - 1 WHERE id = OLD.proposal_id;
  END IF;
END$$

-- comment_vote AFTER INSERT
CREATE TRIGGER trg_comment_vote_after_insert
AFTER INSERT ON comment_vote
FOR EACH ROW
BEGIN
  IF NEW.vote_value = 1 THEN
    UPDATE comment SET upvotes_count = upvotes_count + 1 WHERE id = NEW.comment_id;
  ELSE
    UPDATE comment SET downvotes_count = downvotes_count + 1 WHERE id = NEW.comment_id;
  END IF;
END$$

-- comment_vote AFTER UPDATE
CREATE TRIGGER trg_comment_vote_after_update
AFTER UPDATE ON comment_vote
FOR EACH ROW
BEGIN
  IF OLD.vote_value = 1 THEN
    UPDATE comment SET upvotes_count = upvotes_count - 1 WHERE id = OLD.comment_id;
  ELSE
    UPDATE comment SET downvotes_count = downvotes_count - 1 WHERE id = OLD.comment_id;
  END IF;

  IF NEW.vote_value = 1 THEN
    UPDATE comment SET upvotes_count = upvotes_count + 1 WHERE id = NEW.comment_id;
  ELSE
    UPDATE comment SET downvotes_count = downvotes_count + 1 WHERE id = NEW.comment_id;
  END IF;
END$$

-- comment_vote AFTER DELETE
CREATE TRIGGER trg_comment_vote_after_delete
AFTER DELETE ON comment_vote
FOR EACH ROW
BEGIN
  IF OLD.vote_value = 1 THEN
    UPDATE comment SET upvotes_count = upvotes_count - 1 WHERE id = OLD.comment_id;
  ELSE
    UPDATE comment SET downvotes_count = downvotes_count - 1 WHERE id = OLD.comment_id;
  END IF;
END$$

DELIMITER ;
-- -----------------------
-- Indexes adicionais
-- -----------------------
CREATE INDEX idx_state_region ON state(region_id);
CREATE INDEX idx_state_country ON state(country_id);
CREATE INDEX idx_municipality_state ON municipality(state_id);

CREATE INDEX idx_parliamentarian_region ON parliamentarian(region_id);
CREATE INDEX idx_parliamentarian_state ON parliamentarian(state_id);
CREATE INDEX idx_parliamentarian_municipality ON parliamentarian(municipality_id);
CREATE INDEX idx_parliamentarian_level ON parliamentarian(political_level);
CREATE INDEX idx_parliamentarian_party ON parliamentarian(party);
CREATE INDEX idx_parliamentarian_active ON parliamentarian(active);

CREATE INDEX idx_proposal_category ON proposal(category_id);
CREATE INDEX idx_proposal_user ON proposal(user_id);
CREATE INDEX idx_proposal_municipality ON proposal(municipality_id);
CREATE INDEX idx_comment_proposal ON comment(proposal_id);
CREATE INDEX idx_comment_parent ON comment(parent_comment_id);
CREATE INDEX idx_support_proposal ON proposal_support(proposal_id);
CREATE INDEX idx_support_user ON proposal_support(user_id);
CREATE INDEX idx_share_proposal ON proposal_share(proposal_id);
CREATE INDEX idx_share_user ON proposal_share(shared_by);
CREATE INDEX idx_proposal_vote ON proposal_vote(proposal_id, vote_value);
CREATE INDEX idx_comment_vote ON comment_vote(comment_id, vote_value);
CREATE INDEX idx_proposal_community ON proposal(community_id);
CREATE INDEX idx_proposal_expires_at ON proposal(expires_at);
CREATE INDEX idx_proposal_allow_anonymous ON proposal(allow_anonymous);
CREATE INDEX idx_proposal_parliamentarian_proposal ON proposal_parliamentarian(proposal_id);
CREATE INDEX idx_proposal_parliamentarian_parliamentarian ON proposal_parliamentarian(parliamentarian_id);

-- -----------------------
-- View de BI (usada por utils/database.py no dashboard Streamlit)
-- -----------------------
-- Junta comentário + proposta + classificação de sentimento em uma única
-- linha, já no formato consumido por pages/1_Dashboard.py. Precisa ser
-- recriada (DROP + CREATE) sempre que o schema rodar, para refletir
-- qualquer alteração de estrutura nas tabelas de origem.
DROP VIEW IF EXISTS vw_dashboard_sentimento;
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

