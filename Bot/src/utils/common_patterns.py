#!/usr/bin/env python3
"""
Common patterns and utilities to reduce code duplication
"""
import httpx
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timezone, timedelta
from functools import wraps
import asyncio

class AsyncHTTPClient:
    """Centralized HTTP client with consistent error handling"""
    
    @staticmethod
    async def post_json(url: str, data: Dict[str, Any], timeout: float = 30.0) -> Dict[str, Any]:
        """Standard POST request with JSON"""
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=data)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            raise Exception(f"Request timeout to {url}")
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")

class TimezoneHelper:
    """Centralized timezone operations"""
    
    @staticmethod
    def get_moscow_time() -> datetime:
        """Get current Moscow time"""
        moscow_tz = timezone(timedelta(hours=3))
        return datetime.now(moscow_tz)
    
    @staticmethod
    def get_moscow_hour() -> int:
        """Get current Moscow hour"""
        return TimezoneHelper.get_moscow_time().hour

def async_error_handler(operation_name: str, fallback_result: Any = None):
    """Decorator for consistent async error handling"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger = logging.getLogger(func.__module__)
                logger.error(f"❌ {operation_name} failed: {e}")
                if fallback_result is not None:
                    return fallback_result
                return {"success": False, "error": str(e)}
        return wrapper
    return decorator

def setup_logger(name: str) -> logging.Logger:
    """Standard logger setup"""
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(name)