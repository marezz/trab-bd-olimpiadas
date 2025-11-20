import streamlit as st
import mysql.connector
import pandas as pd
from mysql.connector import Error
import os
from dotenv import load_dotenv
from sqlalchemy import text

# Carregar variáveis de ambiente
load_dotenv()

# Configuração da página
st.set_page_config(page_title="CRUD Olimpíadas", page_icon="🏅", layout="wide")

# Função para criar conexão com o banco
@st.cache_resource
def criar_conexao():
    try:
        conexao = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'olimpiadas_db')
        )
        return conexao
    except Error as e:
        st.error(f"Erro ao conectar ao MySQL: {e}")
        return None

# ==================== FUNÇÕES CRUD - PAÍS ====================
def inserir_pais(conexao, sigla, nome):
    try:
        cursor = conexao.cursor()
        cursor.execute("INSERT INTO Pais (sigla, nome) VALUES (%s, %s)", (sigla, nome))
        conexao.commit()
        cursor.close()
        return True
    except Error as e:
        st.error(f"Erro: {e}")
        return False

def atualizar_pais(conexao, sigla, novo_nome):
    try:
        cursor = conexao.cursor()
        cursor.execute("UPDATE Pais SET nome = %s WHERE sigla = %s", (novo_nome, sigla))
        conexao.commit()
        cursor.close()
        return True
    except Error as e:
        st.error(f"Erro: {e}")
        return False

def deletar_pais(conexao, sigla):
    try:
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM Pais WHERE sigla = %s", (sigla,))
        conexao.commit()
        cursor.close()
        return True
    except Error as e:
        st.error(f"Erro: {e}")
        return False

# ==================== FUNÇÕES CRUD - OLIMPÍADA ====================
def inserir_olimpiada(conexao, ano, estacao, sede):
    try:
        cursor = conexao.cursor()
        cursor.execute("INSERT INTO Olimpiada (ano, estacao, sede) VALUES (%s, %s, %s)", 
                      (ano, estacao, sede))
        conexao.commit()
        cursor.close()
        return True
    except Error as e:
        st.error(f"Erro: {e}")
        return False

def atualizar_olimpiada(conexao, ano, estacao, sede):
    try:
        cursor = conexao.cursor()
        cursor.execute("UPDATE Olimpiada SET estacao = %s, sede = %s WHERE ano = %s", 
                      (estacao, sede, ano))
        conexao.commit()
        cursor.close()
        return True
    except Error as e:
        st.error(f"Erro: {e}")
        return False

def deletar_olimpiada(conexao, ano):
    try:
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM Olimpiada WHERE ano = %s", (ano,))
        conexao.commit()
        cursor.close()
        return True
    except Error as e:
        st.error(f"Erro: {e}")
        return False

# ==================== FUNÇÕES CRUD - ATLETA ====================
def inserir_atleta(conexao, nome, sexo, peso, altura, idade, sigla_pais):
    try:
        cursor = conexao.cursor()
        cursor.execute(
            """INSERT INTO Atleta (nome, sexo, peso, altura, idade, sigla_pais) 
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (nome, sexo, peso, altura, idade, sigla_pais)
        )
        conexao.commit()
        cursor.close()
        return True
    except Error as e:
        st.error(f"Erro: {e}")
        return False

def atualizar_atleta(conexao, id_atleta, nome, sexo, peso, altura, idade, sigla_pais):
    try:
        cursor = conexao.cursor()
        cursor.execute(
            """UPDATE Atleta SET nome = %s, sexo = %s, peso = %s, altura = %s, 
               idade = %s, sigla_pais = %s WHERE id_atleta = %s""",
            (nome, sexo, peso, altura, idade, sigla_pais, id_atleta)
        )
        conexao.commit()
        cursor.close()
        return True
    except Error as e:
        st.error(f"Erro: {e}")
        return False

def deletar_atleta(conexao, id_atleta):
    try:
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM Atleta WHERE id_atleta = %s", (id_atleta,))
        conexao.commit()
        cursor.close()
        return True
    except Error as e:
        st.error(f"Erro: {e}")
        return False

# ==================== FUNÇÕES CRUD - EVENTO ====================
def inserir_evento(conexao, esporte, modalidade, ano_olimpiada):
    try:
        cursor = conexao.cursor()
        cursor.execute(
            """INSERT INTO Evento (esporte, modalidade, ano_olimpiada) 
               VALUES (%s, %s, %s)""",
            (esporte, modalidade, ano_olimpiada)
        )
        conexao.commit()
        cursor.close()
        return True
    except Error as e:
        st.error(f"Erro: {e}")
        return False

def atualizar_evento(conexao, id_evento, esporte, modalidade, ano_olimpiada):
    try:
        cursor = conexao.cursor()
        cursor.execute(
            """UPDATE Evento SET esporte = %s, modalidade = %s, ano_olimpiada = %s 
               WHERE id_evento = %s""",
            (esporte, modalidade, ano_olimpiada, id_evento)
        )
        conexao.commit()
        cursor.close()
        return True
    except Error as e:
        st.error(f"Erro: {e}")
        return False

def deletar_evento(conexao, id_evento):
    try:
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM Evento WHERE id_evento = %s", (id_evento,))
        conexao.commit()
        cursor.close()
        return True
    except Error as e:
        st.error(f"Erro: {e}")
        return False

# ==================== FUNÇÕES CRUD - COMPETE ====================
def inserir_compete(conexao, id_atleta, id_evento, medalha):
    try:
        cursor = conexao.cursor()
        cursor.execute(
            "INSERT INTO Compete (id_atleta, id_evento, medalha) VALUES (%s, %s, %s)",
            (id_atleta, id_evento, medalha)
        )
        conexao.commit()
        cursor.close()
        return True
    except Error as e:
        st.error(f"Erro: {e}")
        return False

def atualizar_compete(conexao, id_atleta, id_evento, medalha):
    try:
        cursor = conexao.cursor()
        cursor.execute(
            "UPDATE Compete SET medalha = %s WHERE id_atleta = %s AND id_evento = %s",
            (medalha, id_atleta, id_evento)
        )
        conexao.commit()
        cursor.close()
        return True
    except Error as e:
        st.error(f"Erro: {e}")
        return False

def deletar_compete(conexao, id_atleta, id_evento):
    try:
        cursor = conexao.cursor()
        cursor.execute(
            "DELETE FROM Compete WHERE id_atleta = %s AND id_evento = %s",
            (id_atleta, id_evento)
        )
        conexao.commit()
        cursor.close()
        return True
    except Error as e:
        st.error(f"Erro: {e}")
        return False

# ==================== LEITURA ====================
def ler_tabela(conexao, tabela):
    try:
        query = f"SELECT * FROM {tabela}"
        df = pd.read_sql(query, conexao)
        return df
    except Error as e:
        st.error(f"Erro ao ler dados: {e}")
        return pd.DataFrame()

# ==================== INTERFACE PRINCIPAL ====================
def main():
    st.title("🏅 Sistema CRUD - Banco de Dados Olimpíadas")
    st.markdown("---")
    
    conexao = criar_conexao()
    
    if conexao and conexao.is_connected():
        st.success("✅ Conectado ao MySQL - olimpiadas_db")
        
        # Sidebar
        st.sidebar.header("📊 Selecione a Tabela")
        tabela = st.sidebar.selectbox(
            "Tabela:",
            ["Pais", "Olimpiada", "Atleta", "Evento", "Compete"]
        )
        
        st.sidebar.markdown("---")
        operacao = st.sidebar.radio(
            "Operação:",
            ["📋 Visualizar", "➕ Inserir", "✏️ Atualizar", "🗑️ Deletar"]
        )
        
        st.markdown("---")
        
        # ========== PAÍS ==========
        if tabela == "Pais":
            st.header(f"🌍 Gerenciar: {tabela}")
            
            if operacao == "📋 Visualizar":
                df = ler_tabela(conexao, "Pais")
                st.dataframe(df, use_container_width=True)
                st.info(f"Total de países: {len(df)}")
            
            elif operacao == "➕ Inserir":
                with st.form("form_pais"):
                    sigla = st.text_input("Sigla (3 letras)", max_chars=3).upper()
                    nome = st.text_input("Nome do País")
                    
                    if st.form_submit_button("💾 Salvar", type="primary"):
                        if sigla and nome:
                            if inserir_pais(conexao, sigla, nome):
                                st.success("✅ País inserido com sucesso!")
                                st.balloons()
                        else:
                            st.warning("Preencha todos os campos!")
            
            elif operacao == "✏️ Atualizar":
                df = ler_tabela(conexao, "Pais")
                if not df.empty:
                    sigla = st.selectbox("Selecione o País (Sigla)", df['sigla'].tolist())
                    nome_atual = df[df['sigla'] == sigla]['nome'].values[0]
                    novo_nome = st.text_input("Novo Nome", value=nome_atual)
                    
                    if st.button("🔄 Atualizar", type="primary"):
                        if atualizar_pais(conexao, sigla, novo_nome):
                            st.success("✅ País atualizado!")
                            st.rerun()
                else:
                    st.warning("Nenhum país disponível.")
            
            elif operacao == "🗑️ Deletar":
                df = ler_tabela(conexao, "Pais")
                if not df.empty:
                    st.dataframe(df, use_container_width=True)
                    sigla = st.selectbox("Selecione o País para deletar", df['sigla'].tolist())
                    st.warning("⚠️ Esta ação não pode ser desfeita!")
                    
                    if st.button("Confirmar Exclusão", type="primary"):
                        if deletar_pais(conexao, sigla):
                            st.success("✅ País deletado!")
                            st.rerun()
                else:
                    st.warning("Nenhum país disponível.")
        
        # ========== OLIMPÍADA ==========
        elif tabela == "Olimpiada":
            st.header(f"🏆 Gerenciar: {tabela}")
            
            if operacao == "📋 Visualizar":
                df = ler_tabela(conexao, "Olimpiada")
                st.dataframe(df, use_container_width=True)
                st.info(f"Total de olimpíadas: {len(df)}")
            
            elif operacao == "➕ Inserir":
                with st.form("form_olimpiada"):
                    ano = st.number_input("Ano", min_value=1896, max_value=2030, step=4)
                    estacao = st.selectbox("Estação", ["Verão", "Inverno", "Summer", "Winter"])
                    sede = st.text_input("Cidade Sede")
                    
                    if st.form_submit_button("💾 Salvar", type="primary"):
                        if ano and sede:
                            if inserir_olimpiada(conexao, ano, estacao, sede):
                                st.success("✅ Olimpíada inserida!")
                                st.balloons()
                        else:
                            st.warning("Preencha todos os campos!")
            
            elif operacao == "✏️ Atualizar":
                df = ler_tabela(conexao, "Olimpiada")
                if not df.empty:
                    ano = st.selectbox("Selecione o Ano", df['ano'].tolist())
                    olimpiada_atual = df[df['ano'] == ano].iloc[0]
                    
                    estacao = st.selectbox("Estação", ["Verão", "Inverno", "Summer", "Winter"], 
                                          index=["Verão", "Inverno", "Summer", "Winter"].index(olimpiada_atual['estacao']))
                    sede = st.text_input("Sede", value=olimpiada_atual['sede'])
                    
                    if st.button("🔄 Atualizar", type="primary"):
                        if atualizar_olimpiada(conexao, ano, estacao, sede):
                            st.success("✅ Olimpíada atualizada!")
                            st.rerun()
                else:
                    st.warning("Nenhuma olimpíada disponível.")
            
            elif operacao == "🗑️ Deletar":
                df = ler_tabela(conexao, "Olimpiada")
                if not df.empty:
                    st.dataframe(df, use_container_width=True)
                    ano = st.selectbox("Selecione o Ano", df['ano'].tolist())
                    st.warning("⚠️ Esta ação não pode ser desfeita!")
                    
                    if st.button("Confirmar Exclusão", type="primary"):
                        if deletar_olimpiada(conexao, ano):
                            st.success("✅ Olimpíada deletada!")
                            st.rerun()
                else:
                    st.warning("Nenhuma olimpíada disponível.")
        
        # ========== ATLETA ==========
        elif tabela == "Atleta":
            st.header(f"🏃 Gerenciar: {tabela}")
            
            if operacao == "📋 Visualizar":
                df = ler_tabela(conexao, "Atleta")
                st.dataframe(df, use_container_width=True)
                st.info(f"Total de atletas: {len(df)}")
            
            elif operacao == "➕ Inserir":
                paises_df = ler_tabela(conexao, "Pais")
                
                if not paises_df.empty:
                    with st.form("form_atleta"):
                        col1, col2 = st.columns(2)
                        with col1:
                            nome = st.text_input("Nome do Atleta")
                            sexo = st.selectbox("Sexo", ["M", "F"])
                            peso = st.number_input("Peso (kg)", min_value=0.0, step=0.1)
                        with col2:
                            altura = st.number_input("Altura (m)", min_value=0.0, max_value=3.0, step=0.01)
                            idade = st.number_input("Idade", min_value=0, step=1)
                            sigla_pais = st.selectbox("País", paises_df['sigla'].tolist())
                        
                        if st.form_submit_button("💾 Salvar", type="primary"):
                            if nome and sigla_pais:
                                if inserir_atleta(conexao, nome, sexo, peso, altura, idade, sigla_pais):
                                    st.success("✅ Atleta inserido!")
                                    st.balloons()
                            else:
                                st.warning("Preencha os campos obrigatórios!")
                else:
                    st.warning("Cadastre países primeiro!")
            
            elif operacao == "✏️ Atualizar":
                df = ler_tabela(conexao, "Atleta")
                paises_df = ler_tabela(conexao, "Pais")
                
                if not df.empty and not paises_df.empty:
                    id_atleta = st.selectbox("Selecione o Atleta", 
                                            df['id_atleta'].tolist(),
                                            format_func=lambda x: f"ID {x} - {df[df['id_atleta']==x]['nome'].values[0]}")
                    atleta_atual = df[df['id_atleta'] == id_atleta].iloc[0]
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        nome = st.text_input("Nome", value=atleta_atual['nome'])
                        sexo = st.selectbox("Sexo", ["M", "F"], index=0 if atleta_atual['sexo']=='M' else 1)
                        peso = st.number_input("Peso", value=float(atleta_atual['peso']) if pd.notna(atleta_atual['peso']) else 0.0)
                    with col2:
                        altura = st.number_input("Altura", value=float(atleta_atual['altura']) if pd.notna(atleta_atual['altura']) else 0.0)
                        idade = st.number_input("Idade", value=int(atleta_atual['idade']) if pd.notna(atleta_atual['idade']) else 0)
                        sigla_pais = st.selectbox("País", paises_df['sigla'].tolist(), 
                                                 index=paises_df['sigla'].tolist().index(atleta_atual['sigla_pais']))
                    
                    if st.button("🔄 Atualizar", type="primary"):
                        if atualizar_atleta(conexao, id_atleta, nome, sexo, peso, altura, idade, sigla_pais):
                            st.success("✅ Atleta atualizado!")
                            st.rerun()
                else:
                    st.warning("Nenhum atleta ou país disponível.")
            
            elif operacao == "🗑️ Deletar":
                df = ler_tabela(conexao, "Atleta")
                if not df.empty:
                    st.dataframe(df, use_container_width=True)
                    id_atleta = st.selectbox("Selecione o Atleta", 
                                            df['id_atleta'].tolist(),
                                            format_func=lambda x: f"ID {x} - {df[df['id_atleta']==x]['nome'].values[0]}")
                    st.warning("⚠️ Esta ação não pode ser desfeita!")
                    
                    if st.button("Confirmar Exclusão", type="primary"):
                        if deletar_atleta(conexao, id_atleta):
                            st.success("✅ Atleta deletado!")
                            st.rerun()
                else:
                    st.warning("Nenhum atleta disponível.")
        
        # ========== EVENTO ==========
        elif tabela == "Evento":
            st.header(f"🎯 Gerenciar: {tabela}")
            
            if operacao == "📋 Visualizar":
                df = ler_tabela(conexao, "Evento")
                st.dataframe(df, use_container_width=True)
                st.info(f"Total de eventos: {len(df)}")
            
            elif operacao == "➕ Inserir":
                olimpiadas_df = ler_tabela(conexao, "Olimpiada")
                
                if not olimpiadas_df.empty:
                    with st.form("form_evento"):
                        esporte = st.text_input("Esporte")
                        modalidade = st.text_input("Modalidade")
                        ano_olimpiada = st.selectbox("Ano da Olimpíada", olimpiadas_df['ano'].tolist())
                        
                        if st.form_submit_button("💾 Salvar", type="primary"):
                            if esporte and modalidade:
                                if inserir_evento(conexao, esporte, modalidade, ano_olimpiada):
                                    st.success("✅ Evento inserido!")
                                    st.balloons()
                            else:
                                st.warning("Preencha todos os campos!")
                else:
                    st.warning("Cadastre olimpíadas primeiro!")
            
            elif operacao == "✏️ Atualizar":
                df = ler_tabela(conexao, "Evento")
                olimpiadas_df = ler_tabela(conexao, "Olimpiada")
                
                if not df.empty and not olimpiadas_df.empty:
                    id_evento = st.selectbox("Selecione o Evento", 
                                            df['id_evento'].tolist(),
                                            format_func=lambda x: f"ID {x} - {df[df['id_evento']==x]['esporte'].values[0]} - {df[df['id_evento']==x]['modalidade'].values[0]}")
                    evento_atual = df[df['id_evento'] == id_evento].iloc[0]
                    
                    esporte = st.text_input("Esporte", value=evento_atual['esporte'])
                    modalidade = st.text_input("Modalidade", value=evento_atual['modalidade'])
                    ano_olimpiada = st.selectbox("Ano da Olimpíada", olimpiadas_df['ano'].tolist(),
                                                index=olimpiadas_df['ano'].tolist().index(evento_atual['ano_olimpiada']))
                    
                    if st.button("🔄 Atualizar", type="primary"):
                        if atualizar_evento(conexao, id_evento, esporte, modalidade, ano_olimpiada):
                            st.success("✅ Evento atualizado!")
                            st.rerun()
                else:
                    st.warning("Nenhum evento ou olimpíada disponível.")
            
            elif operacao == "🗑️ Deletar":
                df = ler_tabela(conexao, "Evento")
                if not df.empty:
                    st.dataframe(df, use_container_width=True)
                    id_evento = st.selectbox("Selecione o Evento", 
                                            df['id_evento'].tolist(),
                                            format_func=lambda x: f"ID {x} - {df[df['id_evento']==x]['esporte'].values[0]}")
                    st.warning("⚠️ Esta ação não pode ser desfeita!")
                    
                    if st.button("Confirmar Exclusão", type="primary"):
                        if deletar_evento(conexao, id_evento):
                            st.success("✅ Evento deletado!")
                            st.rerun()
                else:
                    st.warning("Nenhum evento disponível.")

            st.title("🥇 10 atletas com mais medalhas de cada evento """)
     
            modalidades = pd.read_sql("""
                SELECT DISTINCT modalidade 
                FROM Evento
                ORDER BY modalidade;
            """, conexao)["modalidade"].tolist()

            escolhida = st.selectbox("Selecione a modalidade:", modalidades)
    
            query = f"""
                    SELECT 
                    A.nome,
                    COUNT(*) AS total_medalhas
                FROM Atleta A
                JOIN Compete C ON C.id_atleta = A.id_atleta
                JOIN Evento E ON E.id_evento = C.id_evento
                WHERE C.medalha <> "Sem Medalha"
                AND E.modalidade = %s
                GROUP BY A.id_atleta, A.nome
                ORDER BY total_medalhas DESC;"""


            df = pd.read_sql(query, conexao, params=[escolhida])
            st.dataframe(df)

            st.title("🥇 10 Países com mais medalhas de cada evento """)

            modalidades_pais = pd.read_sql("""
                SELECT DISTINCT modalidade 
                FROM Evento
                ORDER BY modalidade;
            """, conexao)["modalidade"].tolist()

            escolhida_pais = st.selectbox("Selecione a modalidade:", modalidades)

            query = f"""
                    SELECT 
                    A.nome,
                    COUNT(*) AS total_medalhas
                FROM Atleta A
                JOIN Compete C ON C.id_atleta = A.id_atleta
                JOIN Evento E ON E.id_evento = C.id_evento
                WHERE C.medalha <> "Sem Medalha"
                AND E.modalidade = %s
                GROUP BY A.id_atleta, A.nome
                ORDER BY total_medalhas DESC;"""

        
        # ========== COMPETE ==========
        elif tabela == "Compete":
            st.header(f"🥇 Gerenciar: {tabela} (Atleta-Evento-Medalha)")
            
            if operacao == "📋 Visualizar":
                query = """
                    SELECT c.id_atleta, a.nome as atleta, c.id_evento, 
                           e.esporte, e.modalidade, c.medalha
                    FROM Compete c
                    JOIN Atleta a ON c.id_atleta = a.id_atleta
                    JOIN Evento e ON c.id_evento = e.id_evento
                    LIMIT 100
                """
                df = pd.read_sql(query, conexao)
                st.dataframe(df, use_container_width=True)
                st.info(f"Mostrando até 100 competições")
            
            elif operacao == "➕ Inserir":
                atletas_df = ler_tabela(conexao, "Atleta")
                eventos_df = ler_tabela(conexao, "Evento")
                
                if not atletas_df.empty and not eventos_df.empty:
                    with st.form("form_compete"):
                        id_atleta = st.selectbox("Atleta", 
                                                atletas_df['id_atleta'].tolist(),
                                                format_func=lambda x: f"ID {x} - {atletas_df[atletas_df['id_atleta']==x]['nome'].values[0]}")
                        id_evento = st.selectbox("Evento", 
                                                eventos_df['id_evento'].tolist(),
                                                format_func=lambda x: f"ID {x} - {eventos_df[eventos_df['id_evento']==x]['esporte'].values[0]}")
                        medalha = st.selectbox("Medalha", ["Ouro", "Prata", "Bronze", "Sem Medalha"])
                        
                        if st.form_submit_button("💾 Salvar", type="primary"):
                            if inserir_compete(conexao, id_atleta, id_evento, medalha):
                                st.success("✅ Competição inserida!")
                                st.balloons()
                else:
                    st.warning("Cadastre atletas e eventos primeiro!")
            
            elif operacao == "✏️ Atualizar":
                query = """
                    SELECT c.id_atleta, a.nome, c.id_evento, e.esporte, c.medalha
                    FROM Compete c
                    JOIN Atleta a ON c.id_atleta = a.id_atleta
                    JOIN Evento e ON c.id_evento = e.id_evento
                    LIMIT 100
                """
                df = pd.read_sql(query, conexao)
                
                if not df.empty:
                    opcoes = [f"Atleta ID {row['id_atleta']} ({row['nome']}) - Evento ID {row['id_evento']} ({row['esporte']})" 
                             for _, row in df.iterrows()]
                    selecao = st.selectbox("Selecione a Competição", range(len(df)), format_func=lambda x: opcoes[x])
                    
                    registro = df.iloc[selecao]
                    medalha = st.selectbox("Nova Medalha", ["Ouro", "Prata", "Bronze", "Sem Medalha"],
                                          index=["Ouro", "Prata", "Bronze", "Sem Medalha"].index(registro['medalha']) if registro['medalha'] in ["Ouro", "Prata", "Bronze", "Sem Medalha"] else 3)
                    
                    if st.button("🔄 Atualizar", type="primary"):
                        if atualizar_compete(conexao, registro['id_atleta'], registro['id_evento'], medalha):
                            st.success("✅ Competição atualizada!")
                            st.rerun()
                else:
                    st.warning("Nenhuma competição disponível.")
            
            elif operacao == "🗑️ Deletar":
                query = """
                    SELECT c.id_atleta, a.nome, c.id_evento, e.esporte, e.modalidade
                    FROM Compete c
                    JOIN Atleta a ON c.id_atleta = a.id_atleta
                    JOIN Evento e ON c.id_evento = e.id_evento
                    LIMIT 100
                """
                df = pd.read_sql(query, conexao)
                
                if not df.empty:
                    st.dataframe(df, use_container_width=True)
                    opcoes = [f"Atleta ID {row['id_atleta']} ({row['nome']}) - Evento ID {row['id_evento']} ({row['esporte']})" 
                             for _, row in df.iterrows()]
                    selecao = st.selectbox("Selecione a Competição", range(len(df)), format_func=lambda x: opcoes[x])
                    
                    registro = df.iloc[selecao]
                    st.warning("⚠️ Esta ação não pode ser desfeita!")
                    
                    if st.button("Confirmar Exclusão", type="primary"):
                        if deletar_compete(conexao, registro['id_atleta'], registro['id_evento']):
                            st.success("✅ Competição deletada!")
                            st.rerun()
                else:
                    st.warning("Nenhuma competição disponível.")
    
    else:
        st.error("❌ Não foi possível conectar ao banco de dados.")
        st.info("""
        **Verifique:**
        1. O XAMPP está rodando?
        2. O MySQL está ativo?
        3. O banco 'olimpiadas_db' foi criado?
        4. Execute o arquivo popdados.py primeiro para popular o banco!
        5. Configure o arquivo .env com as credenciais corretas
        """)

if __name__ == "__main__":
    main()