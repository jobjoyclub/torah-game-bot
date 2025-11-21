#!/usr/bin/env python3
"""
Enhanced error handling with categorization and standardized responses
"""
from enum import Enum
from typing import Dict, Any, Optional
import traceback
import logging

class ErrorCategory(Enum):
    """Categorize errors for better handling and analysis"""
    USER_ERROR = "user_error"          # Invalid input, user mistakes
    SYSTEM_ERROR = "system_error"      # Internal system issues
    API_ERROR = "api_error"            # External API failures
    NETWORK_ERROR = "network_error"    # Connection, timeout issues
    VALIDATION_ERROR = "validation_error"  # Data validation failures
    PERMISSION_ERROR = "permission_error"  # Access control issues

class ErrorResponse:
    """Standardized error response format"""
    
    def __init__(
        self, 
        category: ErrorCategory,
        code: str,
        message: str,
        user_message: str,
        details: Optional[Dict[str, Any]] = None,
        retryable: bool = False
    ):
        self.category = category
        self.code = code
        self.message = message  # Technical message for logs
        self.user_message = user_message  # User-friendly message
        self.details = details or {}
        self.retryable = retryable
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON responses"""
        return {
            "error": {
                "category": self.category.value,
                "code": self.code,
                "message": self.message,
                "user_message": self.user_message,
                "details": self.details,
                "retryable": self.retryable
            }
        }
    
    def log_error(self, logger: logging.Logger, **context):
        """Log error with appropriate level and context"""
        log_level = logging.WARNING if self.category == ErrorCategory.USER_ERROR else logging.ERROR
        
        extra_context = {
            "error_category": self.category.value,
            "error_code": self.code,
            "retryable": self.retryable,
            **context
        }
        
        if hasattr(logger, '_log'):
            logger._log(log_level, self.message, (), extra=extra_context)
        else:
            logger.log(log_level, self.message, extra=extra_context)

class ErrorHandlerRegistry:
    """Registry of predefined error responses"""
    
    # Common error responses
    ERRORS = {
        # User Errors
        "INVALID_INPUT": ErrorResponse(
            ErrorCategory.USER_ERROR,
            "INVALID_INPUT",
            "Invalid user input provided",
            "Please check your input and try again",
            retryable=True
        ),
        "USER_NOT_FOUND": ErrorResponse(
            ErrorCategory.USER_ERROR,
            "USER_NOT_FOUND", 
            "User not found in system",
            "We couldn't find your account. Please try again",
            retryable=True
        ),
        
        # System Errors
        "DATABASE_ERROR": ErrorResponse(
            ErrorCategory.SYSTEM_ERROR,
            "DATABASE_ERROR",
            "Database operation failed",
            "Sorry, something went wrong. Please try again later",
            retryable=True
        ),
        "INTERNAL_ERROR": ErrorResponse(
            ErrorCategory.SYSTEM_ERROR,
            "INTERNAL_ERROR", 
            "Internal system error occurred",
            "Sorry, something went wrong. Please try again later",
            retryable=True
        ),
        
        # API Errors
        "OPENAI_ERROR": ErrorResponse(
            ErrorCategory.API_ERROR,
            "OPENAI_ERROR",
            "OpenAI API request failed",
            "AI service is temporarily unavailable. Please try again",
            retryable=True
        ),
        "TELEGRAM_ERROR": ErrorResponse(
            ErrorCategory.API_ERROR,
            "TELEGRAM_ERROR",
            "Telegram API request failed", 
            "Message delivery failed. Please try again",
            retryable=True
        ),
        
        # Network Errors
        "TIMEOUT_ERROR": ErrorResponse(
            ErrorCategory.NETWORK_ERROR,
            "TIMEOUT_ERROR",
            "Request timeout occurred",
            "Request took too long. Please try again",
            retryable=True
        ),
        "CONNECTION_ERROR": ErrorResponse(
            ErrorCategory.NETWORK_ERROR,
            "CONNECTION_ERROR",
            "Network connection failed",
            "Connection problem. Please check your internet and try again",
            retryable=True
        ),
        
        # Validation Errors
        "INVALID_FORMAT": ErrorResponse(
            ErrorCategory.VALIDATION_ERROR,
            "INVALID_FORMAT",
            "Data format validation failed",
            "Invalid format. Please check your input",
            retryable=True
        ),
        
        # Permission Errors
        "UNAUTHORIZED": ErrorResponse(
            ErrorCategory.PERMISSION_ERROR,
            "UNAUTHORIZED",
            "User not authorized for this operation",
            "You don't have permission to perform this action",
            retryable=False
        )
    }
    
    @classmethod
    def get_error(cls, error_code: str) -> Optional[ErrorResponse]:
        """Get predefined error response by code"""
        return cls.ERRORS.get(error_code)
    
    @classmethod
    def create_custom_error(
        cls,
        category: ErrorCategory,
        code: str,
        message: str,
        user_message: str,
        **kwargs
    ) -> ErrorResponse:
        """Create custom error response"""
        return ErrorResponse(category, code, message, user_message, **kwargs)

def handle_exception(
    exception: Exception,
    operation: str = "unknown",
    user_id: Optional[int] = None,
    logger: Optional[logging.Logger] = None
) -> ErrorResponse:
    """
    Convert Python exception to standardized error response
    """
    import httpx
    
    # Categorize based on exception type
    if isinstance(exception, (ValueError, TypeError)):
        error = ErrorHandlerRegistry.get_error("INVALID_INPUT")
    elif isinstance(exception, httpx.TimeoutException):
        error = ErrorHandlerRegistry.get_error("TIMEOUT_ERROR") 
    elif isinstance(exception, (httpx.ConnectError, httpx.NetworkError)):
        error = ErrorHandlerRegistry.get_error("CONNECTION_ERROR")
    elif isinstance(exception, httpx.HTTPStatusError):
        if exception.response.status_code == 401:
            error = ErrorHandlerRegistry.get_error("UNAUTHORIZED")
        else:
            error = ErrorHandlerRegistry.get_error("API_ERROR")
    else:
        error = ErrorHandlerRegistry.get_error("INTERNAL_ERROR")
    
    # Add exception details
    if error:
        error.details.update({
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "operation": operation,
            "traceback": traceback.format_exc() if logger else None
        })
        
        # Log the error with context
        if logger:
            context = {"operation": operation}
            if user_id:
                context["user_id"] = str(user_id)
            error.log_error(logger, **context)
    
    # Ensure we always return an ErrorResponse  
    if error is not None:
        return error
    
    # Fallback if predefined error is not found
    fallback_error = ErrorHandlerRegistry.get_error("INTERNAL_ERROR")
    if fallback_error is not None:
        return fallback_error
    
    # Ultimate fallback
    return ErrorResponse(
        ErrorCategory.SYSTEM_ERROR,
        "UNKNOWN_ERROR",
        f"Unknown error in {operation}: {str(exception)}",
        "An unexpected error occurred. Please try again",
        retryable=True
    )

# Convenience functions
def log_error_with_context(
    logger: logging.Logger,
    error_code: str,
    operation: str,
    user_id: Optional[int] = None,
    **extra_context
):
    """Quick function to log predefined errors with context"""
    error = ErrorHandlerRegistry.get_error(error_code)
    if error:
        context = {"operation": operation, **extra_context}
        if user_id:
            context["user_id"] = str(user_id)
        error.log_error(logger, **context)