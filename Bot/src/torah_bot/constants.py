#!/usr/bin/env python3
"""
Constants for Torah Bot - eliminates magic numbers and hardcoded values
"""

# Timeouts (in seconds)
HTTP_TIMEOUT = 30.0
OPENAI_TIMEOUT = 45.0
TELEGRAM_API_TIMEOUT = 20.0

# Limits
MAX_WISDOM_LENGTH = 400
GAME_DURATION_SECONDS = 45
MAX_QUIZ_OPTIONS = 4
SESSION_CLEANUP_INTERVAL = 3600  # 1 hour

# Response limits
MAX_CONTENT_PREVIEW = 100
MAX_LOG_MESSAGE_LENGTH = 200

# Retry configuration
MAX_API_RETRIES = 3
RETRY_DELAY_SECONDS = 2

# Language mappings
LANGUAGE_MAPPINGS = {
    "en": "English",
    "ru": "Russian", 
    "he": "Hebrew",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ar": "Arabic",
    "uk": "Russian",  # Ukrainian uses Russian for now
    "be": "Russian"   # Belarusian uses Russian for now
}

# Default fallback messages
DEFAULT_ERROR_MESSAGE = "❌ Sorry, something went wrong. Please try again."
DEFAULT_LANGUAGE = "English"
DEFAULT_TOPIC = "Torah wisdom"

# Admin user IDs for tests (move to environment in production)
TEST_ADMIN_USER_ID = 6630727156

# File paths
PROMPTS_DIR = "prompts"
IMAGES_DIR = "attached_assets/generated_images"