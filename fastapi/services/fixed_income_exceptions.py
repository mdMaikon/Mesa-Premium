"""
Custom exceptions for Fixed Income Service
Provides specific exception types for better error handling and debugging
"""


class FixedIncomeException(Exception):
    """Base exception for Fixed Income operations"""

    pass


class TokenRetrievalError(FixedIncomeException):
    """Error retrieving token from database"""

    pass


class DataProcessingError(FixedIncomeException):
    """Error during data processing operations"""

    pass


class DataDownloadError(FixedIncomeException):
    """Error downloading data from Hub XP"""

    pass


class DatabaseError(FixedIncomeException):
    """Error with database operations"""

    pass


class DataValidationError(FixedIncomeException):
    """Error validating data format or content"""

    pass


class APIConnectionError(FixedIncomeException):
    """Error connecting to Hub XP API"""

    pass


class DataTransformationError(DataProcessingError):
    """Error during data transformation operations"""

    pass


class ColumnFormattingError(DataTransformationError):
    """Error formatting DataFrame columns"""

    pass


class FilteringError(DataTransformationError):
    """Error filtering DataFrame data"""

    pass


class RuleApplicationError(DataTransformationError):
    """Error applying business rules to data"""

    pass


class DataInsertionError(DatabaseError):
    """Error inserting data into database"""

    pass


class TableClearError(DatabaseError):
    """Error clearing database table"""

    pass


class StatsCalculationError(FixedIncomeException):
    """Error calculating processing statistics"""

    pass


class CategoryProcessingError(DataProcessingError):
    """Error processing specific data category"""

    def __init__(self, category: str, message: str):
        self.category = category
        super().__init__(f"Error processing category '{category}': {message}")
