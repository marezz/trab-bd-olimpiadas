import streamlit as st
import mysql.connector
import pandas as pd
from mysql.connector import Error
from db import get_connection
import os
from dotenv import load_dotenv

st.title("Eventos")

conn = get_connection()
cur = conn.cursor()

st.title("🥇 10 atletas com mais medalhas de cada evento """)
     
modalidade = pd.read_sql("""
    SELECT DISTINCT esporte 
    FROM Evento
    ORDER BY esporte;
""", conn)["esporte"].tolist()

escolhida = st.selectbox("Selecione a esporte:", modalidade)

query = f"""
        SELECT 
        A.nome,
        COUNT(*) AS total_medalhas
    FROM Atleta A
    JOIN Compete C ON C.id_atleta = A.id_atleta
    JOIN Evento E ON E.id_evento = C.id_evento
    WHERE C.medalha <> "Sem Medalha"
    AND E.esporte = %s
    GROUP BY A.id_atleta, A.nome
    ORDER BY total_medalhas DESC;"""


df = pd.read_sql(query, conn, params=[escolhida])
st.dataframe(df)

st.title("🥇 10 Países com mais medalhas de cada evento """)

modalidade_pais = pd.read_sql("""
    SELECT DISTINCT esporte 
    FROM Evento
    ORDER BY esporte;
""", conn)["esporte"].tolist()

escolhida_pais = st.selectbox("Selecione o esporte:", modalidade_pais)

query = f"""
        SELECT 
        A.sigla_pais,
        COUNT(*) AS total_medalhas
    FROM Atleta A
    JOIN Compete C ON C.id_atleta = A.id_atleta
    Join Pais P ON P.sigla = A.sigla_pais
    JOIN Evento E ON E.id_evento = C.id_evento
    WHERE C.medalha <> "Sem Medalha"
    AND E.esporte = %s
    GROUP BY P.sigla
    ORDER BY total_medalhas DESC;"""

df_pais = pd.read_sql(query, conn, params=[escolhida_pais])
st.dataframe(df_pais)

cur.close()
conn.close()
