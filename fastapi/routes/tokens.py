"""
Token extraction API endpoints
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
from models.hub_token import (
    TokenExtractionRequest, 
    TokenExtractionResult, 
    TokenStatus
)
from services.hub_token_service import HubTokenService
from database.connection import execute_query
from utils.log_sanitizer import get_sanitized_logger, mask_username, mask_token
import logging

router = APIRouter()
logger = get_sanitized_logger(__name__)

@router.post("/token/extract", response_model=TokenExtractionResult)
async def extract_hub_token(
    token_request: TokenExtractionRequest,
    background_tasks: BackgroundTasks = None
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
            mfa_code=token_request.credentials.mfa_code
        )
        
        if not result.success:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": result.message,
                    "error_details": result.error_details
                }
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token extraction endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"message": "Internal server error", "error": str(e)}
        )

@router.get("/token/status/{user_login}")
async def get_token_status(user_login: str) -> Dict[str, Any]:
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
                "message": "No token found or error retrieving status"
            }
        
        return status
        
    except Exception as e:
        logger.error(f"Token status endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"message": "Failed to get token status", "error": str(e)}
        )

@router.get("/token/history/{user_login}")
async def get_token_history(user_login: str, limit: int = 10) -> Dict[str, Any]:
    """
    Get token history for user
    """
    try:
        query = """
        SELECT id, token, expires_at, extracted_at, created_at,
               CASE WHEN expires_at < NOW() THEN 1 ELSE 0 END as is_expired
        FROM hub_tokens 
        WHERE user_login = %s 
        ORDER BY created_at DESC 
        LIMIT %s
        """
        
        tokens = execute_query(query, (user_login, limit), fetch=True)
        
        # Ensure tokens is not None
        if tokens is None:
            tokens = []
        
        return {
            "user_login": user_login,
            "total_tokens": len(tokens),
            "tokens": [
                {
                    "id": token['id'],
                    "token": mask_token(token['token']),
                    "expires_at": token['expires_at'].isoformat() if token['expires_at'] else None,
                    "extracted_at": token['extracted_at'].isoformat(),
                    "created_at": token['created_at'].isoformat(),
                    "is_expired": bool(token['is_expired'])
                }
                for token in tokens
            ]
        }
        
    except Exception as e:
        logger.error(f"Token history endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"message": "Failed to get token history", "error": str(e)}
        )

@router.delete("/token/{user_login}")
async def delete_user_tokens(user_login: str) -> Dict[str, Any]:
    """
    Delete all tokens for user
    """
    try:
        query = "DELETE FROM hub_tokens WHERE user_login = %s"
        rows_affected = execute_query(query, (user_login,))
        
        return {
            "message": f"Deleted {rows_affected} tokens for user {user_login}",
            "user_login": user_login,
            "deleted_count": rows_affected
        }
        
    except Exception as e:
        logger.error(f"Token deletion endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"message": "Failed to delete tokens", "error": str(e)}
        )