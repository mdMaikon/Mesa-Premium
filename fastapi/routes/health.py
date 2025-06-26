"""
Health check endpoints
"""

from datetime import datetime

from database.connection import get_database_connection
from pydantic import BaseModel

from fastapi import APIRouter

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    database: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""

    # Test database connection
    try:
        with get_database_connection() as conn:
            if conn and conn.is_connected():
                db_status = "connected"
            else:
                db_status = "disconnected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        timestamp=datetime.now().isoformat(),
        database=db_status,
        version="1.0.0",
    )
