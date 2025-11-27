import streamlit as st
import pandas as pd
import altair as alt
from db import get_connection
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# CONFIGURAÇÃO DA PÁGINA E VARIÁVEL GLOBAL
# ============================================================
st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

if "mostrar_sql" not in st.session_state:
    st.session_state.mostrar_sql = False

st.session_state.mostrar_sql = st.sidebar.toggle(
    "Mostrar consultas SQL",
    value=st.session_state.mostrar_sql
)

# ============================================================
# HEADER
# ============================================================
#ANTIGA ABAIXO NO COMENTÁRIO

#"https://s2-valor.glbimg.com/KYxtrUqkoAYg5M6sotCjBtrzaTI=/0x0:960x540/600x0/smart/filters:gifv():strip_icc()/i.s3.glbimg.com/v1/AUTH_63b422c2caee4269b8b34177e8876b93/internal_photos/bs/2024/x/J/9OkcpdT6qXCJOyRgElDg/primeiros-aneis-olimpicos.avif"


col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.image("Olympics-PNG-FREE (1).png", clamp=True)
    
st.title("Bem vindo à nossa dashboard de Olimpíadas!")

# ============================================================
# ESTILIZAÇÃO DAS TABELAS
# ============================================================
st.markdown("""
<style>
[data-testid="stDataFrame"] table tbody tr { height: 18px; }
div.block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

conn = get_connection()
cur = conn.cursor()

# ============================================================
# FUNÇÃO PARA LAYOUT ADAPTATIVO (CONTEÚDO + SQL)
# ============================================================
def bloco(conteudo_func, consulta_sql=None):
    if st.session_state.mostrar_sql and consulta_sql:
        col1, col2 = st.columns([3, 2])
        with col1:
            conteudo_func()
        with col2:
            st.code(consulta_sql, language="sql")
    else:
        conteudo_func()

# ============================================================
# 1 — RESUMO DO BANCO
# ============================================================
query_resumo = """
SELECT 
    COUNT(DISTINCT p.sigla) AS Paises,
    COUNT(DISTINCT a.id_atleta) AS Atletas,
    COUNT(DISTINCT e.id_evento) AS Modalidades,
    COUNT(DISTINCT e.esporte) AS Esportes,
    COUNT(DISTINCT o.ano) AS Edições,
    COUNT(*) AS Registros
FROM Compete c
JOIN Atleta a ON c.id_atleta = a.id_atleta
JOIN Pais p ON a.sigla_pais = p.sigla
JOIN Evento e ON c.id_evento = e.id_evento
JOIN Olimpiada o ON e.ano_olimpiada = o.ano;
"""

df_resumo = pd.read_sql(query_resumo, conn)
st.subheader("Resumo Geral do Banco")
bloco(lambda: st.dataframe(df_resumo, use_container_width=True, hide_index=True), query_resumo)

# ============================================================
# 2 — PAÍSES POR OLIMPÍADA
# ============================================================
query_paises = """
SELECT o.ano as Ano, COUNT(DISTINCT a.sigla_pais) AS Quantidade_Países
FROM Olimpiada o
JOIN Evento e ON e.ano_olimpiada = o.Ano
JOIN Compete c ON c.id_evento = e.id_evento
JOIN Atleta a ON a.id_atleta = c.id_atleta
GROUP BY o.Ano
ORDER BY o.Ano;
"""

df_paises = pd.read_sql(query_paises, conn)

def grafico_paises():
    chart = (
        alt.Chart(df_paises)
        .mark_bar()
        .encode(
            x=alt.X("Ano:O", axis=alt.Axis(labelAngle=-45)),
            y="Quantidade_Países:Q",
            tooltip=["Ano", "Quantidade_Países"]
        )
    )
    st.altair_chart(chart, use_container_width=True)

st.subheader("Número de países competidores de cada Olimpíada")
bloco(grafico_paises, query_paises)

# ============================================================
# 3 — ANO INAUGURAL
# ============================================================
query_inaug = """
SELECT esporte AS Esporte, MIN(ano_olimpiada) AS Ano_Inauguracao 
FROM evento 
JOIN olimpiada 
GROUP BY esporte  
ORDER BY Ano_Inauguracao;
"""

df_inaug = pd.read_sql(query_inaug, conn)
st.subheader("Ano inaugural de cada esporte")
bloco(lambda: st.dataframe(df_inaug, use_container_width=True, height=320, hide_index=True), query_inaug)

# ============================================================
# 4 — PAÍSES COM MAIS ATLETAS
# ============================================================
query_paises_atletas = """
SELECT p.nome AS Pais, COUNT(*) AS Total_Atletas
FROM Atleta a
JOIN Pais p ON p.sigla = a.sigla_pais
GROUP BY p.nome
ORDER BY Total_Atletas DESC
LIMIT 20;
"""

df_atletas = pd.read_sql(query_paises_atletas, conn)
st.subheader("Países com maior número de atletas")
bloco(lambda: st.dataframe(df_atletas, use_container_width=True, height=350, hide_index=True), query_paises_atletas)

# ============================================================
# 5 — ESPORTES COM MAIS PAÍSES
# ============================================================
query_esportes = """
SELECT e.esporte as Esporte, COUNT(DISTINCT a.sigla_pais) AS Quantidade_Países
FROM Evento e
JOIN Compete c ON c.id_evento = e.id_evento
JOIN Atleta a ON a.id_atleta = c.id_atleta
GROUP BY e.Esporte
ORDER BY Quantidade_Países DESC
LIMIT 10;
"""

df_esportes = pd.read_sql(query_esportes, conn)
st.subheader("Esportes com mais países competindo")
bloco(lambda: st.dataframe(df_esportes, use_container_width=True, height=330, hide_index=True), query_esportes)

# ============================================================
# 6 — MAIS MEDALHAS VS MÉDIA
# ============================================================
query_medalhas = """
SELECT o.ano as Ano, p.nome AS pais, COUNT(c.medalha) AS total_medalhas
FROM Olimpiada o
JOIN Evento e ON e.ano_olimpiada = o.Ano
JOIN Compete c ON c.id_evento = e.id_evento
JOIN Atleta a ON a.id_atleta = c.id_atleta
JOIN Pais p ON p.sigla = a.sigla_pais
WHERE c.medalha IS NOT NULL
GROUP BY o.Ano, p.nome 
ORDER BY o.Ano, total_medalhas DESC;
"""

df_all = pd.read_sql(query_medalhas, conn)
df_max = df_all.groupby("Ano").first().reset_index()
df_media = df_all.groupby("Ano")["total_medalhas"].mean().reset_index()
df_media.rename(columns={"total_medalhas": "media_medalhas"}, inplace=True)
df_join = df_max.merge(df_media, on="Ano")

df_long = pd.melt(
    df_join,
    id_vars=["Ano", "pais"],
    value_vars=["total_medalhas", "media_medalhas"],
    var_name="tipo",
    value_name="Medalhas",
)

def grafico_medalhas():
    chart = (
        alt.Chart(df_long)
        .mark_line(point=True)
        .encode(
            x=alt.X("Ano:O", axis=alt.Axis(labelAngle=-45)),
            y="Medalhas:Q",
            color="tipo:N",
            tooltip=["Ano", "pais", "Medalhas", "tipo"]
        )
    )
    st.altair_chart(chart, use_container_width=True)

st.subheader("País com mais medalhas vs média")
bloco(grafico_medalhas, query_medalhas)

# ============================================================
# 7 — PROPORÇÃO DE MEDALHAS POR PAÍS
# ============================================================
query_proporcao = """
SELECT p.nome AS pais, c.medalha, COUNT(*) AS total
FROM Compete c
JOIN Atleta a ON a.id_atleta = c.id_atleta
JOIN Pais p ON p.sigla = a.sigla_pais
WHERE c.medalha IN ('Ouro', 'Prata', 'Bronze')
GROUP BY p.nome, c.medalha;
"""

df_med = pd.read_sql(query_proporcao, conn)

def agrupar(df, min=10, max=10):
    df = df.sort_values("total", ascending=False).copy()
    if df.shape[0] > max:
        top = df.iloc[: max - 1]
        outros = df.iloc[max - 1 :]
        df = pd.concat(
            [top, pd.DataFrame({"pais": ["Outros"], "total": [outros["total"].sum()]})],
            ignore_index=True,
        )
    if df.shape[0] < min:
        faltando = min - df.shape[0]
        padding = pd.DataFrame(
            {"pais": [f"Outros_{i+1}" for i in range(faltando)], "total": [0] * faltando}
        )
        df = pd.concat([df, padding], ignore_index=True)
    return df

medalhas = ["Ouro", "Prata", "Bronze"]
df_list = []
for m in medalhas:
    df_tmp = agrupar(df_med[df_med["medalha"] == m], 10, 10).copy()
    df_tmp["medalha"] = m
    df_list.append(df_tmp)

df_plot = pd.concat(df_list, ignore_index=True)
paises_unicos = df_plot["pais"].unique()
color_scale = alt.Scale(domain=paises_unicos.tolist(), scheme="category20")

chart = (
    alt.Chart(df_plot)
    .mark_arc()
    .encode(
        theta="total:Q",
        color=alt.Color("pais:N", scale=color_scale, legend=alt.Legend(title="País")),
        column=alt.Column("medalha:N", header=alt.Header(labelAngle=0, title="Medalha"), spacing=100),
        tooltip=["pais", "total"]
    )
    .properties(width=250, height=250)
)

st.subheader("Proporção de medalhas por país")
if st.session_state.mostrar_sql:
    st.code(query_proporcao, language="sql")

st.altair_chart(chart, use_container_width=False)

cur.close()
conn.close()
