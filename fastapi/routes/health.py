"""
Health check endpoints
"""
from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
import mysql.connector
from database.connection import get_database_connection

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
        conn = get_database_connection()
        if conn and conn.is_connected():
            db_status = "connected"
            conn.close()
        else:
            db_status = "disconnected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return HealthResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        timestamp=datetime.now().isoformat(),
        database=db_status,
        version="1.0.0"
    )