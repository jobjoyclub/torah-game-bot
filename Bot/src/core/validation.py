#!/usr/bin/env python3
"""
Input validation utilities for API endpoints
Enhanced with Pydantic models and validation functions
"""
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
import re
from enum import Enum

class SupportedLanguage(str, Enum):
    """Supported languages for validation"""
    ENGLISH = "english"
    RUSSIAN = "russian" 
    HEBREW = "hebrew"
    SPANISH = "spanish"
    FRENCH = "french"
    GERMAN = "german"
    ITALIAN = "italian"
    PORTUGUESE = "portuguese"
    ARABIC = "arabic"

class GameAnalyticsRequest(BaseModel):
    """Validation model for game analytics data"""
    user_id: int = Field(..., ge=1, description="Telegram user ID")
    score: int = Field(..., ge=0, le=10000, description="Game score")
    duration: int = Field(..., ge=1, le=120, description="Game duration in seconds")
    items_collected: int = Field(..., ge=0, le=1000, description="Items collected")
    mistakes: int = Field(..., ge=0, le=500, description="Mistakes made")
    achievements: Optional[List[str]] = Field(default=[], description="Achievements unlocked")
    language: Optional[SupportedLanguage] = Field(default=SupportedLanguage.ENGLISH)
    
    @validator('achievements')
    def validate_achievements(cls, v):
        """Validate achievements list"""
        if v is None:
            return []
        if len(v) > 20:  # Max 20 achievements
            raise ValueError("Too many achievements")
        return v

class TutorialAnalyticsRequest(BaseModel):
    """Validation model for tutorial analytics"""
    user_id: int = Field(..., ge=1, description="Telegram user ID")
    event_type: str = Field(..., regex=r'^(TUTORIAL_STARTED|TUTORIAL_COMPLETED|SCREEN_COMPLETED)$')
    screen_number: Optional[int] = Field(None, ge=1, le=10, description="Tutorial screen number")
    duration: Optional[int] = Field(None, ge=0, le=600, description="Duration in seconds")
    language: Optional[SupportedLanguage] = Field(default=SupportedLanguage.ENGLISH)

class WebhookRequest(BaseModel):
    """Basic validation for Telegram webhook data"""
    update_id: int = Field(..., ge=1, description="Telegram update ID")
    message: Optional[Dict[str, Any]] = None
    callback_query: Optional[Dict[str, Any]] = None
    
    @validator('message', 'callback_query')
    def at_least_one_required(cls, v, values):
        """Ensure at least message or callback_query is present"""
        if not v and not values.get('message') and not values.get('callback_query'):
            raise ValueError("Either message or callback_query must be present")
        return v

class HealthCheckResponse(BaseModel):
    """Health check response format"""
    status: str = Field(..., regex=r'^(healthy|unhealthy)$')
    service: str = Field(..., min_length=1, max_length=100)
    timestamp: Optional[float] = None
    details: Optional[Dict[str, Any]] = None

# Validation functions
def validate_telegram_user_id(user_id: Union[str, int]) -> int:
    """Validate and convert Telegram user ID"""
    try:
        user_id_int = int(user_id)
        if user_id_int <= 0:
            raise ValueError("User ID must be positive")
        if user_id_int > 999999999999:  # Reasonable upper limit
            raise ValueError("User ID too large") 
        return user_id_int
    except (ValueError, TypeError):
        raise ValueError("Invalid user ID format")

def validate_language_code(lang: Optional[str]) -> str:
    """Validate and normalize language code"""
    if not lang:
        return "english"
    
    lang = lang.lower().strip()
    
    # Map common language codes to full names
    lang_mapping = {
        "en": "english",
        "ru": "russian", 
        "he": "hebrew",
        "es": "spanish",
        "fr": "french", 
        "de": "german",
        "it": "italian",
        "pt": "portuguese",
        "ar": "arabic",
        "uk": "russian",  # Ukrainian -> Russian
        "be": "russian"   # Belarusian -> Russian
    }
    
    # Direct mapping or assume it's already a full name
    normalized = lang_mapping.get(lang, lang)
    
    # Validate against supported languages
    try:
        SupportedLanguage(normalized)
        return normalized
    except ValueError:
        return "english"  # Default fallback

def validate_game_score(score: Union[str, int]) -> int:
    """Validate game score"""
    try:
        score_int = int(score)
        if score_int < 0:
            raise ValueError("Score cannot be negative")
        if score_int > 10000:
            raise ValueError("Score too high")
        return score_int
    except (ValueError, TypeError):
        raise ValueError("Invalid score format")

def validate_request_data(data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
    """Generic request data validation"""
    validated = {}
    errors = []
    
    # Check required fields
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
        else:
            validated[field] = data[field]
    
    if errors:
        raise ValueError(f"Validation errors: {', '.join(errors)}")
    
    return validated

def sanitize_text_input(text: str, max_length: int = 1000) -> str:
    """Sanitize text input for safety"""
    if not isinstance(text, str):
        return ""
    
    # Remove control characters and excessive whitespace
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Truncate to max length
    if len(text) > max_length:
        text = text[:max_length]
    
    return text

def validate_url_parameters(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate URL query parameters"""
    validated = {}
    
    # User ID validation
    if 'user_id' in params:
        validated['user_id'] = validate_telegram_user_id(params['user_id'])
    
    # Language validation
    if 'lang' in params:
        validated['lang'] = validate_language_code(params['lang'])
    
    # Version parameters (for cache busting)
    if 'v' in params:
        validated['v'] = sanitize_text_input(str(params['v']), 50)
    
    if 'deploy' in params:
        validated['deploy'] = sanitize_text_input(str(params['deploy']), 50)
    
    return validated

# Error response helpers
def create_validation_error_response(error_message: str) -> Dict[str, Any]:
    """Create standardized validation error response"""
    return {
        "error": {
            "category": "validation_error",
            "code": "INVALID_INPUT",
            "message": error_message,
            "user_message": "Invalid input provided. Please check your data and try again"
        }
    }

def create_missing_field_error(field_name: str) -> Dict[str, Any]:
    """Create error response for missing field"""
    return create_validation_error_response(f"Missing required field: {field_name}")