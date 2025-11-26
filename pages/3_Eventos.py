import streamlit as st
import pandas as pd
import altair as alt
from db import get_connection

st.set_page_config(page_title="Análise de Eventos", page_icon="📅", layout="wide")
st.title("Eventos")

conn = get_connection()

@st.cache_data(ttl=600)
def listar_esportes(_conn):
    q = "SELECT DISTINCT esporte FROM Evento ORDER BY esporte"
    return pd.read_sql(q, _conn)["esporte"].tolist()

esportes = listar_esportes(conn)

# -------------------- Sidebar Toggle --------------------
if "mostrar_sql" not in st.session_state:
    st.session_state.mostrar_sql = False

st.sidebar.toggle("Mostrar SQL", key="mostrar_sql")

# -------------------- Bloco utilitário --------------------
def bloco(conteudo, consulta=None):
    mostrar = st.session_state.get("mostrar_sql", False)
    if mostrar and consulta:
        col1, col2 = st.columns([3, 2], gap="small")
        with col1:
            conteudo()
        with col2:
            st.code(consulta, language="sql")
    else:
        conteudo()


# -------------------- 1. Top 10 atletas --------------------
st.header("Top 10 atletas por medalhas no esporte escolhido")
esporte_sel = st.selectbox("Esporte:", esportes)

q_atletas = """
SELECT 
    A.nome AS Nome,
    (
        SELECT COUNT(*)
        FROM Compete C
        JOIN Evento E ON E.id_evento = C.id_evento
        WHERE C.id_atleta = A.id_atleta
          AND C.medalha <> 'Sem Medalha'
          AND E.esporte = %s
    ) AS Total_Medalhas
FROM Atleta A
ORDER BY Total_Medalhas DESC
LIMIT 10;
"""

df_atletas = pd.read_sql(q_atletas, conn, params=[esporte_sel])

def render_atletas():
    st.dataframe(df_atletas, use_container_width=True)
    chart = (
        alt.Chart(df_atletas.sort_values("Total_Medalhas", ascending=False))
        .mark_bar()
        .encode(
            x=alt.X("Nome:N", sort=None, axis=alt.Axis(labelAngle=-45)),
            y="Total_Medalhas:Q"
        )
        .properties(height=400)
    )
    st.altair_chart(chart, use_container_width=True)

bloco(render_atletas, q_atletas)


# -------------------- 2. Top 10 países --------------------
st.header("Top 10 países por medalhas no esporte escolhido")
esporte_pais = st.selectbox("Esporte:", esportes, key="pais")

q_paises = """
SELECT 
    P.nome AS País,
    COUNT(*) AS Total_Medalhas
FROM Atleta A
JOIN Pais P ON P.sigla = A.sigla_pais
JOIN Compete C ON C.id_atleta = A.id_atleta
JOIN Evento E ON E.id_evento = C.id_evento
WHERE C.medalha <> 'Sem Medalha'
  AND E.esporte = %s
GROUP BY P.nome
ORDER BY Total_Medalhas DESC
LIMIT 10;
"""

df_pais = pd.read_sql(q_paises, conn, params=[esporte_pais])

def render_paises():
    st.dataframe(df_pais, use_container_width=True)

bloco(render_paises, q_paises)


# -------------------- 3. Esportes mais competitivos --------------------
st.header("Esportes com mais países competindo")

q_comp = """
SELECT 
    E.esporte,
    COUNT(DISTINCT A.sigla_pais) AS total_paises 
FROM Evento E 
JOIN Compete C ON C.id_evento = E.id_evento 
JOIN Atleta A ON A.id_atleta = C.id_atleta 
GROUP BY E.esporte 
ORDER BY total_paises DESC
LIMIT 10;
"""

df_comp = pd.read_sql(q_comp, conn)

def render_comp():
    st.dataframe(df_comp, use_container_width=True)
    chart = (
        alt.Chart(df_comp.sort_values("total_paises", ascending=False))
        .mark_bar()
        .encode(
            x=alt.X("esporte:N", sort=None),
            y="total_paises:Q"
        )
        .properties(height=400)
    )
    st.altair_chart(chart, use_container_width=True)

bloco(render_comp, q_comp)


# -------------------- 4. Distribuição por sexo --------------------
st.header("Distribuição de participantes por sexo")
esporte_sexo = st.selectbox("Esporte:", esportes, key="sexo")

q_sexo = """
SELECT A.sexo, COUNT(*) AS total
FROM Atleta A
JOIN Compete C ON C.id_atleta = A.id_atleta
JOIN Evento E ON E.id_evento = C.id_evento
WHERE E.esporte = %s
GROUP BY A.sexo;
"""

df_sexo = pd.read_sql(q_sexo, conn, params=[esporte_sexo])

def render_sexo():
    st.dataframe(df_sexo, use_container_width=True)
    pie = (
        alt.Chart(df_sexo)
        .mark_arc()
        .encode(theta="total:Q", color="sexo:N")
        .properties(height=400)
    )
    st.altair_chart(pie, use_container_width=True)

bloco(render_sexo, q_sexo)


# -------------------- 5. Modalidades do esporte --------------------
st.header("Modalidades disponíveis")
esporte_mod = st.selectbox("Esporte:", esportes, key="mods")

q_mod = """
SELECT DISTINCT modalidade
FROM Evento
WHERE esporte = %s
ORDER BY modalidade;
"""

df_mod = pd.read_sql(q_mod, conn, params=[esporte_mod])

def render_mod():
    st.dataframe(df_mod, use_container_width=True)

bloco(render_mod, q_mod)


# -------------------- 6. Médias físicas --------------------
st.header("Estatísticas médias por esporte")
esporte_media = st.selectbox("Esporte:", esportes, key="media")

q_media = """
SELECT 
    AVG(A.altura) AS altura_media,
    AVG(A.peso) AS peso_medio,
    AVG(A.idade) AS idade_media
FROM Atleta A
JOIN Compete C ON C.id_atleta = A.id_atleta
JOIN Evento E ON E.id_evento = C.id_evento
WHERE E.esporte = %s;
"""

df_media = pd.read_sql(q_media, conn, params=[esporte_media])

def render_media():
    st.dataframe(df_media, use_container_width=True)

bloco(render_media, q_media)

conn.close()
