"""
Log sanitization utilities to prevent sensitive data exposure
"""

import logging
import re
from typing import Any


class SensitiveDataSanitizer:
    """Sanitizes sensitive data from log messages"""

    # Patterns for sensitive data
    SENSITIVE_PATTERNS = {
        "mfa_code": re.compile(r"\b\d{6}\b"),  # 6-digit MFA codes
        "password": re.compile(
            r'(password["\']?\s*[:=]\s*["\']?)([^"\'\s]+)', re.IGNORECASE
        ),
        "token": re.compile(
            r'(token["\']?\s*[:=]\s*["\']?)([a-zA-Z0-9+/]{20,})', re.IGNORECASE
        ),
        "email": re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        ),
        "credit_card": re.compile(
            r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"
        ),
        "cpf": re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"),
    }

    @classmethod
    def sanitize_message(cls, message: str) -> str:
        """Sanitize a log message by masking sensitive data"""
        sanitized = message

        # Replace MFA codes with masked version
        sanitized = cls.SENSITIVE_PATTERNS["mfa_code"].sub("******", sanitized)

        # Replace passwords (keep prefix, mask value)
        sanitized = cls.SENSITIVE_PATTERNS["password"].sub(
            r"\1[MASKED]", sanitized
        )

        # Replace tokens (keep prefix, mask most of the value)
        def mask_token(match):
            prefix = match.group(1)
            token = match.group(2)
            if len(token) > 8:
                return f"{prefix}{token[:4]}...{token[-4:]}"
            return f"{prefix}[MASKED]"

        sanitized = cls.SENSITIVE_PATTERNS["token"].sub(mask_token, sanitized)

        # Mask emails (keep domain, mask user part)
        def mask_email(match):
            email = match.group(0)
            parts = email.split("@")
            if len(parts) == 2:
                user, domain = parts
                masked_user = (
                    user[:2] + "*" * (len(user) - 2)
                    if len(user) > 2
                    else "***"
                )
                return f"{masked_user}@{domain}"
            return email

        sanitized = cls.SENSITIVE_PATTERNS["email"].sub(mask_email, sanitized)

        # Mask credit cards and CPF
        sanitized = cls.SENSITIVE_PATTERNS["credit_card"].sub(
            "****-****-****-****", sanitized
        )
        sanitized = cls.SENSITIVE_PATTERNS["cpf"].sub(
            "***.***.***-**", sanitized
        )

        return sanitized

    @classmethod
    def mask_username(cls, username: str) -> str:
        """Mask username for logging purposes"""
        if not username or len(username) <= 2:
            return "[USER]"

        # Keep first 2 and last 2 characters, mask the middle
        if len(username) <= 4:
            return username[:1] + "*" * (len(username) - 1)

        return username[:2] + "*" * (len(username) - 4) + username[-2:]

    @classmethod
    def mask_token(cls, token: str) -> str:
        """Mask token for logging purposes"""
        if not token or len(token) <= 8:
            return "[TOKEN]"

        # Keep first 4 and last 4 characters, mask the middle
        return token[:4] + "*" * (len(token) - 8) + token[-4:]


class SanitizedLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that automatically sanitizes sensitive data"""

    def process(self, msg, kwargs):
        """Process log message and sanitize sensitive data"""
        if isinstance(msg, str):
            msg = SensitiveDataSanitizer.sanitize_message(msg)
        return msg, kwargs


def get_sanitized_logger(name: str) -> SanitizedLoggerAdapter:
    """Get a logger that automatically sanitizes sensitive data"""
    base_logger = logging.getLogger(name)
    return SanitizedLoggerAdapter(base_logger, {})


def mask_sensitive_data(data: Any) -> str:
    """Mask sensitive data for safe logging"""
    if isinstance(data, str):
        return SensitiveDataSanitizer.sanitize_message(data)
    elif isinstance(data, dict):
        masked = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(
                sensitive in key_lower
                for sensitive in ["password", "token", "mfa", "secret", "key"]
            ):
                masked[key] = "[MASKED]"
            else:
                masked[key] = (
                    mask_sensitive_data(value)
                    if isinstance(value, str | dict | list)
                    else value
                )
        return str(masked)
    elif isinstance(data, list):
        return str([mask_sensitive_data(item) for item in data])
    else:
        return str(data)


def mask_username(username: str) -> str:
    """Convenience function to mask username for logging"""
    return SensitiveDataSanitizer.mask_username(username)


def mask_token(token: str) -> str:
    """Convenience function to mask token for logging"""
    return SensitiveDataSanitizer.mask_token(token)
