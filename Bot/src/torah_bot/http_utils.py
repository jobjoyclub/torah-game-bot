#!/usr/bin/env python3
"""
HTTP utilities with improved error handling
"""
import httpx
import logging
from typing import Dict, Any, Optional
from .constants import HTTP_TIMEOUT, MAX_API_RETRIES, RETRY_DELAY_SECONDS
import asyncio

logger = logging.getLogger(__name__)

class HTTPError(Exception):
    """Custom HTTP error with status code"""
    def __init__(self, message: str, status_code: int = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

async def make_request_with_retry(
    method: str,
    url: str,
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = HTTP_TIMEOUT,
    max_retries: int = MAX_API_RETRIES
) -> Dict[str, Any]:
    """
    Make HTTP request with proper error handling and retries
    """
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                if method.upper() == 'POST':
                    response = await client.post(url, json=data, headers=headers)
                elif method.upper() == 'GET':
                    response = await client.get(url, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException:
            last_exception = HTTPError(f"Request timeout after {timeout}s", 408)
            logger.warning(f"⏰ Timeout on attempt {attempt + 1}/{max_retries}")
            
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code in [429, 500, 502, 503, 504]:  # Retry on these
                last_exception = HTTPError(f"HTTP {status_code}: {e.response.text}", status_code)
                logger.warning(f"🔄 Retryable error {status_code} on attempt {attempt + 1}/{max_retries}")
            else:
                # Don't retry on 4xx client errors (except 429)
                raise HTTPError(f"HTTP {status_code}: {e.response.text}", status_code)
                
        except httpx.NetworkError as e:
            last_exception = HTTPError(f"Network error: {str(e)}")
            logger.warning(f"🌐 Network error on attempt {attempt + 1}/{max_retries}")
            
        except Exception as e:
            last_exception = HTTPError(f"Unexpected error: {str(e)}")
            logger.error(f"❌ Unexpected error on attempt {attempt + 1}/{max_retries}: {e}")
            break  # Don't retry on unexpected errors
        
        # Wait before retrying (exponential backoff)
        if attempt < max_retries - 1:
            wait_time = RETRY_DELAY_SECONDS * (2 ** attempt)
            await asyncio.sleep(wait_time)
    
    # All retries failed
    if last_exception:
        raise last_exception
    else:
        raise HTTPError("Request failed after all retries")

async def post_json(url: str, data: Dict[str, Any], timeout: float = HTTP_TIMEOUT) -> Dict[str, Any]:
    """Simplified POST JSON request"""
    return await make_request_with_retry('POST', url, data, timeout=timeout)

async def get_json(url: str, timeout: float = HTTP_TIMEOUT) -> Dict[str, Any]:
    """Simplified GET JSON request"""
    return await make_request_with_retry('GET', url, timeout=timeout)