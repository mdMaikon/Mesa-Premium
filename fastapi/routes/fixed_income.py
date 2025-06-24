"""
Fixed Income API Routes
Provides endpoints for processing fixed income data from Hub XP
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
from pydantic import BaseModel
import logging
from datetime import datetime
from services.fixed_income_service import FixedIncomeService

logger = logging.getLogger(__name__)
router = APIRouter()

# Response models
class ProcessingResponse(BaseModel):
    """Response model for processing operations"""
    success: bool
    message: str
    records_processed: int = None
    categories_processed: list = None
    processing_date: str = None
    error: str = None

class StatsResponse(BaseModel):
    """Response model for statistics"""
    total_records: int = None
    unique_issuers: int = None
    unique_indexers: int = None
    last_update: str = None
    earliest_maturity: str = None
    latest_maturity: str = None
    error: str = None

# Background task storage for processing status
processing_status = {
    "is_processing": False,
    "last_result": None,
    "start_time": None
}

async def process_fixed_income_background():
    """Background task to process fixed income data"""
    global processing_status
    
    try:
        processing_status["is_processing"] = True
        processing_status["start_time"] = str(datetime.now())
        
        service = FixedIncomeService()
        result = await service.process_and_store_data()
        
        processing_status["last_result"] = result
        processing_status["is_processing"] = False
        
        logger.info(f"Background processing completed: {result}")
        
    except Exception as e:
        logger.error(f"Background processing failed: {e}")
        processing_status["last_result"] = {
            "success": False,
            "message": "Background processing failed",
            "error": str(e)
        }
        processing_status["is_processing"] = False

@router.post("/fixed-income/process", response_model=ProcessingResponse)
async def process_fixed_income_data(background_tasks: BackgroundTasks):
    """
    Process fixed income data from Hub XP
    
    This endpoint:
    - Retrieves a valid token from the database
    - Downloads data from Hub XP for all categories (CP, EB, TPF)
    - Applies filters and business rules
    - Stores processed data in the database
    
    Returns processing results with statistics
    """
    try:
        # Check if already processing
        if processing_status["is_processing"]:
            return ProcessingResponse(
                success=False,
                message="Processing already in progress",
                error="Another processing operation is currently running"
            )
        
        # Start background processing
        background_tasks.add_task(process_fixed_income_background)
        
        return ProcessingResponse(
            success=True,
            message="Fixed income processing started in background",
        )
        
    except Exception as e:
        logger.error(f"Error starting fixed income processing: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start processing: {str(e)}"
        )

@router.get("/fixed-income/process-sync", response_model=ProcessingResponse)
async def process_fixed_income_data_sync():
    """
    Process fixed income data synchronously (for testing/debugging)
    
    This endpoint processes data synchronously and waits for completion.
    Use with caution as it may timeout for large datasets.
    """
    try:
        service = FixedIncomeService()
        result = await service.process_and_store_data()
        
        return ProcessingResponse(
            success=result["success"],
            message=result["message"],
            records_processed=result.get("records_processed"),
            categories_processed=result.get("categories_processed"),
            processing_date=result.get("processing_date"),
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Error in synchronous fixed income processing: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )

@router.get("/fixed-income/status")
async def get_processing_status():
    """
    Get current processing status
    
    Returns information about ongoing or completed processing operations
    """
    try:
        return {
            "is_processing": processing_status["is_processing"],
            "start_time": processing_status["start_time"],
            "last_result": processing_status["last_result"]
        }
        
    except Exception as e:
        logger.error(f"Error getting processing status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get status: {str(e)}"
        )

@router.get("/fixed-income/stats", response_model=StatsResponse)
async def get_fixed_income_stats():
    """
    Get fixed income data statistics
    
    Returns statistics about the processed data including:
    - Total number of records
    - Number of unique issuers
    - Number of unique indexers
    - Last update timestamp
    - Maturity date range
    """
    try:
        service = FixedIncomeService()
        stats = await service.get_processing_stats()
        
        if "error" in stats:
            return StatsResponse(error=stats["error"])
        
        return StatsResponse(
            total_records=stats.get("total_records"),
            unique_issuers=stats.get("unique_issuers"),
            unique_indexers=stats.get("unique_indexers"),
            last_update=stats.get("last_update"),
            earliest_maturity=stats.get("earliest_maturity"),
            latest_maturity=stats.get("latest_maturity")
        )
        
    except Exception as e:
        logger.error(f"Error getting fixed income stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get statistics: {str(e)}"
        )

@router.delete("/fixed-income/clear")
async def clear_fixed_income_data():
    """
    Clear all fixed income data from database
    
    This endpoint removes all records from the fixed_income_data table.
    Use with caution as this operation cannot be undone.
    """
    try:
        service = FixedIncomeService()
        success = await service.clear_all_data()
        
        if success:
            return {
                "success": True,
                "message": "All fixed income data cleared successfully"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to clear data"
            )
            
    except Exception as e:
        logger.error(f"Error clearing fixed income data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear data: {str(e)}"
        )

@router.get("/fixed-income/categories")
async def get_available_categories():
    """
    Get list of available fixed income categories
    
    Returns the categories that can be processed by the system
    """
    try:
        service = FixedIncomeService()
        
        return {
            "categories": [
                {
                    "code": "CREDITOPRIVADO",
                    "name": "Crédito Privado",
                    "abbreviation": "CP",
                    "description": "Private credit fixed income securities"
                },
                {
                    "code": "BANCARIO", 
                    "name": "Bancário",
                    "abbreviation": "EB",
                    "description": "Bank fixed income securities"
                },
                {
                    "code": "TPF",
                    "name": "Títulos Públicos Federais", 
                    "abbreviation": "TPF",
                    "description": "Federal public securities"
                }
            ],
            "total_categories": 3
        }
        
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get categories: {str(e)}"
        )