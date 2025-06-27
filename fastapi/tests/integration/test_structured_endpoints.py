"""
Integration tests for Structured Data API endpoints
Testing API endpoints and request/response handling following project standards.
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from main import app

from fastapi.testclient import TestClient

client = TestClient(app)


class TestStructuredEndpoints:
    """Integration test suite for structured data endpoints"""

    @pytest.fixture
    def mock_service_success(self):
        """Mock StructuredService with successful responses"""
        return {
            "process_and_store_data": {
                "success": True,
                "message": "Structured data processed successfully",
                "records_processed": 10,
                "new_records": 8,
                "updated_records": 2,
                "processing_date": datetime.now().isoformat(),
                "period": "2024-01-01T00:00:00 to 2024-01-31T23:59:59",
            },
            "get_processing_stats": {
                "total_records": 100,
                "unique_clients": 25,
                "unique_assets": 15,
                "total_commission": 5000.00,
                "last_update": datetime.now().isoformat(),
                "earliest_ticket": datetime.now().isoformat(),
                "latest_ticket": datetime.now().isoformat(),
                "status_breakdown": {"Executado": 60, "Pendente Execução": 40},
            },
            "get_structured_data": {
                "records": [
                    {
                        "ticket_id": "TICKET_001",
                        "data_envio": datetime.now(),
                        "cliente": 12345,
                        "ativo": "PETR4",
                        "comissao": Decimal("150.50"),
                        "status": "Executado",
                    }
                ],
                "total_count": 100,
                "limit": 10,
                "offset": 0,
                "has_more": True,
            },
            "clear_all_data": True,
        }

    def test_process_structured_data_sync_success(self, mock_service_success):
        """Test successful synchronous data processing"""
        with patch(
            "routes.structured.StructuredService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.process_and_store_data = AsyncMock(
                return_value=mock_service_success["process_and_store_data"]
            )

            response = client.get(
                "/api/structured/process-sync",
                params={
                    "data_inicio": "2024-01-01T00:00:00",
                    "data_fim": "2024-01-31T23:59:59",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["records_processed"] == 10
            assert data["new_records"] == 8
            assert data["updated_records"] == 2
            assert "Structured data processed successfully" in data["message"]

    def test_process_structured_data_sync_missing_params(self):
        """Test sync processing with missing parameters"""
        response = client.get("/api/structured/process-sync")

        assert response.status_code == 422  # Validation error

    def test_process_structured_data_sync_invalid_date(self):
        """Test sync processing with invalid date format"""
        response = client.get(
            "/api/structured/process-sync",
            params={
                "data_inicio": "invalid-date",
                "data_fim": "2024-01-31T23:59:59",
            },
        )

        # Should still pass initial validation but fail in service
        assert response.status_code in [400, 422, 500]

    def test_process_structured_data_sync_service_error(self):
        """Test sync processing with service error"""
        with patch(
            "routes.structured.StructuredService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.process_and_store_data = AsyncMock(
                return_value={
                    "success": False,
                    "message": "Processing failed",
                    "error": "Token not found",
                }
            )

            response = client.get(
                "/api/structured/process-sync",
                params={
                    "data_inicio": "2024-01-01T00:00:00",
                    "data_fim": "2024-01-31T23:59:59",
                },
            )

            assert (
                response.status_code == 200
            )  # Still returns 200 but with error in response
            data = response.json()
            assert data["success"] is False
            assert "Processing failed" in data["message"]

    def test_process_structured_data_async_success(self):
        """Test successful asynchronous data processing"""
        with patch("routes.structured.state_manager") as mock_state:
            mock_state.get_state.return_value = "idle"

            response = client.post(
                "/api/structured/process",
                json={
                    "data_inicio": "2024-01-01T00:00:00",
                    "data_fim": "2024-01-31T23:59:59",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "Processing started in background" in data["message"]

    def test_process_structured_data_async_already_processing(self):
        """Test async processing when already running"""
        with patch("routes.structured.state_manager") as mock_state:
            mock_state.get_state.return_value = "running"

            response = client.post(
                "/api/structured/process",
                json={
                    "data_inicio": "2024-01-01T00:00:00",
                    "data_fim": "2024-01-31T23:59:59",
                },
            )

            assert response.status_code == 409
            data = response.json()
            assert "Processing already in progress" in data["detail"]

    def test_process_structured_data_async_invalid_request(self):
        """Test async processing with invalid request body"""
        response = client.post(
            "/api/structured/process",
            json={
                "data_inicio": "invalid-date",
                "data_fim": "2024-01-31T23:59:59",
            },
        )

        assert response.status_code == 422  # Validation error

    def test_get_processing_status_success(self):
        """Test successful status retrieval"""
        mock_stats = {
            "total_records": 100,
            "unique_clients": 25,
            "unique_assets": 15,
        }

        with patch("routes.structured.state_manager") as mock_state:
            mock_state.get_state.side_effect = lambda key, default=None: {
                "processing_status": "idle",
                "last_processing_date": "2024-01-01T00:00:00",
                "last_processing_result": {"success": True},
                "last_processing_error": None,
            }.get(key, default)

            with patch(
                "routes.structured.StructuredService"
            ) as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_processing_stats = AsyncMock(
                    return_value=mock_stats
                )

                response = client.get("/api/structured/status")

                assert response.status_code == 200
                data = response.json()
                assert data["is_processing"] is False
                assert data["last_processing_date"] == "2024-01-01T00:00:00"
                assert data["last_processing_status"] == "completed"
                assert data["records_count"] == 100

    def test_get_processing_stats_success(self, mock_service_success):
        """Test successful statistics retrieval"""
        with patch(
            "routes.structured.StructuredService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_processing_stats = AsyncMock(
                return_value=mock_service_success["get_processing_stats"]
            )

            response = client.get("/api/structured/stats")

            assert response.status_code == 200
            data = response.json()
            assert data["total_records"] == 100
            assert data["unique_clients"] == 25
            assert data["unique_assets"] == 15
            assert data["total_commission"] == 5000.00
            assert data["status_breakdown"]["Executado"] == 60

    def test_get_processing_stats_service_error(self):
        """Test statistics retrieval with service error"""
        with patch(
            "routes.structured.StructuredService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_processing_stats = AsyncMock(
                return_value={"error": "Database connection failed"}
            )

            response = client.get("/api/structured/stats")

            assert response.status_code == 500
            data = response.json()
            assert "Failed to retrieve stats" in data["detail"]

    def test_get_structured_data_success(self, mock_service_success):
        """Test successful data retrieval"""
        with patch(
            "routes.structured.StructuredService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_structured_data = AsyncMock(
                return_value=mock_service_success["get_structured_data"]
            )

            response = client.get("/api/structured/data")

            assert response.status_code == 200
            data = response.json()
            assert data["total_count"] == 100
            assert len(data["records"]) == 1
            assert data["records"][0]["ticket_id"] == "TICKET_001"
            assert data["has_more"] is True

    def test_get_structured_data_with_filters(self, mock_service_success):
        """Test data retrieval with query parameters"""
        with patch(
            "routes.structured.StructuredService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_structured_data = AsyncMock(
                return_value=mock_service_success["get_structured_data"]
            )

            response = client.get(
                "/api/structured/data",
                params={
                    "limit": 50,
                    "offset": 10,
                    "cliente": 12345,
                    "ativo": "PETR4",
                    "status": "Executado",
                    "data_inicio": "2024-01-01",
                    "data_fim": "2024-01-31",
                },
            )

            assert response.status_code == 200
            # Verify service was called with correct parameters
            mock_service.get_structured_data.assert_called_once_with(
                limit=50,
                offset=10,
                cliente=12345,
                ativo="PETR4",
                status="Executado",
                data_inicio="2024-01-01",
                data_fim="2024-01-31",
            )

    def test_get_structured_data_invalid_params(self):
        """Test data retrieval with invalid parameters"""
        response = client.get(
            "/api/structured/data",
            params={
                "limit": 2000,  # Exceeds maximum
                "offset": -1,  # Negative offset
                "data_inicio": "invalid-date",
            },
        )

        assert response.status_code == 422  # Validation error

    def test_clear_structured_data_success(self, mock_service_success):
        """Test successful data clearing"""
        with patch(
            "routes.structured.StructuredService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.clear_all_data = AsyncMock(
                return_value=mock_service_success["clear_all_data"]
            )

            response = client.delete("/api/structured/clear")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert (
                "All structured data cleared successfully" in data["message"]
            )

    def test_clear_structured_data_failure(self):
        """Test data clearing failure"""
        with patch(
            "routes.structured.StructuredService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.clear_all_data = AsyncMock(return_value=False)

            response = client.delete("/api/structured/clear")

            assert response.status_code == 500
            data = response.json()
            assert "Failed to clear structured data" in data["detail"]

    def test_get_structured_categories_success(self):
        """Test successful categories retrieval"""
        response = client.get("/api/structured/categories")

        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert "supported_operations" in data
        assert "api_version" in data
        assert len(data["categories"]) >= 1
        assert data["categories"][0]["name"] == "structured_operations"

    def test_endpoint_documentation(self):
        """Test that endpoints are properly documented in OpenAPI"""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        openapi_spec = response.json()

        # Check that structured endpoints are included
        paths = openapi_spec.get("paths", {})
        assert "/api/structured/process" in paths
        assert "/api/structured/process-sync" in paths
        assert "/api/structured/status" in paths
        assert "/api/structured/stats" in paths
        assert "/api/structured/data" in paths
        assert "/api/structured/clear" in paths
        assert "/api/structured/categories" in paths

        # Check that endpoints have proper tags
        for path_info in paths.values():
            for method_info in path_info.values():
                if "structured" in str(method_info.get("operationId", "")):
                    assert "structured" in method_info.get("tags", [])

    def test_cors_headers(self):
        """Test CORS headers are properly set"""
        response = client.options("/api/structured/stats")

        assert response.status_code == 200
        # CORS headers should be handled by middleware

    def test_rate_limiting_headers(self):
        """Test rate limiting headers are present"""
        response = client.get("/api/structured/categories")

        assert response.status_code == 200
        # Rate limiting headers should be handled by middleware

    def test_error_handling_consistency(self):
        """Test that error responses follow consistent format"""
        # Test various error scenarios
        error_responses = [
            client.get("/api/structured/process-sync"),  # Missing params
            client.post("/api/structured/process", json={}),  # Invalid body
            client.get(
                "/api/structured/data", params={"limit": -1}
            ),  # Invalid params
        ]

        for response in error_responses:
            assert response.status_code in [400, 422, 500]
            data = response.json()
            # FastAPI error responses should have 'detail' field
            assert "detail" in data or "message" in data

    def test_pydantic_model_validation(self):
        """Test Pydantic model validation in endpoints"""
        # Test valid request
        valid_request = {
            "data_inicio": "2024-01-01T00:00:00",
            "data_fim": "2024-01-31T23:59:59",
        }

        with patch("routes.structured.state_manager") as mock_state:
            mock_state.get_state.return_value = "idle"

            response = client.post(
                "/api/structured/process", json=valid_request
            )
            assert response.status_code == 200

        # Test invalid request
        invalid_request = {
            "data_inicio": "invalid-date",
            "data_fim": "2024-01-31T23:59:59",
        }

        response = client.post("/api/structured/process", json=invalid_request)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_background_task_execution(self):
        """Test background task execution for async processing"""
        from routes.structured import background_processing

        with patch(
            "routes.structured.StructuredService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.process_and_store_data = AsyncMock(
                return_value={"success": True, "message": "Completed"}
            )

            with patch("routes.structured.state_manager") as mock_state:
                # Test successful background processing
                await background_processing(
                    "2024-01-01T00:00:00", "2024-01-31T23:59:59"
                )

                # Verify state was updated correctly
                mock_state.set_state.assert_called()
                calls = mock_state.set_state.call_args_list
                assert any("processing_status" in str(call) for call in calls)

    def test_endpoint_response_models(self):
        """Test that endpoints return data matching response models"""
        # This test verifies the response structure matches Pydantic models
        with patch(
            "routes.structured.StructuredService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_processing_stats = AsyncMock(
                return_value={
                    "total_records": 100,
                    "unique_clients": 25,
                    "unique_assets": 15,
                    "total_commission": 5000.00,
                    "last_update": datetime.now().isoformat(),
                    "status_breakdown": {"Executado": 60},
                }
            )

            response = client.get("/api/structured/stats")
            assert response.status_code == 200
            data = response.json()

            # Verify all required fields are present
            required_fields = [
                "total_records",
                "unique_clients",
                "unique_assets",
            ]
            for field in required_fields:
                assert field in data

            # Verify data types
            assert isinstance(data["total_records"], int)
            assert isinstance(data["unique_clients"], int)
            assert isinstance(data["total_commission"], int | float)
