import streamlit as st
from db import get_connection

st.title("Olimpiadas")

conn = get_connection()
cur = conn.cursor()

cur.execute("SELECT * FROM olimpiada")
dados = cur.fetchall()

st.write(dados)

cur.close()
conn.close()
