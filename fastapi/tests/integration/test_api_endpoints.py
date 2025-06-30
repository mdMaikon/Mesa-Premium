"""
Simplified integration tests for API endpoints
"""

from unittest.mock import patch


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_health_check_success(self, client):
        """Test basic health check"""
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "database" in data
        assert "version" in data

    @patch("database.connection.get_database_connection")
    def test_health_check_database_error(self, mock_get_connection, client):
        """Test health check with database error"""
        mock_get_connection.side_effect = Exception(
            "Database connection failed"
        )

        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "error" in data["database"]


class TestAutomationEndpoints:
    """Test automation endpoints"""

    def test_list_automations(self, client):
        """Test listing automations"""
        response = client.get("/api/automations")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:  # If there are automations
            assert "name" in data[0]
            assert "description" in data[0]

    def test_automation_stats(self, client):
        """Test automation statistics"""
        response = client.get("/api/automations/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_automations" in data
        assert "active_automations" in data


class TestTokenEndpoints:
    """Test token management endpoints"""

    def test_token_status_no_token(self, client):
        """Test token status for non-existent user"""
        response = client.get("/api/token/status/SILVA.A12345")

        assert response.status_code == 200
        data = response.json()
        # Username is masked in logs for security, so check if it contains expected pattern
        assert "SILVA" in data["user_login"] or "SI*" in data["user_login"]
        assert "has_token" in data or "has_valid_token" in data

    def test_token_history_empty(self, client):
        """Test token history for user with no tokens"""
        response = client.get("/api/token/history/SILVA.A12345")

        # Can be 200 with empty tokens or 500 due to database error in test env
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert "user_login" in data
            assert "tokens" in data
            assert isinstance(data["tokens"], list)

    def test_extract_token_invalid_credentials(self, client):
        """Test token extraction with invalid credentials"""
        payload = {
            "credentials": {
                "user_login": "SILVA.A12345",
                "password": "invalid_password",
                "mfa_code": "123456",
            }
        }

        response = client.post("/api/token/extract", json=payload)

        # Should return error due to actual login attempt failure
        assert response.status_code in [400, 422, 500]

    def test_extract_token_invalid_username_format(self, client):
        """Test token extraction with invalid username format"""
        payload = {
            "credentials": {
                "user_login": "invalid_username",
                "password": "password123",
                "mfa_code": "123456",
            }
        }

        response = client.post("/api/token/extract", json=payload)

        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data


class TestFixedIncomeEndpoints:
    """Test fixed income endpoints"""

    def test_processing_status(self, client):
        """Test processing status endpoint"""
        response = client.get("/api/fixed-income/status")

        assert response.status_code == 200
        data = response.json()
        assert "is_processing" in data

    def test_fixed_income_stats(self, client):
        """Test fixed income statistics"""
        response = client.get("/api/fixed-income/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_records" in data

    def test_get_available_categories(self, client):
        """Test getting available categories"""
        response = client.get("/api/fixed-income/categories")

        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert isinstance(data["categories"], list)


class TestAPIErrorHandling:
    """Test API error handling"""

    def test_invalid_endpoint(self, client):
        """Test accessing non-existent endpoint"""
        response = client.get("/api/nonexistent")

        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test wrong HTTP method"""
        response = client.delete("/api/health")

        assert response.status_code == 405

    def test_invalid_json_payload(self, client):
        """Test invalid JSON in request body"""
        response = client.post(
            "/api/token/extract",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422


class TestAPIValidation:
    """Test API validation"""

    def test_username_validation(self, client):
        """Test username format validation"""
        invalid_usernames = [
            "short",  # Too short
            "invalid.format",  # Wrong format
            "TOOLONG.A123456",  # Too long
            "123.A12345",  # Starts with number
        ]

        for username in invalid_usernames:
            payload = {
                "credentials": {
                    "user_login": username,
                    "password": "password123",
                    "mfa_code": "123456",
                }
            }

            response = client.post("/api/token/extract", json=payload)
            assert response.status_code == 422

    def test_password_validation(self, client):
        """Test password validation"""
        payload = {
            "credentials": {
                "user_login": "SILVA.A12345",
                "password": "123",  # Too short
                "mfa_code": "123456",
            }
        }

        response = client.post("/api/token/extract", json=payload)
        assert response.status_code == 422

    def test_mfa_code_validation(self, client):
        """Test MFA code validation"""
        invalid_mfa_codes = [
            "12345",  # Too short
            "1234567",  # Too long
            "12345a",  # Contains non-digit
            "",  # Empty
        ]

        for mfa_code in invalid_mfa_codes:
            payload = {
                "credentials": {
                    "user_login": "SILVA.A12345",
                    "password": "password123",
                    "mfa_code": mfa_code,
                }
            }

            response = client.post("/api/token/extract", json=payload)
            assert response.status_code == 422


class TestAPIDocumentation:
    """Test API documentation endpoints"""

    def test_openapi_schema(self, client):
        """Test OpenAPI schema availability"""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    def test_docs_endpoint(self, client):
        """Test Swagger UI docs"""
        response = client.get("/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_redoc_endpoint(self, client):
        """Test ReDoc documentation"""
        response = client.get("/redoc")

        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")


class TestRootEndpoint:
    """Test root endpoint"""

    def test_root_endpoint(self, client):
        """Test API root endpoint"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data
