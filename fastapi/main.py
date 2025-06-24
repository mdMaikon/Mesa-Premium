"""
FastAPI Application - Hub XP Token Extraction and Multi-Automation Platform
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from routes import tokens, health, automations, fixed_income
from utils.logging_config import setup_logging
import os

# Setup logging
setup_logging(os.getenv("LOG_LEVEL", "INFO"))

# Create FastAPI instance
app = FastAPI(
    title="MenuAutomacoes API",
    description="API for Hub XP token extraction and multi-automation platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for PHP integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(tokens.router, prefix="/api", tags=["tokens"])
app.include_router(automations.router, prefix="/api", tags=["automations"])
app.include_router(fixed_income.router, prefix="/api", tags=["fixed-income"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "MenuAutomacoes API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )