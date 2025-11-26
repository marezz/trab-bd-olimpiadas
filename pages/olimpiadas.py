import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from db import get_connection

st.set_page_config(page_title="Olimpíadas - Insights", layout="wide")
st.title("Olimpíadas")

# Conexão com o banco
conn = None
try:
    conn = get_connection()
except Exception as e:
    st.error(f"❌ Erro ao conectar ao banco: {e}")
    st.stop()

if conn is None:
    st.error("❌ Não foi possível conectar ao banco de dados.")
    st.stop()


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


st.subheader(f"Proporção de medalhas por atleta — {ano_selecionado}")

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
st.dataframe(df_prop_medalhas, use_container_width=True)


st.subheader(f"Top 10 atletas mais vitoriosos — {ano_selecionado}")

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
st.dataframe(df_top_atletas, use_container_width=True)


st.subheader(f"Top 10 países com atletas mais pesados — {ano_selecionado}")

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
HAVING COUNT(*) >= 3  -- evitar países com poucos atletas (ex: 1 ou 2)
ORDER BY Peso_Medio DESC
LIMIT 10;
"""

df_paises_pesados = pd.read_sql(q_paises_mais_pesados, conn, params=[ano_selecionado])
st.dataframe(df_paises_pesados, use_container_width=True)


st.subheader(f"Atleta mais jovem e mais velho por sexo — {ano_selecionado}")

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
st.dataframe(df_idades_extremas, use_container_width=True)

st.subheader("Proporção de gênero por edição")

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

# Gráfico de pizza do ano selecionado
if not df_genero.empty:
    ano_row = df_genero[df_genero['Ano'] == ano_selecionado]
    if not ano_row.empty:
        homens = int(ano_row['Homens'].iloc[0])
        mulheres = int(ano_row['Mulheres'].iloc[0])
        labels = ['Homens', 'Mulheres']
        sizes = [homens, mulheres]
        colors = ['#1f77b4', '#ff7f0e']

        fig, ax = plt.subplots()
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
        ax.axis('equal')  
        st.pyplot(fig)
    else:
        st.warning(f"Dados de gênero não encontrados para {ano_selecionado}.")
else:
    st.warning("Nenhum dado de gênero encontrado.")

st.write("Evolução da participação feminina (%):")
df_genero['% Mulheres'] = (df_genero['Mulheres'] / (df_genero['Homens'] + df_genero['Mulheres']) * 100).round(1)
st.line_chart(df_genero.set_index('Ano')['% Mulheres'])


st.subheader("Número de países por edição (todas as Olimpíadas)")

q_paises_ano = """
SELECT 
    O.ano AS Ano,
    COUNT(DISTINCT A.sigla_pais) AS Paises_Participantes
FROM Olimpiada O
JOIN Evento E ON E.ano_olimpiada = O.ano
JOIN Compete C ON C.id_evento = E.id_evento
JOIN Atleta A ON A.id_atleta = C.id_atleta
GROUP BY O.ano
ORDER BY O.ano;
"""

df_paises_ano = pd.read_sql(q_paises_ano, conn)
st.bar_chart(df_paises_ano.set_index('Ano'))


if not df_paises_ano.empty:
    max_row = df_paises_ano.loc[df_paises_ano['Paises_Participantes'].idxmax()]
    st.info(f"Recorde de diversidade: **{int(max_row['Paises_Participantes'])} países** em {int(max_row['Ano'])}.")

    st.subheader(f" Países sem medalhas — {ano_selecionado}")
    q_paises_sem_medalha_com_outer_join = """
SELECT 
    P.nome AS Pais
FROM (
    SELECT DISTINCT A.sigla_pais
    FROM Atleta A
    JOIN Compete C ON C.id_atleta = A.id_atleta
    JOIN Evento E ON E.id_evento = C.id_evento
    WHERE E.ano_olimpiada = %s
) AS Participantes
JOIN Pais P ON P.sigla = Participantes.sigla_pais

LEFT JOIN (
    SELECT DISTINCT A.sigla_pais
    FROM Atleta A
    JOIN Compete C ON C.id_atleta = A.id_atleta
    JOIN Evento E ON E.id_evento = C.id_evento
    WHERE E.ano_olimpiada = %s
      AND C.medalha IS NOT NULL
) AS Medalhistas
ON Participantes.sigla_pais = Medalhistas.sigla_pais
WHERE Medalhistas.sigla_pais IS NULL

ORDER BY P.nome;
"""

df_sem_medalha = pd.read_sql(q_paises_sem_medalha_com_outer_join, conn, params=[ano_selecionado, ano_selecionado])

if df_sem_medalha.empty:
    st.success("Todos os países participantes conquistaram pelo menos uma medalha.")
else:
    st.warning(f"{len(df_sem_medalha)} países participaram, mas não ganharam medalhas:")
    st.dataframe(df_sem_medalha, use_container_width=True)

with st.expander("Outras análises (todas as edições)"):
    
    st.subheader("Top 5 edições com mais países")
    st.dataframe(
        df_paises_ano.sort_values('Paises_Participantes', ascending=False).head(5),
        use_container_width=True
    )

    
    st.subheader("Crescimento do número de eventos ao longo dos anos")
    q_eventos = """
    SELECT O.ano AS Ano, COUNT(E.id_evento) AS Total_Eventos
    FROM Olimpiada O
    LEFT JOIN Evento E ON E.ano_olimpiada = O.ano
    GROUP BY O.ano
    ORDER BY Ano;
    """
    df_eventos = pd.read_sql(q_eventos, conn)
    st.line_chart(df_eventos.set_index("Ano"))

st.sidebar.markdown("---")
st.sidebar.info(f"Edição selecionada: **{ano_selecionado}**")