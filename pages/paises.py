import streamlit as st
import pandas as pd
from db import get_connection

st.set_page_config(page_title="Países - Olimpíadas", layout="wide")
st.title("Países")

# Conexão
try:
    conn = get_connection()
except Exception:
    conn = None

if conn is None:
    st.error("❌ Não foi possível conectar ao banco de dados.")
    st.stop()

# Carregar países com nome completo
paises = pd.read_sql("SELECT sigla, nome FROM Pais ORDER BY nome", conn)

# Função para mostrar nome no selectbox
def nome_do_pais(sigla):
    return paises.loc[paises['sigla'] == sigla, 'nome'].iloc[0]

# ----------------------------
# 1) RANKING DE ATLETAS POR PAÍS
# ----------------------------
st.subheader("🥇 Ranking de atletas mais vitoriosos do país")

pais_ranking = st.selectbox(
    "Selecione o país:",
    options=paises['sigla'],
    format_func=nome_do_pais,
    key="rank_selector"
)

q1 = """
SELECT A.nome AS Atleta, COUNT(*) AS Total_Medalhas
FROM Atleta A
JOIN Pais P ON P.sigla = A.sigla_pais
JOIN Compete C ON C.id_atleta = A.id_atleta
WHERE P.sigla = %s AND C.medalha IN ('Ouro','Prata','Bronze')
GROUP BY A.id_atleta
ORDER BY Total_Medalhas DESC;
"""
df1 = pd.read_sql(q1, conn, params=[pais_ranking])
st.dataframe(df1, use_container_width=True)

# ----------------------------
# 2) EVENTOS COM MAIS MEDALHAS
# ----------------------------
st.subheader("🏆 Eventos em que o país mais ganha medalhas")

pais_eventos = st.selectbox(
    "Selecione o país:",
    options=paises['sigla'],
    format_func=nome_do_pais,
    key="eventos_selector"
)

q2 = """
SELECT P.nome AS Pais, E.esporte AS Esporte, E.modalidade AS Modalidade,
       COUNT(*) AS Total_Medalhas
FROM Atleta A
JOIN Pais P ON P.sigla = A.sigla_pais
JOIN Compete C ON C.id_atleta = A.id_atleta
JOIN Evento E ON E.id_evento = C.id_evento
WHERE P.sigla = %s AND C.medalha IN ('Ouro','Prata','Bronze')
GROUP BY P.nome, E.esporte, E.modalidade
ORDER BY Total_Medalhas DESC;
"""
df2 = pd.read_sql(q2, conn, params=[pais_eventos])
st.dataframe(df2, use_container_width=True)

# ----------------------------
# 3) PRIMEIRA PARTICIPAÇÃO POR PAÍS
# ----------------------------
st.subheader("📅 Ano da primeira participação por país")

q3 = """
SELECT P.nome AS Pais, MIN(O.ano) AS Ano_Primeira_Participacao
FROM Pais P
JOIN Atleta A ON A.sigla_pais = P.sigla
JOIN Compete C ON C.id_atleta = A.id_atleta
JOIN Evento E ON E.id_evento = C.id_evento
JOIN Olimpiada O ON O.ano = E.ano_olimpiada
GROUP BY P.nome
ORDER BY Ano_Primeira_Participacao;
"""
df3 = pd.read_sql(q3, conn)
st.dataframe(df3, use_container_width=True)

# ----------------------------
# 4) MAIS ATLETAS INSCRITOS
# ----------------------------
st.subheader("👥 Países com maior número de atletas inscritos")

q4 = """
SELECT P.nome AS Pais, COUNT(*) AS Total_Atletas
FROM Atleta A
JOIN Pais P ON P.sigla = A.sigla_pais
GROUP BY P.nome
ORDER BY Total_Atletas DESC;
"""
df4 = pd.read_sql(q4, conn)
st.dataframe(df4, use_container_width=True)

# ----------------------------
# 5) PROPORÇÃO DE MEDALHAS POR ATLETA
# ----------------------------
st.subheader("📊 Proporção de medalhas por atleta")

q5 = """
SELECT 
    P.nome AS Pais,
    COUNT(CASE WHEN C.medalha IN ('Ouro','Prata','Bronze') THEN 1 END) AS Total_Medalhas,
    COUNT(DISTINCT A.id_atleta) AS Total_Atletas,
    ROUND(
        COUNT(CASE WHEN C.medalha IN ('Ouro','Prata','Bronze') THEN 1 END) /
        NULLIF(COUNT(DISTINCT A.id_atleta), 0), 4
    ) AS Medalhas_por_Atleta
FROM Atleta A
JOIN Pais P ON P.sigla = A.sigla_pais
LEFT JOIN Compete C ON C.id_atleta = A.id_atleta
GROUP BY P.nome
ORDER BY Medalhas_por_Atleta DESC;
"""
df5 = pd.read_sql(q5, conn)
st.dataframe(df5, use_container_width=True)

st.caption("Interface atualizada com seletores independentes e nomes completos dos países.")
