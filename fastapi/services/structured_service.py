"""
Structured Data Processing Service
Migrated and refactored from Estruturadas3.py following project standards.
"""

import os
from datetime import datetime
from decimal import Decimal
from typing import Any

import httpx
from database.connection import execute_query, get_database_connection
from dotenv import load_dotenv
from utils.crypto_utils import (
    CryptoError,
    mask_structured_data,
    prepare_structured_for_storage,
    prepare_structured_from_storage,
    validate_crypto_environment,
)
from utils.log_sanitizer import get_sanitized_logger

import mysql.connector

from .hub_token_service_refactored import TokenRepository
from .structured_exceptions import (
    ApiRequestError,
    DatabaseOperationError,
    TokenRetrievalError,
)

# Load environment variables from project root
project_root = os.path.join(os.path.dirname(__file__), "..", "..")
load_dotenv(os.path.join(project_root, ".env"), override=True)

logger = get_sanitized_logger(__name__)


class StructuredService:
    """Service for processing structured financial operations from Hub XP"""

    def __init__(self):
        self.token: str | None = None

        # Validate cryptographic environment
        if not validate_crypto_environment():
            logger.warning(
                "Cryptographic environment not properly configured - some features may not work"
            )
            self.crypto_enabled = False
        else:
            logger.info("Cryptographic environment validated successfully")
            self.crypto_enabled = True

    async def get_valid_token(self, user_login: str = None) -> str | None:
        """Get a valid token from hub_tokens table with decryption support"""
        try:
            # If user_login is provided, get token for specific user
            if user_login:
                self.token = TokenRepository.get_valid_token(user_login)
                if self.token:
                    logger.info("Valid token retrieved for user")
                    return self.token
                else:
                    logger.error("No valid token found for specified user")
                    return None

            # Fallback: try to get any valid token from any user
            logger.info(
                "No user_login provided, attempting to find any valid token..."
            )
            token_result = TokenRepository.get_any_valid_token()

            if token_result:
                user_login_found, token = token_result
                self.token = token
                logger.info(
                    f"Valid token found for user: {user_login_found[:3]}***{user_login_found[-3:]}"
                )
                return self.token
            else:
                logger.warning("No valid tokens found in database")
                return None

        except Exception as e:
            logger.error(f"Unexpected error retrieving token: {e}")
            raise TokenRetrievalError(
                f"Unexpected error during token retrieval: {e}"
            ) from e

    def get_headers(self) -> dict[str, str]:
        """Return headers for API requests"""
        api_key = os.getenv("HUB_XP_STRUCTURED_API_KEY")
        if not api_key:
            raise ValueError(
                "HUB_XP_STRUCTURED_API_KEY environment variable not found"
            )

        return {
            "Authorization": f"Bearer {self.token}",
            "ocp-apim-subscription-key": api_key,
            "Content-Type": "application/json",
            "Origin": "https://hub.xpi.com.br",
            "Referer": "https://hub.xpi.com.br/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

    def parse_currency(self, valor_str: str) -> Decimal:
        """Convert currency string to Decimal safely"""
        if not valor_str or valor_str == "N/A":
            return Decimal("0.0")

        try:
            # Remove symbols and spaces
            valor_limpo = (
                str(valor_str).replace("R$", "").replace(" ", "").strip()
            )
            if not valor_limpo:
                return Decimal("0.0")

            # Handle different decimal formats
            if "," in valor_limpo and "." in valor_limpo:
                # Brazilian format: 1.234,56 -> 1234.56
                valor_limpo = valor_limpo.replace(".", "").replace(",", ".")
            elif "," in valor_limpo:
                # Only comma: 150,50 -> 150.50
                valor_limpo = valor_limpo.replace(",", ".")
            # If only dots or no separators, use as is

            return Decimal(valor_limpo)

        except (ValueError, AttributeError, Exception) as e:
            logger.warning(
                f"Error converting currency value '{valor_str}': {e}"
            )
            return Decimal("0.0")

    async def buscar_tickets(
        self, data_inicio: str, data_fim: str
    ) -> list[dict]:
        """
        Fetch tickets with optimized pagination using API's tamanhoTotal
        Core function migrated from original Estruturadas3.py
        """
        url = "https://api.xpi.com.br/corporate-estruturados-hub/v1/api/operacao/listartickets"
        todos_tickets = []
        token_proxima_pagina = ""
        pagina = 1
        max_tentativas = 3
        tamanho_total_api = None
        tamanho_pagina = 1000

        logger.info(
            f"Starting ticket search for period: {data_inicio} to {data_fim}"
        )

        while True:
            logger.info(f"Processing page {pagina}")

            payload = {
                "informacoesPagina": {
                    "tamanhoPagina": str(tamanho_pagina),
                    "tokenProximaPagina": token_proxima_pagina,
                },
                "filtro": {
                    "clientes": [],
                    "dataInicio": data_inicio,
                    "dataFim": data_fim,
                    "tipoOperacao": [""],
                },
            }

            # Retry logic for API requests
            response = None
            for tentativa in range(max_tentativas):
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.post(
                            url, headers=self.get_headers(), json=payload
                        )
                        response.raise_for_status()
                        break
                except httpx.RequestError as e:
                    logger.warning(
                        f"Page {pagina}, attempt {tentativa + 1} failed: {e}"
                    )
                    if tentativa == max_tentativas - 1:
                        raise ApiRequestError(
                            f"Failed to fetch page {pagina}: {e}"
                        ) from e

            if response is None:
                raise ApiRequestError(
                    f"Failed to get response for page {pagina}"
                )

            dados = response.json().get("dados", {})
            tickets = dados.get("tickets", [])
            info_paginacao = dados.get("informacoesPagina", {})

            # Get API information on first request
            if pagina == 1:
                tamanho_total_api = info_paginacao.get("tamanhoTotal", 0)
                logger.info(
                    f"API reports total size: {tamanho_total_api} records"
                )

            logger.info(f"Page {pagina}: {len(tickets)} records collected")
            todos_tickets.extend(tickets)

            # Get next page token
            token_proxima_pagina = info_paginacao.get("tokenProximaPagina", "")

            # Check if should continue
            if not token_proxima_pagina or token_proxima_pagina.strip() == "":
                logger.info(
                    f"Pagination completed: empty token on page {pagina}"
                )
                break

            if tamanho_total_api and len(todos_tickets) >= tamanho_total_api:
                logger.info(
                    f"Pagination completed: collected {len(todos_tickets)} of {tamanho_total_api} records"
                )
                break

            if len(tickets) == 0:
                logger.info(f"Pagination completed: page {pagina} was empty")
                break

            pagina += 1

            # Protection against infinite loop
            if pagina > 1000:
                logger.warning("Page limit reached (1000). Stopping.")
                break

        if not todos_tickets:
            logger.info("No tickets found for the specified period")
            return []

        # Final validation with API total size
        coletados = len(todos_tickets)
        if tamanho_total_api and coletados != tamanho_total_api:
            diferenca = abs(coletados - tamanho_total_api)
            if diferenca > 0:
                logger.warning(
                    f"Difference between collected ({coletados}) and API total ({tamanho_total_api}): {diferenca} records"
                )
            else:
                logger.info(
                    f"✅ Validation OK: collected {coletados} records as per API"
                )

        logger.info(
            f"Collection completed: {coletados} records in {pagina} pages "
            f"(API reported {tamanho_total_api} records)"
        )

        return todos_tickets

    def process_ticket_data(self, tickets: list[dict]) -> list[dict]:
        """Process and format ticket data"""
        logger.info(f"Processing {len(tickets)} tickets")
        dados_tratados = []

        for t in tickets:
            # Get status first to filter out cancelled operations
            status = t.get("status", {}).get("nome")

            # Skip cancelled operations
            if status and status.lower() == "cancelado":
                continue

            # Safe conversion of client code
            codigo_cliente = t.get("codigoCliente")
            if codigo_cliente:
                try:
                    codigo_cliente = int(codigo_cliente)
                except (ValueError, TypeError):
                    codigo_cliente = None

            dados_tratados.append(
                {
                    "ticket_id": t.get("id"),
                    "data_envio": t.get("dataCriacao"),
                    "cliente": codigo_cliente,
                    "ativo": t.get("ativo"),
                    "comissao": self.parse_currency(
                        t.get("comissaoAssessor", "R$ 0")
                    ),
                    "estrutura": t.get("estrutura"),
                    "quantidade": t.get("quantidade"),
                    "fixing": t.get("dataFixing"),
                    "status": status,
                    "detalhes": t.get("status", {}).get("detalhes"),
                    "operacao": t.get("tipoOperacao"),
                    "aai_ordem": t.get("codigoAssessor"),
                }
            )

        filtered_count = len(tickets) - len(dados_tratados)
        if filtered_count > 0:
            logger.info(f"Filtered out {filtered_count} cancelled operations")

        logger.info(
            f"Processed {len(dados_tratados)} ticket records (excluding cancelled)"
        )
        return dados_tratados

    async def create_structured_table(self) -> bool:
        """Create structured_data table with encryption support if it doesn't exist"""
        try:
            with get_database_connection() as connection:
                cursor = connection.cursor()

                # Create table with crypto fields - compatible with both encrypted and non-encrypted data
                create_table_query = """
                CREATE TABLE IF NOT EXISTS structured_data (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    data_coleta DATETIME NOT NULL,
                    ticket_id TEXT,
                    ticket_id_hash VARCHAR(64),
                    data_envio DATETIME,
                    cliente TEXT,
                    ativo TEXT,
                    comissao TEXT,
                    estrutura TEXT,
                    quantidade INT,
                    fixing DATETIME,
                    status VARCHAR(100),
                    detalhes TEXT,
                    operacao VARCHAR(100),
                    aai_ordem TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

                    INDEX idx_data_coleta (data_coleta),
                    INDEX idx_ticket_id_hash (ticket_id_hash),
                    INDEX idx_status (status),
                    INDEX idx_data_envio (data_envio),
                    UNIQUE KEY unique_ticket_hash (ticket_id_hash)
                )
                """

                cursor.execute(create_table_query)
                logger.info(
                    "structured_data table created/verified successfully with crypto support"
                )
                cursor.close()

            return True

        except mysql.connector.Error as err:
            logger.error(f"Error creating table: {err}")
            raise DatabaseOperationError(
                f"Failed to create table: {err}"
            ) from err

    async def upsert_structured_data(
        self, processed_data: list[dict]
    ) -> dict[str, int]:
        """
        Insert new records or update existing ones based on ticket_id and commission changes.
        Uses encryption for sensitive fields and hash for ticket_id lookups.
        Returns count of new vs updated records
        """
        if not self.crypto_enabled:
            logger.error(
                "Crypto environment not available - cannot process structured data"
            )
            raise DatabaseOperationError(
                "Cryptographic environment not configured"
            )

        try:
            with get_database_connection() as connection:
                cursor = connection.cursor()

                new_records = 0
                updated_records = 0
                data_coleta = datetime.now()

                for record in processed_data:
                    try:
                        # Prepare encrypted data
                        encrypted_record = prepare_structured_for_storage(
                            record
                        )
                        ticket_id_hash = encrypted_record["ticket_id_hash"]

                        # Check if record exists using hash lookup
                        check_query = """
                        SELECT id, comissao, status FROM structured_data
                        WHERE ticket_id_hash = %s
                        """
                        cursor.execute(check_query, (ticket_id_hash,))
                        existing = cursor.fetchone()

                        if existing:
                            # For existing records, need to decrypt stored commission for comparison
                            try:
                                existing_commission_str = (
                                    existing[1] if existing[1] else "0.0"
                                )
                                # Try to decrypt if it looks encrypted, otherwise use as-is
                                if (
                                    len(existing_commission_str) > 20
                                ):  # Likely encrypted
                                    from utils.crypto_utils import (
                                        decrypt_structured_data,
                                    )

                                    existing_commission = Decimal(
                                        decrypt_structured_data(
                                            existing_commission_str
                                        )
                                    )
                                else:
                                    existing_commission = Decimal(
                                        existing_commission_str
                                    )
                            except (CryptoError, ValueError):
                                existing_commission = Decimal("0.0")

                            new_commission = (
                                record["comissao"]
                                if record["comissao"]
                                else Decimal("0.0")
                            )

                            existing_status = (
                                existing[2] if existing[2] else ""
                            )
                            new_status = (
                                record["status"] if record["status"] else ""
                            )

                            if (
                                existing_commission != new_commission
                                or existing_status != new_status
                            ):
                                # Update existing record with encrypted data
                                update_query = """
                                UPDATE structured_data SET
                                    data_coleta = %s,
                                    ticket_id = %s,
                                    data_envio = %s,
                                    cliente = %s,
                                    ativo = %s,
                                    comissao = %s,
                                    estrutura = %s,
                                    quantidade = %s,
                                    fixing = %s,
                                    status = %s,
                                    detalhes = %s,
                                    operacao = %s,
                                    aai_ordem = %s,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE ticket_id_hash = %s
                                """

                                update_values = (
                                    data_coleta,
                                    encrypted_record["ticket_id"],
                                    record["data_envio"],
                                    encrypted_record["cliente"],
                                    encrypted_record["ativo"],
                                    encrypted_record["comissao"],
                                    encrypted_record["estrutura"],
                                    record["quantidade"],
                                    record["fixing"],
                                    record["status"],
                                    record["detalhes"],
                                    record["operacao"],
                                    encrypted_record["aai_ordem"],
                                    ticket_id_hash,
                                )

                                cursor.execute(update_query, update_values)
                                updated_records += 1

                                # Log what changed (with masked data)
                                changes = []
                                if existing_commission != new_commission:
                                    changes.append("commission")
                                if existing_status != new_status:
                                    changes.append("status")

                                masked_record = mask_structured_data(record)
                                logger.debug(
                                    f"Updated ticket {masked_record['ticket_id']} - {', '.join(changes)} changed"
                                )

                        else:
                            # Insert new record with encrypted data
                            insert_query = """
                            INSERT INTO structured_data
                            (data_coleta, ticket_id, ticket_id_hash, data_envio, cliente, ativo, comissao,
                             estrutura, quantidade, fixing, status, detalhes, operacao, aai_ordem)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """

                            insert_values = (
                                data_coleta,
                                encrypted_record["ticket_id"],
                                ticket_id_hash,
                                record["data_envio"],
                                encrypted_record["cliente"],
                                encrypted_record["ativo"],
                                encrypted_record["comissao"],
                                encrypted_record["estrutura"],
                                record["quantidade"],
                                record["fixing"],
                                record["status"],
                                record["detalhes"],
                                record["operacao"],
                                encrypted_record["aai_ordem"],
                            )

                            cursor.execute(insert_query, insert_values)
                            new_records += 1

                    except CryptoError as e:
                        logger.error(
                            f"Encryption error for ticket {record.get('ticket_id', 'unknown')}: {e}"
                        )
                        continue
                    except Exception as e:
                        logger.error(
                            f"Error processing ticket {record.get('ticket_id', 'unknown')}: {e}"
                        )
                        continue

                connection.commit()
                logger.info(
                    f"Upsert completed: {new_records} new, {updated_records} updated"
                )
                cursor.close()

                return {
                    "new_records": new_records,
                    "updated_records": updated_records,
                }

        except mysql.connector.Error as err:
            logger.error(f"Error during upsert operation: {err}")
            raise DatabaseOperationError(
                f"Failed to upsert data: {err}"
            ) from err

    async def process_and_store_data(
        self, data_inicio: str, data_fim: str
    ) -> dict[str, Any]:
        """Main method to fetch, process and store structured data"""
        try:
            # Get valid token
            if not await self.get_valid_token():
                return {
                    "success": False,
                    "message": "No valid token available",
                    "error": "Unable to retrieve valid token from database",
                }

            # Create table if necessary
            if not await self.create_structured_table():
                return {
                    "success": False,
                    "message": "Failed to create database table",
                    "error": "Database table creation failed",
                }

            # Fetch tickets from API
            tickets = await self.buscar_tickets(data_inicio, data_fim)

            if not tickets:
                return {
                    "success": True,
                    "message": "No tickets found for the specified period",
                    "records_processed": 0,
                    "new_records": 0,
                    "updated_records": 0,
                    "processing_date": datetime.now().isoformat(),
                    "period": f"{data_inicio} to {data_fim}",
                }

            # Process ticket data
            processed_data = self.process_ticket_data(tickets)

            # Upsert data to database
            upsert_result = await self.upsert_structured_data(processed_data)

            logger.info(
                f"Processing completed: {len(processed_data)} records processed, "
                f"{upsert_result['new_records']} new, {upsert_result['updated_records']} updated"
            )

            return {
                "success": True,
                "message": "Structured data processed successfully",
                "records_processed": len(processed_data),
                "new_records": upsert_result["new_records"],
                "updated_records": upsert_result["updated_records"],
                "processing_date": datetime.now().isoformat(),
                "period": f"{data_inicio} to {data_fim}",
            }

        except Exception as e:
            logger.error(f"Error during processing: {e}")
            return {
                "success": False,
                "message": "Processing failed with error",
                "error": str(e),
            }

    async def get_processing_stats(self) -> dict[str, Any]:
        """Get processing statistics - adapted for encrypted data"""
        try:
            # Basic stats that don't require decryption
            query = """
            SELECT
                COUNT(*) as total_records,
                MAX(data_coleta) as last_update,
                MIN(data_envio) as earliest_ticket,
                MAX(data_envio) as latest_ticket
            FROM structured_data
            """

            result = execute_query(query, fetch=True)

            if not result:
                return {"error": "No data found"}

            stats = result[0]

            # Get status breakdown (status is not encrypted)
            status_query = """
            SELECT status, COUNT(*) as count
            FROM structured_data
            WHERE status IS NOT NULL
            GROUP BY status
            """

            status_result = execute_query(status_query, fetch=True)
            status_breakdown = (
                {row["status"]: row["count"] for row in status_result}
                if status_result
                else {}
            )

            # Note: unique_clients, unique_assets, and total_commission are not calculated
            # because they require decryption of all records, which is expensive
            # For these metrics, consider implementing cached/aggregated values or
            # calculate them during data processing

            return {
                "total_records": stats["total_records"],
                "unique_clients": "N/A (encrypted)",
                "unique_assets": "N/A (encrypted)",
                "total_commission": "N/A (encrypted)",
                "last_update": stats["last_update"].isoformat()
                if stats["last_update"]
                else None,
                "earliest_ticket": stats["earliest_ticket"].isoformat()
                if stats["earliest_ticket"]
                else None,
                "latest_ticket": stats["latest_ticket"].isoformat()
                if stats["latest_ticket"]
                else None,
                "status_breakdown": status_breakdown,
                "note": "Some statistics are not available due to encryption. Consider implementing cached aggregation for performance.",
            }

        except Exception as e:
            logger.error(f"Error getting processing stats: {e}")
            return {"error": str(e)}

    async def clear_all_data(self) -> bool:
        """Remove all data from structured_data table"""
        try:
            query = "DELETE FROM structured_data"
            execute_query(query)
            logger.info("Table cleared: all structured data records removed")
            return True

        except Exception as err:
            logger.error(f"Error clearing table: {err}")
            return False

    async def get_structured_data(
        self,
        limit: int = 100,
        offset: int = 0,
        cliente: int | None = None,
        ativo: str | None = None,
        status: str | None = None,
        data_inicio: str | None = None,
        data_fim: str | None = None,
    ) -> dict[str, Any]:
        """Get structured data with filtering and pagination - with decryption support"""
        if not self.crypto_enabled:
            logger.warning(
                "Crypto environment not available - returning encrypted data"
            )

        try:
            # Build WHERE conditions
            where_conditions = []
            params = []

            # Note: filtering by encrypted fields (cliente, ativo) is complex
            # For now, we'll apply filters after decryption or skip them with a warning
            filter_warnings = []

            if cliente:
                filter_warnings.append(
                    "cliente filtering skipped (encrypted field)"
                )

            if ativo:
                filter_warnings.append(
                    "ativo filtering skipped (encrypted field)"
                )

            if status:
                where_conditions.append("status = %s")
                params.append(status)

            if data_inicio:
                where_conditions.append("DATE(data_envio) >= %s")
                params.append(data_inicio)

            if data_fim:
                where_conditions.append("DATE(data_envio) <= %s")
                params.append(data_fim)

            where_clause = (
                " WHERE " + " AND ".join(where_conditions)
                if where_conditions
                else ""
            )

            # Get total count
            count_query = (
                "SELECT COUNT(*) as total FROM structured_data" + where_clause  # nosec B608
            )
            count_result = execute_query(
                count_query, tuple(params), fetch=True
            )
            total_count = count_result[0]["total"] if count_result else 0

            # Get data with pagination - include all fields
            data_query = (  # nosec B608
                "SELECT ticket_id, ticket_id_hash, data_envio, cliente, ativo, comissao, estrutura, "
                "quantidade, fixing, status, detalhes, operacao, aai_ordem, "
                "data_coleta, created_at, updated_at FROM structured_data "
                + where_clause
                + " ORDER BY data_envio DESC, created_at DESC LIMIT %s OFFSET %s"
            )

            data_params = params + [limit, offset]
            raw_records = execute_query(
                data_query, tuple(data_params), fetch=True
            )

            # Decrypt records if crypto is enabled
            decrypted_records = []
            if raw_records and self.crypto_enabled:
                for record in raw_records:
                    try:
                        # Convert record to dict if it's not already
                        record_dict = dict(record) if record else {}

                        # Decrypt sensitive fields
                        decrypted_record = prepare_structured_from_storage(
                            record_dict
                        )

                        # Remove hash field from response
                        decrypted_record.pop("ticket_id_hash", None)

                        # Apply post-decryption filters if specified
                        if (
                            cliente is not None
                            and decrypted_record.get("cliente") != cliente
                        ):
                            continue

                        if (
                            ativo is not None
                            and ativo.lower()
                            not in str(
                                decrypted_record.get("ativo", "")
                            ).lower()
                        ):
                            continue

                        # Mask sensitive data for response
                        masked_record = mask_structured_data(decrypted_record)
                        decrypted_records.append(masked_record)

                    except CryptoError as e:
                        logger.warning(f"Failed to decrypt record: {e}")
                        # Include record with encryption notice
                        record_dict = dict(record) if record else {}
                        record_dict["_encryption_error"] = "Failed to decrypt"
                        decrypted_records.append(record_dict)
                    except Exception as e:
                        logger.error(f"Error processing record: {e}")
                        continue
            else:
                # Return raw records if crypto not enabled
                decrypted_records = (
                    [dict(record) for record in raw_records]
                    if raw_records
                    else []
                )

            response = {
                "records": decrypted_records,
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total_count,
            }

            if filter_warnings:
                response["filter_warnings"] = filter_warnings

            return response

        except Exception as e:
            logger.error(f"Error retrieving structured data: {e}")
            return {"error": str(e)}
