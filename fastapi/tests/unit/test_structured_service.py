"""
Unit tests for StructuredService
Testing business logic and data processing following project standards.
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest
from services.structured_exceptions import (
    ApiRequestError,
    DatabaseOperationError,
    TokenRetrievalError,
)
from services.structured_service import StructuredService

import mysql.connector


class TestStructuredService:
    """Test suite for StructuredService"""

    @pytest.fixture
    def service(self):
        """Create StructuredService instance for testing"""
        return StructuredService()

    @pytest.fixture
    def mock_token_data(self):
        """Mock token data from database"""
        return [{"token": "test_token_123", "expires_at": datetime.now()}]

    @pytest.fixture
    def mock_ticket_data(self):
        """Mock ticket data from API"""
        return [
            {
                "id": "TICKET_001",
                "dataCriacao": "2024-01-15T10:30:00",
                "codigoCliente": "12345",
                "ativo": "PETR4",
                "comissaoAssessor": "R$ 150,50",
                "estrutura": "Call Spread",
                "quantidade": 1000,
                "dataFixing": "2024-02-15T15:00:00",
                "status": {
                    "nome": "Pendente Execução",
                    "detalhes": "Aguardando fixing",
                },
                "tipoOperacao": "Compra",
                "codigoAssessor": "AAI123",
            },
            {
                "id": "TICKET_002",
                "dataCriacao": "2024-01-16T14:20:00",
                "codigoCliente": "67890",
                "ativo": "VALE3",
                "comissaoAssessor": "R$ 75,25",
                "estrutura": "Put Spread",
                "quantidade": 500,
                "dataFixing": "2024-02-20T15:00:00",
                "status": {
                    "nome": "Executado",
                    "detalhes": "Totalmente executado",
                },
                "tipoOperacao": "Venda",
                "codigoAssessor": "AAI456",
            },
        ]

    @pytest.mark.asyncio
    async def test_get_valid_token_success(self, service, mock_token_data):
        """Test successful token retrieval"""
        with patch("services.structured_service.execute_query") as mock_query:
            mock_query.return_value = mock_token_data

            token = await service.get_valid_token()

            assert token == "test_token_123"
            assert service.token == "test_token_123"
            mock_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_valid_token_no_token_found(self, service):
        """Test token retrieval when no valid token exists"""
        with patch("services.structured_service.execute_query") as mock_query:
            mock_query.return_value = []

            token = await service.get_valid_token()

            assert token is None
            assert service.token is None

    @pytest.mark.asyncio
    async def test_get_valid_token_database_error(self, service):
        """Test token retrieval with database error"""
        with patch("services.structured_service.execute_query") as mock_query:
            mock_query.side_effect = mysql.connector.Error(
                "Database connection failed"
            )

            with pytest.raises(TokenRetrievalError) as exc_info:
                await service.get_valid_token()

            assert "Failed to retrieve token from database" in str(
                exc_info.value
            )

    def test_get_headers_success(self, service):
        """Test header generation with valid configuration"""
        service.token = "test_token_123"

        with patch.dict(
            "os.environ", {"HUB_XP_STRUCTURED_API_KEY": "test_api_key"}
        ):
            headers = service.get_headers()

            expected_headers = {
                "Authorization": "Bearer test_token_123",
                "ocp-apim-subscription-key": "test_api_key",
                "Content-Type": "application/json",
                "Origin": "https://hub.xpi.com.br",
                "Referer": "https://hub.xpi.com.br/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }

            assert headers == expected_headers

    def test_get_headers_missing_api_key(self, service):
        """Test header generation with missing API key"""
        service.token = "test_token_123"

        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                service.get_headers()

            assert (
                "HUB_XP_STRUCTURED_API_KEY environment variable not found"
                in str(exc_info.value)
            )

    def test_parse_currency_valid_values(self, service):
        """Test currency parsing with valid values"""
        test_cases = [
            ("R$ 150,50", Decimal("150.50")),
            ("R$ 1.234,56", Decimal("1234.56")),
            ("R$ 0,00", Decimal("0.00")),
            ("150,50", Decimal("150.50")),
            ("1234.56", Decimal("1234.56")),
        ]

        for input_value, expected in test_cases:
            result = service.parse_currency(input_value)
            assert result == expected, f"Failed for input: {input_value}"

    def test_parse_currency_invalid_values(self, service):
        """Test currency parsing with invalid values"""
        test_cases = ["", "N/A", None, "invalid", "R$ abc"]

        for input_value in test_cases:
            result = service.parse_currency(input_value)
            assert result == Decimal("0.0"), f"Failed for input: {input_value}"

    @pytest.mark.asyncio
    async def test_buscar_tickets_success(self, service, mock_ticket_data):
        """Test successful ticket fetching"""
        service.token = "test_token_123"

        # Mock API response
        mock_response_data = {
            "dados": {
                "tickets": mock_ticket_data,
                "informacoesPagina": {
                    "tamanhoTotal": 2,
                    "tokenProximaPagina": "",
                },
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            tickets = await service.buscar_tickets(
                "2024-01-01T00:00:00", "2024-01-31T23:59:59"
            )

            assert len(tickets) == 2
            assert tickets[0]["id"] == "TICKET_001"
            assert tickets[1]["id"] == "TICKET_002"

    @pytest.mark.asyncio
    async def test_buscar_tickets_no_data(self, service):
        """Test ticket fetching with no data returned"""
        service.token = "test_token_123"

        mock_response_data = {
            "dados": {
                "tickets": [],
                "informacoesPagina": {
                    "tamanhoTotal": 0,
                    "tokenProximaPagina": "",
                },
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            tickets = await service.buscar_tickets(
                "2024-01-01T00:00:00", "2024-01-31T23:59:59"
            )

            assert tickets == []

    @pytest.mark.asyncio
    async def test_buscar_tickets_api_error(self, service):
        """Test ticket fetching with API error"""
        service.token = "test_token_123"

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=Exception("API request failed")
            )

            with pytest.raises(ApiRequestError) as exc_info:
                await service.buscar_tickets(
                    "2024-01-01T00:00:00", "2024-01-31T23:59:59"
                )

            assert "Failed to fetch page 1" in str(exc_info.value)

    def test_process_ticket_data_success(self, service, mock_ticket_data):
        """Test successful ticket data processing"""
        processed_data = service.process_ticket_data(mock_ticket_data)

        assert len(processed_data) == 2

        # Check first ticket
        first_ticket = processed_data[0]
        assert first_ticket["ticket_id"] == "TICKET_001"
        assert first_ticket["cliente"] == 12345
        assert first_ticket["ativo"] == "PETR4"
        assert first_ticket["comissao"] == Decimal("150.50")
        assert first_ticket["estrutura"] == "Call Spread"
        assert first_ticket["quantidade"] == 1000
        assert first_ticket["status"] == "Pendente Execução"

        # Check second ticket
        second_ticket = processed_data[1]
        assert second_ticket["ticket_id"] == "TICKET_002"
        assert second_ticket["cliente"] == 67890
        assert second_ticket["comissao"] == Decimal("75.25")

    def test_process_ticket_data_invalid_client_code(self, service):
        """Test ticket processing with invalid client code"""
        invalid_ticket = {
            "id": "TICKET_003",
            "codigoCliente": "invalid",
            "ativo": "TEST3",
            "comissaoAssessor": "R$ 100,00",
        }

        processed_data = service.process_ticket_data([invalid_ticket])

        assert len(processed_data) == 1
        assert processed_data[0]["cliente"] is None

    @pytest.mark.asyncio
    async def test_create_structured_table_success(self, service):
        """Test successful table creation"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor

        with patch(
            "services.structured_service.get_database_connection"
        ) as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_connection

            result = await service.create_structured_table()

            assert result is True
            mock_cursor.execute.assert_called_once()
            mock_cursor.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_structured_table_database_error(self, service):
        """Test table creation with database error"""
        with patch(
            "services.structured_service.get_database_connection"
        ) as mock_get_conn:
            mock_get_conn.side_effect = mysql.connector.Error(
                "Connection failed"
            )

            with pytest.raises(DatabaseOperationError) as exc_info:
                await service.create_structured_table()

            assert "Failed to create table" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upsert_structured_data_new_records(self, service):
        """Test upserting new records"""
        processed_data = [
            {
                "ticket_id": "NEW_TICKET_001",
                "data_envio": "2024-01-15T10:30:00",
                "cliente": 12345,
                "ativo": "PETR4",
                "comissao": Decimal("150.50"),
                "estrutura": "Call Spread",
                "quantidade": 1000,
                "fixing": "2024-02-15T15:00:00",
                "status": "Pendente Execução",
                "detalhes": "Aguardando fixing",
                "operacao": "Compra",
                "aai_ordem": "AAI123",
            }
        ]

        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None  # No existing record

        with patch(
            "services.structured_service.get_database_connection"
        ) as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_connection

            result = await service.upsert_structured_data(processed_data)

            assert result["new_records"] == 1
            assert result["updated_records"] == 0
            mock_connection.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_structured_data_update_commission(self, service):
        """Test updating existing records with changed commission"""
        processed_data = [
            {
                "ticket_id": "EXISTING_TICKET_001",
                "comissao": Decimal("200.00"),
                "data_envio": "2024-01-15T10:30:00",
                "cliente": 12345,
                "ativo": "PETR4",
                "estrutura": "Call Spread",
                "quantidade": 1000,
                "fixing": "2024-02-15T15:00:00",
                "status": "Pendente Execução",
                "detalhes": "Aguardando fixing",
                "operacao": "Compra",
                "aai_ordem": "AAI123",
            }
        ]

        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        # Existing record with different commission
        mock_cursor.fetchone.return_value = (1, Decimal("150.00"))

        with patch(
            "services.structured_service.get_database_connection"
        ) as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_connection

            result = await service.upsert_structured_data(processed_data)

            assert result["new_records"] == 0
            assert result["updated_records"] == 1
            mock_connection.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_all_data_success(self, service):
        """Test successful data clearing"""
        with patch("services.structured_service.execute_query") as mock_query:
            mock_query.return_value = None

            result = await service.clear_all_data()

            assert result is True
            mock_query.assert_called_once_with("DELETE FROM structured_data")

    @pytest.mark.asyncio
    async def test_clear_all_data_error(self, service):
        """Test data clearing with error"""
        with patch("services.structured_service.execute_query") as mock_query:
            mock_query.side_effect = Exception("Delete failed")

            result = await service.clear_all_data()

            assert result is False

    @pytest.mark.asyncio
    async def test_get_processing_stats_success(self, service):
        """Test successful statistics retrieval"""
        mock_stats = [
            {
                "total_records": 100,
                "unique_clients": 25,
                "unique_assets": 15,
                "total_commission": Decimal("5000.00"),
                "last_update": datetime.now(),
                "earliest_ticket": datetime.now(),
                "latest_ticket": datetime.now(),
            }
        ]

        mock_status_breakdown = [
            {"status": "Executado", "count": 60},
            {"status": "Pendente Execução", "count": 40},
        ]

        with patch("services.structured_service.execute_query") as mock_query:
            mock_query.side_effect = [mock_stats, mock_status_breakdown]

            stats = await service.get_processing_stats()

            assert stats["total_records"] == 100
            assert stats["unique_clients"] == 25
            assert stats["unique_assets"] == 15
            assert stats["total_commission"] == 5000.00
            assert stats["status_breakdown"]["Executado"] == 60
            assert stats["status_breakdown"]["Pendente Execução"] == 40

    @pytest.mark.asyncio
    async def test_get_processing_stats_no_data(self, service):
        """Test statistics retrieval with no data"""
        with patch("services.structured_service.execute_query") as mock_query:
            mock_query.return_value = []

            stats = await service.get_processing_stats()

            assert "error" in stats
            assert stats["error"] == "No data found"

    @pytest.mark.asyncio
    async def test_get_structured_data_with_filters(self, service):
        """Test data retrieval with filters"""
        mock_count_result = [{"total": 50}]
        mock_data_result = [
            {
                "ticket_id": "TICKET_001",
                "data_envio": datetime.now(),
                "cliente": 12345,
                "ativo": "PETR4",
                "comissao": Decimal("150.50"),
                "status": "Executado",
            }
        ]

        with patch("services.structured_service.execute_query") as mock_query:
            mock_query.side_effect = [mock_count_result, mock_data_result]

            result = await service.get_structured_data(
                limit=10, offset=0, cliente=12345, ativo="PETR4"
            )

            assert result["total_count"] == 50
            assert len(result["records"]) == 1
            assert result["records"][0]["ticket_id"] == "TICKET_001"
            assert result["has_more"] is True

    @pytest.mark.asyncio
    async def test_process_and_store_data_complete_flow(
        self, service, mock_ticket_data
    ):
        """Test complete data processing flow"""
        # Mock all dependencies
        with patch.object(
            service, "get_valid_token", return_value="test_token"
        ):
            with patch.object(
                service, "create_structured_table", return_value=True
            ):
                with patch.object(
                    service, "buscar_tickets", return_value=mock_ticket_data
                ):
                    with patch.object(
                        service,
                        "upsert_structured_data",
                        return_value={"new_records": 2, "updated_records": 0},
                    ):
                        result = await service.process_and_store_data(
                            "2024-01-01T00:00:00", "2024-01-31T23:59:59"
                        )

                        assert result["success"] is True
                        assert result["records_processed"] == 2
                        assert result["new_records"] == 2
                        assert result["updated_records"] == 0
                        assert "Processing completed" in result["message"]
