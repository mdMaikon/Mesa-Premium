"""
Token extraction API endpoints
"""

from typing import Any

from database.connection import execute_query
from models.hub_token import TokenExtractionRequest, TokenExtractionResult
from services.hub_token_service import HubTokenService
from utils.crypto_utils import (
    generate_user_hash,
    prepare_token_from_storage,
    validate_crypto_environment,
)
from utils.log_sanitizer import get_sanitized_logger, mask_token, mask_username

from fastapi import APIRouter, BackgroundTasks, HTTPException

router = APIRouter()
logger = get_sanitized_logger(__name__)


@router.post("/token/extract", response_model=TokenExtractionResult)
async def extract_hub_token(
    token_request: TokenExtractionRequest,
    background_tasks: BackgroundTasks = None,
):
    """
    Extract Hub XP token for user
    """
    try:
        masked_user = mask_username(token_request.credentials.user_login)
        logger.info(f"Token extraction request for user: {masked_user}")

        # Initialize service
        service = HubTokenService()

        # Extract token
        result = await service.extract_token(
            user_login=token_request.credentials.user_login,
            password=token_request.credentials.password,
            mfa_code=token_request.credentials.mfa_code,
        )

        if not result.success:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": result.message,
                    "error_details": result.error_details,
                },
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token extraction endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"message": "Internal server error", "error": str(e)},
        ) from e


@router.get("/token/status/{user_login}")
async def get_token_status(user_login: str) -> dict[str, Any]:
    """
    Get token status for user
    """
    try:
        service = HubTokenService()
        status = service.get_token_status(user_login)

        if status is None:
            # Return default status when service returns None
            return {
                "user_login": mask_username(user_login),
                "has_token": False,
                "expires_at": None,
                "extracted_at": None,
                "created_at": None,
                "is_valid": False,
                "message": "No token found or error retrieving status",
            }

        return status

    except Exception as e:
        logger.error(f"Token status endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"message": "Failed to get token status", "error": str(e)},
        ) from e


@router.get("/token/history/{user_login}")
async def get_token_history(
    user_login: str, limit: int = 10
) -> dict[str, Any]:
    """
    Get token history for user (with encryption support)
    """
    try:
        # Validate crypto environment
        if not validate_crypto_environment():
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Crypto environment not properly configured"
                },
            )

        # Generate hash for search
        user_hash = generate_user_hash(user_login)

        query = """
        SELECT id, user_login, token, expires_at, extracted_at, created_at,
               CASE WHEN expires_at < NOW() THEN 1 ELSE 0 END as is_expired
        FROM hub_tokens
        WHERE user_login_hash = %s
        ORDER BY created_at DESC
        LIMIT %s
        """

        tokens = execute_query(query, (user_hash, limit), fetch=True)

        # Ensure tokens is not None
        if tokens is None:
            tokens = []

        # Process encrypted tokens
        processed_tokens = []
        for token in tokens:
            try:
                # Decrypt token data
                decrypted_data = prepare_token_from_storage(token)
                processed_tokens.append(
                    {
                        "id": token["id"],
                        "token": mask_token(decrypted_data["token"]),
                        "expires_at": decrypted_data["expires_at"].isoformat()
                        if decrypted_data["expires_at"]
                        else None,
                        "extracted_at": decrypted_data[
                            "extracted_at"
                        ].isoformat(),
                        "created_at": decrypted_data["created_at"].isoformat(),
                        "is_expired": bool(token["is_expired"]),
                    }
                )
            except Exception as decrypt_error:
                logger.error(
                    f"Error decrypting token {token['id']}: {decrypt_error}"
                )
                # Skip tokens that can't be decrypted
                continue

        return {
            "user_login": mask_username(user_login),
            "total_tokens": len(processed_tokens),
            "tokens": processed_tokens,
        }

    except Exception as e:
        logger.error(f"Token history endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"message": "Failed to get token history", "error": str(e)},
        ) from e


@router.delete("/token/{user_login}")
async def delete_user_tokens(user_login: str) -> dict[str, Any]:
    """
    Delete all tokens for user (with encryption support)
    """
    try:
        # Validate crypto environment
        if not validate_crypto_environment():
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Crypto environment not properly configured"
                },
            )

        # Generate hash for deletion
        user_hash = generate_user_hash(user_login)
        query = "DELETE FROM hub_tokens WHERE user_login_hash = %s"
        rows_affected = execute_query(query, (user_hash,))

        masked_user = mask_username(user_login)
        return {
            "message": f"Deleted {rows_affected} tokens for user {masked_user}",
            "user_login": masked_user,
            "deleted_count": rows_affected,
        }

    except Exception as e:
        logger.error(f"Token deletion endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"message": "Failed to delete tokens", "error": str(e)},
        ) from e
