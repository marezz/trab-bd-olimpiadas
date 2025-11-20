import streamlit as st
from db import get_connection

st.title("Cadastro")

conn = get_connection()
cur = conn.cursor()

cur.execute("SELECT * FROM atleta")
dados = cur.fetchall()

st.write(dados)

cur.close()
conn.close()
