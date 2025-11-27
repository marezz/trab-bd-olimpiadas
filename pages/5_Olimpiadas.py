import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import altair as alt
from db import get_connection
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Olimpíadas - Insights", layout="wide")
st.title("Olimpíadas")

# ==================== SQL Toggle ====================
if "mostrar_sql" not in st.session_state:
    st.session_state.mostrar_sql = False

st.session_state.mostrar_sql = st.sidebar.toggle(
    "Mostrar consultas SQL",
    value=st.session_state.mostrar_sql
)

mostrar_sql = st.session_state.mostrar_sql

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

# ==================== Conexão ====================
conn = None
try:
    conn = get_connection()
except Exception as e:
    st.error(f"❌ Erro ao conectar ao banco: {e}")
    st.stop()

if conn is None:
    st.error("❌ Não foi possível conectar ao banco de dados.")
    st.stop()

# ==================== Filtro Global ====================
st.sidebar.header("Filtro Global")
anos_df = pd.read_sql("SELECT DISTINCT ano FROM Olimpiada ORDER BY ano DESC", conn)
anos = anos_df['ano'].tolist()

if not anos:
    st.error("Nenhum dado de Olimpíada encontrado.")
    st.stop()

ano_selecionado = st.sidebar.selectbox(
    "Selecione a edição da Olimpíada",
    options=anos,
    index=0
)

# ==================== Proporção de medalhas por atleta ====================
q_prop_medalhas = """
SELECT 
    A.nome AS Atleta,
    COUNT(*) AS Total_Medalhas,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS Proporcao_Pct
FROM Atleta A
JOIN Compete C ON A.id_atleta = C.id_atleta
JOIN Evento E ON C.id_evento = E.id_evento
WHERE E.ano_olimpiada = %s AND C.medalha IS NOT NULL
GROUP BY A.id_atleta, A.nome
ORDER BY Total_Medalhas DESC
LIMIT 10;
"""
df_prop_medalhas = pd.read_sql(q_prop_medalhas, conn, params=[ano_selecionado])
bloco("Proporção de medalhas por atleta", lambda: st.dataframe(df_prop_medalhas, use_container_width=True, hide_index=True), q_prop_medalhas)

# ==================== Top 10 atletas mais vitoriosos ====================
q_top_atletas = """
SELECT 
    A.nome AS Atleta,
    P.nome AS Pais,
    COUNT(*) AS Total_Medalhas,
    SUM(CASE WHEN C.medalha = 'Ouro' THEN 1 ELSE 0 END) AS Ouro,
    SUM(CASE WHEN C.medalha = 'Prata' THEN 1 ELSE 0 END) AS Prata,
    SUM(CASE WHEN C.medalha = 'Bronze' THEN 1 ELSE 0 END) AS Bronze
FROM Atleta A
JOIN Pais P ON A.sigla_pais = P.sigla
JOIN Compete C ON A.id_atleta = C.id_atleta
JOIN Evento E ON C.id_evento = E.id_evento
WHERE E.ano_olimpiada = %s AND C.medalha IN ('Ouro', 'Prata', 'Bronze')
GROUP BY A.id_atleta, A.nome, P.nome
ORDER BY Total_Medalhas DESC, Ouro DESC, Prata DESC
LIMIT 10;
"""
df_top_atletas = pd.read_sql(q_top_atletas, conn, params=[ano_selecionado])
bloco("Top 10 atletas mais vitoriosos", lambda: st.dataframe(df_top_atletas, use_container_width=True, hide_index=True), q_top_atletas)

# ==================== Top 10 países com atletas mais pesados ====================
q_paises_mais_pesados = """
SELECT 
    P.nome AS Pais,
    ROUND(AVG(A.peso), 2) AS Peso_Medio,
    COUNT(*) AS Qtd_Atletas
FROM Atleta A
JOIN Pais P ON A.sigla_pais = P.sigla
JOIN Compete C ON A.id_atleta = C.id_atleta
JOIN Evento E ON C.id_evento = E.id_evento
WHERE E.ano_olimpiada = %s AND A.peso IS NOT NULL
GROUP BY P.sigla, P.nome
HAVING COUNT(*) >= 3
ORDER BY Peso_Medio DESC
LIMIT 10;
"""
df_paises_pesados = pd.read_sql(q_paises_mais_pesados, conn, params=[ano_selecionado])
bloco("Top 10 países com atletas mais pesados", lambda: st.dataframe(df_paises_pesados, use_container_width=True, hide_index=True), q_paises_mais_pesados)

# ==================== Atleta mais jovem e mais velho por sexo ====================
q_idades_extremas = """
WITH Ranked AS (
    SELECT 
        A.nome,
        A.sexo,
        A.idade,
        ROW_NUMBER() OVER (PARTITION BY A.sexo ORDER BY A.idade ASC) AS rn_jovem,
        ROW_NUMBER() OVER (PARTITION BY A.sexo ORDER BY A.idade DESC) AS rn_velho
    FROM Atleta A
    JOIN Compete C ON A.id_atleta = C.id_atleta
    JOIN Evento E ON C.id_evento = E.id_evento
    WHERE E.ano_olimpiada = %s AND A.idade IS NOT NULL AND A.sexo IN ('M', 'F')
)
SELECT 
    sexo AS Sexo,
    MAX(CASE WHEN rn_jovem = 1 THEN nome END) AS Mais_Jovem,
    MAX(CASE WHEN rn_jovem = 1 THEN idade END) AS Idade_Jovem,
    MAX(CASE WHEN rn_velho = 1 THEN nome END) AS Mais_Velho,
    MAX(CASE WHEN rn_velho = 1 THEN idade END) AS Idade_Velho
FROM Ranked
WHERE rn_jovem = 1 OR rn_velho = 1
GROUP BY sexo;
"""
df_idades_extremas = pd.read_sql(q_idades_extremas, conn, params=[ano_selecionado])
bloco("Atleta mais jovem e mais velho por sexo", lambda: st.dataframe(df_idades_extremas, use_container_width=True, hide_index=True), q_idades_extremas)

# ==================== Proporção de gênero ====================
q_genero = """
SELECT 
    O.ano AS Ano,
    SUM(CASE WHEN A.sexo = 'M' THEN 1 ELSE 0 END) AS Homens,
    SUM(CASE WHEN A.sexo = 'F' THEN 1 ELSE 0 END) AS Mulheres
FROM Olimpiada O
JOIN Evento E ON E.ano_olimpiada = O.ano
JOIN Compete C ON C.id_evento = E.id_evento
JOIN Atleta A ON A.id_atleta = C.id_atleta
WHERE A.sexo IN ('M', 'F')
GROUP BY O.ano
ORDER BY O.ano;
"""
df_genero = pd.read_sql(q_genero, conn)
def plot_genero():
    if not df_genero.empty:
        ano_row = df_genero[df_genero['Ano'] == ano_selecionado]
        if not ano_row.empty:
            df_pizza = pd.DataFrame({
                'Sexo': ['Homens', 'Mulheres'],
                'Quantidade': [int(ano_row['Homens'].iloc[0]), int(ano_row['Mulheres'].iloc[0])]
            })
            chart_pizza = alt.Chart(df_pizza).mark_arc(innerRadius=0).encode(
                theta=alt.Theta(field="Quantidade", type="quantitative"),
                color=alt.Color(field="Sexo", type="nominal", scale=alt.Scale(range=['#1f77b4', "#f065ba"])),
                tooltip=["Sexo", "Quantidade"]
            )
            st.altair_chart(chart_pizza, use_container_width=True)
        
        df_genero['% Mulheres'] = (df_genero['Mulheres'] / (df_genero['Homens'] + df_genero['Mulheres']) * 100).round(1)
        
bloco("Proporção de gênero por edição", plot_genero, q_genero)
chart_linha = alt.Chart(df_genero).mark_line(point=True, color="#f065ba").encode(
        x=alt.X("Ano:O"),
        y=alt.Y("% Mulheres:Q", title="% Mulheres"),
        tooltip=["Ano", "% Mulheres"]
    )
st.altair_chart(chart_linha, use_container_width=True)  

# ==================== Número de países por edição ====================
q_paises_ano = """
SELECT 
    O.ano AS Ano,
    COUNT(DISTINCT A.sigla_pais) AS Paises_Participantes
FROM Olimpiada O
JOIN Evento E ON E.ano_olimpiada = O.Ano
JOIN Compete C ON C.id_evento = E.id_evento
JOIN Atleta A ON A.id_atleta = C.id_atleta
GROUP BY O.Ano
ORDER BY O.Ano;
"""

df_paises_ano = pd.read_sql(q_paises_ano, conn)
bloco("Número de países por edição", lambda: st.dataframe(df_paises_ano, use_container_width=True, hide_index=True), q_paises_ano)
st.bar_chart(df_paises_ano.set_index('Ano'), sort='Paises_Participantes')
