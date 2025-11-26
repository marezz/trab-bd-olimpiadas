import streamlit as st
import pandas as pd
from db import get_connection

st.set_page_config(page_title="Países - Olimpíadas", layout="wide", page_icon="🌍")
st.title("Países")

# ---------------------------- CONEXÃO ----------------------------
try:
    conn = get_connection()
except Exception:
    conn = None

if conn is None:
    st.error("Não foi possível conectar ao banco de dados.")
    st.stop()

paises = pd.read_sql("SELECT sigla, nome FROM Pais ORDER BY nome", conn)

def nome_do_pais(sigla):
    return paises.loc[paises['sigla'] == sigla, 'nome'].iloc[0]

# ---------------------------- FUNÇÃO DE BLOCO COM SQL ----------------------------
def bloco(conteudo_func, consulta_sql=None, params=None):
    if st.session_state.get("mostrar_sql", False) and consulta_sql:
        col1, col2 = st.columns([3, 2])
        with col1:
            conteudo_func()
        with col2:
            st.code(
                pd.io.sql.get_schema(pd.read_sql(consulta_sql, conn, params=params), "query_placeholder")
                if params is None else consulta_sql,
                language="sql"
            )
    else:
        conteudo_func()

if "mostrar_sql" not in st.session_state:
    st.session_state.mostrar_sql = False

st.session_state.mostrar_sql = st.sidebar.toggle(
    "Mostrar consultas SQL",
    value=st.session_state.mostrar_sql
)

# ---------------------------- 1) RANKING DE ATLETAS ----------------------------
st.subheader("Ranking de atletas mais vitoriosos do país")
pais_ranking = st.selectbox("Selecione o país:", options=paises['sigla'], format_func=nome_do_pais, key="rank_selector")

q1 = """
SELECT A.nome AS Atleta, COUNT(*) AS Total_Medalhas
FROM Atleta A
JOIN Pais P ON P.sigla = A.sigla_pais
JOIN Compete C ON C.id_atleta = A.id_atleta
WHERE P.sigla = %s AND C.medalha IN ('Ouro','Prata','Bronze')
GROUP BY A.id_atleta
ORDER BY Total_Medalhas DESC
LIMIT 20;
"""
df1 = pd.read_sql(q1, conn, params=[pais_ranking])
bloco(lambda: st.dataframe(df1, use_container_width=True, hide_index=True), q1, params=[pais_ranking])

# ---------------------------- 2) EVENTOS COM MAIS MEDALHAS ----------------------------
st.subheader("Eventos em que o país mais ganha medalhas")
pais_eventos = st.selectbox("Selecione o país:", options=paises['sigla'], format_func=nome_do_pais, key="eventos_selector")

q2 = """
SELECT P.nome AS Pais, E.esporte AS Esporte, E.modalidade AS Modalidade,
       COUNT(*) AS Total_Medalhas
FROM Atleta A
JOIN Pais P ON P.sigla = A.sigla_pais
JOIN Compete C ON C.id_atleta = A.id_atleta
JOIN Evento E ON E.id_evento = C.id_evento
WHERE P.sigla = %s AND C.medalha IN ('Ouro','Prata','Bronze')
GROUP BY P.nome, E.esporte, E.modalidade
ORDER BY Total_Medalhas DESC
LIMIT 10;
"""
df2 = pd.read_sql(q2, conn, params=[pais_eventos])
bloco(lambda: st.dataframe(df2, use_container_width=True, hide_index=True), q2, params=[pais_eventos])

# ---------------------------- 7) MEDALHAS VS MÉDIA GLOBAL ----------------------------
st.subheader("Medalhas do país vs média global por edição")
pais_comp = st.selectbox("Selecione o país:", options=paises['sigla'], format_func=nome_do_pais, key="comparacao_selector")

q7 = """
WITH medalhas AS (
    SELECT O.ano, A.sigla_pais, COUNT(*) AS Medalhas
    FROM Olimpiada O
    LEFT JOIN Evento E ON E.ano_olimpiada = O.ano
    LEFT JOIN Compete C ON C.id_evento = E.id_evento
    LEFT JOIN Atleta A ON A.id_atleta = C.id_atleta
    WHERE C.medalha IN ('Ouro','Prata','Bronze')
    GROUP BY O.ano, A.sigla_pais
),
medias AS (
    SELECT ano, AVG(Medalhas) AS Media_Global
    FROM medalhas
    GROUP BY ano
)
SELECT m.ano AS Ano,
       COALESCE((SELECT Medalhas FROM medalhas WHERE ano = m.ano AND sigla_pais = %s), 0) AS Medalhas_Pais,
       medias.Media_Global
FROM medias
JOIN medalhas m ON m.ano = medias.ano
GROUP BY Ano
ORDER BY Ano;
"""
df7 = pd.read_sql(q7, conn, params=[pais_comp])
df7 = df7.groupby("Ano", as_index=False).first()
bloco(lambda: st.dataframe(df7, use_container_width=True, hide_index=True), q7, params=[pais_comp])

chart_df7 = df7.set_index("Ano")[["Medalhas_Pais", "Media_Global"]]
colors = ["#FFEE00A7", "#0051FFC8"]
st.line_chart(chart_df7, color=colors)

# ---------------------------- 6) PAÍSES QUE ESTREARAM NO MESMO ANO ----------------------------
st.subheader("Países que estrearam no mesmo ano do país selecionado")
pais_estreia = st.selectbox("Selecione o país:", options=paises['sigla'], format_func=nome_do_pais, key="estreia_selector")

q6 = """
SELECT P2.nome AS Pais, MIN(O2.ano) AS Ano_Estreia
FROM Pais P2
JOIN Atleta A2 ON A2.sigla_pais = P2.sigla
JOIN Compete C2 ON C2.id_atleta = A2.id_atleta
JOIN Evento E2 ON E2.id_evento = C2.id_evento
JOIN Olimpiada O2 ON O2.ano = E2.ano_olimpiada
GROUP BY P2.nome
HAVING Ano_Estreia = (
    SELECT MIN(O.ano)
    FROM Atleta A
    JOIN Compete C ON C.id_atleta = A.id_atleta
    JOIN Evento E ON E.id_evento = C.id_evento
    JOIN Olimpiada O ON O.ano = E.ano_olimpiada
    WHERE A.sigla_pais = %s
)
ORDER BY P2.nome;
"""
df6 = pd.read_sql(q6, conn, params=[pais_estreia])
bloco(lambda: st.dataframe(df6, use_container_width=True, hide_index=True), q6, params=[pais_estreia])

# ---------------------------- 8) ESPORTES SEM MEDALHAS ----------------------------
st.subheader("Esportes em que o país competiu, mas nunca ganhou medalha")
pais_sem_medalha = st.selectbox("Selecione o país:", options=paises['sigla'], format_func=nome_do_pais, key="sem_medalha_selector")

q8 = """
SELECT DISTINCT E.modalidade AS Modalidade, E.esporte AS Esporte
FROM Evento E
LEFT JOIN (
    SELECT C.id_evento
    FROM Compete C
    JOIN Atleta A ON A.id_atleta = C.id_atleta
    WHERE A.sigla_pais = %s
      AND C.medalha IN ('Ouro', 'Prata', 'Bronze')
) M ON M.id_evento = E.id_evento
JOIN Compete C2 ON C2.id_evento = E.id_evento
JOIN Atleta A2 ON A2.id_atleta = C2.id_atleta
WHERE A2.sigla_pais = %s
  AND M.id_evento IS NULL
ORDER BY Esporte, Modalidade;
"""
df8 = pd.read_sql(q8, conn, params=[pais_sem_medalha, pais_sem_medalha])
bloco(lambda: st.dataframe(df8, use_container_width=True, hide_index=True), q8, params=[pais_sem_medalha, pais_sem_medalha])

conn.close()
