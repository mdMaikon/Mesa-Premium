"""
Logging configuration for FastAPI application
"""
import logging
import sys
from pathlib import Path

def setup_logging(log_level: str = "INFO"):
    """
    Setup application logging
    """
    # Create logs directory - use /app/logs in Docker or relative path otherwise
    if Path("/app").exists():
        # Running in Docker container
        log_dir = Path("/app/logs")
    else:
        # Running locally
        project_root = Path(__file__).parent.parent.parent
        log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Clear any existing handlers
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
    
    # Create file handler with explicit mode (only if we can write to logs)
    file_handler = None
    try:
        file_handler = logging.FileHandler(
            log_dir / "fastapi_app.log", 
            mode='a',  # append mode
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(logging.Formatter(log_format))
    except PermissionError:
        # If we can't write to file, just use console logging
        pass
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # Configure root logger
    root.setLevel(getattr(logging, log_level.upper()))
    if file_handler:
        root.addHandler(file_handler)
    root.addHandler(console_handler)
    
    # Configure specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully - file and console")