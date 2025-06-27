"""
Structured Data Processing Exceptions
Custom exceptions for structured data operations following project standards.
"""


class StructuredError(Exception):
    """Base exception for structured data operations"""

    pass


class TokenRetrievalError(StructuredError):
    """Exception raised when token retrieval from database fails"""

    pass


class ApiRequestError(StructuredError):
    """Exception raised when API requests to Hub XP fail"""

    pass


class DataProcessingError(StructuredError):
    """Exception raised during data processing operations"""

    pass


class DatabaseOperationError(StructuredError):
    """Exception raised during database operations"""

    pass


class ValidationError(StructuredError):
    """Exception raised during data validation"""

    pass
