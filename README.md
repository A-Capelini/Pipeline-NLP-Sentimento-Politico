# 🏛️ Civic Data Analytics: Pipeline de NLP e Análise de Sentimento Político

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![MySQL](https://img.shields.io/badge/MySQL-Database-4479A1.svg?logo=mysql&logoColor=white)
![Google Gemini](https://img.shields.io/badge/AI-Google_Gemini_2.5-orange.svg)
![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B.svg?logo=streamlit&logoColor=white)
![Status](https://img.shields.io/badge/Status-Concluído-success.svg)

## 📌 Sobre o Projeto

Este repositório contém a arquitetura completa de um projeto de Engenharia de Dados e Inteligência Artificial voltado para a tecnologia cívica (*Civic Tech*). Desenvolvido como parte do Projeto Integrador III (Fatec), o sistema simula uma plataforma de engajamento público, processando milhares de comentários de cidadãos sobre propostas legislativas e classificando suas intenções políticas utilizando Processamento de Linguagem Natural (NLP).

O foco central deste projeto é demonstrar a construção de um pipeline **ELT (Extract, Load, Transform)** robusto, resiliente e escalável.

## 🗂️ Estrutura do Projeto

```
Civic-Data-Analytics/
├── 1_gerador_massa.py        # Fase 1: geração de dados sintéticos
├── 2_classificador_ia.py     # Fase 2: classificação via Google Gemini
├── app.py                    # Fase 3: ponto de entrada do dashboard Streamlit
├── pages/
│   └── 1_Dashboard.py        # Painel de BI (gráficos, métricas, nuvem de palavras)
├── utils/
│   └── database.py           # Conexão com o MySQL e leitura da view de BI
├── assets/
│   └── style.css             # Estilização customizada do dashboard
├── schema.sql                # Script de criação das tabelas e da view no MySQL
├── environment.yml           # Ambiente conda (multiplataforma)
├── requirements.txt          # Dependências via pip
├── .env.example               # Modelo de variáveis de ambiente
├── scripts_legados/
│   └── populador_banco.py    # Prototípo inicial, mantido apenas como referência histórica
└── README.md
```

## ⚙️ Arquitetura e Destaques Técnicos

A aplicação é dividida em três camadas principais:

1. **Ingestão Massiva (Mock Data Engine)**
   - Script Python otimizado para gerar volumes massivos de dados sintéticos (cidadãos, propostas, votos e comentários) utilizando a biblioteca `Faker`.
   - Operações de I/O de banco de dados otimizadas com transações em lote (`executemany`), reduzindo o número de round-trips de rede.

2. **Motor de Enriquecimento por IA (NLP Pipeline)**
   - Classificação de sentimentos utilizando a API do Google Gemini (modelo 2.5 Flash).
   - **Controle de tráfego avançado:** limite de taxa por janela deslizante (*sliding window rate limiting*, implementado com `collections.deque`) para respeitar o RPM da API.
   - **Resiliência:** lógica de *retry* com *exponential backoff* para instabilidades de servidor, validação da resposta da IA (id e categoria) e isolamento de falhas por lote, para que um lote com erro não interrompa o pipeline inteiro.
   - Paginação eficiente no MySQL via *anti-join* (`LEFT JOIN ... WHERE IS NULL`), processando grandes volumes de registros sem sobrecarregar a memória.

3. **Painel de Business Intelligence (BI)**
   - Dashboard interativo construído com Streamlit e Plotly, consumindo a view `vw_dashboard_sentimento` (criada pelo `schema.sql`) via `utils/database.py`.
   - Visualização de dados em tempo real, nuvem de palavras filtrada por *stopwords* e ranqueamento de propostas por engajamento.

## 🚀 Como Clonar e Executar

### 1. Clonar o repositório

```bash
git clone https://github.com/seu-usuario/Civic-Data-Analytics.git
cd Civic-Data-Analytics
```

### 2. Criar o ambiente virtual

**Opção A — usando `environment.yml` (recomendado, multiplataforma):**

```bash
conda env create -f environment.yml
conda activate opinate_env
```

**Opção B — criando manualmente e instalando via pip:**

```bash
conda create --name opinate_env python=3.10 -y
conda activate opinate_env
pip install -r requirements.txt
```

### 3. Configurar as variáveis de ambiente

Copie o modelo de exemplo e edite com suas credenciais:

```bash
cp .env.example .env
```

O arquivo `.env` deve conter:

```
DB_HOST=localhost
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_NAME=dond
GEMINI_API_KEY=sua_chave_api_do_google
```

### 4. Criar o schema do banco de dados

O schema cria o banco `dond` automaticamente (`CREATE DATABASE IF NOT EXISTS dond`), então não é preciso criar um banco antes — apenas importe o arquivo direto no servidor MySQL:

```bash
mysql -u seu_usuario -p < schema.sql
```

Garanta que `DB_NAME=dond` no seu `.env`, já que esse é o nome fixo definido no script.

### 5. Executar o pipeline

**Fase 1 — Ingestão de dados brutos**

```bash
python 1_gerador_massa.py
```

**Fase 2 — Classificação com NLP**

```bash
python 2_classificador_ia.py
```

**Fase 3 — Visualização do dashboard**

```bash
streamlit run app.py
```

## 📸 Capturas de Tela

> Adicione aqui prints do dashboard Streamlit e/ou do terminal durante a execução do pipeline para dar uma prévia visual do projeto a quem está avaliando o repositório.

## 🗃️ Nota sobre código legado

O arquivo `scripts_legados/populador_banco.py` foi o protótipo inicial do projeto: gerava um pequeno volume de dados manualmente e criava, dentro do próprio script, a tabela `comment_analysis` e a view `vw_dashboard_sentimento`. Essas duas estruturas já fazem parte oficialmente do `schema.sql`, e a geração de dados foi substituída por `1_gerador_massa.py` (mais escalável, com `executemany` e maior volume). O script foi mantido no repositório apenas como referência histórica do desenvolvimento — **não faz parte do fluxo de execução atual** e não precisa ser rodado.

## 👨‍💻 Autor

**Anderson Capelini Andrade**

- Estudante do 4º semestre de Data Science — Fatec Cotia (Turma 2026)
- LinkedIn: [linkedin.com/in/anderson-capelini](https://www.linkedin.com/in/anderson-capelini/)

Projeto desenvolvido com foco em performance, escalabilidade e boas práticas de código.
