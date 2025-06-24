"""
Unit tests for HubTokenService
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from services.hub_token_service import HubTokenService


class TestHubTokenService:
    """Test cases for HubTokenService"""

    @pytest.mark.asyncio
    async def test_get_token_status_no_token(self, mock_db_connection):
        """Test get_token_status when no token exists"""
        mock_db_connection.fetchone.return_value = None
        
        service = HubTokenService()
        result = await service.get_token_status("SILVA.A12345")
        
        assert result["user_login"] == "SILVA.A12345"
        assert result["has_valid_token"] is False
        assert "No token found" in result["message"]

    @pytest.mark.asyncio
    async def test_get_token_status_valid_token(self, mock_db_connection):
        """Test get_token_status with valid token"""
        future_time = datetime.now() + timedelta(hours=1)
        mock_db_connection.fetchone.return_value = {
            'expires_at': future_time,
            'extracted_at': datetime.now(),
            'is_expired': 0
        }
        
        service = HubTokenService()
        result = await service.get_token_status("SILVA.A12345")
        
        assert result["user_login"] == "SILVA.A12345"
        assert result["has_valid_token"] is True
        assert result["expires_at"] == future_time

    @pytest.mark.asyncio
    async def test_get_token_status_expired_token(self, mock_db_connection):
        """Test get_token_status with expired token"""
        past_time = datetime.now() - timedelta(hours=1)
        mock_db_connection.fetchone.return_value = {
            'expires_at': past_time,
            'extracted_at': datetime.now(),
            'is_expired': 1
        }
        
        service = HubTokenService()
        result = await service.get_token_status("SILVA.A12345")
        
        assert result["user_login"] == "SILVA.A12345"
        assert result["has_valid_token"] is False
        assert "expired" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_extract_token_success(self, mock_db_connection, mock_selenium_driver):
        """Test successful token extraction"""
        with patch.object(HubTokenService, '_perform_login', new_callable=AsyncMock) as mock_login, \
             patch.object(HubTokenService, '_extract_token_from_browser', new_callable=AsyncMock) as mock_extract:
            
            mock_login.return_value = True
            mock_extract.return_value = "test_token_12345"
            mock_db_connection.lastrowid = 1
            
            service = HubTokenService()
            result = await service.extract_token("SILVA.A12345", "password123", "123456")
            
            assert result["success"] is True
            assert result["user_login"] == "SILVA.A12345"
            assert result["token_id"] == 1

    @pytest.mark.asyncio
    async def test_extract_token_login_failed(self, mock_selenium_driver):
        """Test token extraction with login failure"""
        with patch.object(HubTokenService, '_perform_login', new_callable=AsyncMock) as mock_login:
            mock_login.return_value = False
            
            service = HubTokenService()
            result = await service.extract_token("SILVA.A12345", "wrong_password", "123456")
            
            assert result["success"] is False
            assert "login failed" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_extract_token_extraction_failed(self, mock_db_connection, mock_selenium_driver):
        """Test token extraction when token extraction fails"""
        with patch.object(HubTokenService, '_perform_login', new_callable=AsyncMock) as mock_login, \
             patch.object(HubTokenService, '_extract_token_from_browser', new_callable=AsyncMock) as mock_extract:
            
            mock_login.return_value = True
            mock_extract.return_value = None
            
            service = HubTokenService()
            result = await service.extract_token("SILVA.A12345", "password123", "123456")
            
            assert result["success"] is False
            assert "extract token" in result["message"].lower()

    def test_detect_environment_wsl(self):
        """Test environment detection for WSL"""
        with patch('platform.system', return_value='Linux'), \
             patch('os.path.exists', return_value=True):
            
            service = HubTokenService()
            env = service._detect_environment()
            assert env == "wsl"

    def test_detect_environment_linux(self):
        """Test environment detection for Linux"""
        with patch('platform.system', return_value='Linux'), \
             patch('os.path.exists', return_value=False):
            
            service = HubTokenService()
            env = service._detect_environment()
            assert env == "linux"

    def test_detect_environment_windows(self):
        """Test environment detection for Windows"""
        with patch('platform.system', return_value='Windows'):
            service = HubTokenService()
            env = service._detect_environment()
            assert env == "windows"

    def test_get_chrome_options_headless(self):
        """Test Chrome options configuration for headless mode"""
        service = HubTokenService()
        options = service._get_chrome_options("linux")
        
        option_args = [arg for arg in options.arguments]
        assert "--headless" in option_args
        assert "--no-sandbox" in option_args
        assert "--disable-dev-shm-usage" in option_args

    def test_get_chrome_options_windows(self):
        """Test Chrome options configuration for Windows"""
        service = HubTokenService()
        options = service._get_chrome_options("windows")
        
        option_args = [arg for arg in options.arguments]
        assert "--disable-blink-features=AutomationControlled" in option_args
        assert "--disable-extensions" in option_args

    @pytest.mark.asyncio
    async def test_cleanup_old_tokens(self, mock_db_connection):
        """Test cleanup of old tokens"""
        mock_db_connection.rowcount = 2
        
        service = HubTokenService()
        await service._cleanup_old_tokens("SILVA.A12345")
        
        # Verify delete query was called
        assert mock_db_connection.execute.called

    @pytest.mark.asyncio
    async def test_save_token_to_database(self, mock_db_connection):
        """Test saving token to database"""
        mock_db_connection.lastrowid = 5
        
        service = HubTokenService()
        token_id = await service._save_token_to_database(
            "SILVA.A12345", 
            "test_token", 
            datetime.now() + timedelta(hours=1)
        )
        
        assert token_id == 5

    def test_mask_sensitive_data(self):
        """Test sensitive data masking"""
        service = HubTokenService()
        
        # Test username masking
        masked_user = service._mask_username("SILVA.A12345")
        assert masked_user == "SI***45"
        
        # Test short username
        masked_short = service._mask_username("AB")
        assert masked_short == "***"

    @pytest.mark.asyncio
    async def test_wait_for_mfa_input(self, mock_selenium_driver):
        """Test waiting for MFA input"""
        # Mock MFA elements
        mock_elements = [Mock(), Mock(), Mock(), Mock(), Mock(), Mock()]
        for i, element in enumerate(mock_elements):
            element.get_attribute.return_value = "1234567890"[i] if i < 6 else ""
        
        mock_selenium_driver.find_elements.return_value = mock_elements
        
        service = HubTokenService()
        result = await service._wait_for_mfa_input(mock_selenium_driver, "123456")
        
        assert result is True

    @pytest.mark.asyncio
    async def test_extract_token_from_browser(self, mock_selenium_driver):
        """Test token extraction from browser"""
        mock_selenium_driver.execute_script.return_value = "test_token_12345"
        
        service = HubTokenService()
        token = await service._extract_token_from_browser(mock_selenium_driver)
        
        assert token == "test_token_12345"

    @pytest.mark.asyncio
    async def test_extract_token_exception_handling(self, mock_selenium_driver):
        """Test exception handling during token extraction"""
        with patch.object(HubTokenService, '_setup_webdriver') as mock_setup:
            mock_setup.side_effect = Exception("WebDriver setup failed")
            
            service = HubTokenService()
            result = await service.extract_token("SILVA.A12345", "password123", "123456")
            
            assert result["success"] is False
            assert "WebDriver setup failed" in result["error_details"]


class TestHubTokenServiceIntegration:
    """Integration tests for HubTokenService with mocked dependencies"""

    @pytest.mark.asyncio
    async def test_full_token_extraction_flow(self, mock_db_connection, mock_selenium_driver):
        """Test complete token extraction flow"""
        # Setup mocks for successful flow
        with patch.object(HubTokenService, '_perform_login', new_callable=AsyncMock) as mock_login, \
             patch.object(HubTokenService, '_extract_token_from_browser', new_callable=AsyncMock) as mock_extract, \
             patch.object(HubTokenService, '_cleanup_old_tokens', new_callable=AsyncMock) as mock_cleanup:
            
            mock_login.return_value = True
            mock_extract.return_value = "complete_test_token"
            mock_cleanup.return_value = None
            mock_db_connection.lastrowid = 10
            
            service = HubTokenService()
            result = await service.extract_token("SILVA.A12345", "password123", "123456")
            
            # Verify all steps were called
            mock_login.assert_called_once()
            mock_extract.assert_called_once()
            mock_cleanup.assert_called_once_with("SILVA.A12345")
            
            # Verify result
            assert result["success"] is True
            assert result["token_id"] == 10
            assert result["user_login"] == "SILVA.A12345"

    @pytest.mark.asyncio
    async def test_token_status_with_database_error(self, mock_db_connection):
        """Test token status when database error occurs"""
        mock_db_connection.execute.side_effect = Exception("Database connection failed")
        
        service = HubTokenService()
        result = await service.get_token_status("SILVA.A12345")
        
        assert result["user_login"] == "SILVA.A12345"
        assert result["has_valid_token"] is False
        assert "error" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_concurrent_token_extraction(self, mock_db_connection, mock_selenium_driver):
        """Test concurrent token extraction attempts"""
        import asyncio
        
        with patch.object(HubTokenService, '_perform_login', new_callable=AsyncMock) as mock_login, \
             patch.object(HubTokenService, '_extract_token_from_browser', new_callable=AsyncMock) as mock_extract:
            
            mock_login.return_value = True
            mock_extract.return_value = "concurrent_token"
            mock_db_connection.lastrowid = 20
            
            service = HubTokenService()
            
            # Run multiple extractions concurrently
            tasks = [
                service.extract_token("SILVA.A12345", "password123", "123456")
                for _ in range(3)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # At least one should succeed
            successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
            assert len(successful_results) >= 1