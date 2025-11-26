import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from db import get_connection

st.set_page_config(page_title="Análise de Atletas", page_icon="🏃", layout="wide")
st.title("Atletas")

# ===================== Funções de conexão e queries =====================
@st.cache_data(ttl=600)
def carregar_atletas_db(_conn):
    return pd.read_sql("SELECT id_atleta, nome FROM Atleta ORDER BY nome", _conn)

@st.cache_data(ttl=600)
def carregar_info_atleta(_conn, id_atleta):
    q = """
    SELECT 
        A.nome,
        A.sexo,
        A.peso,
        A.altura,
        A.idade AS idade_atual,
        P.nome AS pais,
        COUNT(CASE WHEN C.medalha != 'Sem Medalha' THEN 1 END) AS medalhas,
        COUNT(DISTINCT O.ano) AS participacoes
    FROM Atleta A
    JOIN Pais P ON P.sigla = A.sigla_pais
    JOIN Compete C ON C.id_atleta = A.id_atleta
    JOIN Evento E ON E.id_evento = C.id_evento
    JOIN Olimpiada O ON O.ano = E.ano_olimpiada
    WHERE A.id_atleta = %s
    """
    return pd.read_sql(q, _conn, params=[id_atleta])

@st.cache_data(ttl=600)
def participacao(_conn, id_atleta):
    q = """
    SELECT MIN(O.ano) AS primeira, max(O.ano) AS ultima 
    FROM Atleta A
    JOIN Compete C ON C.id_atleta = A.id_atleta
    JOIN Evento E ON E.id_evento = C.id_evento
    JOIN Olimpiada O ON O.ano = E.ano_olimpiada
    WHERE A.id_atleta = %s
    """
    return pd.read_sql(q, _conn, params=[id_atleta])

@st.cache_data(ttl=600)
def desempenho_modalidades(_conn, id_atleta):
    q = """
    SELECT A.nome, P.nome AS pais, O.ano AS edicao, E.modalidade, C.medalha
    FROM Atleta A
    JOIN Pais P ON P.sigla = A.sigla_pais
    JOIN Compete C ON C.id_atleta = A.id_atleta
    JOIN Evento E ON E.id_evento = C.id_evento
    JOIN Olimpiada O ON O.ano = E.ano_olimpiada
    WHERE A.id_atleta = %s
    ORDER BY O.ano ASC
    """
    return pd.read_sql(q, _conn, params=[id_atleta])

@st.cache_data(ttl=600)
def atletas_mesmo_esporte(_conn, id_atleta):
    q = """
    SELECT DISTINCT a2.id_atleta, a2.nome, a2.altura, a2.peso, e2.esporte
    FROM Atleta a1
    JOIN Compete c1 ON c1.id_atleta = a1.id_atleta
    JOIN Evento e1 ON e1.id_evento = c1.id_evento
    JOIN Evento e2 ON e2.esporte = e1.esporte
    JOIN Compete c2 ON c2.id_evento = e2.id_evento
    JOIN Atleta a2 ON a2.id_atleta = c2.id_atleta
    WHERE a1.id_atleta = %s
      AND e2.esporte IS NOT NULL
      AND a2.altura IS NOT NULL
      AND a2.peso IS NOT NULL
    ORDER BY a2.altura DESC, a2.peso DESC
    """
    return pd.read_sql(q, _conn, params=[id_atleta])

@st.cache_data(ttl=600)
def evolucao_medalhas(_conn, id_atleta):
    q = """
    SELECT O.ano, COUNT(CASE WHEN C.medalha != 'Sem Medalha' THEN 1 END) AS medalhas
    FROM Compete C
    JOIN Evento E ON E.id_evento = C.id_evento
    JOIN Olimpiada O ON O.ano = E.ano_olimpiada
    WHERE C.id_atleta = %s
    GROUP BY O.ano
    ORDER BY O.ano
    """
    return pd.read_sql(q, _conn, params=[id_atleta])

@st.cache_data(ttl=600)
def medalhas_por_modalidade(_conn, id_atleta):
    q = """
    SELECT E.modalidade, COUNT(C.medalha) AS medalhas
    FROM Compete C
    JOIN Evento E ON E.id_evento = C.id_evento
    WHERE C.id_atleta = %s AND C.medalha != 'Sem Medalha'
    GROUP BY E.modalidade
    ORDER BY medalhas DESC
    """
    return pd.read_sql(q, _conn, params=[id_atleta])

# ===================== Conexão e seleção =====================
conn = get_connection()
df_atletas = carregar_atletas_db(conn)
atleta = st.selectbox(
    "Selecione o atleta:",
    options=df_atletas['id_atleta'],
    format_func=lambda x: df_atletas.loc[df_atletas['id_atleta']==x, 'nome'].iloc[0]
)

# ===================== Informações gerais =====================
st.subheader("Informações Gerais")
df_info = carregar_info_atleta(conn, atleta)
st.dataframe(df_info, width='stretch')

df_primeira = participacao(conn, atleta)
st.markdown(f"Primeira participação: __*{df_primeira.iloc[0,0]}*__")
st.markdown(f"Última participação: __*{df_primeira.iloc[0,1]}*__")

# ===================== Evolução de medalhas =====================
st.subheader("Evolução de medalhas por edição")
df_evolucao = evolucao_medalhas(conn, atleta)
if not df_evolucao.empty:
    fig_med = go.Figure(go.Scatter(x=df_evolucao['ano'], y=df_evolucao['medalhas'], mode='lines+markers'))
    fig_med.update_layout(title="Medalhas ao longo do tempo", xaxis_title="Ano", yaxis_title="Medalhas")
    st.plotly_chart(fig_med, use_container_width=True)
else:
    st.write("Sem dados de medalhas para este atleta.")
    
# ===================== Medalhas por modalidade =====================
st.subheader("Medalhas por modalidade")
df_modalidade = medalhas_por_modalidade(conn, atleta)
if not df_modalidade.empty:
    fig_modal = go.Figure(go.Bar(x=df_modalidade['modalidade'], y=df_modalidade['medalhas']))
    fig_modal.update_layout(title="Medalhas por modalidade", xaxis_title="Modalidade", yaxis_title="Medalhas")
    st.plotly_chart(fig_modal, use_container_width=True)
else:
    st.write("Este atleta ainda não conquistou medalhas em nenhuma modalidade.")

st.markdown("Desempenho por modalidades")
df_desempenho = desempenho_modalidades(conn, atleta)
st.dataframe(df_desempenho, width='stretch')

# ===================== Comparação com categoria =====================
st.subheader("Comparações com seu esporte")
df_esporte = atletas_mesmo_esporte(conn, atleta)

def grafico_comparacao(df, atleta_id, coluna, nome_coluna, unidade):
    df_outros = df[df['id_atleta'] != atleta_id].sample(
        n=min(19, len(df[df['id_atleta'] != atleta_id])), random_state=42
    )
    df_plot = pd.concat([df_outros, df[df['id_atleta'] == atleta_id]]).reset_index(drop=True)
    df_plot = df_plot.sort_values(by=coluna).reset_index(drop=True)
    df_plot['cor'] = ['orange' if x == atleta_id else 'skyblue' for x in df_plot['id_atleta']]
    media = df_plot[coluna].mean()

    fig = go.Figure([
        go.Bar(x=df_plot['nome'], y=df_plot[coluna], marker_color=df_plot['cor'], name=nome_coluna),
        go.Scatter(x=df_plot['nome'], y=[media]*len(df_plot), mode='lines',
                   line=dict(color='red', dash='dash'),
                   name=f'Média da categoria ({media:.2f} {unidade})')
    ])
    fig.update_layout(
        title=f'{nome_coluna} dos atletas na categoria de {df_plot["esporte"].iloc[0]}',
        yaxis_title=f'{nome_coluna} ({unidade})',
        xaxis_tickangle=-45,
        height=500,
        showlegend=True
    )
    st.plotly_chart(fig, use_container_width=True)

if df_esporte.empty:
    st.warning("Não há atletas nesta categoria para comparação.")
else:
    st.markdown(f"Esporte: {df_esporte.iloc[0]['esporte']}")
    grafico_comparacao(df_esporte, atleta, 'peso', 'Peso', 'kg')
    grafico_comparacao(df_esporte, atleta, 'altura', 'Altura', 'm')
    st.dataframe(df_esporte, width='stretch')

# ===================== Fechar conexão =====================
conn.close()
