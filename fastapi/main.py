"""
FastAPI Application - Hub XP Token Extraction and Multi-Automation Platform
"""

import os

import uvicorn
from middleware.rate_limiting import rate_limit_middleware
from routes import automations, fixed_income, health, tokens
from utils.logging_config import setup_logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Setup logging
setup_logging(os.getenv("LOG_LEVEL", "INFO"))

# Create FastAPI instance
app = FastAPI(
    title="MenuAutomacoes API",
    description="API for Hub XP token extraction and multi-automation platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for security
# Allow origins based on environment
allowed_origins = [
    "http://localhost:3000",  # Frontend development
    "http://localhost:8080",  # Alternative frontend port
    "http://127.0.0.1:3000",  # Local development
    "http://127.0.0.1:8080",  # Alternative local port
]

# Add production origins if environment variable is set
production_origins = os.getenv("ALLOWED_ORIGINS")
if production_origins:
    allowed_origins.extend(production_origins.split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With",
    ],
)

# Add rate limiting middleware
app.middleware("http")(rate_limit_middleware)

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
        "health": "/api/health",
    }


def get_uvicorn_config():
    """Get uvicorn configuration based on environment"""
    environment = os.getenv("ENVIRONMENT", "development").lower()

    # Base configuration
    config = {
        "app": "main:app",
        "host": os.getenv("HOST", "0.0.0.0"),
        "port": int(os.getenv("PORT", "8000")),
    }

    if environment == "production":
        # Production configuration
        config.update(
            {
                "reload": False,
                "workers": int(os.getenv("WORKERS", "4")),
                "log_level": os.getenv("LOG_LEVEL", "warning").lower(),
                "access_log": False,  # Reduce logging overhead
                "server_header": False,  # Hide server information
                "date_header": False,  # Reduce response headers
            }
        )
    elif environment == "staging":
        # Staging configuration
        config.update(
            {
                "reload": False,
                "workers": int(os.getenv("WORKERS", "2")),
                "log_level": os.getenv("LOG_LEVEL", "info").lower(),
                "access_log": True,
            }
        )
    else:
        # Development configuration
        config.update(
            {
                "reload": True,
                "log_level": os.getenv("LOG_LEVEL", "debug").lower(),
                "access_log": True,
            }
        )

    return config


if __name__ == "__main__":
    config = get_uvicorn_config()
    uvicorn.run(**config)
