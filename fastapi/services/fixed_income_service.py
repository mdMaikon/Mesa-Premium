"""
Fixed Income Data Processing Service
Migrated and refactored from juro_mensal_mysql.py
"""
import os
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
from database.connection import get_database_connection, execute_query

logger = logging.getLogger(__name__)


class FixedIncomeService:
    """Service for downloading and processing fixed income data from Hub XP"""

    def __init__(self):
        self.token: Optional[str] = None
        self.categorias = {
            "CREDITOPRIVADO": "CP",
            "BANCARIO": "EB", 
            "TPF": "TPF",
        }

    async def get_valid_token(self) -> Optional[str]:
        """Get a valid token from hub_tokens table"""
        try:
            query = """
            SELECT token, expires_at 
            FROM hub_tokens 
            WHERE expires_at > NOW() 
            ORDER BY created_at DESC 
            LIMIT 1
            """
            
            result = execute_query(query, fetch=True)
            
            if not result:
                logger.error("No valid token found in database")
                return None
                
            token_data = result[0]
            self.token = token_data['token']
            logger.info(f"Valid token retrieved, expires at: {token_data['expires_at']}")
            return self.token
            
        except Exception as e:
            logger.error(f"Error retrieving token from database: {e}")
            return None

    def get_headers(self) -> Dict[str, str]:
        """Return headers for API requests"""
        return {
            "Authorization": f"Bearer {self.token}",
            "ocp-apim-subscription-key": "3923e12297e7448398ba9a9046c4fced",
            "Content-Type": "application/json",
            "Origin": "https://hub.xpi.com.br",
            "Referer": "https://hub.xpi.com.br/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def extract_percentage_value(self, text) -> float:
        """Extract numeric value from rate strings"""
        if pd.isna(text) or text == "":
            return 0.0

        text = str(text)
        
        # Look for numbers (with or without comma) followed or preceded by %
        match = re.search(r'(\d+(?:,\d+)?)', text)
        
        if match:
            value = match.group(1).replace(',', '.')
            return float(value) / 100  # Divide by 100 for Excel % format
            
        return 0.0

    def format_tax_columns(self, df) -> pd.DataFrame:
        """Format tax columns creating clean versions"""
        try:
            logger.info("Formatting tax columns...")
            
            # Process only Tax.Mín - creating clean version
            if 'Tax.Mín' in df.columns:
                logger.info("Creating Tax.Mín_Clean - keeping original intact")
                df['Tax.Mín_Clean'] = df['Tax.Mín'].apply(self.extract_percentage_value)
                logger.info("Tax.Mín_Clean created successfully")
            else:
                logger.warning("Tax.Mín column not found")
            
            # Format ROA E. Aprox. column
            if 'ROA E. Aprox.' in df.columns:
                logger.info("Formatting ROA E. Aprox. column")
                df['ROA E. Aprox.'] = df['ROA E. Aprox.'].apply(self.extract_percentage_value)
            
            # Format Taxa de Emissão column
            if 'Taxa de Emissão' in df.columns:
                logger.info("Formatting Taxa de Emissão column")
                df['Taxa de Emissão'] = df['Taxa de Emissão'].apply(self.extract_percentage_value)
            
            logger.info("Column formatting completed")
            return df
            
        except Exception as e:
            logger.error(f"Error during column formatting: {e}")
            return df

    def filter_igpm_assets(self, df) -> pd.DataFrame:
        """Remove assets with IGP-M indexer"""
        try:
            if 'Indexador' not in df.columns:
                logger.warning("'Indexador' column not found")
                return df
            
            lines_before = len(df)
            df_filtered = df[df['Indexador'] != 'IGP-M'].copy()
            lines_removed = lines_before - len(df_filtered)
            
            logger.info(f"IGP-M filter applied: {lines_removed} assets removed")
            return df_filtered
            
        except Exception as e:
            logger.error(f"Error filtering IGP-M assets: {e}")
            return df

    def apply_ntn_rules(self, df) -> pd.DataFrame:
        """Apply specific rules for NTN assets"""
        try:
            if 'Ativo' not in df.columns:
                logger.warning("'Ativo' column not found")
                return df
            
            ntn_aaa_count = 0
            ntn_f_count = 0
            
            for index, row in df.iterrows():
                ativo = str(row.get('Ativo', ''))
                
                # Rule 2: NTN receives AAA Rating
                if ativo.startswith('NTN'):
                    df.at[index, 'Rating'] = 'AAA'
                    ntn_aaa_count += 1
                
                # Rule 3: NTN-F receives 10% emission rate
                if 'NTN-F' in ativo:
                    df.at[index, 'Taxa de Emissão'] = '10%'
                    ntn_f_count += 1
            
            logger.info(f"NTN rules applied: {ntn_aaa_count} NTN assets with AAA Rating, {ntn_f_count} NTN-F assets with 10% rate")
            return df
            
        except Exception as e:
            logger.error(f"Error applying NTN rules: {e}")
            return df

    def create_new_columns(self, df) -> pd.DataFrame:
        """Create new columns and apply rating rules"""
        try:
            logger.info("Creating new columns...")
            
            # Público Resumido column
            if 'Público' in df.columns:
                df['Público Resumido'] = df['Público'].map({
                    'Investidor Geral': 'R',
                    'Investidor Qualificado': 'Q', 
                    'Investidor Profissional': 'P'
                }).fillna('')
                logger.info("'Público Resumido' column created")
            
            # Emissor column
            if 'Ativo' in df.columns:
                def extract_emissor(ativo):
                    if pd.isna(ativo):
                        return ""
                    
                    ativo = str(ativo)
                    
                    # Special case: NTN = TESOURO NACIONAL
                    if ativo.startswith('NTN'):
                        return "TESOURO NACIONAL"
                    
                    # Remove prefixes
                    prefixes = ['CDB', 'CRI', 'CRA', 'CDCA', 'DEB', 'LCI', 'LCA']
                    for prefix in prefixes:
                        if ativo.startswith(prefix):
                            ativo = ativo[len(prefix):].strip()
                            break
                    
                    # Remove everything after "-" (maturity)
                    if '-' in ativo:
                        ativo = ativo.split('-')[0].strip()
                    
                    return ativo
                
                df['Emissor'] = df['Ativo'].apply(extract_emissor)
                logger.info("'Emissor' column created")
            
            # Cupom column
            if 'Vencimento' in df.columns and 'Juros' in df.columns:
                def extract_cupom(row):
                    juros = row['Juros']
                    vencimento = row['Vencimento']
                    
                    if juros == 'Mensal':
                        return 'Mensal'
                    
                    if juros == 'Semestral':
                        if pd.isna(vencimento):
                            return ""
                        
                        try:
                            if isinstance(vencimento, str):
                                vencimento = pd.to_datetime(vencimento, errors='coerce')
                            
                            if pd.isna(vencimento):
                                return ""
                            
                            month = vencimento.month
                            
                            months_cupom = {
                                1: "Janeiro e Julho", 2: "Fevereiro e Agosto",
                                3: "Março e Setembro", 4: "Abril e Outubro", 
                                5: "Maio e Novembro", 6: "Junho e Dezembro",
                                7: "Janeiro e Julho", 8: "Fevereiro e Agosto",
                                9: "Março e Setembro", 10: "Abril e Outubro",
                                11: "Maio e Novembro", 12: "Junho e Dezembro"
                            }
                            
                            return months_cupom.get(month, "")
                            
                        except Exception:
                            return ""
                    
                    return ""
                
                df['Cupom'] = df.apply(extract_cupom, axis=1)
                logger.info("'Cupom' column created")
            
            # Clean Rating column and apply "Sem Rating" rule
            if 'Rating' in df.columns:
                def clean_rating(rating):
                    if pd.isna(rating) or rating == "":
                        return "Sem Rating"
                    
                    rating = str(rating).strip()
                    
                    # Remove "br" at beginning
                    if rating.lower().startswith('br'):
                        rating = rating[2:]
                    
                    # Remove ".br" at end
                    if rating.lower().endswith('.br'):
                        rating = rating[:-3]
                    
                    final_rating = rating.strip()
                    
                    if final_rating == "":
                        return "Sem Rating"
                    
                    return final_rating
                
                df['Rating'] = df['Rating'].apply(clean_rating)
                logger.info("'Rating' column cleaned with 'Sem Rating' rule applied")
            
            # Maturity Classification
            if 'Vencimento' in df.columns:
                def classify_vencimento(vencimento):
                    if pd.isna(vencimento):
                        return ""
                    
                    try:
                        if isinstance(vencimento, str):
                            vencimento = pd.to_datetime(vencimento, errors='coerce')
                        
                        if pd.isna(vencimento):
                            return ""
                        
                        current_year = datetime.now().year
                        maturity_year = vencimento.year
                        years_diff = maturity_year - current_year
                        
                        if years_diff <= 0:
                            category = "[Vencido]"
                        elif years_diff <= 7:
                            category = f"[{years_diff} Ano{'s' if years_diff > 1 else ''}]"
                        elif years_diff <= 10:
                            category = "[10 Anos]"
                        elif years_diff <= 15:
                            category = "[15 Anos]"
                        elif years_diff <= 20:
                            category = "[20 Anos]"
                        else:
                            return "Sem Limite de Vencimento"
                        
                        result = f"{category} - Até Dez/{maturity_year}"
                        
                        # Limit size to 255 characters
                        if len(result) > 255:
                            result = result[:252] + "..."
                        
                        return result
                        
                    except Exception as e:
                        logger.warning(f"Error classifying maturity: {e}")
                        return ""
                
                df['Classificar Vencimento'] = df['Vencimento'].apply(classify_vencimento)
                logger.info("'Classificar Vencimento' column created")
            
            logger.info("New columns created successfully")
            return df
            
        except Exception as e:
            logger.error(f"Error creating new columns: {e}")
            return df

    def select_columns(self, df) -> pd.DataFrame:
        """Select only required columns"""
        try:
            columns_to_keep = [
                'Ativo', 'Instrumento', 'Duration', 'Indexador', 'Juros',
                'Primeira Data de Juros', 'Isento', 'Rating', 'Vencimento',
                'Tax.Mín', 'Tax.Mín_Clean',
                'ROA E. Aprox.', 'Taxa de Emissão', 'Público',
                'Público Resumido', 'Emissor', 'Cupom', 'Classificar Vencimento'
            ]
            
            existing_columns = [col for col in columns_to_keep if col in df.columns]
            removed_columns = len(df.columns) - len(existing_columns)
            
            df_final = df[existing_columns]
            
            logger.info(f"Column selection: {removed_columns} columns removed")
            logger.info(f"Columns kept: {len(existing_columns)}")
            
            return df_final
            
        except Exception as e:
            logger.error(f"Error in column selection: {e}")
            return df

    def clean_dataframe_for_mysql(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean DataFrame for MySQL insertion"""
        try:
            logger.info("Cleaning DataFrame for MySQL...")
            
            # Replace NaN with default values in text columns
            text_columns = ['Ativo', 'Instrumento', 'Indexador', 'Juros', 'Isento',
                           'Rating', 'Público', 'Público Resumido', 'Emissor',
                           'Cupom', 'Classificar Vencimento']
            
            for col in text_columns:
                if col in df.columns:
                    df[col] = df[col].fillna('')
                    df[col] = df[col].astype(str).replace('nan', '')
            
            # Replace NaN with 0 in numeric columns
            numeric_columns = ['Duration', 'Tax.Mín_Clean', 'ROA E. Aprox.', 'Taxa de Emissão']
            
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
            # Clean date columns
            date_columns = ['Primeira Data de Juros', 'Vencimento']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            
            logger.info(f"DataFrame cleaned: {len(df)} rows prepared for MySQL")
            return df
            
        except Exception as e:
            logger.error(f"Error cleaning DataFrame: {e}")
            return df

    async def download_and_process_category(self, categoria: str, nome_arquivo: str) -> Optional[pd.DataFrame]:
        """Download and process a specific category"""
        try:
            url = f"https://api-advisor.xpi.com.br/rf-fixedincome-hub-apim/v2/available-assets/export?category={categoria}&brand=XP"
            headers = self.get_headers()
            
            logger.info(f"Downloading category: {categoria}")
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Process Excel directly from memory
            excel_content = response.content
            file_size = len(excel_content)
            logger.info(f"Category {categoria} downloaded: {file_size:,} bytes")
            
            # Read Excel from memory
            excel_buffer = BytesIO(excel_content)
            df = pd.read_excel(excel_buffer)
            
            # Add Duration column with value 0 if it doesn't exist
            if 'Duration' not in df.columns:
                df['Duration'] = 0
                logger.info(f"Duration column added to category {categoria}")
            
            logger.info(f"Category {categoria} processed: {len(df)} rows")
            return df
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout in request for category {categoria}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for category {categoria}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error processing category {categoria}: {e}")
            return None

    async def create_fixed_income_table(self) -> bool:
        """Create fixed income table if it doesn't exist"""
        try:
            connection = get_database_connection()
            if not connection:
                return False
            
            cursor = connection.cursor()
            
            # Drop table if exists to ensure new structure
            drop_table_query = "DROP TABLE IF EXISTS fixed_income_data"
            cursor.execute(drop_table_query)
            logger.info("Previous table removed (if existed)")
            
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
            logger.info("fixed_income_data table created with TEXT field for classificar_vencimento!")
            cursor.close()
            connection.close()
            return True
            
        except mysql.connector.Error as err:
            logger.error(f"Error creating table: {err}")
            return False

    async def clear_all_data(self) -> bool:
        """Remove all data from table to insert fresh data"""
        try:
            query = "DELETE FROM fixed_income_data"
            execute_query(query)
            logger.info("Table cleared: all records removed")
            return True
            
        except Exception as err:
            logger.error(f"Error clearing table: {err}")
            return False

    async def insert_fixed_income_data(self, df: pd.DataFrame) -> bool:
        """Insert fixed income data into database"""
        try:
            connection = get_database_connection()
            if not connection:
                return False
            
            cursor = connection.cursor()
            
            # Add collection timestamp
            df['data_coleta'] = datetime.now()
            
            # Convert DataFrame to list of dicts
            records = df.to_dict('records')
            logger.info(f"Converted {len(records)} records for insertion")
            
            # Convert records to list of tuples
            data_tuples = []
            for record in records:
                def get_safe_value(key, default='', is_numeric=False):
                    value = record.get(key, default)
                    
                    if pd.isna(value):
                        return 0.0 if is_numeric else ''
                    
                    if is_numeric:
                        try:
                            return float(value) if value != '' else 0.0
                        except (ValueError, TypeError):
                            return 0.0
                    
                    if isinstance(value, str):
                        return value.strip()
                    elif value is None:
                        return ''
                    else:
                        return str(value).strip()
                
                tuple_data = (
                    record.get('data_coleta'),
                    get_safe_value('Ativo'),
                    get_safe_value('Instrumento'),
                    get_safe_value('Duration', 0.0, is_numeric=True),
                    get_safe_value('Indexador'),
                    get_safe_value('Juros'),
                    record.get('Primeira Data de Juros'),
                    get_safe_value('Isento'),
                    get_safe_value('Rating'),
                    record.get('Vencimento'),
                    get_safe_value('Tax.Mín'),
                    get_safe_value('Tax.Mín_Clean', 0.0, is_numeric=True),
                    get_safe_value('ROA E. Aprox.', 0.0, is_numeric=True),
                    get_safe_value('Taxa de Emissão', 0.0, is_numeric=True),
                    get_safe_value('Público'),
                    get_safe_value('Público Resumido'),
                    get_safe_value('Emissor'),
                    get_safe_value('Cupom'),
                    get_safe_value('Classificar Vencimento')
                )
                
                data_tuples.append(tuple_data)
            
            insert_query = """
            INSERT INTO fixed_income_data 
            (data_coleta, ativo, instrumento, duration, indexador, juros, 
            primeira_data_juros, isento, rating, vencimento, tax_min, tax_min_clean,
            roa_aprox, taxa_emissao, publico, publico_resumido, 
            emissor, cupom, classificar_vencimento)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # Batch insertion for better performance
            cursor.executemany(insert_query, data_tuples)
            connection.commit()
            
            logger.info(f"Inserted {len(data_tuples)} records into MySQL!")
            cursor.close()
            connection.close()
            return True
            
        except mysql.connector.Error as err:
            logger.error(f"Error inserting data into MySQL: {err}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error inserting data: {e}")
            return False

    async def process_and_store_data(self) -> Dict[str, Any]:
        """Main method to download, process and store all categories"""
        try:
            # Get valid token
            if not await self.get_valid_token():
                return {
                    "success": False,
                    "message": "No valid token available",
                    "error": "Unable to retrieve valid token from database"
                }
            
            # Create table if necessary
            if not await self.create_fixed_income_table():
                return {
                    "success": False,
                    "message": "Failed to create database table",
                    "error": "Database table creation failed"
                }
            
            dataframes = []
            logger.info("Starting download and processing of categories...")
            
            # Download and process each category
            for categoria, nome_arquivo in self.categorias.items():
                df = await self.download_and_process_category(categoria, nome_arquivo)
                if df is not None:
                    dataframes.append(df)
                else:
                    return {
                        "success": False,
                        "message": f"Failed to download category: {categoria}",
                        "error": f"Category {categoria} download failed"
                    }
            
            # Consolidate all spreadsheets
            df_consolidated = pd.concat(dataframes, ignore_index=True)
            logger.info(f"Data consolidated: {len(df_consolidated)} total rows")
            
            # Apply filters and rules
            df_sem_igpm = self.filter_igpm_assets(df_consolidated)
            
            # Filter by interest rates (only Monthly and Semiannual)
            if 'Juros' in df_sem_igpm.columns:
                df_filtered = df_sem_igpm[df_sem_igpm['Juros'].isin(['Mensal', 'Semestral'])]
                removed_lines = len(df_sem_igpm) - len(df_filtered)
                logger.info(f"Interest filter applied: {removed_lines} rows removed, {len(df_filtered)} kept")
            else:
                logger.warning("'Juros' column not found, keeping all records")
                df_filtered = df_sem_igpm
            
            # Process data with rules (correct order)
            df_com_ntn_rules = self.apply_ntn_rules(df_filtered)
            df_formatado = self.format_tax_columns(df_com_ntn_rules)
            df_com_novas_colunas = self.create_new_columns(df_formatado)
            df_pre_final = self.select_columns(df_com_novas_colunas)
            df_final = self.clean_dataframe_for_mysql(df_pre_final)
            
            # Clear old data before inserting new ones
            if not await self.clear_all_data():
                return {
                    "success": False,
                    "message": "Failed to clear old data",
                    "error": "Database clear operation failed"
                }
            
            # Insert new data into MySQL
            if not await self.insert_fixed_income_data(df_final):
                return {
                    "success": False,
                    "message": "Failed to insert data into database",
                    "error": "Database insertion failed"
                }
            
            logger.info(f"Processing completed: {len(df_final)} records inserted into MySQL")
            return {
                "success": True,
                "message": "Fixed income data processed successfully",
                "records_processed": len(df_final),
                "categories_processed": list(self.categorias.keys()),
                "processing_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error during processing: {e}")
            return {
                "success": False,
                "message": "Processing failed with error",
                "error": str(e)
            }

    async def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        try:
            query = """
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT emissor) as unique_issuers,
                COUNT(DISTINCT indexador) as unique_indexers,
                MAX(data_coleta) as last_update,
                MIN(vencimento) as earliest_maturity,
                MAX(vencimento) as latest_maturity
            FROM fixed_income_data
            """
            
            result = execute_query(query, fetch=True)
            
            if not result:
                return {"error": "No data found"}
            
            stats = result[0]
            
            return {
                "total_records": stats['total_records'],
                "unique_issuers": stats['unique_issuers'],
                "unique_indexers": stats['unique_indexers'],
                "last_update": stats['last_update'].isoformat() if stats['last_update'] else None,
                "earliest_maturity": stats['earliest_maturity'].isoformat() if stats['earliest_maturity'] else None,
                "latest_maturity": stats['latest_maturity'].isoformat() if stats['latest_maturity'] else None
            }
            
        except Exception as e:
            logger.error(f"Error getting processing stats: {e}")
            return {"error": str(e)}