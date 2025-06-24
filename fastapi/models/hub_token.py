"""
Pydantic models for Hub XP token operations
"""
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List
import re

class HubCredentials(BaseModel):
    """Hub XP login credentials"""
    user_login: str = Field(..., min_length=3, max_length=100, description="Hub XP login username")
    password: str = Field(..., min_length=6, max_length=200, description="Hub XP password")
    mfa_code: Optional[str] = Field(None, min_length=6, max_length=6, description="MFA code if required")
    
    @validator('user_login')
    def validate_user_login(cls, v):
        """Sanitiza e valida username conforme padrão XP"""
        if not v:
            raise ValueError('Username é obrigatório')
        
        # Remove espaços
        v = v.strip()
        
        # Padrão XP: NOME.A12345 (nome seguido de ponto, letra e números)
        if not re.match(r'^[A-Z]+\.[A-Z]\d{5}$', v):
            raise ValueError('Username deve seguir o padrão XP: NOME.A12345 (ex: SILVA.A12345)')
        
        return v
    
    @validator('password')
    def validate_password(cls, v):
        """Valida força da senha"""
        if not v:
            raise ValueError('Senha é obrigatória')
        
        if len(v) < 6:
            raise ValueError('Senha deve ter pelo menos 6 caracteres')
        
        # Verifica se tem pelo menos uma letra
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('Senha deve conter pelo menos uma letra')
        
        return v
    
    @validator('mfa_code')
    def validate_mfa_code(cls, v):
        """Valida código MFA de 6 dígitos"""
        if v is None:
            return v
        
        # Remove espaços
        v = v.strip()
        
        # Verifica se é exatamente 6 dígitos
        if not re.match(r'^\d{6}$', v):
            raise ValueError('Código MFA deve conter exatamente 6 dígitos numéricos')
        
        return v

class TokenExtractionRequest(BaseModel):
    """Request for token extraction"""
    credentials: HubCredentials
    force_refresh: bool = Field(False, description="Force token refresh even if valid token exists")
    
    @validator('force_refresh')
    def validate_force_refresh(cls, v):
        """Garante que force_refresh é boolean"""
        if not isinstance(v, bool):
            raise ValueError('force_refresh deve ser um valor booleano')
        return v

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