import streamlit as st
import pandas as pd
import plotly.express as px
from utils.database import carregar_dados_cidadao_avancado

st.set_page_config(page_title="Raio-X do Cidadão", page_icon="👤", layout="wide")

st.title("👤 Raio-X do Cidadão (CRM Cívico)")
st.markdown("Filtre o território ou alvo político para mapear o perfil comportamental e obter sugestões de engajamento.")

# ==========================================
# 1. CARREGAMENTO DOS DADOS
# ==========================================
df = carregar_dados_cidadao_avancado()

if df.empty:
    st.warning("Nenhum dado encontrado no banco.")
    st.stop()

# ==========================================
# 2. FILTROS DE PROSPECÇÃO EM CASCATA
# ==========================================
st.sidebar.header("🎯 1. Critérios de Prospecção")
st.sidebar.markdown("Use os filtros abaixo para restringir a lista de cidadãos.")

df_filtrado = df.copy()

# Filtro 1: Partido
partidos_disponiveis = ["Todos"] + sorted(df_filtrado['sigla_partido'].dropna().unique().tolist())
filtro_partido = st.sidebar.selectbox("Foco Partidário:", partidos_disponiveis)
if filtro_partido != "Todos":
    df_filtrado = df_filtrado[df_filtrado['sigla_partido'] == filtro_partido]

# Filtro 2: Parlamentar (Cascata: mostra apenas políticos do partido selecionado)
politicos_disponiveis = ["Todos"] + sorted(df_filtrado['nome_politico'].dropna().unique().tolist())
filtro_politico = st.sidebar.selectbox("Foco Parlamentar:", politicos_disponiveis)
if filtro_politico != "Todos":
    df_filtrado = df_filtrado[df_filtrado['nome_politico'] == filtro_politico]

# Filtro 3: Proposta (Cascata: mostra apenas propostas vinculadas aos filtros anteriores)
propostas_disponiveis = ["Todas"] + sorted(df_filtrado['tema_proposta'].dropna().unique().tolist())
filtro_proposta = st.sidebar.selectbox("Foco Proposta:", propostas_disponiveis)
if filtro_proposta != "Todas":
    df_filtrado = df_filtrado[df_filtrado['tema_proposta'] == filtro_proposta]

# ==========================================
# 3. SELEÇÃO DO CIDADÃO
# ==========================================
st.sidebar.header("🔍 2. Perfil do Cidadão")

contagem_usuarios = df_filtrado['cidadao_anonimo'].value_counts()
if contagem_usuarios.empty:
    st.sidebar.warning("Nenhum usuário encontrado com estes critérios de busca.")
    st.stop()

usuarios_ordenados = contagem_usuarios.index.tolist()
opcoes_seletor = [f"Cidadão #{uid} ({contagem_usuarios[uid]} interações)" for uid in usuarios_ordenados]

usuario_selecionado = st.sidebar.selectbox("Selecione um perfil para analisar:", opcoes_seletor)
id_alvo = usuario_selecionado.split("#")[1].split(" ")[0]

# O df_user contém APENAS o histórico do cidadão escolhido (ignorando os filtros para mostrar o TODO do usuário)
df_user = df[df['cidadao_anonimo'] == id_alvo].copy()

st.divider()

# ==========================================
# 4. MOTORES DE CLASSIFICAÇÃO (BADGE & SUGESTÕES)
# ==========================================
def calcular_percentuais(df_usuario):
    total = len(df_usuario)
    if total == 0: return 0, 0
    contagem = df_usuario['classificacao_sentimento'].value_counts()
    apoio = contagem.get("Apoio Total", 0) + contagem.get("Apoio com Alteração", 0)
    rejeicao = contagem.get("Rejeição Total", 0) + contagem.get("Oposição com Remoção", 0)
    return apoio / total, rejeicao / total

def gerar_badge_perfil(pct_apoio, pct_rejeicao):
    if pct_rejeicao >= 0.6:
        return '<div style="background-color: #ffebee; border: 1px solid #ef5350; border-radius: 15px; padding: 6px 16px; display: inline-block; color: #c62828; font-weight: bold; font-size: 16px;">🔥 Detrator Feroz</div>'
    elif pct_apoio >= 0.6:
        return '<div style="background-color: #e8f5e9; border: 1px solid #66bb6a; border-radius: 15px; padding: 6px 16px; display: inline-block; color: #2e7d32; font-weight: bold; font-size: 16px;">🛡️ Advogado da Base</div>'
    else:
        return '<div style="background-color: #f5f5f5; border: 1px solid #bdbdbd; border-radius: 15px; padding: 6px 16px; display: inline-block; color: #616161; font-weight: bold; font-size: 16px;">⚖️ Eleitor Moderado / Analítico</div>'

def gerar_analise_prescritiva(pct_apoio, pct_rejeicao):
    if pct_rejeicao >= 0.6:
        return """
        **📉 Diagnóstico:** Usuário com forte tendência de oposição. Interage predominantemente para criticar projetos ou a gestão.
        
        **🎯 Ações Sugeridas:**
        * **Monitoramento Ativo:** Acompanhe as objeções deste usuário para evitar a escalada de narrativas negativas em propostas sensíveis.
        * **Comunicação Factual:** Não engaje em respostas puramente emocionais. Responda com dados concretos, links oficiais e transparência.
        * **Identificação de Dores:** Isole as críticas construtivas do "ruído". Muitas vezes, detratores apontam falhas reais e técnicas em projetos de lei.
        """
    elif pct_apoio >= 0.6:
        return """
        **📈 Diagnóstico:** Usuário com forte alinhamento propositivo. Atua como defensor orgânico e entusiasta das pautas governamentais/partidárias.
        
        **🎯 Ações Sugeridas:**
        * **Validação Pública:** Curta e valide institucionalmente os comentários bem estruturados deste usuário para reforçar seu comportamento positivo.
        * **Mobilização:** Trata-se de um excelente perfil para ser convidado para pesquisas qualitativas, audiências públicas ou testes de novas políticas.
        * **Termômetro de Pauta:** Utilize as defesas deste usuário como argumento base para contornar objeções de eleitores indecisos.
        """
    else:
        return """
        **📊 Diagnóstico:** Eleitor pragmático e focado no mérito das propostas. Tende a ler os projetos e apresentar dúvidas ou apoios condicionais.
        
        **🎯 Ações Sugeridas:**
        * **Atenção às Condicionais:** Leia atentamente os comentários classificados como "Apoio com Alteração". Este perfil contribui ativamente para a melhoria de textos legais.
        * **Poder de Persuasão:** Este é o perfil mais valioso para a comunicação. Eles são persuadíveis e mudam de "Dúvida" para "Apoio Total" se a comunicação oficial for clara.
        * **Foco no Esclarecimento:** Direcione esforços para responder dúvidas técnicas e explicar o "como" e o "porquê" das propostas que ele acompanha.
        """

pct_apoio, pct_rejeicao = calcular_percentuais(df_user)

# ==========================================
# 5. RENDERIZAÇÃO DO CABEÇALHO
# ==========================================
col_titulo, col_badge = st.columns([2, 1])
with col_titulo:
    st.subheader(f"Dashboard Comportamental: Cidadão #{id_alvo}")
with col_badge:
    st.markdown(gerar_badge_perfil(pct_apoio, pct_rejeicao), unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
volume_voz = len(df_user)
influencia = int(df_user['engajamento_recebido'].sum())

cidade_principal = df_user['cidade'].mode()[0] if not df_user.empty else "N/A"
uf_principal = df_user['uf'].mode()[0] if not df_user.empty else "N/A"
zona_interesse = f"{cidade_principal} - {uf_principal}"

col1.metric("Volume de Voz", f"{volume_voz} interações")
col2.metric("Índice de Influência", f"{influencia} upvotes")
col3.metric("📍 Zona de Interesse (Afinidade)", zona_interesse)

st.divider()

# ==========================================
# 6. MÓDULO ANALÍTICO (RADAR + SUGESTÕES)
# ==========================================
col_grafico, col_insights = st.columns([1.2, 1])

with col_grafico:
    st.markdown("#### 🕸️ Espectro de Atuação")
    categorias_base = ["Apoio Total", "Apoio com Alteração", "Dúvida / Neutro", "Oposição com Remoção", "Rejeição Total"]
    contagem_radar = df_user['classificacao_sentimento'].value_counts().reindex(categorias_base, fill_value=0).reset_index()
    contagem_radar.columns = ['Sentimento', 'Frequencia']

    fig_radar = px.line_polar(
        contagem_radar, 
        r='Frequencia', 
        theta='Sentimento', 
        line_close=True,
        color_discrete_sequence=['#1976D2']
    )
    fig_radar.update_traces(fill='toself')
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=40, t=20, b=20)
    )
    st.plotly_chart(fig_radar, use_container_width=True)

with col_insights:
    st.markdown("#### 💡 Insights e Recomendações")
    # Utilizamos o st.info para criar um card com destaque visual para o texto gerado
    st.info(gerar_analise_prescritiva(pct_apoio, pct_rejeicao))

st.divider()

# ==========================================
# 7. TABELA DE AUDITORIA
# ==========================================
st.markdown("#### 📄 Extrato de Opiniões")

df_exibicao = df_user[['data_comentario', 'sigla_partido', 'nome_politico', 'tema_proposta', 'classificacao_sentimento', 'texto_comentario']].copy()
df_exibicao['data_comentario'] = pd.to_datetime(df_exibicao['data_comentario']).dt.strftime('%d/%m/%Y %H:%M')
df_exibicao.columns = ['Data', 'Partido Alvo', 'Parlamentar', 'Proposta', 'Intenção (IA)', 'Comentário Escrito']

st.dataframe(df_exibicao, use_container_width=True, hide_index=True)