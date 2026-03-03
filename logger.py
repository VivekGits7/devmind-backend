import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

from config import settings

# Create logs directory if not exists
LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)


def setup_logging(
    level: Optional[str] = None,
    log_format: Optional[str] = None,
) -> None:
    """Configure application-wide logging with file handlers."""
    if level is None:
        level = settings.LOG_LEVEL
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(console_handler)

    # App log file (all logs)
    app_handler = RotatingFileHandler(
        f"{LOGS_DIR}/app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(app_handler)

    # Error log file (errors only)
    error_handler = RotatingFileHandler(
        f"{LOGS_DIR}/error.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(error_handler)

    # Access log file (HTTP requests)
    access_logger = logging.getLogger("uvicorn.access")
    access_handler = RotatingFileHandler(
        f"{LOGS_DIR}/access.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
    )
    access_handler.setFormatter(logging.Formatter(log_format))
    access_logger.addHandler(access_handler)

    # Reduce noise from third-party loggers
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("asyncpg").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module."""
    return logging.getLogger(name)
