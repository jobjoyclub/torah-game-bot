#!/usr/bin/env python3
"""
Telegram webhook security utilities
Handles webhook authentication and IP validation
"""
import hashlib
import hmac
import ipaddress
import logging
from typing import Optional, List
from fastapi import Request

logger = logging.getLogger(__name__)

# Telegram server IP ranges (as of 2025)
TELEGRAM_IP_RANGES = [
    ipaddress.IPv4Network("149.154.160.0/20"),
    ipaddress.IPv4Network("91.108.4.0/22"),
    ipaddress.IPv4Network("91.108.8.0/22"),
    ipaddress.IPv4Network("91.108.12.0/22"),
    ipaddress.IPv4Network("91.108.16.0/22"),
    ipaddress.IPv4Network("91.108.56.0/22"),
    ipaddress.IPv4Network("95.161.64.0/20"),
    ipaddress.IPv6Network("2001:67c:4e8::/48"),
    ipaddress.IPv6Network("2001:b28:f23d::/48"),
    ipaddress.IPv6Network("2001:b28:f23f::/48"),
]

class TelegramWebhookSecurityError(Exception):
    """Custom exception for webhook security errors"""
    pass

def verify_telegram_secret_token(request: Request, expected_secret: str) -> bool:
    """
    Verify Telegram webhook using X-Telegram-Bot-Api-Secret-Token header
    This is the recommended method for webhook authentication
    """
    if not expected_secret:
        logger.error("🔒 No secret token configured for webhook verification")
        return False
    
    received_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if not received_token:
        logger.warning("🔒 Missing X-Telegram-Bot-Api-Secret-Token header")
        return False
    
    # Use constant-time comparison to prevent timing attacks
    is_valid = hmac.compare_digest(expected_secret, received_token)
    
    if not is_valid:
        logger.warning("🔒 Invalid X-Telegram-Bot-Api-Secret-Token")
    else:
        logger.debug("✅ Telegram secret token verified")
    
    return is_valid

def verify_telegram_ip(request: Request) -> bool:
    """
    Verify request comes from Telegram IP ranges
    Fallback method when secret token is not available
    """
    # Get client IP, considering proxy headers
    client_ip = None
    
    # Check common proxy headers
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.headers.get("X-Real-IP")
    
    # Fallback to direct connection
    if not client_ip and hasattr(request, 'client') and request.client:
        client_ip = request.client.host
    
    if not client_ip:
        logger.warning("🔒 Could not determine client IP for verification")
        return False
    
    try:
        ip_address = ipaddress.ip_address(client_ip)
        
        # Check if IP is in any Telegram range
        for ip_range in TELEGRAM_IP_RANGES:
            if ip_address in ip_range:
                logger.debug(f"✅ Valid Telegram IP: {client_ip}")
                return True
        
        logger.warning(f"🔒 Invalid source IP: {client_ip} (not from Telegram)")
        return False
        
    except ValueError:
        logger.warning(f"🔒 Invalid IP address format: {client_ip}")
        return False

def verify_telegram_webhook(request: Request, secret_token: Optional[str] = None) -> bool:
    """
    Main webhook verification function
    Uses secret token if available, falls back to IP verification
    """
    try:
        # Primary method: secret token verification
        if secret_token:
            return verify_telegram_secret_token(request, secret_token)
        
        # Fallback method: IP range verification  
        logger.info("🔒 No secret token available, using IP verification")
        return verify_telegram_ip(request)
        
    except Exception as e:
        logger.error(f"🔒 Webhook verification error: {e}")
        return False

def generate_webhook_secret_token() -> str:
    """Generate a secure random token for webhook setup"""
    import secrets
    import string
    
    # Generate 32-character random token
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(32))

def log_security_event(event_type: str, request: Request, details: str = ""):
    """Log security-related events for audit purposes"""
    client_ip = "unknown"
    
    # Get client IP for logging
    if hasattr(request, 'client') and request.client:
        client_ip = request.client.host
    
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    
    from datetime import datetime
    
    logger.warning(
        f"🔒 SECURITY EVENT: {event_type}",
        extra={
            "event_type": event_type,
            "client_ip": client_ip,
            "user_agent": request.headers.get("User-Agent", "unknown"),
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
    )