"""
Structured Data API Routes
REST endpoints for structured financial operations following project standards.
"""

from typing import Any

from models.structured_data import (
    StructuredDataResponse,
    StructuredProcessingResponse,
    StructuredStatsResponse,
    StructuredStatusResponse,
    StructuredTicketRequest,
)
from services.structured_exceptions import (
    ApiRequestError,
    DatabaseOperationError,
    TokenRetrievalError,
)
from services.structured_service import StructuredService
from utils.log_sanitizer import get_sanitized_logger
from utils.state_manager import StateManager

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

logger = get_sanitized_logger(__name__)
router = APIRouter(prefix="/api/structured", tags=["Produtos Estruturados"])

# State manager for tracking processing status
state_manager = StateManager()


async def background_processing(data_inicio: str, data_fim: str) -> None:
    """Background task for processing structured data"""
    try:
        state_manager.set_state("processing_status", "running")
        state_manager.set_state("last_processing_date", data_inicio)

        service = StructuredService()
        result = await service.process_and_store_data(data_inicio, data_fim)

        state_manager.set_state("processing_status", "completed")
        state_manager.set_state("last_processing_result", result)
        logger.info(f"Background processing completed: {result}")

    except Exception as e:
        state_manager.set_state("processing_status", "failed")
        state_manager.set_state("last_processing_error", str(e))
        logger.error(f"Background processing failed: {e}")


@router.post(
    "/process",
    response_model=StructuredProcessingResponse,
    summary="Process structured data asynchronously",
    description="Fetch and process structured tickets from Hub XP for a given period (async)",
)
async def process_structured_data_async(
    request: StructuredTicketRequest, background_tasks: BackgroundTasks
) -> StructuredProcessingResponse:
    """
    Process structured data asynchronously in background

    This endpoint starts processing in background and returns immediately.
    Use /status endpoint to check processing progress.
    """
    try:
        # Check if already processing
        current_status = state_manager.get_state("processing_status")
        if current_status == "running":
            raise HTTPException(
                status_code=409,
                detail="Processing already in progress. Please wait for completion.",
            )

        # Start background processing
        background_tasks.add_task(
            background_processing, request.data_inicio, request.data_fim
        )

        return StructuredProcessingResponse(
            success=True,
            message="Processing started in background",
            processing_date=None,
            period=f"{request.data_inicio} to {request.data_fim}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting async processing: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start processing: {str(e)}"
        ) from e


@router.get(
    "/process-sync",
    response_model=StructuredProcessingResponse,
    summary="Process structured data synchronously",
    description="Fetch and process structured tickets from Hub XP for a given period (sync)",
)
async def process_structured_data_sync(
    data_inicio: str = Query(
        ..., description="Start date (YYYY-MM-DDTHH:MM:SS)"
    ),
    data_fim: str = Query(..., description="End date (YYYY-MM-DDTHH:MM:SS)"),
) -> StructuredProcessingResponse:
    """
    Process structured data synchronously

    This endpoint processes data and waits for completion before returning.
    Use for smaller date ranges or when immediate results are needed.
    """
    try:
        service = StructuredService()
        result = await service.process_and_store_data(data_inicio, data_fim)

        if result["success"]:
            return StructuredProcessingResponse(
                success=True,
                message=result["message"],
                records_processed=result.get("records_processed"),
                new_records=result.get("new_records"),
                updated_records=result.get("updated_records"),
                processing_date=result.get("processing_date"),
                period=result.get("period"),
            )
        else:
            return StructuredProcessingResponse(
                success=False,
                message=result["message"],
                error=result.get("error"),
            )

    except TokenRetrievalError as e:
        logger.error(f"Token retrieval error: {e}")
        raise HTTPException(
            status_code=401,
            detail="Unable to retrieve valid authentication token",
        ) from e
    except ApiRequestError as e:
        logger.error(f"API request error: {e}")
        raise HTTPException(
            status_code=502, detail="Failed to communicate with Hub XP API"
        ) from e
    except DatabaseOperationError as e:
        logger.error(f"Database operation error: {e}")
        raise HTTPException(
            status_code=500, detail="Database operation failed"
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error in sync processing: {e}")
        raise HTTPException(
            status_code=500, detail=f"Processing failed: {str(e)}"
        ) from e


@router.get(
    "/status",
    response_model=StructuredStatusResponse,
    summary="Get processing status",
    description="Check the status of current or last processing operation",
)
async def get_processing_status() -> StructuredStatusResponse:
    """Get current processing status and last processing information"""
    try:
        processing_status = state_manager.get_state(
            "processing_status", "idle"
        )
        last_processing_date = state_manager.get_state("last_processing_date")
        last_result = state_manager.get_state("last_processing_result")
        last_error = state_manager.get_state("last_processing_error")

        # Get current records count
        service = StructuredService()
        stats = await service.get_processing_stats()
        records_count = (
            stats.get("total_records", 0) if "error" not in stats else 0
        )

        last_status = "completed"
        if last_error:
            last_status = "failed"
        elif last_result and not last_result.get("success", True):
            last_status = "failed"

        return StructuredStatusResponse(
            is_processing=(processing_status == "running"),
            last_processing_date=last_processing_date,
            last_processing_status=last_status,
            records_count=records_count,
        )

    except Exception as e:
        logger.error(f"Error getting processing status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get status: {str(e)}"
        ) from e


@router.get(
    "/stats",
    response_model=StructuredStatsResponse,
    summary="Get processing statistics",
    description="Get comprehensive statistics about processed structured data",
)
async def get_processing_stats() -> StructuredStatsResponse:
    """Get detailed statistics about processed structured data"""
    try:
        service = StructuredService()
        stats = await service.get_processing_stats()

        if "error" in stats:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve stats: {stats['error']}",
            )

        return StructuredStatsResponse(
            total_records=stats["total_records"],
            unique_clients=stats["unique_clients"],
            unique_assets=stats["unique_assets"],
            total_commission=stats.get("total_commission"),
            last_update=stats.get("last_update"),
            earliest_ticket=stats.get("earliest_ticket"),
            latest_ticket=stats.get("latest_ticket"),
            status_breakdown=stats.get("status_breakdown"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting processing stats: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get statistics: {str(e)}"
        ) from e


@router.get(
    "/data",
    response_model=StructuredDataResponse,
    summary="Query structured data",
    description="Retrieve structured data with filtering and pagination",
)
async def get_structured_data(
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum records to return"
    ),
    offset: int = Query(0, ge=0, description="Records to skip"),
    cliente: int = Query(None, description="Filter by client code"),
    ativo: str = Query(None, description="Filter by asset name"),
    status: str = Query(None, description="Filter by status"),
    data_inicio: str = Query(
        None, description="Filter from date (YYYY-MM-DD)"
    ),
    data_fim: str = Query(None, description="Filter to date (YYYY-MM-DD)"),
) -> StructuredDataResponse:
    """Query structured data with filtering and pagination support"""
    try:
        service = StructuredService()
        result = await service.get_structured_data(
            limit=limit,
            offset=offset,
            cliente=cliente,
            ativo=ativo,
            status=status,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        if "error" in result:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve data: {result['error']}",
            )

        return StructuredDataResponse(
            records=result["records"],
            total_count=result["total_count"],
            limit=result["limit"],
            offset=result["offset"],
            has_more=result["has_more"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting structured data: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve data: {str(e)}"
        ) from e


@router.delete(
    "/clear",
    response_model=dict[str, Any],
    summary="Clear all structured data",
    description="Remove all structured data from the database",
)
async def clear_structured_data() -> dict[str, Any]:
    """Clear all structured data from database"""
    try:
        service = StructuredService()
        success = await service.clear_all_data()

        if success:
            return {
                "success": True,
                "message": "All structured data cleared successfully",
            }
        else:
            raise HTTPException(
                status_code=500, detail="Failed to clear structured data"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing structured data: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to clear data: {str(e)}"
        ) from e


@router.get(
    "/categories",
    response_model=dict[str, Any],
    summary="Get available categories",
    description="Get list of available structured data categories and operations",
)
async def get_structured_categories() -> dict[str, Any]:
    """Get available structured data categories"""
    return {
        "categories": [
            {
                "name": "structured_operations",
                "description": "Structured financial operations from Hub XP",
                "endpoint": "/api/structured/process",
            }
        ],
        "supported_operations": [
            "fetch_tickets",
            "process_data",
            "upsert_records",
        ],
        "api_version": "1.0.0",
    }
