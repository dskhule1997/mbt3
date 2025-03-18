"""
Logger utility for the Solana Trading Bot.
Sets up logging configuration for the entire application.
"""
import os
import sys
from datetime import datetime
from loguru import logger

def setup_logger(log_level=None):
    """
    Configure the logger for the application.
    Sets up log format, log level, and log file.
    
    Args:
        log_level: Optional log level override. If None, uses LOG_LEVEL from environment or defaults to INFO.
    
    Returns:
        Configured logger instance
    """
    # Clear any existing handlers
    logger.remove()
    
    # Get log level from environment or parameter
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f"solana_bot_{timestamp}.log")
    
    # Configure console logging
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level
    )
    
    # Configure file logging
    logger.add(
        log_file,
        rotation="10 MB",
        retention="1 week",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG"  # Always log everything to file
    )
    
    # Add error log file for critical errors only
    error_log_file = os.path.join(logs_dir, f"solana_bot_errors_{timestamp}.log")
    logger.add(
        error_log_file,
        rotation="5 MB",
        retention="1 month",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        filter=lambda record: record["level"].name in ["ERROR", "CRITICAL"]
    )
    
    logger.info(f"Logger initialized with level: {log_level}")
    logger.info(f"Log files: {log_file} and {error_log_file}")
    
    return logger

def get_component_logger(component_name):
    """
    Get a logger instance for a specific component.
    
    Args:
        component_name: Name of the component
    
    Returns:
        Logger instance with component context
    """
    return logger.bind(component=component_name)
