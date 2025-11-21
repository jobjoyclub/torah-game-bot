#!/usr/bin/env python3
"""
UserContext - unified user data structure for Torah Bot
Ensures consistent user information across all modules
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class UserContext:
    """Unified user context for consistent data flow"""
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None
    language: Optional[str] = None
    
    @property
    def display_name(self) -> str:
        """Get user's display name with fallback"""
        if self.username:
            return f"@{self.username}"
        if self.first_name:
            return self.first_name
        return f"user_{self.user_id}"
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts) if parts else self.display_name
    
    def to_dict(self) -> dict:
        """Convert to dictionary for backward compatibility"""
        return {
            "id": self.user_id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "language_code": self.language_code,
            "language": self.language
        }
    
    @classmethod
    def from_telegram_user(cls, telegram_data: dict, language: Optional[str] = None) -> Optional["UserContext"]:
        """Create UserContext from Telegram user data"""
        user_id = telegram_data.get("id")
        if not user_id:
            return None
            
        return cls(
            user_id=user_id,
            username=telegram_data.get("username"),
            first_name=telegram_data.get("first_name"),
            last_name=telegram_data.get("last_name"),
            language_code=telegram_data.get("language_code"),
            language=language
        )


class UnifiedLogFormatter:
    """Unified log formatter for TorahLogs - consistent message format"""
    
    @staticmethod
    def format_log(
        event_type: str,
        user_context: Optional[UserContext],
        emoji: str = "📊",
        **details
    ) -> str:
        """
        Format unified log message for TorahLogs
        
        Args:
            event_type: Type of event (e.g., "GAME_COMPLETED", "WISDOM_REQUEST")
            user_context: User context with ID, username, language
            emoji: Event emoji (default: 📊)
            **details: Additional event-specific details
        
        Returns:
            Formatted log message for Telegram
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # User info with fallback
        if user_context:
            user_id = user_context.user_id
            username = user_context.display_name
            language = user_context.language or "unknown"
        else:
            user_id = "unknown"
            username = "@unknown"
            language = "unknown"
        
        # Header
        lines = [
            f"{emoji} <b>{event_type}</b> [{timestamp}]",
            f"🆔 User: {user_id} ({username})",
            f"🌐 Language: {language}"
        ]
        
        # Add details if provided
        if details:
            lines.append("")  # Empty line
            for key, value in details.items():
                # Format key (convert snake_case to Title Case)
                display_key = key.replace("_", " ").title()
                
                # Format value
                if isinstance(value, float):
                    display_value = f"{value:.1f}"
                elif isinstance(value, bool):
                    display_value = "✅" if value else "❌"
                else:
                    display_value = str(value)
                
                # Add emoji based on key
                key_emoji = UnifiedLogFormatter._get_emoji_for_key(key)
                lines.append(f"{key_emoji} {display_key}: {display_value}")
        
        return "\n".join(lines)
    
    @staticmethod
    def _get_emoji_for_key(key: str) -> str:
        """Get appropriate emoji for log field"""
        emoji_map = {
            "score": "🏆",
            "duration": "⏱️",
            "items_collected": "✨",
            "mistakes": "❌",
            "achievements": "🎖️",
            "topic": "📚",
            "success": "✅",
            "error": "⚠️",
            "language": "🌐",
            "after_tutorial": "📖"
        }
        return emoji_map.get(key, "▫️")
