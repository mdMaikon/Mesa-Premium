import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from pathlib import Path
import logging
from datetime import datetime
from contextlib import contextmanager

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gerenciador de conexão com banco de dados MySQL"""
    
    def __init__(self, validate_on_init=True):
        self._load_env()
        self.connection_config = {
            'host': os.getenv('DB_HOST'),
            'user': os.getenv('DB_USER'), 
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DB_NAME'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'charset': 'utf8mb4',
            'autocommit': True,
            'connection_timeout': 10,
            'pool_name': 'automacoes_pool',
            'pool_size': 5,
            'pool_reset_session': True
        }
        
        if validate_on_init:
            self._validate_config()
            self._create_tables()
    
    def _load_env(self):
        """Carrega variáveis do arquivo .env"""
        env_file = Path(__file__).parent / '.env'
        if env_file.exists():
            load_dotenv(env_file)
        else:
            logger.warning(f"Arquivo .env não encontrado em {env_file}")
    
    def _validate_config(self):
        """Valida configurações de conexão"""
        required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Variáveis de ambiente faltando: {', '.join(missing_vars)}")
    
    def _ensure_validated(self):
        """Garante que a configuração foi validada antes do uso"""
        if not hasattr(self, '_validated'):
            self._validate_config()
            self._validated = True
            self._create_tables()
    
    @contextmanager
    def get_connection(self):
        """Context manager para conexões seguras"""
        self._ensure_validated()
        connection = None
        try:
            connection = mysql.connector.connect(**self.connection_config)
            yield connection
        except Error as e:
            logger.error(f"Erro de conexão com banco: {e}")
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()
    
    def _create_tables(self):
        """Cria tabelas necessárias se não existirem"""
        tables = {
            'automacoes_execucoes': '''
                CREATE TABLE IF NOT EXISTS automacoes_execucoes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nome_automacao VARCHAR(255) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    inicio_execucao DATETIME NOT NULL,
                    fim_execucao DATETIME,
                    tempo_execucao INT, -- em segundos
                    mensagem_erro TEXT,
                    dados_resultado JSON,
                    usuario VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_nome_automacao (nome_automacao),
                    INDEX idx_status (status),
                    INDEX idx_inicio_execucao (inicio_execucao)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''',
            
            'automacoes_dados': '''
                CREATE TABLE IF NOT EXISTS automacoes_dados (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    automacao_id INT,
                    tipo_dado VARCHAR(100) NOT NULL,
                    dados JSON NOT NULL,
                    data_coleta DATETIME NOT NULL,
                    hash_dados VARCHAR(64), -- para evitar duplicatas
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (automacao_id) REFERENCES automacoes_execucoes(id) ON DELETE CASCADE,
                    INDEX idx_tipo_dado (tipo_dado),
                    INDEX idx_data_coleta (data_coleta),
                    INDEX idx_hash_dados (hash_dados)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''',
            
            'configuracoes_sistema': '''
                CREATE TABLE IF NOT EXISTS configuracoes_sistema (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    chave VARCHAR(100) NOT NULL UNIQUE,
                    valor TEXT,
                    descricao VARCHAR(255),
                    categoria VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_categoria (categoria)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            '''
        }
        
        try:
            # Conexão direta para evitar recursão
            connection = mysql.connector.connect(**self.connection_config)
            cursor = connection.cursor()
            for table_name, create_sql in tables.items():
                cursor.execute(create_sql)
                logger.info(f"Tabela {table_name} verificada/criada")
            connection.commit()
            connection.close()
        except Error as e:
            logger.error(f"Erro ao criar tabelas: {e}")
            raise
    
    def registrar_inicio_execucao(self, nome_automacao, usuario=None):
        """Registra início de execução de automação"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = '''
                    INSERT INTO automacoes_execucoes 
                    (nome_automacao, status, inicio_execucao, usuario)
                    VALUES (%s, %s, %s, %s)
                '''
                cursor.execute(query, (
                    nome_automacao, 
                    'EXECUTANDO', 
                    datetime.now(),
                    usuario or 'sistema'
                ))
                conn.commit()
                return cursor.lastrowid
        except Error as e:
            logger.error(f"Erro ao registrar início de execução: {e}")
            return None
    
    def registrar_fim_execucao(self, execucao_id, status, mensagem_erro=None, dados_resultado=None):
        """Registra fim de execução de automação"""
        try:
            import json
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Buscar início da execução
                cursor.execute(
                    "SELECT inicio_execucao FROM automacoes_execucoes WHERE id = %s",
                    (execucao_id,)
                )
                result = cursor.fetchone()
                
                if result:
                    inicio = result[0]
                    fim = datetime.now()
                    tempo_execucao = int((fim - inicio).total_seconds())
                    
                    # Converter dados_resultado para JSON se for dict/list
                    dados_resultado_json = None
                    if dados_resultado is not None:
                        if isinstance(dados_resultado, (dict, list)):
                            dados_resultado_json = json.dumps(dados_resultado, ensure_ascii=False)
                        else:
                            dados_resultado_json = str(dados_resultado)
                    
                    query = '''
                        UPDATE automacoes_execucoes 
                        SET status = %s, fim_execucao = %s, tempo_execucao = %s,
                            mensagem_erro = %s, dados_resultado = %s
                        WHERE id = %s
                    '''
                    cursor.execute(query, (
                        status, fim, tempo_execucao, mensagem_erro, 
                        dados_resultado_json, execucao_id
                    ))
                    conn.commit()
                    return True
        except Error as e:
            logger.error(f"Erro ao registrar fim de execução: {e}")
            return False
    
    def salvar_dados_automacao(self, execucao_id, tipo_dado, dados, data_coleta=None):
        """Salva dados específicos de uma automação"""
        try:
            import json
            import hashlib
            
            if data_coleta is None:
                data_coleta = datetime.now()
            
            # Gerar hash dos dados para evitar duplicatas
            dados_str = json.dumps(dados, sort_keys=True)
            hash_dados = hashlib.sha256(dados_str.encode()).hexdigest()
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Verificar se dados já existem
                cursor.execute(
                    "SELECT id FROM automacoes_dados WHERE hash_dados = %s",
                    (hash_dados,)
                )
                
                if not cursor.fetchone():
                    query = '''
                        INSERT INTO automacoes_dados 
                        (automacao_id, tipo_dado, dados, data_coleta, hash_dados)
                        VALUES (%s, %s, %s, %s, %s)
                    '''
                    cursor.execute(query, (
                        execucao_id, tipo_dado, dados_str, data_coleta, hash_dados
                    ))
                    conn.commit()
                    return cursor.lastrowid
                else:
                    logger.info(f"Dados duplicados ignorados para {tipo_dado}")
                    return None
                    
        except Error as e:
            logger.error(f"Erro ao salvar dados da automação: {e}")
            return None
    
    def obter_historico_execucoes(self, nome_automacao=None, limite=50):
        """Obtém histórico de execuções"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                
                if nome_automacao:
                    query = '''
                        SELECT * FROM automacoes_execucoes 
                        WHERE nome_automacao = %s 
                        ORDER BY inicio_execucao DESC 
                        LIMIT %s
                    '''
                    cursor.execute(query, (nome_automacao, limite))
                else:
                    query = '''
                        SELECT * FROM automacoes_execucoes 
                        ORDER BY inicio_execucao DESC 
                        LIMIT %s
                    '''
                    cursor.execute(query, (limite,))
                
                return cursor.fetchall()
                
        except Error as e:
            logger.error(f"Erro ao obter histórico: {e}")
            return []
    
    def obter_ultima_execucao(self, nome_automacao):
        """Obtém informações da última execução de uma automação"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                query = '''
                    SELECT * FROM automacoes_execucoes 
                    WHERE nome_automacao = %s 
                    ORDER BY inicio_execucao DESC 
                    LIMIT 1
                '''
                cursor.execute(query, (nome_automacao,))
                result = cursor.fetchone()
                
                if result:
                    return {
                        'status': result['status'],
                        'inicio': result['inicio_execucao'],
                        'fim': result['fim_execucao'],
                        'tempo_execucao': result['tempo_execucao'],
                        'erro': result['mensagem_erro']
                    }
                return None
                
        except Error as e:
            logger.error(f"Erro ao obter última execução: {e}")
            return None
    
    def salvar_configuracao(self, chave, valor, descricao=None, categoria='geral'):
        """Salva configuração do sistema"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = '''
                    INSERT INTO configuracoes_sistema (chave, valor, descricao, categoria)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                    valor = VALUES(valor), 
                    descricao = VALUES(descricao),
                    categoria = VALUES(categoria)
                '''
                cursor.execute(query, (chave, valor, descricao, categoria))
                conn.commit()
                return True
        except Error as e:
            logger.error(f"Erro ao salvar configuração: {e}")
            return False
    
    def obter_configuracao(self, chave, default=None):
        """Obtém configuração do sistema"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT valor FROM configuracoes_sistema WHERE chave = %s",
                    (chave,)
                )
                result = cursor.fetchone()
                return result[0] if result else default
        except Error as e:
            logger.error(f"Erro ao obter configuração: {e}")
            return default
    
    def test_connection(self):
        """Testa conexão com banco de dados"""
        try:
            self._ensure_validated()
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result[0] == 1
        except Error as e:
            logger.error(f"Teste de conexão falhou: {e}")
            return False