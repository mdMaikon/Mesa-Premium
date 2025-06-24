import os
import sys
import requests
import json
import pandas as pd
import re
from datetime import datetime
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import mysql.connector
from io import BytesIO


def setup_logging():
    """Configura o logging com caminho absoluto"""
    log_dir = Path(
        os.environ.get('USERPROFILE', ''),
        "OneDrive - BLUE3 INVESTIMENTOS ASSESSOR DE INVESTIMENTOS S S LTDA (1)",
        "MESA RV",
        "AUTOMAÇÕES",
        "LOGS"
    )

    # Cria a pasta de logs se não existir
    log_dir.mkdir(parents=True, exist_ok=True)

    # Caminho completo do arquivo de log
    log_file = log_dir / 'juro_mensal_mysql.log'

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(str(log_file), encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    return str(log_file)


# Configura o logging
log_path = setup_logging()
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Classe responsável pela gestão do banco MySQL para renda fixa"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None

    def connect(self) -> bool:
        """Estabelece conexão com o banco MySQL"""
        try:
            self.connection = mysql.connector.connect(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database'],
                charset='utf8mb4',
                autocommit=True
            )
            logger.info("Conectado ao MySQL com sucesso!")
            return True
        except mysql.connector.Error as err:
            logger.error(f"Erro ao conectar ao MySQL: {err}")
            return False

    def disconnect(self):
        """Fecha a conexão com o banco"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Conexão MySQL fechada.")

    def create_fixed_income_table(self) -> bool:
        """VERSÃO CORRIGIDA - Cria a tabela com campo VARCHAR maior"""
        try:
            cursor = self.connection.cursor()

            # DROPA a tabela se existir para garantir nova estrutura
            drop_table_query = "DROP TABLE IF EXISTS fixed_income_data"
            cursor.execute(drop_table_query)
            logger.info("Tabela anterior removida (se existia)")

            # 🔧 CORREÇÃO: Aumenta tamanho do campo classificar_vencimento
            create_table_query = """
            CREATE TABLE fixed_income_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                data_coleta DATETIME NOT NULL,
                ativo VARCHAR(255),
                instrumento VARCHAR(100),
                duration DECIMAL(10,6),
                indexador VARCHAR(100),
                juros VARCHAR(50),
                primeira_data_juros DATE,
                isento VARCHAR(10),
                rating VARCHAR(50),
                vencimento DATE,
                tax_min VARCHAR(255),
                tax_min_clean DECIMAL(8,4),
                roa_aprox DECIMAL(8,4),
                taxa_emissao DECIMAL(8,4),
                publico VARCHAR(100),
                publico_resumido VARCHAR(10),
                emissor VARCHAR(255),
                cupom VARCHAR(100),
                classificar_vencimento TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                
                INDEX idx_data_coleta (data_coleta),
                INDEX idx_ativo (ativo),
                INDEX idx_emissor (emissor),
                INDEX idx_vencimento (vencimento),
                INDEX idx_rating (rating),
                INDEX idx_indexador (indexador)
            )
            """

            cursor.execute(create_table_query)
            logger.info(
                "Tabela fixed_income_data criada com campo TEXT para classificar_vencimento!")
            cursor.close()
            return True

        except mysql.connector.Error as err:
            logger.error(f"Erro ao criar tabela: {err}")
            return False

    def safe_get_value(self, row, column: str, default_value=None):
        """VERSÃO CORRIGIDA - Função auxiliar para obter valores do DataFrame tratando NaN"""
        try:
            value = row.get(column, default_value)

            # Trata valores NaN do pandas
            if pd.isna(value):
                if isinstance(default_value, (int, float)):
                    return 0.0
                else:
                    return ''

            # Trata especificamente datas
            if 'data' in column.lower() or 'vencimento' in column.lower():
                if isinstance(value, str):
                    try:
                        parsed_date = pd.to_datetime(value, errors='coerce')
                        if pd.isna(parsed_date):
                            return None
                        return parsed_date
                    except:
                        return None
                elif pd.isna(value):
                    return None
                return value

            # Para valores numéricos
            if isinstance(value, (int, float)) and not pd.isna(value):
                return float(value)
            elif pd.isna(value) and isinstance(default_value, (int, float)):
                return 0.0

            # Para strings
            if isinstance(value, str):
                cleaned_value = value.strip()
                # 🔧 CORREÇÃO: Limita tamanho da string para evitar problemas no MySQL
                if len(cleaned_value) > 255:
                    cleaned_value = cleaned_value[:252] + "..."
                    logger.warning(
                        f"String truncada na coluna {column}: tamanho original {len(value)}")
                return cleaned_value
            elif pd.isna(value):
                return ''

            # 🔧 CORREÇÃO: Converte outros tipos para string e limita tamanho
            str_value = str(value).strip()
            if len(str_value) > 255:
                str_value = str_value[:252] + "..."
                logger.warning(
                    f"Valor convertido e truncado na coluna {column}")
            return str_value

        except Exception as e:
            logger.warning(f"Erro ao processar valor da coluna {column}: {e}")
            if isinstance(default_value, (int, float)):
                return 0.0
            return ''

    def insert_fixed_income_data(self, df: pd.DataFrame) -> bool:
        """VERSÃO CORRIGIDA - Usa .to_dict() em vez de iterrows() para resolver problema do 'None'"""
        try:
            cursor = self.connection.cursor()

            # Adiciona apenas timestamp de coleta
            df['data_coleta'] = datetime.now()

            # 🔧 CORREÇÃO PRINCIPAL: Converte DataFrame para lista de dicts primeiro
            records = df.to_dict('records')  # Converte cada linha para dict

            logger.info(f"Convertidos {len(records)} registros para inserção")

            # DEBUG: Verifica primeiro registro
            if records and 'Classificar Vencimento' in records[0]:
                first_classificar = records[0]['Classificar Vencimento']
                logger.info(
                    f"DEBUG - Primeiro 'Classificar Vencimento': '{first_classificar}' (tipo: {type(first_classificar)})")

            # Converte records para lista de tuplas
            data_tuples = []
            for i, record in enumerate(records):
                # Função auxiliar para tratar valores de forma segura
                def get_safe_value(key, default='', is_numeric=False):
                    value = record.get(key, default)

                    # Trata NaN do pandas
                    if pd.isna(value):
                        return 0.0 if is_numeric else ''

                    # Para valores numéricos
                    if is_numeric:
                        try:
                            return float(value) if value != '' else 0.0
                        except (ValueError, TypeError):
                            return 0.0

                    # Para strings
                    if isinstance(value, str):
                        return value.strip()
                    elif value is None:
                        return ''
                    else:
                        return str(value).strip()

                # Acessa diretamente do dict (mais confiável que pandas Series)
                tuple_data = (
                    record.get('data_coleta'),
                    get_safe_value('Ativo'),
                    get_safe_value('Instrumento'),
                    get_safe_value('Duration', 0.0, is_numeric=True),
                    get_safe_value('Indexador'),
                    get_safe_value('Juros'),
                    # Mantém como está para datas
                    record.get('Primeira Data de Juros'),
                    get_safe_value('Isento'),
                    get_safe_value('Rating'),
                    record.get('Vencimento'),  # Mantém como está para datas
                    get_safe_value('Tax.Mín'),  # Mantém como string original
                    get_safe_value('Tax.Mín_Clean', 0.0, is_numeric=True),
                    get_safe_value('ROA E. Aprox.', 0.0, is_numeric=True),
                    get_safe_value('Taxa de Emissão', 0.0, is_numeric=True),
                    get_safe_value('Público'),
                    get_safe_value('Público Resumido'),
                    get_safe_value('Emissor'),
                    get_safe_value('Cupom'),
                    # 🎯 PROBLEMA RESOLVIDO AQUI
                    get_safe_value('Classificar Vencimento')
                )

                # DEBUG das primeiras 3 linhas
                if i < 3:
                    classificar_val = get_safe_value('Classificar Vencimento')
                    logger.info(
                        f"DEBUG Linha {i} - Classificar processado: '{classificar_val}'")

                data_tuples.append(tuple_data)

            # Query de inserção (mantém a mesma)
            insert_query = """
            INSERT INTO fixed_income_data 
            (data_coleta, ativo, instrumento, duration, indexador, juros, 
            primeira_data_juros, isento, rating, vencimento, tax_min, tax_min_clean,
            roa_aprox, taxa_emissao, publico, publico_resumido, 
            emissor, cupom, classificar_vencimento)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            # Teste de inserção da primeira linha
            if data_tuples:
                try:
                    # último item = classificar_vencimento
                    test_classificar = data_tuples[0][-1]
                    logger.info(
                        f"🧪 TESTE - Tentando inserir classificar_vencimento: '{test_classificar}'")
                    cursor.execute(insert_query, data_tuples[0])
                    logger.info(
                        "✅ Teste de inserção da primeira linha bem-sucedido")

                    # Verifica se foi inserido corretamente
                    cursor.execute(
                        "SELECT classificar_vencimento FROM fixed_income_data ORDER BY id DESC LIMIT 1")
                    resultado = cursor.fetchone()
                    if resultado:
                        logger.info(
                            f"✅ Valor CONFIRMADO no banco: '{resultado[0]}'")
                        if resultado[0] and resultado[0] != 'None':
                            logger.info(
                                "🎉 PROBLEMA RESOLVIDO - Classificar Vencimento inserido corretamente!")
                        else:
                            logger.error("❌ Ainda inserindo NULL/None")
                    else:
                        logger.error(
                            "❌ Nenhum resultado encontrado após inserção")

                except mysql.connector.Error as err:
                    logger.error(f"❌ Erro no teste de inserção: {err}")
                    cursor.close()
                    return False

            # Inserção em lote para melhor performance
            cursor.executemany(insert_query, data_tuples)

            logger.info(f"Inseridos {len(data_tuples)} registros no MySQL!")
            cursor.close()
            return True

        except mysql.connector.Error as err:
            logger.error(f"Erro ao inserir dados no MySQL: {err}")
            return False
        except Exception as e:
            logger.error(f"Erro inesperado ao inserir dados: {e}")
            return False

    def clear_all_data(self) -> bool:
        """Remove todos os dados da tabela para inserir dados frescos"""
        try:
            cursor = self.connection.cursor()

            # Remove todos os registros da tabela
            clear_query = "DELETE FROM fixed_income_data"
            cursor.execute(clear_query)

            rows_deleted = cursor.rowcount
            logger.info(f"Tabela limpa: {rows_deleted} registros removidos")

            cursor.close()
            return True

        except mysql.connector.Error as err:
            logger.error(f"Erro ao limpar tabela: {err}")
            return False


class FixedIncomeDownloader:
    """Classe responsável pelo download de categorias de renda fixa do HUB XPI com integração MySQL"""

    def __init__(self):
        self.token: Optional[str] = None
        self.base_path: Optional[Path] = None
        self.db_manager: Optional[DatabaseManager] = None
        self.db_config: Optional[Dict] = None
        self.categorias = {
            "CREDITOPRIVADO": "CP",
            "BANCARIO": "EB",
            "TPF": "TPF",
        }

    def load_configuration(self) -> bool:
        """Carrega as configurações"""
        try:
            # Carrega token do arquivo JSON (mantém o existente)
            config_path = Path(
                os.environ.get('USERPROFILE', ''),
                "OneDrive - BLUE3 INVESTIMENTOS ASSESSOR DE INVESTIMENTOS S S LTDA (1)",
                "MESA RV",
                "AUTOMAÇÕES",
                "TOKEN",
                "hub_config.json"
            )

            if not config_path.exists():
                logger.error(
                    f"Arquivo de configuração não encontrado em: {config_path}")
                return False

            # Carrega as configurações do JSON
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # Valida token do HUB
            self.token = config_data.get("hub_token")

            if not self.token:
                logger.error(
                    "Token HUB não encontrado no arquivo de configuração")
                return False

            # ========================================
            # CONFIGURAÇÕES MYSQL HOSTINGER - TESTE
            # ========================================
            # ALTERE ESTAS CREDENCIAIS PARA AS SUAS:
            self.db_config = {
                'host': 'srv719.hstgr.io',  # ou o host que a Hostinger forneceu
                'port': 3306,
                'user': 'u272626296_mesapremium',    # <<<< ALTERE AQUI
                'password': 'Blue@@10',  # <<<< ALTERE AQUI
                'database': 'u272626296_automacoes'   # <<<< ALTERE AQUI
            }
            # ========================================

            logger.info("Configurações carregadas com sucesso")
            logger.info(f"MySQL Host: {self.db_config['host']}")
            logger.info(f"MySQL Database: {self.db_config['database']}")
            return True

        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro ao carregar configurações: {e}")
            return False

    def setup_destination_folder(self) -> bool:
        """Configura e cria a pasta de destino se necessário (para backup)"""
        try:
            self.base_path = Path(
                os.environ.get('USERPROFILE', ''),
                "OneDrive - BLUE3 INVESTIMENTOS ASSESSOR DE INVESTIMENTOS S S LTDA (1)",
                "MESA RV",
                "AUTOMAÇÕES",
                "CARTEIRA JUROS MENSAL",
                "Backup_MySQL"
            )

            # Cria a pasta se não existir
            self.base_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Pasta de backup configurada: {self.base_path}")
            return True

        except Exception as e:
            logger.error(f"Erro ao configurar pasta de destino: {e}")
            return False

    def get_headers(self) -> Dict[str, str]:
        """Retorna os headers para a requisição"""
        return {
            "Authorization": f"Bearer {self.token}",
            "ocp-apim-subscription-key": "3923e12297e7448398ba9a9046c4fced",
            "Content-Type": "application/json",
            "Origin": "https://hub.xpi.com.br",
            "Referer": "https://hub.xpi.com.br/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def extract_percentage_value(self, text) -> float:
        """Extrai valor numérico de strings com taxas"""
        if pd.isna(text) or text == "":
            return 0.0

        text = str(text)

        # Procura por números (com ou sem vírgula) seguidos ou precedidos de %
        # Exemplos: "6,15%", "+ 6,15%", "6,15", "100%", "2,415%"
        match = re.search(r'(\d+(?:,\d+)?)', text)

        if match:
            value = match.group(1).replace(',', '.')
            return float(value) / 100  # Divide por 100 para formato Excel %

        return 0.0

    def format_tax_columns(self, df) -> pd.DataFrame:
        """CORRIGIDO: Formata apenas Tax.Mín criando coluna limpa e mantendo original + ROA e Taxa de Emissão"""
        try:
            logger.info("Formatando colunas de taxas...")

            # Processa APENAS Tax.Mín - criando versão clean
            if 'Tax.Mín' in df.columns:
                logger.info(
                    "Criando Tax.Mín_Clean - mantendo original intacta")
                # Cria nova coluna com valores limpos SEM alterar a original
                df['Tax.Mín_Clean'] = df['Tax.Mín'].apply(
                    self.extract_percentage_value)
                logger.info("Tax.Mín_Clean criada com sucesso")
            else:
                logger.warning("Coluna Tax.Mín não encontrada")

            # Formata coluna ROA E. Aprox. (original - substitui valores como no código inicial)
            if 'ROA E. Aprox.' in df.columns:
                logger.info("Formatando coluna: ROA E. Aprox.")
                df['ROA E. Aprox.'] = df['ROA E. Aprox.'].apply(
                    self.extract_percentage_value)

            # Formata coluna Taxa de Emissão (original - substitui valores como no código inicial)
            if 'Taxa de Emissão' in df.columns:
                logger.info("Formatando coluna: Taxa de Emissão")
                df['Taxa de Emissão'] = df['Taxa de Emissão'].apply(
                    self.extract_percentage_value)

            logger.info("Formatação das colunas concluída")
            return df

        except Exception as e:
            logger.error(f"Erro durante formatação das colunas: {e}")
            return df

    def filter_igpm_assets(self, df) -> pd.DataFrame:
        """NOVA FUNÇÃO: Remove ativos com indexador IGP-M"""
        try:
            if 'Indexador' not in df.columns:
                logger.warning("Coluna 'Indexador' não encontrada")
                return df

            linhas_antes = len(df)
            df_filtrado = df[df['Indexador'] != 'IGP-M'].copy()
            linhas_removidas = linhas_antes - len(df_filtrado)

            logger.info(
                f"Filtro IGP-M aplicado: {linhas_removidas} ativos removidos")
            return df_filtrado

        except Exception as e:
            logger.error(f"Erro ao filtrar ativos IGP-M: {e}")
            return df

    def apply_ntn_rules(self, df) -> pd.DataFrame:
        """NOVA FUNÇÃO: Aplica regras específicas para ativos NTN - APLICADA ANTES DA FORMATAÇÃO"""
        try:
            if 'Ativo' not in df.columns:
                logger.warning("Coluna 'Ativo' não encontrada")
                return df

            # Contador para log
            ntn_aaa_count = 0
            ntn_f_count = 0

            for index, row in df.iterrows():
                ativo = str(row.get('Ativo', ''))

                # Regra 2: NTN recebe Rating AAA
                if ativo.startswith('NTN'):
                    df.at[index, 'Rating'] = 'AAA'
                    ntn_aaa_count += 1

                # Regra 3: NTN-F recebe Taxa de Emissão 10% (formato string para posterior processamento)
                if 'NTN-F' in ativo:
                    # String que será processada por extract_percentage_value
                    df.at[index, 'Taxa de Emissão'] = '10%'
                    ntn_f_count += 1

            logger.info(
                f"Regras NTN aplicadas: {ntn_aaa_count} ativos NTN com Rating AAA, {ntn_f_count} ativos NTN-F com Taxa 10%")
            return df

        except Exception as e:
            logger.error(f"Erro ao aplicar regras NTN: {e}")
            return df

    def create_new_columns(self, df) -> pd.DataFrame:
        """MODIFICADO: Cria as novas colunas e aplica regra de Rating"""
        try:
            logger.info("Criando novas colunas...")

            # Coluna Público Resumido
            if 'Público' in df.columns:
                df['Público Resumido'] = df['Público'].map({
                    'Investidor Geral': 'R',
                    'Investidor Qualificado': 'Q',
                    'Investidor Profissional': 'P'
                }).fillna('')
                logger.info("Coluna 'Público Resumido' criada")

            # Coluna Emissor
            if 'Ativo' in df.columns:
                def extract_emissor(ativo):
                    if pd.isna(ativo):
                        return ""

                    ativo = str(ativo)

                    # Caso especial: NTN = TESOURO NACIONAL
                    if ativo.startswith('NTN'):
                        return "TESOURO NACIONAL"

                    # Remove prefixos (CDB, CRI, CRA, CDCA, DEB, LCI, LCA)
                    prefixos = ['CDB', 'CRI', 'CRA',
                                'CDCA', 'DEB', 'LCI', 'LCA']
                    for prefixo in prefixos:
                        if ativo.startswith(prefixo):
                            ativo = ativo[len(prefixo):].strip()
                            break

                    # Remove tudo após o "-" (vencimento)
                    if '-' in ativo:
                        ativo = ativo.split('-')[0].strip()

                    return ativo

                df['Emissor'] = df['Ativo'].apply(extract_emissor)
                logger.info("Coluna 'Emissor' criada")

            # Coluna Cupom
            if 'Vencimento' in df.columns and 'Juros' in df.columns:
                def extract_cupom(row):
                    juros = row['Juros']
                    vencimento = row['Vencimento']

                    # Se juros for Mensal
                    if juros == 'Mensal':
                        return 'Mensal'

                    # Se juros for Semestral, extrai o mês do vencimento
                    if juros == 'Semestral':
                        if pd.isna(vencimento):
                            return ""

                        try:
                            # Converte para datetime se for string
                            if isinstance(vencimento, str):
                                vencimento = pd.to_datetime(
                                    vencimento, errors='coerce')

                            if pd.isna(vencimento):
                                return ""

                            mes = vencimento.month

                            # Mapeia os meses para cupons semestrais
                            meses_cupom = {
                                1: "Janeiro e Julho",      # Jan -> Jan/Jul
                                2: "Fevereiro e Agosto",   # Fev -> Fev/Ago
                                3: "Março e Setembro",     # Mar -> Mar/Set
                                4: "Abril e Outubro",      # Abr -> Abr/Out
                                5: "Maio e Novembro",      # Mai -> Mai/Nov
                                6: "Junho e Dezembro",     # Jun -> Jun/Dez
                                7: "Janeiro e Julho",      # Jul -> Jan/Jul
                                8: "Fevereiro e Agosto",   # Ago -> Fev/Ago
                                9: "Março e Setembro",     # Set -> Mar/Set
                                10: "Abril e Outubro",     # Out -> Abr/Out
                                11: "Maio e Novembro",     # Nov -> Mai/Nov
                                12: "Junho e Dezembro"     # Dez -> Jun/Dez
                            }

                            return meses_cupom.get(mes, "")

                        except Exception:
                            return ""

                    return ""

                df['Cupom'] = df.apply(extract_cupom, axis=1)
                logger.info("Coluna 'Cupom' criada")

            # MODIFICADO: Limpa coluna Rating E aplica regra "Sem Rating"
            if 'Rating' in df.columns:
                def clean_rating(rating):
                    if pd.isna(rating) or rating == "":
                        return "Sem Rating"  # NOVA REGRA 4

                    rating = str(rating).strip()

                    # Remove "br" no início (brAAA -> AAA)
                    if rating.lower().startswith('br'):
                        rating = rating[2:]

                    # Remove ".br" no final (AAA.br -> AAA)
                    if rating.lower().endswith('.br'):
                        rating = rating[:-3]

                    final_rating = rating.strip()

                    # Se após limpeza ficou vazio, retorna "Sem Rating"
                    if final_rating == "":
                        return "Sem Rating"

                    return final_rating

                df['Rating'] = df['Rating'].apply(clean_rating)
                logger.info(
                    "Coluna 'Rating' limpa com regra 'Sem Rating' aplicada")

            # Classificação de Vencimento
            if 'Vencimento' in df.columns:
                def classify_vencimento(vencimento):
                    """VERSÃO CORRIGIDA - Limita tamanho da string"""
                    if pd.isna(vencimento):
                        return ""

                    try:
                        # Converte para datetime se for string
                        if isinstance(vencimento, str):
                            vencimento = pd.to_datetime(
                                vencimento, errors='coerce')

                        if pd.isna(vencimento):
                            return ""

                        # Ano atual automaticamente
                        ano_atual = datetime.now().year
                        ano_vencimento = vencimento.year

                        # Calcula diferença em anos
                        anos_diferenca = ano_vencimento - ano_atual

                        # Determina categoria
                        if anos_diferenca <= 0:
                            categoria = "[Vencido]"
                        elif anos_diferenca <= 7:
                            categoria = f"[{anos_diferenca} Ano{'s' if anos_diferenca > 1 else ''}]"
                        elif anos_diferenca <= 10:
                            categoria = "[10 Anos]"
                        elif anos_diferenca <= 15:
                            categoria = "[15 Anos]"
                        elif anos_diferenca <= 20:
                            categoria = "[20 Anos]"
                        else:
                            # 🔧 CORREÇÃO: String mais curta
                            return "Acima 20 Anos"

                        # Formato padrão: sempre "Até Dez/YYYY"
                        resultado = f"{categoria} - Até Dez/{ano_vencimento}"

                        # 🔧 CORREÇÃO: Limita o tamanho para 255 caracteres (tamanho do campo MySQL)
                        if len(resultado) > 255:
                            resultado = resultado[:252] + "..."

                        return resultado

                    except Exception as e:
                        logger.warning(f"Erro ao classificar vencimento: {e}")
                        return ""

                df['Classificar Vencimento'] = df['Vencimento'].apply(
                    classify_vencimento)
                logger.info("Coluna 'Classificar Vencimento' criada")

            logger.info("Novas colunas criadas com sucesso")
            return df

        except Exception as e:
            logger.error(f"Erro ao criar novas colunas: {e}")
            return df

    def select_columns(self, df) -> pd.DataFrame:
        """CORRIGIDO: Seleciona apenas as colunas do código original + Tax.Mín_Clean"""
        try:
            # Colunas originais + apenas Tax.Mín_Clean
            colunas_manter = [
                'Ativo', 'Instrumento', 'Duration', 'Indexador', 'Juros',
                'Primeira Data de Juros', 'Isento', 'Rating', 'Vencimento',
                'Tax.Mín', 'Tax.Mín_Clean',  # Apenas esta taxa tem versão clean
                'ROA E. Aprox.', 'Taxa de Emissão', 'Público',
                'Público Resumido', 'Emissor', 'Cupom', 'Classificar Vencimento'
            ]

            # Verifica quais colunas existem no DataFrame
            colunas_existentes = [
                col for col in colunas_manter if col in df.columns]
            colunas_removidas = len(df.columns) - len(colunas_existentes)

            df_final = df[colunas_existentes]

            logger.info(
                f"Seleção de colunas: {colunas_removidas} colunas removidas")
            logger.info(f"Colunas mantidas: {len(colunas_existentes)}")

            return df_final

        except Exception as e:
            logger.error(f"Erro na seleção de colunas: {e}")
            return df

    def clean_dataframe_for_mysql(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpa o DataFrame para inserção no MySQL - CORRIGIDO apenas colunas necessárias"""
        try:
            logger.info("Limpando DataFrame para MySQL...")

            # Substitui NaN por valores padrão em colunas de texto (apenas as que usamos)
            text_columns = ['Ativo', 'Instrumento', 'Indexador', 'Juros', 'Isento',
                            'Rating', 'Público', 'Público Resumido', 'Emissor',
                            'Cupom', 'Classificar Vencimento']

            for col in text_columns:
                if col in df.columns:
                    df[col] = df[col].fillna('')
                    # Remove strings 'nan' se existirem
                    df[col] = df[col].astype(str).replace('nan', '')

            # Substitui NaN por 0 em colunas numéricas (apenas as que usamos) - SEM Tax.Mín
            numeric_columns = ['Duration', 'Tax.Mín_Clean',
                               'ROA E. Aprox.', 'Taxa de Emissão']

            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(
                        df[col], errors='coerce').fillna(0.0)

            # Limpa colunas de data
            date_columns = ['Primeira Data de Juros', 'Vencimento']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')

            logger.info(
                f"DataFrame limpo: {len(df)} linhas preparadas para MySQL")
            return df

        except Exception as e:
            logger.error(f"Erro ao limpar DataFrame: {e}")
            return df

    def download_and_process_category(self, categoria: str, nome_arquivo: str) -> Optional[pd.DataFrame]:
        """Faz o download e processa uma categoria específica"""
        try:
            url = f"https://api-advisor.xpi.com.br/rf-fixedincome-hub-apim/v2/available-assets/export?category={categoria}&brand=XP"
            headers = self.get_headers()

            logger.info(f"Baixando categoria: {categoria}")

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            # Processa o Excel direto da memória
            excel_content = response.content
            tamanho_arquivo = len(excel_content)
            logger.info(
                f"Categoria {categoria} baixada: {tamanho_arquivo:,} bytes")

            # Salva backup opcional
            data_hoje = datetime.today().strftime("%Y-%m-%d")
            backup_path = self.base_path / f"{nome_arquivo}_{data_hoje}.xlsx"
            with open(backup_path, "wb") as f:
                f.write(excel_content)
            logger.info(f"Backup salvo: {backup_path}")

            # Lê o Excel da memória
            excel_buffer = BytesIO(excel_content)
            df = pd.read_excel(excel_buffer)

            # Adiciona coluna Duration com valor 0 se não existir (caso da planilha EB)
            if 'Duration' not in df.columns:
                df['Duration'] = 0
                logger.info(
                    f"Coluna 'Duration' adicionada à categoria {categoria}")

            logger.info(f"Categoria {categoria} processada: {len(df)} linhas")
            return df

        except requests.exceptions.Timeout:
            logger.error(f"Timeout na requisição para categoria {categoria}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição para categoria {categoria}: {e}")
            return None
        except Exception as e:
            logger.error(
                f"Erro inesperado ao processar categoria {categoria}: {e}")
            return None

    def process_and_store_data(self) -> bool:
        """MODIFICADO: Baixa, processa e armazena todas as categorias no MySQL com novas regras"""
        try:
            dataframes = []

            # Conecta ao banco
            self.db_manager = DatabaseManager(self.db_config)
            if not self.db_manager.connect():
                return False

            # Cria tabela se necessário
            if not self.db_manager.create_fixed_income_table():
                return False

            logger.info("Iniciando download e processamento das categorias...")

            # Baixa e processa cada categoria
            for categoria, nome_arquivo in self.categorias.items():
                df = self.download_and_process_category(
                    categoria, nome_arquivo)
                if df is not None:
                    dataframes.append(df)
                else:
                    logger.error(
                        f"Falha no download da categoria: {categoria}")
                    return False

            # Consolida todas as planilhas
            df_consolidado = pd.concat(dataframes, ignore_index=True)
            logger.info(
                f"Dados consolidados: {len(df_consolidado)} linhas totais")

            # NOVA REGRA 1: Remove ativos com indexador IGP-M
            df_sem_igpm = self.filter_igpm_assets(df_consolidado)

            # Filtra por juros (apenas Mensal e Semestral)
            if 'Juros' in df_sem_igpm.columns:
                df_filtrado = df_sem_igpm[df_sem_igpm['Juros'].isin(
                    ['Mensal', 'Semestral'])]
                linhas_removidas = len(df_sem_igpm) - len(df_filtrado)
                logger.info(
                    f"Filtro por juros aplicado: {linhas_removidas} linhas removidas, {len(df_filtrado)} mantidas")
            else:
                logger.warning(
                    "Coluna 'Juros' não encontrada, mantendo todos os registros")
                df_filtrado = df_sem_igpm

            # Processa os dados com NOVAS REGRAS (ordem corrigida)
            # Aplica regras NTN ANTES da formatação
            df_com_ntn_rules = self.apply_ntn_rules(df_filtrado)
            df_formatado = self.format_tax_columns(
                df_com_ntn_rules)  # Cria colunas limpas
            df_com_novas_colunas = self.create_new_columns(
                df_formatado)  # Inclui "Sem Rating"
            df_pre_final = self.select_columns(df_com_novas_colunas)
            df_final = self.clean_dataframe_for_mysql(
                df_pre_final)  # NOVA ETAPA: Limpa para MySQL

            # Salva planilha consolidada (backup)
            data_hoje = datetime.today().strftime("%Y-%m-%d")
            arquivo_consolidado = self.base_path / \
                f"Consolidado_MySQL_{data_hoje}.xlsx"

            with pd.ExcelWriter(arquivo_consolidado, engine='xlsxwriter') as writer:
                df_final.to_excel(
                    writer, sheet_name='Consolidado', index=False)

                # Formatação de porcentagem para colunas específicas
                workbook = writer.book
                worksheet = writer.sheets['Consolidado']
                percent_format = workbook.add_format({'num_format': '0.00%'})

                # Aplica formatação apenas às colunas que devem ter formato %
                percent_columns = ['Tax.Mín_Clean',
                                   'ROA E. Aprox.', 'Taxa de Emissão']
                for col in percent_columns:
                    if col in df_final.columns:
                        col_idx = df_final.columns.get_loc(col)
                        worksheet.set_column(
                            col_idx, col_idx, None, percent_format)

            logger.info(f"Backup consolidado salvo: {arquivo_consolidado}")

            # Limpa todos os dados antigos antes de inserir os novos
            if not self.db_manager.clear_all_data():
                logger.error("Falha ao limpar dados antigos")
                return False

            # Insere os novos dados no MySQL
            if not self.db_manager.insert_fixed_income_data(df_final):
                return False

            logger.info(
                f"Processamento concluído: {len(df_final)} registros inseridos no MySQL")
            return True

        except Exception as e:
            logger.error(f"Erro durante processamento: {e}")
            return False
        finally:
            if self.db_manager:
                self.db_manager.disconnect()

    def test_mysql_connection(self) -> bool:
        """Testa apenas a conexão com o MySQL"""
        logger.info("=== Testando conexão MySQL ===")

        if not self.load_configuration():
            return False

        # Testa conexão
        self.db_manager = DatabaseManager(self.db_config)

        if not self.db_manager.connect():
            logger.error("Falha na conexão com MySQL")
            return False

        # Testa criação de tabela
        if not self.db_manager.create_fixed_income_table():
            logger.error("Falha ao criar/verificar tabela")
            return False

        # Testa uma consulta simples
        try:
            cursor = self.db_manager.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM fixed_income_data")
            count = cursor.fetchone()[0]
            logger.info(
                f"Tabela fixed_income_data existe e tem {count} registros")
            cursor.close()

            logger.info("=== Teste de conexão MySQL bem-sucedido! ===")
            return True

        except mysql.connector.Error as err:
            logger.error(f"Erro ao consultar tabela: {err}")
            return False
        finally:
            if self.db_manager:
                self.db_manager.disconnect()

    def run(self) -> bool:
        """Executa o processo completo de download e inserção no MySQL"""
        logger.info(
            "=== Iniciando processo de renda fixa para MySQL (estrutura corrigida) ===")
        logger.info("📋 Colunas finais: Ativo, Instrumento, Duration, Indexador, Juros, Primeira Data de Juros, Isento, Rating, Vencimento, Tax.Mín, Tax.Mín_Clean, ROA E. Aprox., Taxa de Emissão, Público, Público Resumido, Emissor, Cupom, Classificar Vencimento")

        # Carrega configurações
        if not self.load_configuration():
            return False

        # Configura pasta de destino (para backup)
        if not self.setup_destination_folder():
            return False

        # Processa e armazena os dados
        success = self.process_and_store_data()

        if success:
            logger.info("=== Processo concluído com sucesso ===")
        else:
            logger.error("=== Processo finalizado com erros ===")

        return success


def main():
    """Função principal"""
    try:
        downloader = FixedIncomeDownloader()

        # Se passou argumento 'test', testa apenas a conexão MySQL
        if len(sys.argv) > 1 and sys.argv[1] == 'test':
            success = downloader.test_mysql_connection()
        else:
            success = downloader.run()

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        logger.info("Processo interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erro crítico: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
