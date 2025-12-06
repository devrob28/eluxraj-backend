import logging
import sys
import json
from datetime import datetime
from typing import Any
from pathlib import Path

# Create logs directory
Path("logs").mkdir(exist_ok=True)

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "endpoint"):
            log_data["endpoint"] = record.endpoint
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        
        # Add exception info
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

def setup_logging(debug: bool = False) -> logging.Logger:
    """Configure application logging"""
    
    level = logging.DEBUG if debug else logging.INFO
    
    # Root logger
    logger = logging.getLogger("eluxraj")
    logger.setLevel(level)
    
    # Console handler (human readable in dev, JSON in prod)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    if debug:
        console_format = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
        )
    else:
        console_format = JSONFormatter()
    
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler (always JSON)
    file_handler = logging.FileHandler("logs/app.log")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.FileHandler("logs/error.log")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    logger.addHandler(error_handler)
    
    return logger

# Create logger instance
logger = setup_logging()
