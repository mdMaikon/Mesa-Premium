"""
Secure Logging Module
Sistema de logging seguro que evita vazamento de dados sensíveis
"""

import logging
import re
from typing import Any, Dict, List, Optional, Union
from functools import wraps
import hashlib

class SecureFormatter(logging.Formatter):
    """Formatter que remove dados sensíveis dos logs"""
    
    # Padrões de dados sensíveis
    SENSITIVE_PATTERNS = [
        (r'password["\']?\s*[:=]\s*["\']?([^"\'}\s,]+)', 'password=***'),
        (r'senha["\']?\s*[:=]\s*["\']?([^"\'}\s,]+)', 'senha=***'),
        (r'token["\']?\s*[:=]\s*["\']?([^"\'}\s,]+)', 'token=***'),
        (r'key["\']?\s*[:=]\s*["\']?([^"\'}\s,]+)', 'key=***'),
        (r'secret["\']?\s*[:=]\s*["\']?([^"\'}\s,]+)', 'secret=***'),
        (r'authorization["\']?\s*[:=]\s*["\']?([^"\'}\s,]+)', 'authorization=***'),
        (r'bearer\s+([a-zA-Z0-9\-_]+)', 'bearer ***'),
        (r'mysql://[^:]+:([^@]+)@', 'mysql://user:***@'),
        (r'postgresql://[^:]+:([^@]+)@', 'postgresql://user:***@'),
        # Padrões de email e CPF
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '***@***.***'),
        (r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b', '***.***.***-**'),
        (r'\b\d{11}\b', '***********'),
    ]
    
    def format(self, record: logging.LogRecord) -> str:
        """Formata o log removendo dados sensíveis"""
        # Aplicar formatação padrão
        msg = super().format(record)
        
        # Remover dados sensíveis
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            msg = re.sub(pattern, replacement, msg, flags=re.IGNORECASE)
        
        return msg

class SecureLogger:
    """Logger seguro com métodos para evitar vazamento de dados"""
    
    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Configurar handler seguro se não existir
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = SecureFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _sanitize_data(self, data: Any) -> Any:
        """Sanitiza dados removendo informações sensíveis"""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if self._is_sensitive_key(key):
                    sanitized[key] = '***'
                else:
                    sanitized[key] = self._sanitize_data(value)
            return sanitized
        elif isinstance(data, (list, tuple)):
            return [self._sanitize_data(item) for item in data]
        elif isinstance(data, str):
            return self._sanitize_string(data)
        else:
            return data
    
    def _is_sensitive_key(self, key: str) -> bool:
        """Verifica se uma chave contém dados sensíveis"""
        sensitive_keys = [
            'password', 'senha', 'token', 'secret', 'key', 'auth',
            'authorization', 'credential', 'login', 'email', 'cpf',
            'cnpj', 'telefone', 'celular', 'api_key', 'access_token'
        ]
        return key.lower() in sensitive_keys
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitiza string removendo dados sensíveis"""
        for pattern, replacement in SecureFormatter.SENSITIVE_PATTERNS:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text
    
    def _hash_sensitive_data(self, data: str) -> str:
        """Gera hash de dados sensíveis para logging"""
        return hashlib.sha256(data.encode()).hexdigest()[:8]
    
    def info(self, msg: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log de informação com dados sanitizados"""
        if extra_data:
            sanitized_data = self._sanitize_data(extra_data)
            self.logger.info(f"{msg} - Data: {sanitized_data}")
        else:
            self.logger.info(msg)
    
    def error(self, msg: str, error: Optional[Exception] = None, extra_data: Optional[Dict[str, Any]] = None):
        """Log de erro sem vazar dados sensíveis"""
        if error:
            # Não logar detalhes da exception que podem conter dados sensíveis
            error_type = type(error).__name__
            self.logger.error(f"{msg} - Erro: {error_type}")
        else:
            self.logger.error(msg)
        
        if extra_data:
            sanitized_data = self._sanitize_data(extra_data)
            self.logger.error(f"Dados adicionais: {sanitized_data}")
    
    def warning(self, msg: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log de warning com dados sanitizados"""
        if extra_data:
            sanitized_data = self._sanitize_data(extra_data)
            self.logger.warning(f"{msg} - Data: {sanitized_data}")
        else:
            self.logger.warning(msg)
    
    def debug(self, msg: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log de debug com dados sanitizados"""
        if extra_data:
            sanitized_data = self._sanitize_data(extra_data)
            self.logger.debug(f"{msg} - Data: {sanitized_data}")
        else:
            self.logger.debug(msg)
    
    def log_user_action(self, action: str, user_id: Optional[str] = None, success: bool = True):
        """Log de ação do usuário sem expor dados sensíveis"""
        if user_id:
            # Hash do user_id para não expor dados pessoais
            hashed_id = self._hash_sensitive_data(user_id)
            status = "SUCCESS" if success else "FAILED"
            self.logger.info(f"User action: {action} - User: {hashed_id} - Status: {status}")
        else:
            status = "SUCCESS" if success else "FAILED"
            self.logger.info(f"System action: {action} - Status: {status}")
    
    def log_database_operation(self, operation: str, table: str, success: bool = True, error: Optional[Exception] = None):
        """Log de operação de banco sem expor dados sensíveis"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"DB Operation: {operation} on {table} - Status: {status}")
        
        if error:
            error_type = type(error).__name__
            self.logger.error(f"DB Error: {error_type} during {operation} on {table}")

def secure_log(logger_name: str = None):
    """Decorator para logging seguro de métodos"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            _logger = SecureLogger(logger_name or func.__module__)
            
            try:
                result = func(*args, **kwargs)
                _logger.log_user_action(f"{func.__name__}", success=True)
                return result
            except Exception as e:
                _logger.log_user_action(f"{func.__name__}", success=False)
                _logger.error(f"Error in {func.__name__}", error=e)
                raise
        
        return wrapper
    return decorator

# Instância global para uso direto
secure_logger = SecureLogger("MenuAutomacoes")