#!/usr/bin/env python3
"""
Tests for Webhook Auto-Subscription System
Tests for automatic user subscription on webhook boundary in UnifiedWebhookService
"""

import pytest
import asyncio
import os
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, date, time, timezone
import sys

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(project_root, 'src'))
sys.path.append(project_root)  # Add for unified_webhook_service.py


class TestWebhookAutoSubscription:
    """Test automatic user subscription at webhook boundary"""
    
    @pytest.fixture
    def mock_newsletter_manager(self):
        """Mock newsletter manager for testing"""
        manager = AsyncMock()
        manager.subscribe_user = AsyncMock(return_value=True)
        return manager
    
    @pytest.fixture
    def mock_telegram_update_new_user(self):
        """Mock Telegram update for new user"""
        return {
            "update_id": 12345,
            "message": {
                "message_id": 123,
                "from": {
                    "id": 987654321,
                    "is_bot": False,
                    "first_name": "TestUser",
                    "username": "testuser",
                    "language_code": "en"
                },
                "chat": {
                    "id": 987654321,
                    "first_name": "TestUser",
                    "username": "testuser",
                    "type": "private"
                },
                "date": 1695230400,
                "text": "/start"
            }
        }
    
    @pytest.fixture
    def mock_telegram_update_existing_user(self):
        """Mock Telegram update for existing user"""
        return {
            "update_id": 12346,
            "message": {
                "message_id": 124,
                "from": {
                    "id": 123456789,  # User ID that already exists in DB
                    "is_bot": False,
                    "first_name": "ExistingUser",
                    "username": "existing_user",
                    "language_code": "ru"
                },
                "chat": {
                    "id": 123456789,
                    "first_name": "ExistingUser", 
                    "username": "existing_user",
                    "type": "private"
                },
                "date": 1695230500,
                "text": "Hello"
            }
        }
    
    @pytest.fixture
    def mock_callback_query_update(self):
        """Mock Telegram callback query update"""
        return {
            "update_id": 12347,
            "callback_query": {
                "id": "callback_123",
                "from": {
                    "id": 555666777,
                    "is_bot": False,
                    "first_name": "CallbackUser",
                    "username": "callback_user",
                    "language_code": "es"
                },
                "message": {
                    "message_id": 125,
                    "chat": {
                        "id": 555666777,
                        "type": "private"
                    },
                    "date": 1695230600
                },
                "data": "some_callback_data"
            }
        }
    
    @pytest.mark.asyncio
    async def test_ensure_user_subscription_new_user_happy_path(self, mock_newsletter_manager):
        """Happy path: New user gets automatically subscribed to newsletter"""
        # Import the function we'll implement
        from unified_webhook_service import ensure_user_subscription
        
        user_id = 987654321
        language_code = "en"
        
        # Call the function
        result = await ensure_user_subscription(user_id, language_code, mock_newsletter_manager)
        
        # Verify subscription was attempted
        mock_newsletter_manager.subscribe_user.assert_called_once_with(
            telegram_user_id=user_id,
            language="English",
            delivery_time="09:00",
            timezone="UTC"
        )
        assert result is True
    
    @pytest.mark.asyncio 
    async def test_ensure_user_subscription_existing_user_edge_case(self, mock_newsletter_manager):
        """Edge case: Existing user subscription should be updated, not duplicated"""
        # Import the function we'll implement
        from unified_webhook_service import ensure_user_subscription
        
        user_id = 123456789  # Existing user
        language_code = "ru"
        
        # Mock that subscription succeeds (ON CONFLICT DO UPDATE logic)
        mock_newsletter_manager.subscribe_user.return_value = True
        
        # Call the function
        result = await ensure_user_subscription(user_id, language_code, mock_newsletter_manager)
        
        # Verify subscription was attempted with Russian language
        mock_newsletter_manager.subscribe_user.assert_called_once_with(
            telegram_user_id=user_id,
            language="Russian",
            delivery_time="09:00", 
            timezone="UTC"
        )
        assert result is True
    
    @pytest.mark.asyncio
    async def test_ensure_user_subscription_handles_failures(self, mock_newsletter_manager):
        """Test that subscription failures are handled gracefully"""
        # Import the function we'll implement
        from unified_webhook_service import ensure_user_subscription
        
        user_id = 999888777
        language_code = "fr"
        
        # Mock subscription failure
        mock_newsletter_manager.subscribe_user.return_value = False
        
        # Call the function
        result = await ensure_user_subscription(user_id, language_code, mock_newsletter_manager)
        
        # Verify subscription was attempted
        mock_newsletter_manager.subscribe_user.assert_called_once_with(
            telegram_user_id=user_id,
            language="French",
            delivery_time="09:00",
            timezone="UTC"
        )
        # Should return False on failure but not crash
        assert result is False
    
    @pytest.mark.asyncio
    async def test_ensure_user_subscription_exception_handling(self, mock_newsletter_manager):
        """Test that exceptions during subscription are handled gracefully"""
        # Import the function we'll implement  
        from unified_webhook_service import ensure_user_subscription
        
        user_id = 111222333
        language_code = "de"
        
        # Mock subscription exception
        mock_newsletter_manager.subscribe_user.side_effect = Exception("Database connection failed")
        
        # Call the function
        result = await ensure_user_subscription(user_id, language_code, mock_newsletter_manager)
        
        # Should handle exception gracefully and return False
        assert result is False
    
    @pytest.mark.asyncio
    async def test_language_code_mapping(self, mock_newsletter_manager):
        """Test correct mapping of language codes to language names"""
        # Import the function we'll implement
        from unified_webhook_service import ensure_user_subscription
        
        test_cases = [
            ("en", "English"),
            ("ru", "Russian"),
            ("es", "Spanish"),
            ("fr", "French"),
            ("de", "German"),
            ("he", "Hebrew"),
            ("ar", "Arabic"),
            ("unknown", "English"),  # Default fallback
            (None, "English")  # None fallback
        ]
        
        for lang_code, expected_language in test_cases:
            mock_newsletter_manager.reset_mock()
            
            await ensure_user_subscription(999, lang_code, mock_newsletter_manager)
            
            # Verify correct language was used
            mock_newsletter_manager.subscribe_user.assert_called_once_with(
                telegram_user_id=999,
                language=expected_language,
                delivery_time="09:00",
                timezone="UTC"
            )

    def test_extract_user_data_from_message_update(self, mock_telegram_update_new_user):
        """Test extracting user data from message update"""
        # Import the function we'll implement
        from unified_webhook_service import extract_user_data_from_update
        
        user_id, lang_code = extract_user_data_from_update(mock_telegram_update_new_user)
        
        assert user_id == 987654321
        assert lang_code == "en"
    
    def test_extract_user_data_from_callback_query_update(self, mock_callback_query_update):
        """Test extracting user data from callback query update"""  
        # Import the function we'll implement
        from unified_webhook_service import extract_user_data_from_update
        
        user_id, lang_code = extract_user_data_from_update(mock_callback_query_update)
        
        assert user_id == 555666777
        assert lang_code == "es"
    
    def test_extract_user_data_from_invalid_update(self):
        """Test extracting user data from invalid update returns None"""
        # Import the function we'll implement
        from unified_webhook_service import extract_user_data_from_update
        
        invalid_update = {"update_id": 999}  # No message or callback_query
        
        user_id, lang_code = extract_user_data_from_update(invalid_update)
        
        assert user_id is None
        assert lang_code is None


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])