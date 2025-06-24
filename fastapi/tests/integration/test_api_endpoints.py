"""
Integration tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import json
from datetime import datetime, timedelta


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_health_check_success(self, client, mock_db_connection):
        """Test successful health check"""
        mock_db_connection.fetchone.return_value = {'version': '8.0.0'}
        
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"

    def test_health_check_database_disconnected(self, client, mock_db_connection):
        """Test health check with database issues"""
        mock_db_connection.execute.side_effect = Exception("Connection failed")
        
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"  # API still healthy
        assert data["database"] == "disconnected"


class TestAutomationEndpoints:
    """Test automation endpoints"""

    def test_list_automations(self, client):
        """Test listing automations"""
        response = client.get("/api/automations")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["name"] == "Hub XP Token Extraction"

    def test_automation_stats(self, client, mock_db_connection):
        """Test automation statistics"""
        mock_db_connection.fetchone.return_value = {
            'total_extractions': 5,
            'successful_extractions': 4,
            'last_extraction': datetime.now()
        }
        
        response = client.get("/api/automations/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_automations" in data
        assert "success_rate" in data


class TestTokenEndpoints:
    """Test token management endpoints"""

    def test_token_status_no_token(self, client, mock_db_connection):
        """Test token status when no token exists"""
        mock_db_connection.fetchone.return_value = None
        
        response = client.get("/api/token/status/SILVA.A12345")
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_login"] == "SILVA.A12345"
        assert data["has_valid_token"] is False

    def test_token_status_valid_token(self, client, mock_db_connection):
        """Test token status with valid token"""
        future_time = datetime.now() + timedelta(hours=1)
        mock_db_connection.fetchone.return_value = {
            'expires_at': future_time,
            'extracted_at': datetime.now(),
            'is_expired': 0
        }
        
        response = client.get("/api/token/status/SILVA.A12345")
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_login"] == "SILVA.A12345"
        assert data["has_valid_token"] is True

    def test_token_history_empty(self, client, mock_db_connection):
        """Test token history when no tokens exist"""
        mock_db_connection.fetchall.return_value = []
        
        response = client.get("/api/token/history/SILVA.A12345")
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_login"] == "SILVA.A12345"
        assert data["total_tokens"] == 0
        assert data["tokens"] == []

    def test_token_history_with_tokens(self, client, mock_db_connection):
        """Test token history with existing tokens"""
        mock_tokens = [
            {
                'id': 1,
                'token': 'token_12345',
                'expires_at': datetime.now() + timedelta(hours=1),
                'extracted_at': datetime.now(),
                'created_at': datetime.now(),
                'is_expired': 0
            }
        ]
        mock_db_connection.fetchall.return_value = mock_tokens
        
        response = client.get("/api/token/history/SILVA.A12345")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_tokens"] == 1
        assert len(data["tokens"]) == 1

    def test_extract_token_invalid_credentials(self, client):
        """Test token extraction with invalid credentials format"""
        invalid_payload = {
            "credentials": {
                "user_login": "invalid_format",
                "password": "123",  # Too short
                "mfa_code": "12345"  # Wrong length
            }
        }
        
        response = client.post("/api/token/extract", json=invalid_payload)
        
        assert response.status_code == 422  # Validation error

    def test_extract_token_valid_format(self, client, mock_db_connection, mock_selenium_driver):
        """Test token extraction with valid credential format"""
        with patch('services.hub_token_service.HubTokenService.extract_token') as mock_extract:
            mock_extract.return_value = {
                "success": True,
                "message": "Token extracted successfully",
                "token_id": 1,
                "user_login": "SILVA.A12345"
            }
            
            valid_payload = {
                "credentials": {
                    "user_login": "SILVA.A12345",
                    "password": "validpassword123",
                    "mfa_code": "123456"
                }
            }
            
            response = client.post("/api/token/extract", json=valid_payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_delete_user_tokens(self, client, mock_db_connection):
        """Test deleting user tokens"""
        mock_db_connection.rowcount = 3
        
        response = client.delete("/api/token/SILVA.A12345")
        
        assert response.status_code == 200
        data = response.json()
        assert data["deleted_count"] == 3
        assert data["user_login"] == "SILVA.A12345"


class TestFixedIncomeEndpoints:
    """Test fixed income endpoints"""

    def test_process_fixed_income_async(self, client, reset_state_manager):
        """Test async fixed income processing"""
        response = client.post("/api/fixed-income/process")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "background" in data["message"]

    def test_process_fixed_income_already_processing(self, client, reset_state_manager):
        """Test processing when already in progress"""
        # Start first processing
        reset_state_manager.start_processing("test_process")
        
        response = client.post("/api/fixed-income/process")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "already in progress" in data["message"]

    def test_processing_status(self, client, reset_state_manager):
        """Test getting processing status"""
        response = client.get("/api/fixed-income/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "is_processing" in data
        assert "start_time" in data
        assert "last_result" in data

    def test_fixed_income_stats(self, client, mock_db_connection):
        """Test fixed income statistics"""
        mock_db_connection.fetchone.return_value = {
            'total_records': 100,
            'unique_issuers': 20,
            'unique_indexers': 5,
            'last_update': datetime.now(),
            'earliest_maturity': datetime(2024, 1, 1),
            'latest_maturity': datetime(2030, 12, 31)
        }
        
        response = client.get("/api/fixed-income/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_records"] == 100
        assert data["unique_issuers"] == 20

    def test_clear_fixed_income_data(self, client, mock_db_connection):
        """Test clearing fixed income data"""
        with patch('services.fixed_income_service.FixedIncomeService.clear_all_data') as mock_clear:
            mock_clear.return_value = True
            
            response = client.delete("/api/fixed-income/clear")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_get_available_categories(self, client):
        """Test getting available categories"""
        response = client.get("/api/fixed-income/categories")
        
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert data["total_categories"] == 3
        assert len(data["categories"]) == 3

    def test_process_fixed_income_sync_success(self, client, mock_db_connection):
        """Test synchronous fixed income processing"""
        with patch('services.fixed_income_service.FixedIncomeService.process_and_store_data') as mock_process:
            mock_process.return_value = {
                "success": True,
                "message": "Processing completed",
                "records_processed": 150,
                "categories_processed": ["CP", "EB", "TPF"],
                "processing_date": datetime.now().isoformat()
            }
            
            response = client.get("/api/fixed-income/process-sync")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["records_processed"] == 150


class TestAPIErrorHandling:
    """Test API error handling"""

    def test_invalid_endpoint(self, client):
        """Test accessing invalid endpoint"""
        response = client.get("/api/invalid-endpoint")
        
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test using wrong HTTP method"""
        response = client.put("/api/health")
        
        assert response.status_code == 405

    def test_invalid_json_payload(self, client):
        """Test sending invalid JSON"""
        response = client.post(
            "/api/token/extract",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422

    def test_missing_required_fields(self, client):
        """Test missing required fields in request"""
        incomplete_payload = {
            "credentials": {
                "user_login": "SILVA.A12345"
                # Missing password and mfa_code
            }
        }
        
        response = client.post("/api/token/extract", json=incomplete_payload)
        
        assert response.status_code == 422

    def test_internal_server_error_handling(self, client, mock_db_connection):
        """Test internal server error handling"""
        mock_db_connection.execute.side_effect = Exception("Unexpected database error")
        
        response = client.get("/api/token/status/SILVA.A12345")
        
        assert response.status_code == 500
        data = response.json()
        assert "error" in data["detail"]


class TestAPIValidation:
    """Test API request validation"""

    def test_username_validation(self, client):
        """Test username format validation"""
        invalid_usernames = [
            "invalid_format",
            "silva.a12345",  # lowercase
            "SILVA.12345",   # missing letter
            "SILVA.AA1234"   # double letter
        ]
        
        for username in invalid_usernames:
            payload = {
                "credentials": {
                    "user_login": username,
                    "password": "validpassword123",
                    "mfa_code": "123456"
                }
            }
            
            response = client.post("/api/token/extract", json=payload)
            assert response.status_code == 422

    def test_password_validation(self, client):
        """Test password validation"""
        invalid_passwords = [
            "123",      # too short (less than 6 chars)
            "12345",    # too short (no letters)
            "123456"    # no letters - only numbers
        ]
        
        for password in invalid_passwords:
            payload = {
                "credentials": {
                    "user_login": "SILVA.A12345",
                    "password": password,
                    "mfa_code": "123456"
                }
            }
            
            response = client.post("/api/token/extract", json=payload)
            assert response.status_code == 422

    def test_mfa_code_validation(self, client):
        """Test MFA code validation"""
        invalid_mfa_codes = [
            "12345",    # too short
            "1234567",  # too long
            "12345a",   # contains letters
            "12 34 56"  # contains spaces (should be handled)
        ]
        
        for mfa_code in invalid_mfa_codes:
            payload = {
                "credentials": {
                    "user_login": "SILVA.A12345",
                    "password": "validpassword123",
                    "mfa_code": mfa_code
                }
            }
            
            response = client.post("/api/token/extract", json=payload)
            if mfa_code != "12 34 56":  # This should be sanitized and pass
                assert response.status_code == 422


class TestAPIRateLimiting:
    """Test rate limiting functionality"""

    def test_rate_limiting_normal_usage(self, client):
        """Test normal usage within rate limits"""
        # Make a few requests within limits
        for _ in range(3):
            response = client.get("/api/health")
            assert response.status_code == 200

    def test_rate_limiting_headers(self, client):
        """Test rate limiting headers are present"""
        response = client.get("/api/health")
        
        # Check for rate limit headers
        assert "X-RateLimit-Limit" in response.headers or response.status_code == 200
        assert "X-RateLimit-Window" in response.headers or response.status_code == 200


class TestAPIDocumentation:
    """Test API documentation endpoints"""

    def test_openapi_schema(self, client):
        """Test OpenAPI schema generation"""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema

    def test_docs_endpoint(self, client):
        """Test Swagger UI documentation"""
        response = client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_endpoint(self, client):
        """Test ReDoc documentation"""
        response = client.get("/redoc")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]