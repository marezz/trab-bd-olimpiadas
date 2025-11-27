import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from db import get_connection

st.set_page_config(page_title="Análise de Atletas", page_icon="🏃", layout="wide")
st.title("Atletas")

# ===================== Toggle na sidebar =====================
mostrar_sql = st.sidebar.toggle("Mostrar SQL", key="mostrar_sql")

# ===================== Funções de conexão =====================
def conexao():
    return get_connection()

conn = conexao()
cur = conn.cursor(dictionary=True)

# ===================== Função bloco =====================
def bloco(titulo, conteudo, consulta=None):
    st.subheader(titulo)
    if mostrar_sql and consulta:
        col1, col2 = st.columns([3, 2])
        with col1:
            conteudo()
        with col2:
            st.code(consulta, language="sql")
    else:
        conteudo()

# ===================== Funções de query =====================
def carregar_atletas_db():
    q = "SELECT id_atleta, nome FROM Atleta ORDER BY nome"
    exibir_sql = q if mostrar_sql else None
    df = pd.read_sql(q, conn)
    return df, exibir_sql

def carregar_info_atleta(id_atleta):
    q = """
    SELECT 
        A.nome AS Nome,
        A.sexo AS Sexo,
        A.peso AS Peso,
        A.altura As Altura,
        A.idade AS Idade_Atual,
        P.nome AS País,
        COUNT(CASE WHEN C.medalha != 'Sem Medalha' THEN 1 END) AS Medalhas,
        COUNT(DISTINCT O.ano) AS Participações
    FROM Atleta A
    JOIN Pais P ON P.sigla = A.sigla_pais
    JOIN Compete C ON C.id_atleta = A.id_atleta
    JOIN Evento E ON E.id_evento = C.id_evento
    JOIN Olimpiada O ON O.ano = E.ano_olimpiada
    WHERE A.id_atleta = %s
    """
    df = pd.read_sql(q, conn, params=[id_atleta])
    return df, q

def participacao(id_atleta):
    q = """
    SELECT MIN(O.ano) AS primeira, MAX(O.ano) AS ultima 
    FROM Atleta A
    JOIN Compete C ON C.id_atleta = A.id_atleta
    JOIN Evento E ON E.id_evento = C.id_evento
    JOIN Olimpiada O ON O.ano = E.ano_olimpiada
    WHERE A.id_atleta = %s
    """
    df = pd.read_sql(q, conn, params=[id_atleta])
    return df, q

def desempenho_modalidades(id_atleta):
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
    df = pd.read_sql(q, conn, params=[id_atleta])
    return df, q

def atletas_mesmo_esporte(id_atleta):
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
    df = pd.read_sql(q, conn, params=[id_atleta])
    return df, q

def evolucao_medalhas(id_atleta):
    q = """
    SELECT O.ano, COUNT(CASE WHEN C.medalha != 'Sem Medalha' THEN 1 END) AS medalhas
    FROM Compete C
    JOIN Evento E ON E.id_evento = C.id_evento
    JOIN Olimpiada O ON O.ano = E.ano_olimpiada
    WHERE C.id_atleta = %s
    GROUP BY O.ano
    ORDER BY O.ano
    """
    df = pd.read_sql(q, conn, params=[id_atleta])
    return df, q

def medalhas_por_modalidade(id_atleta):
    q = """
    SELECT E.modalidade, COUNT(C.medalha) AS medalhas
    FROM Compete C
    JOIN Evento E ON E.id_evento = C.id_evento
    WHERE C.id_atleta = %s AND C.medalha != 'Sem Medalha'
    GROUP BY E.modalidade
    ORDER BY medalhas DESC
    """
    df = pd.read_sql(q, conn, params=[id_atleta])
    return df, q

# ===================== Seleção de atleta =====================
df_atletas, q_atletas = carregar_atletas_db()
atleta = st.selectbox(
    "Selecione o atleta:",
    options=df_atletas['id_atleta'],
    format_func=lambda x: df_atletas.loc[df_atletas['id_atleta']==x, 'nome'].iloc[0]
)

# ===================== Informações gerais =====================
# Carrega dados e queries
df_info, q_info = carregar_info_atleta(atleta)
df_primeira, q_part = participacao(atleta)

# Função que mostra a tabela e as métricas
def mostrar_info():
    # Tabela ocupando largura total
    st.dataframe(df_info, width=1200, hide_index=True)
    # Datas de primeira/última participação em formato de cards
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Primeira participação", df_primeira.iloc[0,0])
    with col2:
        st.metric("Última participação", df_primeira.iloc[0,1])

# Exibe usando bloco() para que SQL apareça na lateral quando toggle ativo
bloco("Informações gerais do atleta", mostrar_info, consulta=q_info)

# ===================== Evolução de medalhas =====================
def mostrar_evolucao():
    df_evolucao, q_evol = evolucao_medalhas(atleta)
    if not df_evolucao.empty:
        fig_med = go.Figure(go.Scatter(x=df_evolucao['ano'], y=df_evolucao['medalhas'], mode='lines+markers'))
        fig_med.update_layout(title="Medalhas ao longo do tempo", xaxis_title="Ano", yaxis_title="Medalhas")
        st.plotly_chart(fig_med, use_container_width=True)
    else:
        st.write("Sem dados de medalhas para este atleta.")

bloco("Evolução de medalhas por edição", mostrar_evolucao, consulta=evolucao_medalhas(atleta)[1])

# ===================== Medalhas por modalidade =====================
def mostrar_modalidade():
    df_modalidade, q_modal = medalhas_por_modalidade(atleta)
    if not df_modalidade.empty:
        fig_modal = go.Figure(go.Bar(x=df_modalidade['modalidade'], y=df_modalidade['medalhas']))
        fig_modal.update_layout(title="Medalhas por modalidade", xaxis_title="Modalidade", yaxis_title="Medalhas")
        st.plotly_chart(fig_modal, use_container_width=True)
    else:
        st.write("Este atleta ainda não conquistou medalhas em nenhuma modalidade.")

bloco("Medalhas por modalidade", mostrar_modalidade, consulta=medalhas_por_modalidade(atleta)[1])

# ===================== Desempenho por modalidades =====================
def mostrar_desempenho():
    df_desempenho, q_desem = desempenho_modalidades(atleta)
    st.dataframe(df_desempenho, width='stretch', hide_index=True)

bloco("Desempenho por modalidades", mostrar_desempenho, consulta=desempenho_modalidades(atleta)[1])

# ===================== Comparação com categoria =====================
def mostrar_comparacao():
    df_esporte, q_esp = atletas_mesmo_esporte(atleta)
    if df_esporte.empty:
        st.warning("Não há atletas nesta categoria para comparação.")
        return

    st.markdown(f"Esporte: {df_esporte.iloc[0]['esporte']}")

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

    grafico_comparacao(df_esporte, atleta, 'peso', 'Peso', 'kg')
    grafico_comparacao(df_esporte, atleta, 'altura', 'Altura', 'm')
    st.dataframe(df_esporte, width='stretch', hide_index=True)

bloco("Comparações com seu esporte", mostrar_comparacao, consulta=atletas_mesmo_esporte(atleta)[1])

# ===================== Fechar conexão =====================
cur.close()
conn.close()
