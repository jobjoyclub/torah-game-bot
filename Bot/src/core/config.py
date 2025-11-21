#!/usr/bin/env python3
"""
Centralized configuration management for Torah Bot
Handles environment variables, defaults, and validation
"""
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

class DeploymentMode(str, Enum):
    """Available deployment modes"""
    DEVELOPMENT = "development"
    AUTOSCALE = "autoscale"
    PRODUCTION = "production"

class LogLevel(str, Enum):
    """Available log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    url: str
    pool_size: int = 10
    timeout: int = 30
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Create database config from environment variables"""
        return cls(
            url=os.getenv('DATABASE_URL', ''),
            pool_size=int(os.getenv('DB_POOL_SIZE', '10')),
            timeout=int(os.getenv('DB_TIMEOUT', '30'))
        )

@dataclass
class TelegramConfig:
    """Telegram bot configuration"""
    bot_token: str
    webhook_url: Optional[str] = None
    api_timeout: int = 30
    max_retries: int = 3
    
    @classmethod
    def from_env(cls) -> 'TelegramConfig':
        """Create Telegram config from environment variables"""
        return cls(
            bot_token=os.getenv('BOT_TOKEN', ''),
            webhook_url=os.getenv('WEBHOOK_URL'),
            api_timeout=int(os.getenv('TELEGRAM_API_TIMEOUT', '30')),
            max_retries=int(os.getenv('TELEGRAM_MAX_RETRIES', '3'))
        )

@dataclass
class OpenAIConfig:
    """OpenAI API configuration"""
    api_key: str
    model_primary: str = "gpt-4o-mini"
    model_fallback: str = "gpt-3.5-turbo"
    max_tokens: int = 400
    temperature: float = 0.7
    timeout: int = 30
    
    @classmethod
    def from_env(cls) -> 'OpenAIConfig':
        """Create OpenAI config from environment variables"""
        return cls(
            api_key=os.getenv('OPENAI_API_KEY', ''),
            model_primary=os.getenv('OPENAI_MODEL_PRIMARY', 'gpt-4o-mini'),
            model_fallback=os.getenv('OPENAI_MODEL_FALLBACK', 'gpt-3.5-turbo'),
            max_tokens=int(os.getenv('OPENAI_MAX_TOKENS', '400')),
            temperature=float(os.getenv('OPENAI_TEMPERATURE', '0.7')),
            timeout=int(os.getenv('OPENAI_TIMEOUT', '30'))
        )

@dataclass
class ServerConfig:
    """Server and networking configuration"""
    host: str = "0.0.0.0"
    port: int = 5000
    workers: int = 1
    max_request_size: int = 16777216  # 16MB
    timeout: int = 30
    
    @classmethod
    def from_env(cls) -> 'ServerConfig':
        """Create server config from environment variables"""
        return cls(
            host=os.getenv('SERVER_HOST', '0.0.0.0'),
            port=int(os.getenv('PORT', '5000')),
            workers=int(os.getenv('WORKERS', '1')),
            max_request_size=int(os.getenv('MAX_REQUEST_SIZE', '16777216')),
            timeout=int(os.getenv('SERVER_TIMEOUT', '30'))
        )

@dataclass
class NewsletterConfig:
    """Newsletter system configuration"""
    enabled: bool = True
    max_subscribers: int = 10000
    broadcast_rate_limit: int = 30  # messages per second
    retry_attempts: int = 3
    
    @classmethod
    def from_env(cls) -> 'NewsletterConfig':
        """Create newsletter config from environment variables"""
        return cls(
            enabled=os.getenv('NEWSLETTER_ENABLED', 'true').lower() == 'true',
            max_subscribers=int(os.getenv('NEWSLETTER_MAX_SUBSCRIBERS', '10000')),
            broadcast_rate_limit=int(os.getenv('NEWSLETTER_RATE_LIMIT', '30')),
            retry_attempts=int(os.getenv('NEWSLETTER_RETRY_ATTEMPTS', '3'))
        )

@dataclass
class GameConfig:
    """Mini game configuration"""
    max_score_share: int = 1000
    session_timeout: int = 300  # 5 minutes
    analytics_enabled: bool = True
    cache_timeout: int = 3600  # 1 hour
    
    @classmethod
    def from_env(cls) -> 'GameConfig':
        """Create game config from environment variables"""
        return cls(
            max_score_share=int(os.getenv('GAME_MAX_SCORE', '1000')),
            session_timeout=int(os.getenv('GAME_SESSION_TIMEOUT', '300')),
            analytics_enabled=os.getenv('GAME_ANALYTICS_ENABLED', 'true').lower() == 'true',
            cache_timeout=int(os.getenv('GAME_CACHE_TIMEOUT', '3600'))
        )

@dataclass
class SecurityConfig:
    """Security and authentication configuration"""
    admin_secret: str
    rate_limit_per_minute: int = 60
    allowed_origins: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.allowed_origins is None:
            self.allowed_origins = ["*"]
    
    @classmethod
    def from_env(cls) -> 'SecurityConfig':
        """Create security config from environment variables"""
        origins_str = os.getenv('ALLOWED_ORIGINS', '*')
        origins = [o.strip() for o in origins_str.split(',') if o.strip()]
        
        return cls(
            admin_secret=os.getenv('ADMIN_SECRET', ''),
            rate_limit_per_minute=int(os.getenv('RATE_LIMIT_PER_MINUTE', '60')),
            allowed_origins=origins
        )

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: LogLevel = LogLevel.INFO
    format_json: bool = True
    include_request_id: bool = True
    max_file_size: int = 10485760  # 10MB
    backup_count: int = 5
    
    @classmethod
    def from_env(cls) -> 'LoggingConfig':
        """Create logging config from environment variables"""
        return cls(
            level=LogLevel(os.getenv('LOG_LEVEL', 'INFO')),
            format_json=os.getenv('LOG_FORMAT_JSON', 'true').lower() == 'true',
            include_request_id=os.getenv('LOG_INCLUDE_REQUEST_ID', 'true').lower() == 'true',
            max_file_size=int(os.getenv('LOG_MAX_FILE_SIZE', '10485760')),
            backup_count=int(os.getenv('LOG_BACKUP_COUNT', '5'))
        )

class AppConfig:
    """Main application configuration container"""
    
    def __init__(self):
        """Initialize configuration from environment variables"""
        self.deployment_mode = self._detect_deployment_mode()
        self.database = DatabaseConfig.from_env()
        self.telegram = TelegramConfig.from_env()
        self.openai = OpenAIConfig.from_env()
        self.server = ServerConfig.from_env()
        self.newsletter = NewsletterConfig.from_env()
        self.game = GameConfig.from_env()
        self.security = SecurityConfig.from_env()
        self.logging = LoggingConfig.from_env()
        
        # Validate critical settings
        self._validate_config()
    
    def _detect_deployment_mode(self) -> DeploymentMode:
        """Auto-detect deployment mode from environment"""
        if os.getenv('REPLIT_DEPLOYMENT') == "1":
            return DeploymentMode.AUTOSCALE
        elif os.getenv('DEPLOYMENT_MODE') == 'production':
            return DeploymentMode.PRODUCTION
        else:
            return DeploymentMode.DEVELOPMENT
    
    def _validate_config(self):
        """Validate critical configuration settings"""
        errors = []
        
        # Check required environment variables
        if not self.telegram.bot_token:
            errors.append("BOT_TOKEN is required")
        
        if not self.database.url:
            errors.append("DATABASE_URL is required")
        
        if not self.security.admin_secret:
            errors.append("ADMIN_SECRET is required")
        
        if self.deployment_mode != DeploymentMode.DEVELOPMENT:
            if not self.openai.api_key:
                errors.append("OPENAI_API_KEY is required for production")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {', '.join(errors)}")
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.deployment_mode in [DeploymentMode.PRODUCTION, DeploymentMode.AUTOSCALE]
    
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.deployment_mode == DeploymentMode.DEVELOPMENT
    
    def get_webhook_url(self) -> str:
        """Get webhook URL based on deployment mode"""
        if self.telegram.webhook_url:
            return self.telegram.webhook_url
        
        # Auto-generate based on deployment
        if self.deployment_mode == DeploymentMode.AUTOSCALE:
            return "https://torah-project-jobjoyclub.replit.app/webhook"
        elif self.deployment_mode == DeploymentMode.DEVELOPMENT:
            return f"http://localhost:{self.server.port}/webhook"
        else:
            # Production needs manual configuration
            raise ValueError("WEBHOOK_URL must be set for production deployment")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (for debugging)"""
        return {
            "deployment_mode": self.deployment_mode.value,
            "database": {
                "url": "***" if self.database.url else None,
                "pool_size": self.database.pool_size,
                "timeout": self.database.timeout
            },
            "telegram": {
                "bot_token": "***" if self.telegram.bot_token else None,
                "webhook_url": self.telegram.webhook_url,
                "api_timeout": self.telegram.api_timeout,
                "max_retries": self.telegram.max_retries
            },
            "server": {
                "host": self.server.host,
                "port": self.server.port,
                "workers": self.server.workers
            },
            "newsletter": {
                "enabled": self.newsletter.enabled,
                "max_subscribers": self.newsletter.max_subscribers
            },
            "game": {
                "analytics_enabled": self.game.analytics_enabled,
                "session_timeout": self.game.session_timeout
            },
            "security": {
                "admin_secret": "***" if self.security.admin_secret else None,
                "rate_limit_per_minute": self.security.rate_limit_per_minute
            },
            "logging": {
                "level": self.logging.level.value,
                "format_json": self.logging.format_json
            }
        }

# Global configuration instance
config = AppConfig()

# Convenience functions for common config access
def get_config() -> AppConfig:
    """Get the global configuration instance"""
    return config

def is_production() -> bool:
    """Quick check if running in production"""
    return config.is_production()

def is_development() -> bool:
    """Quick check if running in development"""
    return config.is_development()

def get_deployment_mode() -> DeploymentMode:
    """Get current deployment mode"""
    return config.deployment_mode