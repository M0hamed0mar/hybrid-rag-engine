"""Structured logging configuration"""
import sys
from pathlib import Path
from loguru import logger

# Remove default handler
logger.remove()

# Console handler with colors
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True
)

# File handler for errors
error_log = Path("data/logs/error.log")
error_log.parent.mkdir(parents=True, exist_ok=True)

logger.add(
    error_log,
    rotation="10 MB",
    retention="7 days",
    level="ERROR",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)

# File handler for all logs
app_log = Path("data/logs/app.log")
logger.add(
    app_log,
    rotation="50 MB",
    retention="14 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)