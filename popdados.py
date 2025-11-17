import pandas as pd
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente (opcional, mas recomendado)
load_dotenv()

class OlimpiadasCSVToMySQL:
    def __init__(self, host, database, user, password):
        """
        Inicializa a conexão com o banco de dados MySQL para Olimpíadas
        """
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
    
    def conectar(self):
        """Estabelece conexão com o banco de dados"""
        try:
            # Primeira conexão sem especificar database
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password
            )
            if self.connection.is_connected():
                print(f"✓ Conectado ao MySQL Server versão {self.connection.get_server_info()}")
                return True
        except Error as e:
            print(f"✗ Erro ao conectar ao MySQL: {e}")
            return False
    
    def drop_database(self):
        """Remove o banco de dados se ele existir"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"DROP DATABASE IF EXISTS {self.database}")
            print(f"🗑️  Banco de dados '{self.database}' removido (se existia)")
            cursor.close()
        except Error as e:
            print(f"✗ Erro ao remover banco: {e}")
    
    def criar_database(self):
        """Cria o banco de dados"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"CREATE DATABASE {self.database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.execute(f"USE {self.database}")
            print(f"✓ Banco de dados '{self.database}' criado com sucesso!")
            cursor.close()
        except Error as e:
            print(f"✗ Erro ao criar banco: {e}")
    
    def criar_schema(self):
        """Cria as tabelas do modelo lógico de Olimpíadas"""
        try:
            cursor = self.connection.cursor()
            
            # SQL de criação das tabelas
            tabelas = [
                """
                CREATE TABLE IF NOT EXISTS Pais (
                    sigla VARCHAR(3) PRIMARY KEY,
                    nome VARCHAR(100) NOT NULL UNIQUE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """,
                
                """
                CREATE TABLE IF NOT EXISTS Olimpiada (
                    ano INT PRIMARY KEY,
                    estacao VARCHAR(20) NOT NULL,
                    sede VARCHAR(100) NOT NULL,
                    CHECK (estacao IN ('Verão', 'Inverno', 'Summer', 'Winter'))
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """,
                
                """
                CREATE TABLE IF NOT EXISTS Atleta (
                    id_atleta INT PRIMARY KEY AUTO_INCREMENT,
                    nome VARCHAR(150) NOT NULL,
                    sexo CHAR(1),
                    peso DECIMAL(5,2),
                    altura DECIMAL(3,2),
                    idade INT,
                    sigla_pais VARCHAR(3) NOT NULL,
                    FOREIGN KEY (sigla_pais) REFERENCES Pais(sigla)
                        ON DELETE RESTRICT
                        ON UPDATE CASCADE,
                    CHECK (peso > 0 AND altura > 0 AND idade > 0),
                    CHECK (sexo IN ('M', 'F'))
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """,
                
                """
                CREATE TABLE IF NOT EXISTS Evento (
                    id_evento INT PRIMARY KEY AUTO_INCREMENT,
                    esporte VARCHAR(100) NOT NULL,
                    modalidade VARCHAR(100) NOT NULL,
                    ano_olimpiada INT NOT NULL,
                    FOREIGN KEY (ano_olimpiada) REFERENCES Olimpiada(ano)
                        ON DELETE RESTRICT
                        ON UPDATE CASCADE,
                    UNIQUE KEY unique_evento (esporte, modalidade, ano_olimpiada)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """,
                
                """
                CREATE TABLE IF NOT EXISTS Compete (
                    id_atleta INT,
                    id_evento INT,
                    medalha ENUM('Ouro', 'Prata', 'Bronze', 'Sem Medalha', 'Gold', 'Silver', 'Bronze', 'NA') DEFAULT 'Sem Medalha',
                    PRIMARY KEY (id_atleta, id_evento),
                    FOREIGN KEY (id_atleta) REFERENCES Atleta(id_atleta)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE,
                    FOREIGN KEY (id_evento) REFERENCES Evento(id_evento)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            ]
            
            for sql in tabelas:
                cursor.execute(sql)
                self.connection.commit()
            
            print("✓ Todas as tabelas foram criadas/verificadas com sucesso!")
            cursor.close()
            
        except Error as e:
            print(f"✗ Erro ao criar schema: {e}")
    
    def processar_csv_unico(self, csv_path, batch_size=500, ano_inicial=2006, ano_final=2016):
        """
        Processa o arquivo olimpiadasfiltrado.csv com todas as informações
        
        Args:
            csv_path: Caminho do arquivo CSV
            batch_size: Tamanho do lote para commit
            ano_inicial: Ano inicial do filtro (padrão: 2006)
            ano_final: Ano final do filtro (padrão: 2016)
        
        Colunas do CSV:
        - id: ID original do atleta
        - nome: Nome do atleta
        - sexo: Sexo (M/F)
        - idade: Idade do atleta
        - altura: Altura em cm
        - peso: Peso em kg
        - equipe: Nome do país/equipe
        - sigla: Sigla do país (NOC)
        - jogos: Nome completo dos jogos (ex: "2016 Summer")
        - ano: Ano da olimpíada
        - temporada: Verão/Inverno (Summer/Winter)
        - cidade: Cidade sede
        - esporte: Esporte praticado
        - evento: Modalidade/evento específico
        - medalha: Medalha conquistada (Gold/Silver/Bronze/NA)
        """
        try:
            print(f"\n📂 Carregando CSV: {csv_path}")
            df = pd.read_csv(csv_path)
            
            # Normalizar nomes das colunas - remover espaços e deixar minúsculas
            df.columns = df.columns.str.strip().str.lower()
            
            print(f"✓ CSV carregado: {len(df)} registros")
            
            # Filtrar por ano
            df = df[(df['ano'] >= ano_inicial) & (df['ano'] <= ano_final)]
            print(f"✓ Após filtro ({ano_inicial}-{ano_final}): {len(df)} registros")
            print(f"📊 Colunas encontradas: {', '.join(df.columns)}\n")
            
            # Verificar se as colunas necessárias existem
            colunas_necessarias = ['nome', 'equipe', 'sigla', 'ano', 'temporada', 'cidade', 'esporte', 'evento', 'medalha', 'peso', 'altura', 'idade', 'sexo']
            colunas_faltando = [col for col in colunas_necessarias if col not in df.columns]
            
            if colunas_faltando:
                print(f"❌ ERRO: Colunas faltando no CSV: {', '.join(colunas_faltando)}")
                print(f"📋 Colunas disponíveis: {', '.join(df.columns)}")
                return
            
            # Mapeamento flexível de colunas (ajuste conforme necessário)
            col_map = self._mapear_colunas(df.columns)
            
            cursor = self.connection.cursor()
            
            # Dicionários para cache de IDs
            paises_cache = {}
            atletas_cache = {}
            eventos_cache = {}
            olimpiadas_cache = set()
            
            total = len(df)
            erros = 0
            
            print("🔄 Processando registros...\n")
            
            for idx, row in df.iterrows():
                try:
                    # 1. PAÍS
                    pais_nome = str(row[col_map['pais']]).strip()
                    pais_sigla = str(row[col_map['sigla']]).strip().upper()
                    
                    if pais_sigla not in paises_cache:
                        cursor.execute(
                            "INSERT IGNORE INTO Pais (sigla, nome) VALUES (%s, %s)",
                            (pais_sigla, pais_nome)
                        )
                        paises_cache[pais_sigla] = True
                    
                    # 2. OLIMPÍADA
                    ano = int(row[col_map['ano']])
                    estacao = str(row[col_map['estacao']]).strip()
                    sede = str(row[col_map['sede']]).strip()
                    
                    if ano not in olimpiadas_cache:
                        cursor.execute(
                            "INSERT IGNORE INTO Olimpiada (ano, estacao, sede) VALUES (%s, %s, %s)",
                            (ano, estacao, sede)
                        )
                        olimpiadas_cache.add(ano)
                    
                    # 3. ATLETA
                    atleta_nome = str(row[col_map['nome']]).strip()
                    sexo = str(row[col_map['sexo']]).strip()[0].upper() if pd.notna(row[col_map['sexo']]) else None
                    peso = None if pd.isna(row[col_map['peso']]) else float(row[col_map['peso']])
                    altura = None if pd.isna(row[col_map['altura']]) else float(row[col_map['altura']])
                    idade = None if pd.isna(row[col_map['idade']]) else int(row[col_map['idade']])
                    
                    chave_atleta = (atleta_nome, pais_sigla)
                    
                    if chave_atleta not in atletas_cache:
                        cursor.execute(
                            """INSERT INTO Atleta (nome, sexo, peso, altura, idade, sigla_pais) 
                               VALUES (%s, %s, %s, %s, %s, %s)
                               ON DUPLICATE KEY UPDATE id_atleta=LAST_INSERT_ID(id_atleta)""",
                            (atleta_nome, sexo, peso, altura, idade, pais_sigla)
                        )
                        atletas_cache[chave_atleta] = cursor.lastrowid
                    
                    id_atleta = atletas_cache[chave_atleta]
                    
                    # 4. EVENTO
                    esporte = str(row[col_map['esporte']]).strip()
                    modalidade = str(row[col_map['modalidade']]).strip()
                    
                    chave_evento = (esporte, modalidade, ano)
                    
                    if chave_evento not in eventos_cache:
                        cursor.execute(
                            """INSERT IGNORE INTO Evento (esporte, modalidade, ano_olimpiada) 
                               VALUES (%s, %s, %s)""",
                            (esporte, modalidade, ano)
                        )
                        cursor.execute(
                            """SELECT id_evento FROM Evento 
                               WHERE esporte=%s AND modalidade=%s AND ano_olimpiada=%s""",
                            (esporte, modalidade, ano)
                        )
                        result = cursor.fetchone()
                        if result:
                            eventos_cache[chave_evento] = result[0]
                    
                    id_evento = eventos_cache.get(chave_evento)
                    if not id_evento:
                        continue
                    
                    # 5. COMPETE (Relacionamento)
                    medalha_raw = str(row[col_map['medalha']]).strip()
                    
                    # Normalizar medalha
                    medalha_map = {
                        'Gold': 'Ouro', 'Ouro': 'Ouro',
                        'Silver': 'Prata', 'Prata': 'Prata',
                        'Bronze': 'Bronze',
                        'NA': 'null', 'nan': 'null', 'None': 'null'
                    }
                    medalha = medalha_map.get(medalha_raw, 'Sem Medalha')
                    
                    cursor.execute(
                        """INSERT IGNORE INTO Compete (id_atleta, id_evento, medalha) 
                           VALUES (%s, %s, %s)""",
                        (id_atleta, id_evento, medalha)
                    )
                    
                    # Commit em lotes
                    if (idx + 1) % batch_size == 0:
                        self.connection.commit()
                        progresso = ((idx + 1) / total) * 100
                        print(f"   Progresso: {idx + 1}/{total} ({progresso:.1f}%) - Erros: {erros}")
                
                except Exception as e:
                    erros += 1
                    if erros <= 5:  # Mostrar apenas os primeiros 5 erros
                        print(f"   ⚠ Erro na linha {idx + 1}: {str(e)[:100]}")
            
            # Commit final
            self.connection.commit()
            cursor.close()
            
            print(f"\n{'='*60}")
            print(f"✓ IMPORTAÇÃO CONCLUÍDA!")
            print(f"{'='*60}")
            print(f"📊 Total de registros processados: {total}")
            print(f"✓ Países únicos: {len(paises_cache)}")
            print(f"✓ Atletas únicos: {len(atletas_cache)}")
            print(f"✓ Eventos únicos: {len(eventos_cache)}")
            print(f"✓ Olimpíadas: {len(olimpiadas_cache)}")
            print(f"⚠ Erros encontrados: {erros}")
            print(f"{'='*60}\n")
            
        except Error as e:
            print(f"✗ Erro ao processar CSV: {e}")
            self.connection.rollback()
    
    def _mapear_colunas(self, colunas):
        """
        Mapeia as colunas do CSV olimpiadasfiltrado.csv
        Colunas: id, nome, sexo, idade, altura, peso, equipe, sigla, jogos, ano, temporada, cidade, esporte, evento, medalha
        """
        # Colunas já devem estar em lowercase devido ao processamento anterior
        mapeamento = {}
        
        # Mapeamento direto
        if 'nome' in colunas:
            mapeamento['nome'] = 'nome'
        if 'equipe' in colunas:
            mapeamento['pais'] = 'equipe'
        if 'sigla' in colunas:
            mapeamento['sigla'] = 'sigla'
        if 'ano' in colunas:
            mapeamento['ano'] = 'ano'
        if 'temporada' in colunas:
            mapeamento['estacao'] = 'temporada'
        if 'cidade' in colunas:
            mapeamento['sede'] = 'cidade'
        if 'esporte' in colunas:
            mapeamento['esporte'] = 'esporte'
        if 'evento' in colunas:
            mapeamento['modalidade'] = 'evento'
        if 'medalha' in colunas:
            mapeamento['medalha'] = 'medalha'
        if 'peso' in colunas:
            mapeamento['peso'] = 'peso'
        if 'altura' in colunas:
            mapeamento['altura'] = 'altura'
        if 'idade' in colunas:
            mapeamento['idade'] = 'idade'
        if 'sexo' in colunas:
            mapeamento['sexo'] = 'sexo'
        
        print("🔍 Mapeamento de colunas:")
        for chave, valor in mapeamento.items():
            print(f"   {chave}: '{valor}'")
        print()
        
        return mapeamento
    
    def desconectar(self):
        """Fecha a conexão com o banco de dados"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("✓ Conexão MySQL fechada")


# ============ EXEMPLO DE USO ============

if __name__ == "__main__":
    # Configurações do banco de dados
    DB_CONFIG = {
        'host': 'localhost',
        'database': 'olimpiadas_db',
        'user': 'root',
        'password': ''
    }
    
    # Caminho do CSV único
    CSV_FILE = 'C:/Users/marce/Documents/trabalhos/bd/olimpiadasfiltrado.csv'
    
    # Executar importação
    print("=" * 60)
    print("IMPORTAÇÃO DE DADOS - SISTEMA OLIMPÍADAS")
    print("=" * 60)
    
    db = OlimpiadasCSVToMySQL(**DB_CONFIG)
    
    if db.conectar():
        print("\n[1/3] Recriando banco de dados...")
        db.drop_database()
        db.criar_database()
        
        print("\n[2/3] Criando estrutura do banco de dados...")
        db.criar_schema()
        
        print("\n[3/3] Processando arquivo CSV único...")
        db.processar_csv_unico(CSV_FILE, batch_size=500, ano_inicial=2006, ano_final=2016)
        
        db.desconectar()