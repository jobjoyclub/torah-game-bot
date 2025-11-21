#!/usr/bin/env python3
"""
CENTRALIZED DEPLOYMENT CONFIGURATION
Single source of truth for all deployment settings
"""
import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class DeploymentMode(Enum):
    """Supported deployment modes"""
    DEVELOPMENT = "development"
    AUTOSCALE = "autoscale" 
    PRODUCTION = "production"
    UNKNOWN = "unknown"

class BotMode(Enum):
    """Bot operation modes"""
    WEBHOOK = "webhook"
    POLLING = "polling"

@dataclass
class DeploymentConfig:
    """Centralized deployment configuration"""
    
    # Core settings
    mode: DeploymentMode
    bot_mode: BotMode
    
    # Network settings
    host: str = "0.0.0.0"
    port: int = 80
    
    # Service naming
    service_name: str = "torah-bot"
    
    # Features
    enable_keepalive: bool = False
    enable_microservices: bool = False
    enable_logging_to_chat: bool = False
    
    # Timeouts
    webhook_timeout: int = 30
    keepalive_interval: int = 600  # 10 minutes
    
    @classmethod
    def auto_detect(cls) -> 'DeploymentConfig':
        """Auto-detect optimal deployment configuration"""
        
        # Detect deployment mode - DEPLOYMENT_MODE has highest priority
        if os.environ.get("DEPLOYMENT_MODE") == "production":
            mode = DeploymentMode.PRODUCTION
        elif os.environ.get("REPLIT_DEPLOYMENT"):
            mode = DeploymentMode.AUTOSCALE
        elif os.environ.get("REPL_ID"):
            mode = DeploymentMode.DEVELOPMENT
        else:
            mode = DeploymentMode.UNKNOWN
        
        # Determine bot mode based on deployment
        if mode == DeploymentMode.AUTOSCALE:
            bot_mode = BotMode.WEBHOOK  # Request-based, better for Autoscale
        else:
            bot_mode = BotMode.POLLING  # Always-on, better for Reserved VM
        
        # Port configuration
        port = int(os.environ.get("PORT", 80))
        
        # Service naming based on mode
        if mode == DeploymentMode.PRODUCTION:
            service_name = "torah-bot-production"
        elif mode == DeploymentMode.AUTOSCALE:
            service_name = "torah-bot-autoscale"
        else:
            service_name = "torah-bot-development"
        
        # Feature flags based on mode
        enable_keepalive = (mode == DeploymentMode.AUTOSCALE)
        enable_microservices = (mode == DeploymentMode.PRODUCTION)
        enable_logging_to_chat = (mode in [DeploymentMode.PRODUCTION, DeploymentMode.AUTOSCALE])
        
        config = cls(
            mode=mode,
            bot_mode=bot_mode,
            port=port,
            service_name=service_name,
            enable_keepalive=enable_keepalive,
            enable_microservices=enable_microservices,
            enable_logging_to_chat=enable_logging_to_chat
        )
        
        logger.info(f"🎯 Auto-detected config: {mode.value} mode, {bot_mode.value} bot")
        return config
    
    def validate(self) -> Dict[str, Any]:
        """Validate configuration and return status"""
        validation = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
        # Check required environment variables
        required_vars = ["TELEGRAM_BOT_TOKEN"]
        for var in required_vars:
            if not os.environ.get(var):
                validation["errors"].append(f"Missing required environment variable: {var}")
                validation["is_valid"] = False
        
        # Check optional but recommended variables
        recommended_vars = ["OPENAI_API_KEY"]
        for var in recommended_vars:
            if not os.environ.get(var):
                validation["warnings"].append(f"Missing recommended environment variable: {var}")
        
        # Mode-specific validations
        if self.mode == DeploymentMode.AUTOSCALE and self.bot_mode == BotMode.POLLING:
            validation["warnings"].append("Polling mode on Autoscale may cause sleep issues")
            validation["recommendations"].append("Consider webhook mode for Autoscale")
        
        if self.mode == DeploymentMode.PRODUCTION and not self.enable_microservices:
            validation["warnings"].append("Production mode without microservices")
        
        # Port validations
        if self.mode in [DeploymentMode.AUTOSCALE, DeploymentMode.PRODUCTION] and self.port != 80:
            validation["warnings"].append(f"Non-standard port {self.port} for {self.mode.value}")
        
        return validation
    
    def get_health_check_data(self) -> Dict[str, Any]:
        """Generate standardized health check response"""
        return {
            "status": "healthy",
            "service": self.service_name,
            "mode": self.mode.value,
            "bot_mode": self.bot_mode.value,
            "timestamp": int(__import__('time').time()),
            "features": {
                "keepalive": self.enable_keepalive,
                "microservices": self.enable_microservices,
                "logging_to_chat": self.enable_logging_to_chat
            }
        }
    
    def get_endpoints(self) -> list:
        """Get available endpoints based on configuration"""
        endpoints = ["health", "game"]
        
        if self.bot_mode == BotMode.WEBHOOK:
            endpoints.extend(["webhook", "setup_webhook"])
        
        return endpoints

# Global configuration instance
_config: Optional[DeploymentConfig] = None

def get_config() -> DeploymentConfig:
    """Get global configuration instance (singleton)"""
    global _config
    if _config is None:
        _config = DeploymentConfig.auto_detect()
    return _config

def reset_config():
    """Reset configuration cache - for development/testing"""
    global _config
    _config = None
    logger.info("🔄 Configuration cache cleared")

def validate_deployment() -> Dict[str, Any]:
    """Validate current deployment configuration"""
    config = get_config()
    return config.validate()

# Legacy compatibility
def safe_startup_check() -> bool:
    """Legacy function for backward compatibility"""
    validation = validate_deployment()
    return validation["is_valid"]

class DeploymentGuard:
    """Legacy class for backward compatibility"""
    
    def __init__(self):
        self.config = get_config()
    
    def validate_environment(self) -> Dict[str, Any]:
        return self.config.validate()
    
    def get_startup_mode(self) -> str:
        return self.config.bot_mode.value
    
    def deployment_checklist(self) -> Dict[str, bool]:
        validation = self.config.validate()
        return {
            "environment_ok": validation["is_valid"],
            "tokens_present": len(validation["errors"]) == 0,
            "configuration_valid": len(validation["errors"]) == 0
        }