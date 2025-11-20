import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="CRUD Olimpíadas", page_icon="🏅", layout="wide")
st.title("Início")
st.write("Use o menu lateral para navegar.")
st.write("Este aplicativo permite realizar operações CRUD em um banco de dados SQLite contendo informações sobre as Olimpíadas.")