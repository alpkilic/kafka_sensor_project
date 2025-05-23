import logging
import sys
from datetime import datetime
import os

def get_logger(name: str) -> logging.Logger:
    """Create a logger instance with consistent formatting"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)
        
        # File handler
        log_file = f'logs/{name}_{datetime.now().strftime("%Y%m%d")}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Prevent logging from propagating to the root logger
        logger.propagate = False
    
    return logger