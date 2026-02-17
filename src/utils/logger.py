"""
Logger configuration for RPA Lab.
Uses loguru for advanced logging capabilities.
"""
import sys
from pathlib import Path
from loguru import logger
from typing import Optional

from src.utils.config import config


def setup_logger() -> None:
    """Configure loguru logger with file and console handlers."""
    # Remove default handler
    logger.remove()

    # Ensure log directory exists
    log_path = config.log_path
    log_path.mkdir(parents=True, exist_ok=True)

    # Console handler — só adiciona se sys.stdout estiver disponível
    # (quando rodando como .exe sem console, sys.stdout é None)
    if sys.stdout is not None:
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=config.get('logging.level', 'INFO'),
            colorize=True
        )
    
    # File handler for all logs
    logger.add(
        log_path / "rpa_lab_{time:YYYY-MM-DD}.log",
        rotation=config.get('logging.max_file_size', '10 MB'),
        retention=config.get('logging.retention', '7 days'),
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        encoding="utf-8"
    )
    
    # Separate file for errors
    logger.add(
        log_path / "errors_{time:YYYY-MM-DD}.log",
        rotation="10 MB",
        retention="30 days",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}",
        encoding="utf-8"
    )
    
    logger.info("Logger initialized successfully")


def get_logger(name: Optional[str] = None):
    """Get a logger instance with optional name binding."""
    if name:
        return logger.bind(name=name)
    return logger


# Initialize logger on import
setup_logger()