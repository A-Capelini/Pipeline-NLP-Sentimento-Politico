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
├── app.py                    # Fase 3: dashboard em Streamlit
├── schema.sql                # Script de criação das tabelas no MySQL
├── requirements.txt          # Dependências do projeto
├── .env.example               # Modelo de variáveis de ambiente
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
   - Dashboard interativo construído com Streamlit e Plotly.
   - Visualização de dados em tempo real, nuvem de palavras filtrada por *stopwords* e ranqueamento de propostas por engajamento.

## 🚀 Como Clonar e Executar

### 1. Clonar o repositório

```bash
git clone https://github.com/seu-usuario/Civic-Data-Analytics.git
cd Civic-Data-Analytics
```

### 2. Criar o ambiente virtual

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
DB_NAME=seu_banco
GEMINI_API_KEY=sua_chave_api_do_google
```

### 4. Criar o schema do banco de dados

Antes de rodar o pipeline, crie as tabelas necessárias no MySQL:

```bash
mysql -u seu_usuario -p seu_banco < schema.sql
```

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

## 👨‍💻 Autor

**Anderson Capelini Andrade**

- Estudante do 4º semestre de Data Science — Fatec Cotia 2026
- LinkedIn: [linkedin.com/in/anderson-capelini](https://www.linkedin.com/in/anderson-capelini/)

Projeto desenvolvido com foco em performance, escalabilidade e boas práticas de código.