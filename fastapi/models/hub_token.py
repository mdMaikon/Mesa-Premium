"""
Pydantic models for Hub XP token operations
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class HubCredentials(BaseModel):
    """Hub XP login credentials"""
    user_login: str = Field(..., min_length=1, description="Hub XP login username")
    password: str = Field(..., min_length=1, description="Hub XP password")
    mfa_code: Optional[str] = Field(None, description="MFA code if required")

class TokenExtractionRequest(BaseModel):
    """Request for token extraction"""
    credentials: HubCredentials
    force_refresh: bool = Field(False, description="Force token refresh even if valid token exists")

class TokenResponse(BaseModel):
    """Token extraction response"""
    id: int
    user_login: str
    token: str
    expires_at: datetime
    extracted_at: datetime
    created_at: datetime

class TokenStatus(BaseModel):
    """Token status information"""
    user_login: str
    has_valid_token: bool
    expires_at: Optional[datetime] = None
    extracted_at: Optional[datetime] = None
    time_until_expiry: Optional[str] = None

class TokenExtractionResult(BaseModel):
    """Result of token extraction operation"""
    success: bool
    message: str
    token_id: Optional[int] = None
    user_login: str
    expires_at: Optional[datetime] = None
    error_details: Optional[str] = None

class TokenHistoryItem(BaseModel):
    """Single token history item"""
    id: int
    token: str
    expires_at: datetime
    extracted_at: datetime
    created_at: datetime
    is_expired: bool

class TokenHistory(BaseModel):
    """Token history for a user"""
    user_login: str
    total_tokens: int
    tokens: List[TokenHistoryItem]