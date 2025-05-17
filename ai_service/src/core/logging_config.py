import logging
import sys
import os
from pathlib import Path

def setup_logging():
    """Setup logging configuration for the application."""
    # Get root logger
    root_logger = logging.getLogger()
    
    # Clear previous handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set log level
    log_level = logging.INFO
    root_logger.setLevel(log_level)
    
    # Log format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Create formatter
    formatter = logging.Formatter(log_format, date_format)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Logs dizinini oluştur
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    
    # Create file handler
    file_handler = logging.FileHandler(logs_dir / 'ai_service.log')
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Set level for third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    
    # Initial log message
    root_logger.info("Logging system started.")