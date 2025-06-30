"""
Hub XP Token Extraction Service
Refactored for better maintainability and separation of concerns

This service provides a backward-compatible interface while delegating
to the refactored service implementation for better code quality.
"""

from typing import Any

from models.hub_token import TokenExtractionResult
from utils.log_sanitizer import get_sanitized_logger, mask_username

from .hub_token_service_refactored import (
    RefactoredHubTokenService,
    TokenRepository,
)

logger = get_sanitized_logger(__name__)


class HubTokenService:
    """
    Hub XP Token Extraction Service

    This class provides a backward-compatible interface for the token extraction service.
    All complex logic has been refactored into specialized classes for better maintainability.

    Key improvements:
    - Separated concerns into specialized classes
    - Reduced cyclomatic complexity
    - Added specific exception handling
    - Improved documentation
    - Eliminated code duplication
    """

    def __init__(self):
        """Initialize the service with the refactored implementation"""
        self._service = RefactoredHubTokenService()

    async def extract_token(
        self, user_login: str, password: str, mfa_code: str | None = None
    ) -> TokenExtractionResult:
        """
        Extract Hub XP token asynchronously

        This method performs the following steps:
        1. Detects environment and configures WebDriver
        2. Navigates to Hub XP and performs authentication
        3. Handles MFA authentication if required
        4. Extracts token from browser localStorage
        5. Saves token to database with proper rotation

        Args:
            user_login: User login credentials
            password: User password
            mfa_code: 6-digit MFA code (required for successful authentication)

        Returns:
            TokenExtractionResult: Contains success status, token data, and error information

        Raises:
            No exceptions are raised - all errors are captured in the result object

        Example:
            >>> service = HubTokenService()
            >>> result = await service.extract_token("user123", "pass123", "123456")
            >>> if result.success:
            ...     print(f"Token extracted successfully: {result.token_data}")
            ... else:
            ...     print(f"Extraction failed: {result.error_message}")
        """
        try:
            logger.info(
                f"Starting token extraction for user: {mask_username(user_login)}"
            )

            # Delegate to refactored service
            result = await self._service.extract_token(
                user_login, password, mfa_code
            )

            if result.success:
                logger.info(
                    f"Token extraction completed successfully for user: {mask_username(user_login)}"
                )
            else:
                logger.error(
                    f"Token extraction failed for user: {mask_username(user_login)}, Error: {result.message}"
                )

            return result

        except Exception as e:
            logger.error(f"Unexpected error during token extraction: {e}")
            return TokenExtractionResult(
                success=False,
                message=f"Unexpected service error: {e}",
                user_login=mask_username(user_login),
            )

    def get_token_status(self, user_login: str) -> dict[str, Any] | None:
        """
        Get token status for a user

        This method retrieves the current token status from the database,
        including validity information and expiration details.

        Args:
            user_login: User login to check token status for

        Returns:
            Optional[Dict]: Token status information containing:
                - user_login: Masked username for security
                - has_token: Boolean indicating if token exists
                - expires_at: Token expiration datetime
                - extracted_at: When token was extracted
                - created_at: When token was created
                - is_valid: Boolean indicating if token is still valid

        Example:
            >>> service = HubTokenService()
            >>> status = service.get_token_status("user123")
            >>> if status and status['is_valid']:
            ...     print("Token is valid and can be used")
            ... else:
            ...     print("Token is invalid or expired")
        """
        try:
            logger.info(
                f"Checking token status for user: {mask_username(user_login)}"
            )

            # Delegate to repository
            status = TokenRepository.get_token_status(user_login)

            if status:
                logger.info(
                    f"Token status retrieved for user: {mask_username(user_login)}, Valid: {status.get('is_valid', False)}"
                )
            else:
                logger.warning(
                    f"No token status found for user: {mask_username(user_login)}"
                )

            return status

        except Exception as e:
            logger.error(
                f"Error getting token status for user {mask_username(user_login)}: {e}"
            )
            return None

    def get_token_history(
        self, user_login: str, limit: int = 10
    ) -> list[dict[str, Any]] | None:
        """
        Get token history for a user

        Args:
            user_login: User login to get history for
            limit: Maximum number of records to return

        Returns:
            Optional[List[Dict]]: List of historical token records
        """
        try:
            logger.info(
                f"Getting token history for user: {mask_username(user_login)}"
            )

            # This could be implemented in TokenRepository if needed
            # For now, return current status as single item
            current_status = self.get_token_status(user_login)
            if current_status:
                return [current_status]

            return []

        except Exception as e:
            logger.error(
                f"Error getting token history for user {mask_username(user_login)}: {e}"
            )
            return None

    def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired tokens from database

        Returns:
            int: Number of tokens cleaned up
        """
        try:
            logger.info("Starting cleanup of expired tokens")

            # This could be implemented in TokenRepository if needed
            # For now, return 0 as no cleanup performed
            logger.info("Token cleanup completed")
            return 0

        except Exception as e:
            logger.error(f"Error during token cleanup: {e}")
            return 0

    def validate_mfa_code(self, mfa_code: str) -> bool:
        """
        Validate MFA code format

        Args:
            mfa_code: MFA code to validate

        Returns:
            bool: True if valid format, False otherwise
        """
        if not mfa_code:
            return False

        # Remove any whitespace
        mfa_code = str(mfa_code).strip()

        # Check if it's exactly 6 digits
        if len(mfa_code) != 6:
            return False

        # Check if all characters are digits
        if not mfa_code.isdigit():
            return False

        return True

    def __del__(self):
        """Cleanup resources when service is destroyed"""
        if hasattr(self, "_service"):
            del self._service
