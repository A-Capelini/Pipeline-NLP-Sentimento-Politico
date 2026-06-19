# pages/2_Termometro_Partidario.py
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.database import carregar_dados_partidarios

st.set_page_config(page_title="Termômetro Partidário", page_icon="🏛️", layout="wide")

st.title("🏛️ Termômetro Partidário")
st.markdown("Análise da taxa de aceitação e rejeição popular segmentada por legendas políticas.")

# Nota Metodológica de Transparência
st.info(
    "**Nota Metodológica:** No sistema legislativo, propostas costumam ter coautoria multipartidária. "
    "Quando um cidadão avalia um projeto, o impacto desse sentimento reflete em todos os partidos "
    "que o assinaram em conjunto. Por isso, a análise abaixo utiliza a **proporção percentual**, "
    "revelando a real taxa de rejeição e apoio de cada legenda independentemente do seu volume absoluto de propostas."
)

st.divider()

# 1. Carrega os dados
df_partidos = carregar_dados_partidarios()

if df_partidos.empty:
    st.warning("Nenhum dado partidário processado ainda. Aguarde o classificador finalizar alguns lotes.")
    st.stop()

# 2. Prepara os dados: Agrupamento e Cálculo de Porcentagem
df_agrupado = df_partidos.groupby(['partido', 'classificacao_sentimento'])['total_comentarios'].sum().reset_index()

# Calcula o total de comentários que atingiram o partido para criar a base do 100%
total_por_partido = df_agrupado.groupby('partido')['total_comentarios'].transform('sum')
df_agrupado['percentual'] = (df_agrupado['total_comentarios'] / total_por_partido) * 100

# Arredonda e cria uma coluna de texto para exibir dentro do gráfico (ex: 25.4%)
df_agrupado['texto_exibicao'] = df_agrupado['percentual'].apply(lambda x: f"{x:.1f}%")

# 3. Mapeamento de cores (Consistência Visual com a Página 1)
cores_map = {
    "Apoio Total": "#00C853",        
    "Apoio com Alteração": "#FFD600", 
    "Dúvida / Neutro": "#9E9E9E",     
    "Oposição com Remoção": "#FF6D00",
    "Rejeição Total": "#D50000"       
}

# 4. Gráfico Principal (Barras 100% Empilhadas)
st.subheader("Taxa de Aprovação vs Rejeição por Legenda")

fig = px.bar(
    df_agrupado, 
    x="partido", 
    y="percentual", 
    color="classificacao_sentimento", 
    color_discrete_map=cores_map,
    text="texto_exibicao",
    hover_data={
        "partido": True,
        "classificacao_sentimento": True,
        "percentual": ":.1f", 
        "total_comentarios": True,
        "texto_exibicao": False
    },
    labels={
        "partido": "Legenda Partidária",
        "percentual": "Proporção (%)",
        "classificacao_sentimento": "Intenção",
        "total_comentarios": "Volume Absoluto (Impactos)"
    }
)

# Ajustes visuais e comportamento do gráfico
fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", 
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis_title="Legenda Partidária",
    yaxis_title="Proporção do Impacto (%)",
    barmode="stack",
    hovermode="x unified" # Cria uma linha guia ao passar o mouse
)

# Trava o eixo Y exatamente entre 0 e 100% para não sobrar espaço em branco
fig.update_yaxes(range=[0, 100])

st.plotly_chart(fig, use_container_width=True)

# 5. Tabela de Detalhamento para Auditoria
st.subheader("Detalhamento de Impacto Bruto por Proposta (Auditoria)")
st.markdown("A tabela abaixo contém os dados absolutos (contagem direta) que geraram os percentuais acima.")

st.dataframe(
    df_partidos.sort_values(by="total_comentarios", ascending=False),
    use_container_width=True,
    hide_index=True
)