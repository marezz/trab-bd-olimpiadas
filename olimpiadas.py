import streamlit as st
import pandas as pd
from db import get_connection

st.set_page_config(page_title="Olimpíadas - Insights", layout="wide")
st.title("Olimpíadas")

# Conexão com o banco
ttry = None
try:
    conn = get_connection()
except Exception:
    conn = None

if conn is None:
    st.error("❌ Não foi possível conectar ao banco de dados.")
    st.stop()

# ----------------------------
# 1) Maior diversidade de países participantes
# ----------------------------
st.subheader("🌍 Olimpíadas com maior diversidade de países participantes")

q1 = """
SELECT O.ano AS Ano,
       COUNT(DISTINCT A.sigla_pais) AS Paises_Participantes
FROM Olimpiada O
JOIN Evento E ON E.ano_olimpiada = O.ano
JOIN Compete C ON C.id_evento = E.id_evento
JOIN Atleta A ON A.id_atleta = C.id_atleta
GROUP BY O.ano
ORDER BY Paises_Participantes DESC;
"""

df1 = pd.read_sql(q1, conn)
st.dataframe(df1, use_container_width=True)

# ----------------------------
# 2) Crescimento no número de eventos ao longo dos anos
# ----------------------------
st.subheader("📈 Crescimento do número de eventos ao longo dos anos")

q2 = """
SELECT O.ano AS Ano, COUNT(E.id_evento) AS Total_Eventos
FROM Olimpiada O
LEFT JOIN Evento E ON E.ano_olimpiada = O.ano
GROUP BY O.ano
ORDER BY Ano;
"""

df2 = pd.read_sql(q2, conn)
st.line_chart(df2.set_index("Ano"))
st.dataframe(df2, use_container_width=True)

# ----------------------------
# 3) Atletas mais jovens em uma Olimpíada específica
# ----------------------------
st.subheader("👶 Atletas mais jovens a competir (selecione a Olimpíada)")

# Carregar lista de olimpíadas
ot = pd.read_sql("SELECT ano FROM Olimpiada ORDER BY ano", conn)
olimpiada_selected = st.selectbox("Selecione a edição:", ot['ano'], key="jovens_selector")

q3 = """
SELECT A.nome AS Atleta, A.idade AS Idade, P.nome AS Pais, O.ano AS Ano, E.esporte AS Esporte
FROM Atleta A
JOIN Pais P ON P.sigla = A.sigla_pais
JOIN Compete C ON C.id_atleta = A.id_atleta
JOIN Evento E ON E.id_evento = C.id_evento
JOIN Olimpiada O ON O.ano = E.ano_olimpiada
WHERE O.ano = %s AND A.idade IS NOT NULL
ORDER BY A.idade ASC
LIMIT 20;
"""

df3 = pd.read_sql(q3, conn, params=[olimpiada_selected])
st.dataframe(df3, use_container_width=True)

# ----------------------------
# 4) Peso e altura médios por sexo
# ----------------------------
st.subheader("⚖️ Peso e altura médios por sexo")

q4 = """
SELECT sexo AS Sexo,
       ROUND(AVG(peso),2) AS Peso_Medio,
       ROUND(AVG(altura),2) AS Altura_Media
FROM Atleta
WHERE peso IS NOT NULL AND altura IS NOT NULL AND sexo IN ('M','F')
GROUP BY sexo;
"""

df4 = pd.read_sql(q4, conn)
st.dataframe(df4, use_container_width=True)