"""
Fixed Income Data Processing Service
Migrated and refactored from juro_mensal_mysql.py
"""

import asyncio
import os
import re
from datetime import datetime
from io import BytesIO
from typing import Any

import httpx
import pandas as pd
from database.connection import execute_query, get_database_connection
from dotenv import load_dotenv
from utils.log_sanitizer import get_sanitized_logger

import mysql.connector

from .fixed_income_exceptions import (
    ColumnFormattingError,
    FilteringError,
    TokenRetrievalError,
)

# Load environment variables from project root
project_root = os.path.join(os.path.dirname(__file__), "..", "..")
load_dotenv(os.path.join(project_root, ".env"), override=True)

logger = get_sanitized_logger(__name__)


class FixedIncomeService:
    """Service for downloading and processing fixed income data from Hub XP"""

    def __init__(self):
        self.token: str | None = None
        self.categorias = {
            "CREDITOPRIVADO": "CP",
            "BANCARIO": "EB",
            "TPF": "TPF",
        }

    async def get_valid_token(self) -> str | None:
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
            self.token = token_data["token"]
            logger.info(
                f"Valid token retrieved, expires at: {token_data['expires_at']}"
            )
            return self.token

        except mysql.connector.Error as e:
            logger.error(f"Database error retrieving token: {e}")
            raise TokenRetrievalError(
                f"Failed to retrieve token from database: {e}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error retrieving token: {e}")
            raise TokenRetrievalError(
                f"Unexpected error during token retrieval: {e}"
            ) from e

    def get_headers(self) -> dict[str, str]:
        """Return headers for API requests"""
        api_key = os.getenv("HUB_XP_API_KEY")
        if not api_key:
            raise ValueError("HUB_XP_API_KEY environment variable not found")

        return {
            "Authorization": f"Bearer {self.token}",
            "ocp-apim-subscription-key": api_key,
            "Content-Type": "application/json",
            "Origin": "https://hub.xpi.com.br",
            "Referer": "https://hub.xpi.com.br/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

    def extract_percentage_value(self, text) -> float:
        """
        Extract numeric value from rate strings and convert to decimal format

        This method processes Brazilian financial rate formats and converts them
        to standardized decimal values for calculations and storage.

        Args:
            text: Input string containing percentage value (e.g., "12,5%", "8.25%", "CDI + 2,3%")

        Returns:
            float: Decimal representation of the percentage (e.g., 0.125 for "12,5%")
                  Returns 0.0 for invalid or empty inputs

        Examples:
            >>> extract_percentage_value("12,5%")
            0.125
            >>> extract_percentage_value("CDI + 2,3%")
            0.023
            >>> extract_percentage_value("")
            0.0

        Note:
            - Handles both comma (Brazilian) and dot (international) decimal separators
            - Extracts first numeric value found in complex strings
            - Automatically converts to decimal by dividing by 100
        """
        if pd.isna(text) or text == "":
            return 0.0

        text = str(text)

        # Look for numbers (with or without comma) followed or preceded by %
        match = re.search(r"(\d+(?:,\d+)?)", text)

        if match:
            value = match.group(1).replace(",", ".")
            return float(value) / 100  # Divide by 100 for Excel % format

        return 0.0

    def format_tax_columns(self, df) -> pd.DataFrame:
        """
        Format tax columns creating clean numeric versions for analysis

        This method processes financial data columns that contain Brazilian
        rate formats and creates clean decimal versions suitable for calculations
        and database storage. The original columns are preserved for reference.

        Columns processed:
        - Tax.Mín: Creates Tax.Mín_Clean with decimal values
        - ROA E. Aprox.: Converts to decimal format
        - Taxa de Emissão: Converts to decimal format

        Args:
            df: DataFrame containing financial data with Brazilian rate formats

        Returns:
            pd.DataFrame: Enhanced DataFrame with additional clean numeric columns

        Raises:
            ColumnFormattingError: If required columns are missing or data types are invalid

        Examples:
            Input: Tax.Mín = "CDI + 2,5%"
            Output: Tax.Mín_Clean = 0.025

        Business Logic:
        - Preserves original columns for audit trails
        - Standardizes percentage formats across different sources
        - Enables numerical analysis and database operations
        """
        try:
            logger.info("Formatting tax columns...")

            # Process only Tax.Mín - creating clean version
            if "Tax.Mín" in df.columns:
                logger.info("Creating Tax.Mín_Clean - keeping original intact")
                df["Tax.Mín_Clean"] = df["Tax.Mín"].apply(
                    self.extract_percentage_value
                )
                logger.info("Tax.Mín_Clean created successfully")
            else:
                logger.warning("Tax.Mín column not found")

            # Format ROA E. Aprox. column
            if "ROA E. Aprox." in df.columns:
                logger.info("Formatting ROA E. Aprox. column")
                df["ROA E. Aprox."] = df["ROA E. Aprox."].apply(
                    self.extract_percentage_value
                )

            # Format Taxa de Emissão column
            if "Taxa de Emissão" in df.columns:
                logger.info("Formatting Taxa de Emissão column")
                df["Taxa de Emissão"] = df["Taxa de Emissão"].apply(
                    self.extract_percentage_value
                )

            logger.info("Column formatting completed")
            return df

        except (KeyError, AttributeError) as e:
            logger.error(f"Column access error during formatting: {e}")
            raise ColumnFormattingError(
                f"Missing or invalid column during formatting: {e}"
            ) from e
        except (ValueError, TypeError) as e:
            logger.error(f"Data type error during column formatting: {e}")
            raise ColumnFormattingError(
                f"Invalid data type during formatting: {e}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error during column formatting: {e}")
            raise ColumnFormattingError(
                f"Unexpected error during column formatting: {e}"
            ) from e

    def filter_igpm_assets(self, df) -> pd.DataFrame:
        """Remove assets with IGP-M indexer (optimized for pipeline)"""
        try:
            if "Indexador" not in df.columns:
                logger.warning("'Indexador' column not found")
                return df

            lines_before = len(df)
            # Use query method for better performance with large datasets
            df_filtered = df.query("Indexador != 'IGP-M'").copy()
            lines_removed = lines_before - len(df_filtered)

            logger.info(
                f"IGP-M filter applied: {lines_removed} assets removed"
            )
            return df_filtered

        except KeyError as e:
            logger.error(f"Missing column during IGP-M filtering: {e}")
            raise FilteringError(
                f"Required column missing for IGP-M filtering: {e}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error filtering IGP-M assets: {e}")
            raise FilteringError(
                f"Unexpected error during IGP-M filtering: {e}"
            ) from e

    def apply_ntn_rules(self, df) -> pd.DataFrame:
        """Apply specific rules for NTN assets"""
        try:
            if "Ativo" not in df.columns:
                logger.warning("'Ativo' column not found")
                return df

            ntn_aaa_count = 0
            ntn_f_count = 0

            for index, row in df.iterrows():
                ativo = str(row.get("Ativo", ""))

                # Rule 2: NTN receives AAA Rating
                if ativo.startswith("NTN"):
                    df.at[index, "Rating"] = "AAA"
                    ntn_aaa_count += 1

                # Rule 3: NTN-F receives 10% emission rate
                if "NTN-F" in ativo:
                    df.at[index, "Taxa de Emissão"] = "10%"
                    ntn_f_count += 1

            logger.info(
                f"NTN rules applied: {ntn_aaa_count} NTN assets with AAA Rating, {ntn_f_count} NTN-F assets with 10% rate"
            )
            return df

        except Exception as e:
            logger.error(f"Error applying NTN rules: {e}")
            return df

    def create_new_columns(self, df) -> pd.DataFrame:
        """Create new columns and apply rating rules"""
        try:
            logger.info("Creating new columns...")

            # Público Resumido column
            if "Público" in df.columns:
                df["Público Resumido"] = (
                    df["Público"]
                    .map(
                        {
                            "Investidor Geral": "R",
                            "Investidor Qualificado": "Q",
                            "Investidor Profissional": "P",
                        }
                    )
                    .fillna("")
                )
                logger.info("'Público Resumido' column created")

            # Emissor column
            if "Ativo" in df.columns:

                def extract_emissor(ativo):
                    if pd.isna(ativo):
                        return ""

                    ativo = str(ativo)

                    # Special case: NTN = TESOURO NACIONAL
                    if ativo.startswith("NTN"):
                        return "TESOURO NACIONAL"

                    # Remove prefixes
                    prefixes = [
                        "CDB",
                        "CRI",
                        "CRA",
                        "CDCA",
                        "DEB",
                        "LCI",
                        "LCA",
                    ]
                    for prefix in prefixes:
                        if ativo.startswith(prefix):
                            ativo = ativo[len(prefix) :].strip()
                            break

                    # Remove everything after "-" (maturity)
                    if "-" in ativo:
                        ativo = ativo.split("-")[0].strip()

                    return ativo

                df["Emissor"] = df["Ativo"].apply(extract_emissor)
                logger.info("'Emissor' column created")

            # Cupom column
            if "Vencimento" in df.columns and "Juros" in df.columns:

                def extract_cupom(row):
                    juros = row["Juros"]
                    vencimento = row["Vencimento"]

                    if juros == "Mensal":
                        return "Mensal"

                    if juros == "Semestral":
                        if pd.isna(vencimento):
                            return ""

                        try:
                            if isinstance(vencimento, str):
                                vencimento = pd.to_datetime(
                                    vencimento, errors="coerce"
                                )

                            if pd.isna(vencimento):
                                return ""

                            month = vencimento.month

                            months_cupom = {
                                1: "Janeiro e Julho",
                                2: "Fevereiro e Agosto",
                                3: "Março e Setembro",
                                4: "Abril e Outubro",
                                5: "Maio e Novembro",
                                6: "Junho e Dezembro",
                                7: "Janeiro e Julho",
                                8: "Fevereiro e Agosto",
                                9: "Março e Setembro",
                                10: "Abril e Outubro",
                                11: "Maio e Novembro",
                                12: "Junho e Dezembro",
                            }

                            return months_cupom.get(month, "")

                        except Exception:
                            return ""

                    return ""

                df["Cupom"] = df.apply(extract_cupom, axis=1)
                logger.info("'Cupom' column created")

            # Clean Rating column and apply "Sem Rating" rule
            if "Rating" in df.columns:

                def clean_rating(rating):
                    if pd.isna(rating) or rating == "":
                        return "Sem Rating"

                    rating = str(rating).strip()

                    # Remove "br" at beginning
                    if rating.lower().startswith("br"):
                        rating = rating[2:]

                    # Remove ".br" at end
                    if rating.lower().endswith(".br"):
                        rating = rating[:-3]

                    final_rating = rating.strip()

                    if final_rating == "":
                        return "Sem Rating"

                    return final_rating

                df["Rating"] = df["Rating"].apply(clean_rating)
                logger.info(
                    "'Rating' column cleaned with 'Sem Rating' rule applied"
                )

            # Maturity Classification
            if "Vencimento" in df.columns:

                def classify_vencimento(vencimento):
                    if pd.isna(vencimento):
                        return ""

                    try:
                        if isinstance(vencimento, str):
                            vencimento = pd.to_datetime(
                                vencimento, errors="coerce"
                            )

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

                df["Classificar Vencimento"] = df["Vencimento"].apply(
                    classify_vencimento
                )
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
                "Ativo",
                "Instrumento",
                "Duration",
                "Indexador",
                "Juros",
                "Primeira Data de Juros",
                "Isento",
                "Rating",
                "Vencimento",
                "Tax.Mín",
                "Tax.Mín_Clean",
                "ROA E. Aprox.",
                "Taxa de Emissão",
                "Público",
                "Público Resumido",
                "Emissor",
                "Cupom",
                "Classificar Vencimento",
            ]

            existing_columns = [
                col for col in columns_to_keep if col in df.columns
            ]
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
            text_columns = [
                "Ativo",
                "Instrumento",
                "Indexador",
                "Juros",
                "Isento",
                "Rating",
                "Público",
                "Público Resumido",
                "Emissor",
                "Cupom",
                "Classificar Vencimento",
            ]

            for col in text_columns:
                if col in df.columns:
                    df[col] = df[col].fillna("")
                    df[col] = df[col].astype(str).replace("nan", "")

            # Replace NaN with 0 in numeric columns
            numeric_columns = [
                "Duration",
                "Tax.Mín_Clean",
                "ROA E. Aprox.",
                "Taxa de Emissão",
            ]

            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(
                        0.0
                    )

            # Clean date columns
            date_columns = ["Primeira Data de Juros", "Vencimento"]
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce")

            logger.info(
                f"DataFrame cleaned: {len(df)} rows prepared for MySQL"
            )
            return df

        except Exception as e:
            logger.error(f"Error cleaning DataFrame: {e}")
            return df

    async def download_and_process_category(
        self, categoria: str, nome_arquivo: str
    ) -> pd.DataFrame | None:
        """Download and process a specific category asynchronously"""
        try:
            url = f"https://api-advisor.xpi.com.br/rf-fixedincome-hub-apim/v2/available-assets/export?category={categoria}&brand=XP"
            headers = self.get_headers()

            logger.info(f"Downloading category: {categoria}")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

                # Process Excel directly from memory
                excel_content = response.content
                file_size = len(excel_content)
                logger.info(
                    f"Category {categoria} downloaded: {file_size:,} bytes"
                )

                # Read Excel from memory using asyncio thread pool
                excel_buffer = BytesIO(excel_content)
                loop = asyncio.get_event_loop()
                df = await loop.run_in_executor(
                    None, pd.read_excel, excel_buffer
                )

                # Add Duration column with value 0 if it doesn't exist
                if "Duration" not in df.columns:
                    df["Duration"] = 0
                    logger.info(
                        f"Duration column added to category {categoria}"
                    )

                logger.info(f"Category {categoria} processed: {len(df)} rows")
                return df

        except httpx.TimeoutException:
            logger.error(f"Timeout in request for category {categoria}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error for category {categoria}: {e}")
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error processing category {categoria}: {e}"
            )
            return None

    async def create_fixed_income_table(self) -> bool:
        """Create fixed income table if it doesn't exist"""
        try:
            with get_database_connection() as connection:
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
                logger.info(
                    "fixed_income_data table created with TEXT field for classificar_vencimento!"
                )
                cursor.close()

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
            with get_database_connection() as connection:
                cursor = connection.cursor()

                # Add collection timestamp
                df["data_coleta"] = datetime.now()

                # Convert DataFrame to list of dicts
                records = df.to_dict("records")
                logger.info(f"Converted {len(records)} records for insertion")

                # Convert records to list of tuples
                data_tuples = []
                for record in records:

                    def get_safe_value(
                        key,
                        default="",
                        is_numeric=False,
                        current_record=record,
                    ):
                        value = current_record.get(key, default)

                        if pd.isna(value):
                            return 0.0 if is_numeric else ""

                        if is_numeric:
                            try:
                                return float(value) if value != "" else 0.0
                            except (ValueError, TypeError):
                                return 0.0

                        if isinstance(value, str):
                            return value.strip()
                        elif value is None:
                            return ""
                        else:
                            return str(value).strip()

                    tuple_data = (
                        record.get("data_coleta"),
                        get_safe_value("Ativo"),
                        get_safe_value("Instrumento"),
                        get_safe_value("Duration", 0.0, is_numeric=True),
                        get_safe_value("Indexador"),
                        get_safe_value("Juros"),
                        record.get("Primeira Data de Juros"),
                        get_safe_value("Isento"),
                        get_safe_value("Rating"),
                        record.get("Vencimento"),
                        get_safe_value("Tax.Mín"),
                        get_safe_value("Tax.Mín_Clean", 0.0, is_numeric=True),
                        get_safe_value("ROA E. Aprox.", 0.0, is_numeric=True),
                        get_safe_value(
                            "Taxa de Emissão", 0.0, is_numeric=True
                        ),
                        get_safe_value("Público"),
                        get_safe_value("Público Resumido"),
                        get_safe_value("Emissor"),
                        get_safe_value("Cupom"),
                        get_safe_value("Classificar Vencimento"),
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

            return True

        except mysql.connector.Error as err:
            logger.error(f"Error inserting data into MySQL: {err}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error inserting data: {e}")
            return False

    async def process_and_store_data(self) -> dict[str, Any]:
        """Main method to download, process and store all categories"""
        try:
            # Get valid token
            if not await self.get_valid_token():
                return {
                    "success": False,
                    "message": "No valid token available",
                    "error": "Unable to retrieve valid token from database",
                }

            # Create table if necessary
            if not await self.create_fixed_income_table():
                return {
                    "success": False,
                    "message": "Failed to create database table",
                    "error": "Database table creation failed",
                }

            logger.info(
                "Starting parallel download and processing of categories..."
            )

            # Download and process all categories in parallel using asyncio.gather()
            download_tasks = [
                self.download_and_process_category(categoria, _nome_arquivo)
                for categoria, _nome_arquivo in self.categorias.items()
            ]

            results = await asyncio.gather(
                *download_tasks, return_exceptions=True
            )

            # Process results and check for failures
            dataframes = []
            for i, (categoria, _nome_arquivo) in enumerate(
                self.categorias.items()
            ):
                result = results[i]
                if isinstance(result, Exception):
                    logger.error(
                        f"Exception in category {categoria}: {result}"
                    )
                    return {
                        "success": False,
                        "message": f"Failed to download category: {categoria}",
                        "error": f"Category {categoria} download failed: {str(result)}",
                    }
                elif result is not None:
                    dataframes.append(result)
                else:
                    return {
                        "success": False,
                        "message": f"Failed to download category: {categoria}",
                        "error": f"Category {categoria} download failed",
                    }

            # Consolidate all spreadsheets
            df_consolidated = pd.concat(dataframes, ignore_index=True)
            logger.info(
                f"Data consolidated: {len(df_consolidated)} total rows"
            )

            # Process data using optimized pipeline (single pass, reduced memory usage)
            df_final = self.process_dataframe_pipeline(df_consolidated)

            # Clear old data before inserting new ones
            if not await self.clear_all_data():
                return {
                    "success": False,
                    "message": "Failed to clear old data",
                    "error": "Database clear operation failed",
                }

            # Insert new data into MySQL
            if not await self.insert_fixed_income_data(df_final):
                return {
                    "success": False,
                    "message": "Failed to insert data into database",
                    "error": "Database insertion failed",
                }

            logger.info(
                f"Processing completed: {len(df_final)} records inserted into MySQL"
            )
            return {
                "success": True,
                "message": "Fixed income data processed successfully",
                "records_processed": len(df_final),
                "categories_processed": list(self.categorias.keys()),
                "processing_date": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error during processing: {e}")
            return {
                "success": False,
                "message": "Processing failed with error",
                "error": str(e),
            }

    def process_dataframe_pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Optimized DataFrame processing pipeline using method chaining
        Combines multiple transformations to reduce memory usage and improve performance
        """
        try:
            logger.info("Starting optimized DataFrame processing pipeline...")

            # Apply all transformations in a single pipeline using method chaining
            df_processed = (
                df.pipe(self.filter_igpm_assets)
                # Interest filter
                .pipe(
                    lambda x: x[x["Juros"].isin(["Mensal", "Semestral"])]
                    if "Juros" in x.columns
                    else x
                )
                .pipe(self.apply_ntn_rules)
                .pipe(self.format_tax_columns)
                .pipe(self.create_new_columns)
                .pipe(self.select_columns)
                .pipe(self.clean_dataframe_for_mysql)
            )

            logger.info(
                f"Pipeline processing completed: {len(df_processed)} records processed"
            )
            return df_processed

        except Exception as e:
            logger.error(f"Error in DataFrame processing pipeline: {e}")
            return df

    async def get_processing_stats(self) -> dict[str, Any]:
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
                "total_records": stats["total_records"],
                "unique_issuers": stats["unique_issuers"],
                "unique_indexers": stats["unique_indexers"],
                "last_update": stats["last_update"].isoformat()
                if stats["last_update"]
                else None,
                "earliest_maturity": stats["earliest_maturity"].isoformat()
                if stats["earliest_maturity"]
                else None,
                "latest_maturity": stats["latest_maturity"].isoformat()
                if stats["latest_maturity"]
                else None,
            }

        except Exception as e:
            logger.error(f"Error getting processing stats: {e}")
            return {"error": str(e)}
