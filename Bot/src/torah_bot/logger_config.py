#!/usr/bin/env python3
"""
Centralized logging configuration for Torah Bot
Enhanced with structured logging and context management
"""
import logging
import os
import json
import time
from typing import Optional, Dict, Any
from contextlib import contextmanager

class StructuredFormatter(logging.Formatter):
    """JSON-based structured formatter for better log analysis"""
    
    def format(self, record):
        # Base log structure
        log_entry = {
            "timestamp": time.time(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add context if available
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = getattr(record, 'user_id', None)
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = getattr(record, 'request_id', None)
        if hasattr(record, 'operation'):
            log_entry["operation"] = getattr(record, 'operation', None)
        if hasattr(record, 'duration_ms'):
            log_entry["duration_ms"] = getattr(record, 'duration_ms', None)
            
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry, ensure_ascii=False)

class TorahBotLogger:
    """Centralized logger setup with context management"""
    
    _loggers = {}  # Cache loggers to avoid recreation
    
    @classmethod
    def get_logger(cls, name: str, level: Optional[str] = None) -> logging.Logger:
        """Get or create logger with consistent configuration"""
        if name in cls._loggers:
            return cls._loggers[name]
        
        # Create logger
        logger = logging.getLogger(name)
        
        # Set level from environment or parameter
        log_level = level or os.environ.get("LOG_LEVEL", "INFO")
        logger.setLevel(getattr(logging, log_level.upper()))
        
        # Avoid duplicate handlers
        if not logger.handlers:
            # Create handler
            handler = logging.StreamHandler()
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            
            # Add handler to logger
            logger.addHandler(handler)
        
        # Cache and return
        cls._loggers[name] = logger
        return logger
    
    @classmethod
    def log_with_context(cls, logger_name: str, level: str, message: str, **context):
        """Log message with additional context fields"""
        logger = cls.get_logger(logger_name)
        
        # Create a log record with context
        if hasattr(logger, '_log'):
            logger._log(getattr(logging, level.upper()), message, (), extra=context)
        else:
            # Fallback for older Python versions
            getattr(logger, level.lower())(message, extra=context)
    
    @classmethod
    @contextmanager
    def timed_operation(cls, logger_name: str, operation: str, **context):
        """Context manager for timing operations"""
        logger = cls.get_logger(logger_name)
        start_time = time.time()
        
        try:
            cls.log_with_context(logger_name, "INFO", f"🚀 Starting {operation}", operation=operation, **context)
            yield
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            cls.log_with_context(
                logger_name, "ERROR", 
                f"❌ {operation} failed: {e}", 
                operation=operation, 
                duration_ms=duration_ms,
                **context
            )
            raise
        else:
            duration_ms = (time.time() - start_time) * 1000
            cls.log_with_context(
                logger_name, "INFO", 
                f"✅ {operation} completed", 
                operation=operation, 
                duration_ms=duration_ms,
                **context
            )
    
    @classmethod
    def setup_production_logging(cls):
        """Setup production logging with file output"""
        # Setup file handler for production
        if not os.path.exists("logs"):
            os.makedirs("logs")
            
        file_handler = logging.FileHandler("logs/torah_bot.log")
        file_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # Add to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)

# Convenience function
def get_logger(name: str) -> logging.Logger:
    """Get logger for current module"""
    return TorahBotLogger.get_logger(name)