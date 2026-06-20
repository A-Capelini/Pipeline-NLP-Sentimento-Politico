import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.database import carregar_dados_geopoliticos

st.set_page_config(page_title="Geopolítica", page_icon="🗺️", layout="wide")

st.title("🗺️ Inteligência Geopolítica")
st.markdown("Analise a aceitação de partidos, parlamentares e propostas distribuída pelo território nacional.")

# ==========================================
# 1. CARREGAMENTO DOS DADOS
# ==========================================
df_geo = carregar_dados_geopoliticos()
if df_geo.empty:
    st.warning("Nenhum dado geográfico processado ainda.")
    st.stop()

# ==========================================
# 2. FILTROS LATERAIS EM CASCATA
# ==========================================
st.sidebar.header("🎯 Filtros Regionais")
df_filtrado = df_geo.copy()

partidos_disponiveis = ["Todos"] + sorted(df_geo['partido'].dropna().unique().tolist())
filtro_partido = st.sidebar.selectbox("Foco Partidário:", partidos_disponiveis)

if filtro_partido != "Todos":
    df_filtrado = df_filtrado[df_filtrado['partido'] == filtro_partido]

politicos_disponiveis = ["Todos"] + sorted(df_filtrado['parlamentar'].dropna().unique().tolist())
filtro_politico = st.sidebar.selectbox("Foco Parlamentar:", politicos_disponiveis)

if filtro_politico != "Todos":
    df_filtrado = df_filtrado[df_filtrado['parlamentar'] == filtro_politico]

propostas_disponiveis = ["Todas"] + sorted(df_filtrado['tema_proposta'].dropna().unique().tolist())
filtro_proposta = st.sidebar.selectbox("Foco Proposta:", propostas_disponiveis)

if filtro_proposta != "Todas":
    df_filtrado = df_filtrado[df_filtrado['tema_proposta'] == filtro_proposta]

# ==========================================
# 3. MOTOR DE CÁLCULO
# ==========================================
todas_ufs = pd.DataFrame({
    'uf': ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'],
    'estado_nome': ['Acre', 'Alagoas', 'Amapá', 'Amazonas', 'Bahia', 'Ceará', 'Distrito Federal', 'Espírito Santo', 'Goiás', 'Maranhão', 'Mato Grosso', 'Mato Grosso do Sul', 'Minas Gerais', 'Pará', 'Paraíba', 'Paraná', 'Pernambuco', 'Piauí', 'Rio de Janeiro', 'Rio Grande do Norte', 'Rio Grande do Sul', 'Rondônia', 'Roraima', 'Santa Catarina', 'São Paulo', 'Sergipe', 'Tocantins']
})

dados_mapa = []
if not df_filtrado.empty:
    df_estados = df_filtrado.groupby(['uf', 'classificacao_sentimento'])['total_comentarios'].sum().reset_index()
    
    for uf in df_estados['uf'].unique():
        df_uf = df_estados[df_estados['uf'] == uf]
        total_uf = df_uf['total_comentarios'].sum()
        
        apoio = df_uf[df_uf['classificacao_sentimento'].isin(['Apoio Total', 'Apoio com Alteração'])]['total_comentarios'].sum()
        rejeicao = df_uf[df_uf['classificacao_sentimento'].isin(['Rejeição Total', 'Oposição com Remoção'])]['total_comentarios'].sum()
        
        taxa_aprovacao = (apoio / total_uf * 100) if total_uf > 0 else 0
        taxa_rejeicao = (rejeicao / total_uf * 100) if total_uf > 0 else 0
        
        dados_mapa.append({'uf': uf, 'volume': total_uf, 'taxa_aprovacao': taxa_aprovacao, 'taxa_rejeicao': taxa_rejeicao})

df_mapa_calculado = pd.DataFrame(dados_mapa) if dados_mapa else pd.DataFrame(columns=['uf', 'volume', 'taxa_aprovacao', 'taxa_rejeicao'])

# Junta com todas as UFs para ter certeza que nenhum estado falta
df_mapa_final = pd.merge(todas_ufs, df_mapa_calculado, on='uf', how='left')
df_mapa_final['volume'] = df_mapa_final['volume'].fillna(0)

estado_fortaleza, estado_critico = "N/A", "N/A"
taxa_fortaleza, taxa_critico = 0.0, 0.0

df_relevante = df_mapa_final[df_mapa_final['volume'] > 0]
if not df_relevante.empty:
    idx_fortaleza = df_relevante['taxa_aprovacao'].idxmax()
    idx_critico = df_relevante['taxa_rejeicao'].idxmax()
    estado_fortaleza = df_relevante.loc[idx_fortaleza, 'estado_nome']
    taxa_fortaleza = df_relevante.loc[idx_fortaleza, 'taxa_aprovacao']
    estado_critico = df_relevante.loc[idx_critico, 'estado_nome']
    taxa_critico = df_relevante.loc[idx_critico, 'taxa_rejeicao']

# ==========================================
# 4. KPIs ESTRATÉGICOS
# ==========================================
st.markdown("#### 📊 Diagnóstico Territorial")
col_k1, col_k2, col_k3 = st.columns(3)

total_coments = df_filtrado['total_comentarios'].sum() if not df_filtrado.empty else 0
col_k1.metric("Volume Total Filtrado", f"{total_coments:,}")

if estado_fortaleza != "N/A":
    col_k2.metric("🛡️ Fortaleza Regional (Maior Apoio)", f"{estado_fortaleza}", f"{taxa_fortaleza:.1f}% aprovação")
    col_k3.metric("🔥 Zona de Atrito (Maior Rejeição)", f"{estado_critico}", f"-{taxa_critico:.1f}% rejeição", delta_color="inverse")
else:
    col_k2.metric("🛡️ Fortaleza Regional", "Sem dados")
    col_k3.metric("🔥 Zona de Atrito", "Sem dados")

st.divider()

# ==========================================
# 5. O MAPA TÉRMICO DE SENTIMENTO (DUPLA CAMADA)
# ==========================================
st.subheader("Termômetro Geopolítico: Taxa de Aprovação por Estado")
st.markdown("Cores quentes indicam oposição; cores frias/verdes indicam base aliada. **Estados em cinza claro não possuem informações para os filtros atuais.**")

url_geojson = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
fig_map = go.Figure()

# CAMADA 1: O "Molde" do Brasil (Todos os estados em cinza quase branco)
fig_map.add_trace(go.Choropleth(
    geojson=url_geojson,
    locations=todas_ufs['uf'],
    z=[0] * len(todas_ufs), # Valores vazios apenas para renderizar
    featureidkey='properties.sigla',
    colorscale=[[0, '#f8f9fa'], [1, '#f8f9fa']], 
    showscale=False, # Esconde a barra de cor desta camada
    marker_line_color='#e0e0e0',
    marker_line_width=0.8,
    hoverinfo='text',
    text=todas_ufs['estado_nome'] + "<br>Sem dados"
))

# CAMADA 2: Os Dados Reais (Sobreposição)
if not df_relevante.empty:
    fig_map.add_trace(go.Choropleth(
        geojson=url_geojson,
        locations=df_relevante['uf'],
        z=df_relevante['taxa_aprovacao'],
        featureidkey='properties.sigla',
        colorscale="RdYlGn",
        zmin=0, zmax=100,
        marker_line_color='#888888',
        marker_line_width=1.2,
        colorbar_title="Aprovação (%)",
        hoverinfo='text',
        text=df_relevante['estado_nome'] + "<br>Aprovação: " + df_relevante['taxa_aprovacao'].apply(lambda x: f"{x:.1f}%") + "<br>Interações: " + df_relevante['volume'].astype(int).astype(str)
    ))

fig_map.update_geos(fitbounds="locations", visible=False)
fig_map.update_layout(
    margin={"r":0,"t":0,"l":0,"b":0}, 
    paper_bgcolor="rgba(0,0,0,0)", 
    height=500
)

st.plotly_chart(fig_map, use_container_width=True)

st.divider()

# ==========================================
# 6. GRÁFICOS DE PROFUNDIDADE
# ==========================================
if not df_filtrado.empty:
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("**Matriz de Sentimento por Região**")
        df_regiao = df_filtrado.groupby(['regiao', 'classificacao_sentimento'])['total_comentarios'].sum().reset_index()
        total_regiao = df_regiao.groupby('regiao')['total_comentarios'].transform('sum')
        df_regiao['percentual'] = (df_regiao['total_comentarios'] / total_regiao) * 100
        df_regiao['texto'] = df_regiao['percentual'].apply(lambda x: f"{x:.1f}%" if x > 5 else "") 
        
        cores_map = {
            "Apoio Total": "#00C853", "Apoio com Alteração": "#FFD600", 
            "Dúvida / Neutro": "#9E9E9E", "Oposição com Remoção": "#FF6D00", "Rejeição Total": "#D50000"
        }
        
        fig_bar = px.bar(
            df_regiao, x="regiao", y="percentual", color="classificacao_sentimento",
            color_discrete_map=cores_map, text="texto",
            labels={'percentual': 'Proporção (%)', 'regiao': 'Região do Brasil', 'classificacao_sentimento': 'Intenção'}
        )
        fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", barmode="stack", showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_g2:
        st.markdown("**Top 10 Estados (Volume de Engajamento)**")
        df_top = df_filtrado.groupby('estado')['total_comentarios'].sum().nlargest(10).reset_index()
        fig_top = px.bar(
            df_top, x='total_comentarios', y='estado', orientation='h', 
            color='total_comentarios', color_continuous_scale='Blues',
            labels={'total_comentarios': 'Volume de Voz', 'estado': ''}
        )
        fig_top.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", yaxis={'categoryorder':'total ascending'}, showlegend=False)
        st.plotly_chart(fig_top, use_container_width=True)
else:
    st.info("Utilize os filtros laterais para carregar os gráficos de profundidade.")