"""
Structured Data Models
Pydantic models for structured financial operations following project standards.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StructuredTicketRequest(BaseModel):
    """Request model for structured tickets processing"""

    data_inicio: str = Field(
        ...,
        description="Start date in ISO format (YYYY-MM-DDTHH:MM:SS)",
        json_schema_extra={"example": "2025-01-01T00:00:00"},
    )
    data_fim: str = Field(
        ...,
        description="End date in ISO format (YYYY-MM-DDTHH:MM:SS)",
        json_schema_extra={"example": "2025-01-31T23:59:59"},
    )

    @field_validator("data_inicio", "data_fim")
    @classmethod
    def validate_date_format(cls, v):
        """Validate ISO datetime format"""
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
            return v
        except ValueError as e:
            raise ValueError(
                f"Invalid datetime format. Use YYYY-MM-DDTHH:MM:SS: {e}"
            ) from e


class StructuredTicketData(BaseModel):
    """Model for structured ticket data from API"""

    ticket_id: str = Field(..., description="Unique ticket ID from API")
    data_envio: datetime | None = Field(
        None, description="Ticket creation date"
    )
    cliente: int | None = Field(None, description="Client code")
    ativo: str | None = Field(None, max_length=255, description="Asset name")
    comissao: Decimal | None = Field(None, description="Advisor commission")
    estrutura: str | None = Field(
        None, max_length=255, description="Structure type"
    )
    quantidade: int | None = Field(None, description="Quantity")
    fixing: datetime | None = Field(None, description="Fixing date")
    status: str | None = Field(
        None, max_length=100, description="Operation status"
    )
    detalhes: str | None = Field(None, description="Status details")
    operacao: str | None = Field(
        None, max_length=100, description="Operation type"
    )
    aai_ordem: str | None = Field(
        None, max_length=100, description="AAI order code"
    )

    model_config = ConfigDict(from_attributes=True)


class StructuredProcessingResponse(BaseModel):
    """Response model for structured data processing"""

    success: bool = Field(..., description="Processing success status")
    message: str = Field(..., description="Processing result message")
    records_processed: int | None = Field(
        None, description="Number of records processed"
    )
    new_records: int | None = Field(
        None, description="Number of new records inserted"
    )
    updated_records: int | None = Field(
        None, description="Number of records updated"
    )
    processing_date: str | None = Field(
        None, description="Processing timestamp"
    )
    period: str | None = Field(None, description="Data period processed")
    error: str | None = Field(None, description="Error message if failed")


class StructuredStatsResponse(BaseModel):
    """Response model for structured data statistics"""

    total_records: int = Field(..., description="Total records in database")
    unique_clients: int | str = Field(
        ..., description="Number of unique clients (or 'N/A (encrypted)')"
    )
    unique_assets: int | str = Field(
        ..., description="Number of unique assets (or 'N/A (encrypted)')"
    )
    total_commission: Decimal | str | None = Field(
        None, description="Total commission amount (or 'N/A (encrypted)')"
    )
    last_update: str | None = Field(
        None, description="Last data update timestamp"
    )
    earliest_ticket: str | None = Field(
        None, description="Earliest ticket date"
    )
    latest_ticket: str | None = Field(None, description="Latest ticket date")
    status_breakdown: dict[str, int] | None = Field(
        None, description="Count by status"
    )

    model_config = ConfigDict()


class StructuredStatusResponse(BaseModel):
    """Response model for processing status"""

    is_processing: bool = Field(
        ..., description="Whether processing is currently running"
    )
    last_processing_date: str | None = Field(
        None, description="Last processing date"
    )
    last_processing_status: str | None = Field(
        None, description="Last processing result"
    )
    records_count: int | None = Field(
        None, description="Current records count"
    )


class StructuredDataQueryParams(BaseModel):
    """Query parameters for structured data retrieval"""

    limit: int | None = Field(
        100, ge=1, le=1000, description="Maximum records to return"
    )
    offset: int | None = Field(0, ge=0, description="Records to skip")
    cliente: int | None = Field(None, description="Filter by client code")
    ativo: str | None = Field(None, description="Filter by asset name")
    status: str | None = Field(None, description="Filter by status")
    data_inicio: str | None = Field(
        None, description="Filter from date (YYYY-MM-DD)"
    )
    data_fim: str | None = Field(
        None, description="Filter to date (YYYY-MM-DD)"
    )

    @field_validator("data_inicio", "data_fim")
    @classmethod
    def validate_date_format(cls, v):
        """Validate date format"""
        if v is None:
            return v
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError as e:
            raise ValueError(
                f"Invalid date format. Use YYYY-MM-DD: {e}"
            ) from e


class StructuredDataResponse(BaseModel):
    """Response model for structured data queries"""

    records: list[StructuredTicketData] = Field(
        ..., description="List of structured tickets"
    )
    total_count: int = Field(..., description="Total records available")
    limit: int = Field(..., description="Records limit applied")
    offset: int = Field(..., description="Records offset applied")
    has_more: bool = Field(
        ..., description="Whether more records are available"
    )
