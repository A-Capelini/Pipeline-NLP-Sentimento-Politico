# 🏛️ Civic Data Analytics: Pipeline de NLP e Análise de Sentimento Político

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![MySQL](https://img.shields.io/badge/MySQL-Database-4479A1.svg?logo=mysql&logoColor=white)
![Google Gemini](https://img.shields.io/badge/AI-Google_Gemini_2.5_Flash-orange.svg)
![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B.svg?logo=streamlit&logoColor=white)
![Aiven](https://img.shields.io/badge/Cloud_DB-Aiven.io-FF4B4B.svg)
![Status](https://img.shields.io/badge/Status-Concluído-success.svg)

🌐 **[sentimento-politico.streamlit.app](https://sentimento-politico.streamlit.app/)**

---

## 📌 Sobre o Projeto

Este repositório contém a arquitetura completa de um projeto de Engenharia de Dados e Inteligência Artificial voltado para tecnologia cívica (*Civic Tech*). Desenvolvido como Projeto Integrador III (Fatec Cotia — Ciência de Dados, Turma 2026), o sistema simula uma plataforma de engajamento público, processando milhares de comentários de cidadãos sobre propostas legislativas e classificando suas intenções políticas utilizando Processamento de Linguagem Natural (NLP).

O foco central é demonstrar a construção de um pipeline **ELT (Extract, Load, Transform)** robusto, resiliente e escalável — do banco de dados à nuvem, passando por IA generativa e um dashboard interativo em produção.

---

## 🌐 Infraestrutura em Produção

| Camada | Tecnologia | Detalhe |
|---|---|---|
| **Dashboard** | Streamlit Cloud | Deploy automático via branch `main` do GitHub |
| **Banco de Dados** | Aiven.io (MySQL 8) | Servidor gerenciado — DigitalOcean, Região SFO |
| **IA / NLP** | Google Gemini 2.5 Flash | Classificação *Zero-Shot* via API |

> O banco de dados roda em instância gratuita do Aiven.io (1 vCPU, 1 GB RAM, 1 GB Storage). Por ser um servidor compartilhado com latência variável, o `requirements.txt` é o arquivo de dependências usado pelo Streamlit Cloud em produção — o `environment.yml` é recomendado apenas para reprodução local do ambiente via Conda.

---

## 🗂️ Estrutura do Projeto

```
Civic-Data-Analytics/
├── 1_gerador_massa.py          # Fase 1: geração de dados sintéticos (roda local)
├── 2_classificador_ia.py       # Fase 2: classificação via Google Gemini (roda local)
├── app.py                      # Fase 3: ponto de entrada do dashboard Streamlit
│
├── pages/
│   ├── 1_Visao_Geral.py        # KPIs globais e nuvem de palavras
│   ├── 2_Termometro_Partidario.py  # Sentimento por partido e parlamentar
│   ├── 3_Geopolitica.py        # Mapa de calor por estado
│   ├── 4_Tendencias.py         # Série temporal do sentimento
│   ├── 5_Analise_Qualitativa.py    # N-Gramas e grafo de coocorrência
│   ├── 6_Simulador.py          # Simulador de cenários de campanha
│   └── 7_Raio_X_Cidadao.py     # CRM Cívico — perfil individual
│
├── utils/
│   └── database.py             # Engine SQLAlchemy e funções de leitura do banco
│
├── assets/
│   └── style.css               # Estilização customizada (tema claro)
│
├── schema.sql                  # Schema completo: tabelas, triggers, índices e view de BI
├── GeradorDatasAleatorias.sql  # Script auxiliar: randomiza created_at dos comentários
│
├── setup/
│   └── environment.yml         # Ambiente Conda (recomendado para uso local)
│
├── requirements.txt            # Dependências pip — usado pelo Streamlit Cloud
├── .env.example                # Modelo de variáveis de ambiente
│
└── scripts_legados/
    └── populador_banco.py      # Protótipo inicial (referência histórica, não executar)
```

---

## ⚙️ Arquitetura e Destaques Técnicos

A aplicação é dividida em três fases de pipeline, mais a camada de BI:

### Fase 1 — Ingestão Massiva (Mock Data Engine)
Script Python que gera volumes massivos de dados sintéticos usando a biblioteca `Faker`: 1.000 cidadãos, 40 parlamentares, 50 propostas, votos e 3.000 comentários com intenções semânticas pré-definidas (apoio, oposição, neutralidade). Usa `executemany` para reduzir round-trips de rede e faz TRUNCATE em cascata antes de repopular, permitindo re-execuções limpas.

### Fase 2 — Motor de Enriquecimento por IA (NLP Pipeline)
Classificação de sentimentos via Google Gemini 2.5 Flash em modo *Zero-Shot*, com as seguintes garantias de resiliência:

- **Rate Limiting com janela deslizante** (`collections.deque`): respeita o limite de RPM do tier gratuito sem depender de janelas fixas de 1 minuto.
- **Tratamento diferenciado de cota diária (RPD)**: erros de cota esgotada abortam imediatamente o pipeline (continuar tentando seria inútil); erros 429/503 momentâneos entram no fluxo de retry com backoff.
- **Anti-join no MySQL** (`LEFT JOIN ... WHERE IS NULL`) para buscar apenas comentários pendentes, sem o bug silencioso do `NOT IN` com NULLs.
- **Validação da resposta da IA**: cada item devolvido é verificado quanto ao `id` (pertence ao lote?) e à `intencao` (é uma das 5 categorias exatas?). Itens inválidos são descartados e ficam pendentes para a próxima execução sem interromper o lote.

### Fase 3 — Painel de Business Intelligence
Dashboard em Streamlit com 7 páginas analíticas, consumindo o banco em tempo real via `utils/database.py`. Toda leitura usa a view `vw_dashboard_sentimento` (para a visão geral) ou queries SQL diretas com JOINs otimizados para as demais páginas. Cache de dados configurado com `@st.cache_data(ttl=600)` para equilibrar atualização e performance.

---

## 🗺️ Páginas do Dashboard

| Página | O que entrega |
|---|---|
| **Visão Geral** | KPIs globais, termômetro dos 5 sentimentos e nuvem de palavras da oposição |
| **Termômetro Partidário** | Matriz de risco vs. relevância (bolhas) e gráfico Tornado por partido/parlamentar |
| **Geopolítica** | Mapa de calor choropleth por estado e ranking de engajamento por região |
| **Tendências** | Série temporal com detecção automática de pico de crise e pico de apoio |
| **Análise Qualitativa** | Grafo de coocorrência (NetworkX + Plotly) e ranking de bigramas |
| **Simulador** | Simulação de conversão de sentimento (funil de marketing político) |
| **Raio-X do Cidadão** | Perfil comportamental individual com badge, radar e análise prescritiva |

---

## 🛠️ Stack Tecnológico

| Categoria | Tecnologias |
|---|---|
| **Engenharia & Simulação** | Python, MySQL 8, Faker, SQLAlchemy |
| **IA & NLP** | Google Gemini 2.5 Flash, N-Gramas, NetworkX |
| **Visualização & Frontend** | Streamlit, Plotly, Pandas, WordCloud, Matplotlib |
| **Infraestrutura** | Aiven.io (MySQL gerenciado), Streamlit Cloud, GitHub CI/CD |

---

## 🚀 Como Executar Localmente

### 1. Clonar o repositório

```bash
git clone https://github.com/A-Capelini/Pipeline-NLP-Sentimento-Politico.git
cd Pipeline-NLP-Sentimento-Politico
```

### 2. Criar o ambiente virtual

**Recomendado — Conda via `environment.yml` (setup local completo):**

```bash
conda env create -f setup/environment.yml
conda activate opinate_env
```

**Alternativa — pip puro:**

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

> ⚠️ O `environment.yml` fica dentro da pasta `setup/` e é ideal para reproduzir o ambiente local com Conda. O Streamlit Cloud usa exclusivamente o `requirements.txt` na raiz do projeto.

### 3. Configurar as variáveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` com suas credenciais:

```env
DB_HOST=seu_host_aiven_ou_localhost
DB_PORT=3306
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_NAME=dond
GEMINI_API_KEY=sua_chave_api_do_google_ai_studio
```

> A porta (`DB_PORT`) é obrigatória ao conectar no Aiven — o servidor remoto não usa a 3306 padrão.

### 4. Criar o schema do banco de dados

O script cria o banco `dond` automaticamente (`CREATE DATABASE IF NOT EXISTS`):

```bash
mysql -u seu_usuario -p < schema.sql
```

### 5. Executar o pipeline

```bash
# Fase 1: gera os dados sintéticos no banco
python 1_gerador_massa.py

# Fase 2: classifica os comentários com Gemini (respeita RPM/RPD do tier gratuito)
python 2_classificador_ia.py

# Fase 3: sobe o dashboard localmente
streamlit run app.py
```

> **Sobre o limite de API do Gemini (tier gratuito):** a Fase 2 implementa rate limiting automático de 8 RPM. Para classificar os 3.000 comentários em lotes de 50, espere alguns minutos de execução. Se a cota diária (RPD) for atingida, o script aborta limpo e retoma de onde parou na próxima execução — nenhum comentário é perdido.

---

## 📸 Capturas de Tela

> *Adicione aqui prints do dashboard e do terminal durante a execução do pipeline.*

---

## 🗃️ Nota sobre Código Legado

`scripts_legados/populador_banco.py` foi o protótipo inicial: gerava um pequeno volume de dados manualmente e criava, dentro do próprio script, a tabela `comment_analysis` e a view `vw_dashboard_sentimento`. Essas estruturas agora fazem parte oficialmente do `schema.sql`, e a geração de dados foi substituída por `1_gerador_massa.py`. O script foi mantido apenas como referência histórica do desenvolvimento — **não faz parte do fluxo de execução atual**.

---

## 👨‍💻 Autor

**Anderson Capelini Andrade**
Estudante do 4º semestre de Ciência de Dados — Fatec Cotia (Turma 2026)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-anderson--capelini-0077B5?logo=linkedin)](https://www.linkedin.com/in/anderson-capelini/)
[![GitHub](https://img.shields.io/badge/GitHub-A--Capelini-181717?logo=github)](https://github.com/A-Capelini/Pipeline-NLP-Sentimento-Politico)

---

*Projeto desenvolvido com foco em performance, resiliência e boas práticas de engenharia de dados.*
