import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from db import get_connection
from dotenv import load_dotenv
import altair as alt

load_dotenv()

conn = get_connection()
cur = conn.cursor()

st.set_page_config(page_title="Dashboard", page_icon="📊", layout='wide')
st.title("Bem vindo a nossa dashboard de Olimpíadas!")

st.subheader("Resumo Geral do Banco")

query = f"""
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
;"""

df_resumo = pd.read_sql(query, conn)
st.dataframe(df_resumo)

st.subheader("Maior quantidade de países por Olimpíada")

# Consulta SQL: contar países distintos por ano de Olimpíada
query = """
SELECT o.ano, COUNT(DISTINCT a.sigla_pais) AS qtd_paises
FROM Olimpiada o
JOIN Evento e ON e.ano_olimpiada = o.ano
JOIN Compete c ON c.id_evento = e.id_evento
JOIN Atleta a ON a.id_atleta = c.id_atleta
GROUP BY o.ano
ORDER BY o.ano
"""

df = pd.read_sql(query, conn)

# Gráfico de barras Altair
chart = alt.Chart(df).mark_bar().encode(
    x=alt.X('ano:O', sort='-y', title='Ano da Olimpíada'),
    y=alt.Y('qtd_paises:Q', title='Quantidade de países'),
    tooltip=['ano', 'qtd_paises']
).properties(
    width=700,
    height=400
)

st.altair_chart(chart)

st.subheader("Ano inaugural de cada esporte nas olimpíadas """)

query = f"""
        SELECT esporte as Esporte, min(ano_olimpiada) as Ano_Inauguracao 
        FROM evento join olimpiada 
        GROUP BY esporte  
        ORDER BY Ano_Inauguracao;"""

df_inauguracao = pd.read_sql(query, conn)
st.dataframe(df_inauguracao)

st.subheader("Países com maior número de atletas inscritos")

q4 = """
SELECT P.nome AS Pais, COUNT(*) AS Total_Atletas
FROM Atleta A
JOIN Pais P ON P.sigla = A.sigla_pais
GROUP BY P.nome
ORDER BY Total_Atletas DESC;
"""
df4 = pd.read_sql(q4, conn)
st.dataframe(df4, use_container_width=True)

st.subheader("Esportes com mais países competindo")

# Consulta SQL: contar países distintos por esporte
query = """
SELECT e.esporte, COUNT(DISTINCT a.sigla_pais) AS qtd_paises
FROM Evento e
JOIN Compete c ON c.id_evento = e.id_evento
JOIN Atleta a ON a.id_atleta = c.id_atleta
GROUP BY e.esporte
ORDER BY qtd_paises DESC
LIMIT 10
"""

df = pd.read_sql(query, conn)
st.dataframe(df, use_container_width=True)

st.subheader("Pais com mais medalhas VS média por Olimpíada")

# Consulta SQL sem usar window functions
query = """
-- Total de medalhas por país e ano
SELECT o.ano, p.nome AS pais, COUNT(c.medalha) AS total_medalhas
FROM Olimpiada o
JOIN Evento e ON e.ano_olimpiada = o.ano
JOIN Compete c ON c.id_evento = e.id_evento
JOIN Atleta a ON a.id_atleta = c.id_atleta
JOIN Pais p ON p.sigla = a.sigla_pais
WHERE c.medalha IS NOT NULL
GROUP BY o.ano, p.nome
ORDER BY o.ano, total_medalhas DESC
"""

df_all = pd.read_sql(query, conn)

# Selecionar o país com mais medalhas por ano
df_max = df_all.groupby('ano').first().reset_index()  # pega o primeiro após sort decrescente

# Média de medalhas por edição
df_media = df_all.groupby('ano')['total_medalhas'].mean().reset_index()
df_media.rename(columns={'total_medalhas': 'media_medalhas'}, inplace=True)

# Juntar
df = df_max.merge(df_media, on='ano')

# Transformar em formato long para Altair
df_long = pd.melt(df, id_vars=['ano', 'pais'], value_vars=['total_medalhas', 'media_medalhas'],
                  var_name='tipo', value_name='medalhas')

# Gráfico de linha Altair
chart = alt.Chart(df_long).mark_line(point=True).encode(
    x=alt.X('ano:O', title='Ano da Olimpíada'),
    y=alt.Y('medalhas:Q', title='Medalhas'),
    color=alt.Color('tipo:N', title='Tipo', scale=alt.Scale(domain=['total_medalhas', 'media_medalhas'],
                                                            range=['#1f77b4', '#ff7f0e'])),
    tooltip=['ano', 'pais', 'medalhas', 'tipo']
).properties(
    width=700,
    height=400
)

st.altair_chart(chart)

st.subheader("Proporção de medalhas por país")

# Consulta SQL: contar medalhas por país e tipo
query = """
SELECT p.nome AS pais, c.medalha, COUNT(*) AS total
FROM Compete c
JOIN Atleta a ON a.id_atleta = c.id_atleta
JOIN Pais p ON p.sigla = a.sigla_pais
WHERE c.medalha IN ('Ouro', 'Prata', 'Bronze')
GROUP BY p.nome, c.medalha
"""

df = pd.read_sql(query, conn)

def agrupar_outros(df_medalha, min_fatias=15, max_fatias=20):
    df_medalha = df_medalha.copy()
    df_medalha = df_medalha.sort_values("total", ascending=False)

    # máximo: agrega excedentes em "Outros"
    if df_medalha.shape[0] > max_fatias:
        top = df_medalha.iloc[:max_fatias - 1]
        outros = df_medalha.iloc[max_fatias - 1:]
        df_medalha = pd.concat([
            top[["pais", "total"]],
            pd.DataFrame({"pais": ["Outros"], "total": [outros["total"].sum()]})
        ], ignore_index=True)

    # mínimo: preenche com "Outros_x" até atingir min_fatias
    if df_medalha.shape[0] < min_fatias:
        faltam = min_fatias - df_medalha.shape[0]
        df_pad = pd.DataFrame({
            "pais": [f"Outros_{i+1}" for i in range(faltam)],
            "total": [0] * faltam
        })
        df_medalha = pd.concat([df_medalha, df_pad], ignore_index=True)

    return df_medalha


def pie_chart(df_medalha, titulo, min_fatias=10, max_fatias=10):
    df_plot = agrupar_outros(df_medalha, min_fatias, max_fatias)
    df_plot = df_plot.sort_values("total", ascending=False)

    chart = (
        alt.Chart(df_plot)
        .mark_arc()
        .encode(
            theta="total:Q",
            color=alt.Color("pais:N", sort=df_plot["pais"].tolist()),
            tooltip=["pais", "total"],
        )
        .properties(title=titulo)
    )

    return chart


# Criar gráficos separados
df_gold = df[df['medalha'] == 'Ouro']
df_silver = df[df['medalha'] == 'Prata']
df_bronze = df[df['medalha'] == 'Bronze']

st.altair_chart(pie_chart(df_gold, "Ouro"))
st.altair_chart(pie_chart(df_silver, "Prata"))
st.altair_chart(pie_chart(df_bronze, "Bronze"))

cur.close()
conn.close()
