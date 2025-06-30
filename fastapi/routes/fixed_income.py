"""
Fixed Income API Routes
Provides endpoints for processing fixed income data from Hub XP
"""

import logging
from datetime import datetime

from pydantic import BaseModel
from services.fixed_income_exceptions import (
    APIConnectionError,
    TokenRetrievalError,
)
from services.fixed_income_service import FixedIncomeService
from utils.state_manager import get_state_manager

from fastapi import APIRouter, BackgroundTasks, HTTPException

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


# Thread-safe state manager instance
state_manager = get_state_manager()


async def process_fixed_income_background(process_id: str):
    """Background task to process fixed income data"""
    try:
        service = FixedIncomeService()
        result = await service.process_and_store_data()

        # Finish processing with result
        state_manager.finish_processing(result)

        logger.info(f"Background processing completed: {result}")

    except Exception as e:
        logger.error(f"Background processing failed: {e}")
        error_result = {
            "success": False,
            "message": "Background processing failed",
            "error": str(e),
        }
        state_manager.finish_processing(error_result)


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
        # Try to start processing
        process_id = f"fixed_income_{int(datetime.now().timestamp())}"

        if not state_manager.start_processing(process_id):
            return ProcessingResponse(
                success=False,
                message="Processing already in progress",
                error="Another processing operation is currently running",
            )

        # Start background processing
        background_tasks.add_task(process_fixed_income_background, process_id)

        return ProcessingResponse(
            success=True,
            message="Fixed income processing started in background",
        )

    except TokenRetrievalError as e:
        logger.error(f"Token retrieval failed: {e}")
        raise HTTPException(
            status_code=401, detail=f"Authentication failed: {str(e)}"
        ) from e
    except APIConnectionError as e:
        logger.error(f"API connection failed: {e}")
        raise HTTPException(
            status_code=503, detail=f"External service unavailable: {str(e)}"
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error starting fixed income processing: {e}")
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {str(e)}"
        ) from e


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
            error=result.get("error"),
        )

    except Exception as e:
        logger.error(f"Error in synchronous fixed income processing: {e}")
        raise HTTPException(
            status_code=500, detail=f"Processing failed: {str(e)}"
        ) from e


@router.get("/fixed-income/status")
async def get_processing_status():
    """
    Get current processing status

    Returns information about ongoing or completed processing operations
    """
    try:
        return state_manager.get_status()

    except Exception as e:
        logger.error(f"Error getting processing status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get status: {str(e)}"
        ) from e


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
            latest_maturity=stats.get("latest_maturity"),
        )

    except Exception as e:
        logger.error(f"Error getting fixed income stats: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get statistics: {str(e)}"
        ) from e


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
                "message": "All fixed income data cleared successfully",
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to clear data")

    except Exception as e:
        logger.error(f"Error clearing fixed income data: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to clear data: {str(e)}"
        ) from e


@router.get("/fixed-income/categories")
async def get_available_categories():
    """
    Get list of available fixed income categories

    Returns the categories that can be processed by the system
    """
    try:
        _ = FixedIncomeService()

        return {
            "categories": [
                {
                    "code": "CREDITOPRIVADO",
                    "name": "Crédito Privado",
                    "abbreviation": "CP",
                    "description": "Private credit fixed income securities",
                },
                {
                    "code": "BANCARIO",
                    "name": "Bancário",
                    "abbreviation": "EB",
                    "description": "Bank fixed income securities",
                },
                {
                    "code": "TPF",
                    "name": "Títulos Públicos Federais",
                    "abbreviation": "TPF",
                    "description": "Federal public securities",
                },
            ],
            "total_categories": 3,
        }

    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get categories: {str(e)}"
        ) from e
