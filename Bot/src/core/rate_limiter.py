#!/usr/bin/env python3
"""
Rate limiting middleware for API endpoints
Protects against abuse and DDoS attacks
"""
import asyncio
import time
import logging
from collections import defaultdict, deque
from typing import Dict, Optional, Tuple
from fastapi import Request, HTTPException
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RateLimitRule:
    """Rate limit configuration"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_limit: int = 10  # Maximum requests in burst window (10 seconds)
    
class RateLimiter:
    """In-memory rate limiter with sliding window algorithm"""
    
    def __init__(self):
        # Track requests per IP per minute  
        self._minute_windows: Dict[str, deque] = defaultdict(deque)
        # Track requests per IP per hour
        self._hour_windows: Dict[str, deque] = defaultdict(deque)
        # Track burst requests (last 10 seconds)
        self._burst_windows: Dict[str, deque] = defaultdict(deque)
        # Lock for thread safety
        self._lock = asyncio.Lock()
        # Default rules
        self.default_rule = RateLimitRule()
        # Custom rules per endpoint
        self.endpoint_rules: Dict[str, RateLimitRule] = {}
        
    def add_endpoint_rule(self, endpoint_pattern: str, rule: RateLimitRule):
        """Add custom rate limit rule for specific endpoint"""
        self.endpoint_rules[endpoint_pattern] = rule
        logger.info(f"🚦 Rate limit rule added for {endpoint_pattern}: {rule.requests_per_minute}/min")
        
    def get_client_identifier(self, request: Request) -> str:
        """Get client identifier for rate limiting (IP + User-Agent hash)"""
        # Get client IP
        client_ip = "unknown"
        
        # Check proxy headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            real_ip = request.headers.get("X-Real-IP")
            if real_ip:
                client_ip = real_ip
            elif hasattr(request, 'client') and request.client:
                client_ip = request.client.host
                
        # Add user agent hash for additional uniqueness
        user_agent = request.headers.get("User-Agent", "")
        ua_hash = str(hash(user_agent))[:8] if user_agent else "none"
        
        return f"{client_ip}:{ua_hash}"
    
    def get_rule_for_endpoint(self, path: str) -> RateLimitRule:
        """Get rate limit rule for specific endpoint"""
        for pattern, rule in self.endpoint_rules.items():
            if pattern in path:
                return rule
        return self.default_rule
    
    async def is_allowed(self, request: Request) -> Tuple[bool, Optional[str]]:
        """
        Check if request is allowed under rate limits
        Returns (allowed, error_message)
        """
        async with self._lock:
            client_id = self.get_client_identifier(request)
            rule = self.get_rule_for_endpoint(request.url.path)
            current_time = time.time()
            
            # Clean old entries
            await self._cleanup_old_entries(client_id, current_time)
            
            # Check burst limit (last 10 seconds)
            burst_count = len(self._burst_windows[client_id])
            if burst_count >= rule.burst_limit:
                logger.warning(f"🚦 Burst limit exceeded for {client_id}: {burst_count}/{rule.burst_limit}")
                return False, f"Too many requests in short period. Limit: {rule.burst_limit} per 10 seconds"
            
            # Check minute limit
            minute_count = len(self._minute_windows[client_id])
            if minute_count >= rule.requests_per_minute:
                logger.warning(f"🚦 Minute limit exceeded for {client_id}: {minute_count}/{rule.requests_per_minute}")
                return False, f"Too many requests per minute. Limit: {rule.requests_per_minute}"
                
            # Check hour limit
            hour_count = len(self._hour_windows[client_id])
            if hour_count >= rule.requests_per_hour:
                logger.warning(f"🚦 Hour limit exceeded for {client_id}: {hour_count}/{rule.requests_per_hour}")
                return False, f"Too many requests per hour. Limit: {rule.requests_per_hour}"
            
            # Record this request
            self._burst_windows[client_id].append(current_time)
            self._minute_windows[client_id].append(current_time)
            self._hour_windows[client_id].append(current_time)
            
            return True, None
    
    async def _cleanup_old_entries(self, client_id: str, current_time: float):
        """Remove expired entries from tracking windows"""
        # Clean burst window (10 seconds)
        burst_cutoff = current_time - 10
        while (self._burst_windows[client_id] and 
               self._burst_windows[client_id][0] < burst_cutoff):
            self._burst_windows[client_id].popleft()
            
        # Clean minute window (60 seconds)
        minute_cutoff = current_time - 60
        while (self._minute_windows[client_id] and 
               self._minute_windows[client_id][0] < minute_cutoff):
            self._minute_windows[client_id].popleft()
            
        # Clean hour window (3600 seconds)
        hour_cutoff = current_time - 3600
        while (self._hour_windows[client_id] and 
               self._hour_windows[client_id][0] < hour_cutoff):
            self._hour_windows[client_id].popleft()
    
    async def cleanup_inactive_clients(self):
        """Periodic cleanup of inactive client data"""
        current_time = time.time()
        hour_cutoff = current_time - 3600
        
        async with self._lock:
            # Find inactive clients (no requests in last hour)
            inactive_clients = []
            for client_id in list(self._hour_windows.keys()):
                if not self._hour_windows[client_id]:
                    inactive_clients.append(client_id)
                elif self._hour_windows[client_id][-1] < hour_cutoff:
                    inactive_clients.append(client_id)
            
            # Remove inactive clients
            for client_id in inactive_clients:
                self._burst_windows.pop(client_id, None)
                self._minute_windows.pop(client_id, None) 
                self._hour_windows.pop(client_id, None)
                
            if inactive_clients:
                logger.info(f"🧹 Cleaned up {len(inactive_clients)} inactive rate limit clients")

# Global rate limiter instance
rate_limiter = RateLimiter()

# Configure strict limits for admin endpoints
admin_rule = RateLimitRule(
    requests_per_minute=10,  # Very restrictive for admin endpoints
    requests_per_hour=100,
    burst_limit=3
)

# Configure moderate limits for scheduler endpoints  
scheduler_rule = RateLimitRule(
    requests_per_minute=20,
    requests_per_hour=200,
    burst_limit=5
)

# Configure limits for webhook (should be mostly Telegram traffic)
webhook_rule = RateLimitRule(
    requests_per_minute=120,  # Higher for webhook
    requests_per_hour=2000,
    burst_limit=20
)

# Add endpoint-specific rules
rate_limiter.add_endpoint_rule("/api/manual_broadcast", admin_rule)
rate_limiter.add_endpoint_rule("/api/scheduler", scheduler_rule)
rate_limiter.add_endpoint_rule("/webhook", webhook_rule)

async def rate_limit_middleware(request: Request):
    """
    FastAPI middleware function for rate limiting
    Raises HTTPException if rate limit is exceeded
    """
    allowed, error_message = await rate_limiter.is_allowed(request)
    
    if not allowed:
        client_id = rate_limiter.get_client_identifier(request)
        logger.warning(f"🚦 Rate limit exceeded for {client_id} on {request.url.path}: {error_message}")
        
        # Log security event
        from src.core.telegram_security import log_security_event
        log_security_event("RATE_LIMIT_EXCEEDED", request, error_message or "Rate limit exceeded")
        
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": error_message,
                "retry_after": 60  # Suggest retry after 60 seconds
            }
        )

# Background cleanup task
async def start_rate_limiter_cleanup():
    """Start background task for cleaning up inactive rate limit data"""
    while True:
        try:
            await asyncio.sleep(300)  # Clean up every 5 minutes
            await rate_limiter.cleanup_inactive_clients()
        except Exception as e:
            logger.error(f"🚦 Rate limiter cleanup error: {e}")