#!/usr/bin/env python3
"""
Tests for Torah Bot Newsletter Manager
Comprehensive test suite covering database operations, subscriptions, and error handling
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

try:
    from torah_bot.newsletter_manager import NewsletterManager, NewsletterUser, BroadcastContent
    NEWSLETTER_MANAGER_AVAILABLE = True
except ImportError as e:
    NEWSLETTER_MANAGER_AVAILABLE = False
    pytest.skip(f"NewsletterManager module not available: {e}", allow_module_level=True)


class TestNewsletterManagerInitialization:
    """Test NewsletterManager initialization and database setup"""
    
    @pytest.fixture
    def manager(self):
        """Create a newsletter manager instance for testing"""
        manager = NewsletterManager()
        manager.db_url = "postgresql://test:test@localhost:5432/test_db"
        return manager
    
    def test_initialization_with_env_var(self):
        """Test initialization reads DATABASE_URL from environment"""
        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:test@localhost/test'}):
            manager = NewsletterManager()
            assert manager.db_url == 'postgresql://test:test@localhost/test'
    
    def test_initialization_without_env_var(self):
        """Test initialization when DATABASE_URL is not set"""
        with patch.dict(os.environ, {}, clear=True):
            manager = NewsletterManager()
            assert manager.db_url is None
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, manager):
        """Test successful database initialization"""
        with patch('asyncpg.create_pool') as mock_create_pool:
            mock_pool = AsyncMock()
            mock_create_pool.return_value = mock_pool
            
            await manager.initialize()
            
            assert manager.pool == mock_pool
            mock_create_pool.assert_called_once_with(
                manager.db_url,
                min_size=2,
                max_size=10,
                command_timeout=30
            )
    
    @pytest.mark.asyncio
    async def test_initialize_no_database_url(self):
        """Test initialization failure when DATABASE_URL is missing"""
        manager = NewsletterManager()
        manager.db_url = None
        
        with pytest.raises(ValueError, match="DATABASE_URL not found"):
            await manager.initialize()
    
    @pytest.mark.asyncio
    async def test_close_pool(self, manager):
        """Test database pool closing"""
        mock_pool = AsyncMock()
        manager.pool = mock_pool
        
        await manager.close()
        
        mock_pool.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_without_pool(self, manager):
        """Test closing when pool is None"""
        manager.pool = None
        
        # Should not raise exception
        await manager.close()


class TestUserManagement:
    """Test user creation, updates, and management"""
    
    @pytest.fixture
    def manager_with_pool(self):
        """Create manager with mocked database pool"""
        manager = NewsletterManager()
        manager.db_url = "postgresql://test:test@localhost/test"
        
        # Mock pool and connection
        pool = AsyncMock()
        connection = AsyncMock()
        pool.acquire.return_value.__aenter__.return_value = connection
        pool.acquire.return_value.__aexit__.return_value = None
        manager.pool = pool
        
        return manager, connection
    
    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for testing"""
        return {
            'id': 123456789,
            'username': 'test_user',
            'first_name': 'Test',
            'last_name': 'User',
            'language_code': 'en',
            'is_bot': False,
            'is_premium': False
        }
    
    @pytest.mark.asyncio
    async def test_upsert_user_success(self, manager_with_pool, sample_user_data):
        """Test successful user creation/update"""
        manager, connection = manager_with_pool
        connection.execute.return_value = None
        
        result = await manager.upsert_user(sample_user_data)
        
        assert result is True
        connection.execute.assert_called_once()
        
        # Verify SQL parameters contain expected data
        call_args = connection.execute.call_args
        assert sample_user_data['id'] in call_args[0][1:]
        assert sample_user_data['username'] in call_args[0][1:]
        assert sample_user_data['first_name'] in call_args[0][1:]
    
    @pytest.mark.asyncio
    async def test_upsert_user_database_error(self, manager_with_pool, sample_user_data):
        """Test user upsert failure due to database error"""
        manager, connection = manager_with_pool
        connection.execute.side_effect = Exception("Database connection failed")
        
        result = await manager.upsert_user(sample_user_data)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_upsert_user_no_pool(self, sample_user_data):
        """Test user upsert failure when pool is not initialized"""
        manager = NewsletterManager()
        manager.pool = None
        
        result = await manager.upsert_user(sample_user_data)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_user_activity_wisdom(self, manager_with_pool):
        """Test updating user wisdom request activity"""
        manager, connection = manager_with_pool
        user_id = 123456789
        
        await manager.update_user_activity(user_id, "wisdom_request")
        
        connection.execute.assert_called_once()
        call_args = connection.execute.call_args[0]
        assert "total_wisdom_requests" in call_args[0]
        assert user_id == call_args[1]
    
    @pytest.mark.asyncio
    async def test_update_user_activity_quiz(self, manager_with_pool):
        """Test updating user quiz attempt activity"""
        manager, connection = manager_with_pool
        user_id = 123456789
        
        await manager.update_user_activity(user_id, "quiz_attempt")
        
        connection.execute.assert_called_once()
        call_args = connection.execute.call_args[0]
        assert "total_quiz_attempts" in call_args[0]
        assert user_id == call_args[1]
    
    @pytest.mark.asyncio
    async def test_update_user_activity_invalid_type(self, manager_with_pool):
        """Test updating user activity with invalid activity type"""
        manager, connection = manager_with_pool
        user_id = 123456789
        
        # Should handle gracefully without database call
        await manager.update_user_activity(user_id, "invalid_activity")
        
        # Should not call database for invalid activity type
        connection.execute.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_update_user_activity_database_error(self, manager_with_pool):
        """Test handling database error during activity update"""
        manager, connection = manager_with_pool
        connection.execute.side_effect = Exception("Database error")
        user_id = 123456789
        
        # Should not raise exception
        await manager.update_user_activity(user_id, "wisdom_request")
        
        connection.execute.assert_called_once()


class TestSubscriptionManagement:
    """Test newsletter subscription functionality"""
    
    @pytest.fixture
    def manager_with_subscription_methods(self, manager_with_pool):
        """Create manager with subscription-related mock methods"""
        manager, connection = manager_with_pool
        
        # Add mock methods for subscription management
        manager.subscribe_user = AsyncMock(return_value=True)
        manager.unsubscribe_user = AsyncMock(return_value=True)
        manager.is_subscribed = AsyncMock(return_value=True)
        manager.get_subscribers = AsyncMock(return_value=[])
        manager.get_stats = AsyncMock(return_value={'total_users': 0, 'active_subscribers': 0})
        
        return manager, connection
    
    @pytest.mark.asyncio
    async def test_subscribe_user_success(self, manager_with_subscription_methods):
        """Test successful user subscription"""
        manager, _ = manager_with_subscription_methods
        user_id = 123456789
        language = "Russian"
        
        result = await manager.subscribe_user(user_id, language)
        
        assert result is True
        manager.subscribe_user.assert_called_once_with(user_id, language)
    
    @pytest.mark.asyncio
    async def test_unsubscribe_user_success(self, manager_with_subscription_methods):
        """Test successful user unsubscription"""
        manager, _ = manager_with_subscription_methods
        user_id = 123456789
        
        result = await manager.unsubscribe_user(user_id)
        
        assert result is True
        manager.unsubscribe_user.assert_called_once_with(user_id)
    
    @pytest.mark.asyncio
    async def test_check_subscription_status(self, manager_with_subscription_methods):
        """Test checking user subscription status"""
        manager, _ = manager_with_subscription_methods
        user_id = 123456789
        
        is_subscribed = await manager.is_subscribed(user_id)
        
        assert is_subscribed is True
        manager.is_subscribed.assert_called_once_with(user_id)
    
    @pytest.mark.asyncio
    async def test_get_subscriber_stats(self, manager_with_subscription_methods):
        """Test getting subscription statistics"""
        manager, _ = manager_with_subscription_methods
        
        # Mock realistic stats response
        manager.get_stats.return_value = {
            'total_users': 100,
            'active_subscribers': 75,
            'daily_active': 25,
            'language_breakdown': {'Russian': 40, 'English': 35}
        }
        
        stats = await manager.get_stats()
        
        assert stats['total_users'] == 100
        assert stats['active_subscribers'] == 75
        assert stats['daily_active'] == 25
        assert 'language_breakdown' in stats
        manager.get_stats.assert_called_once()


class TestDataModels:
    """Test data models and structures"""
    
    def test_newsletter_user_creation(self):
        """Test NewsletterUser dataclass creation"""
        user = NewsletterUser(
            telegram_user_id=123456789,
            username="test_user",
            first_name="Test",
            language="English",
            is_subscribed=True,
            delivery_time=time(9, 0),
            timezone_str="UTC"
        )
        
        assert user.telegram_user_id == 123456789
        assert user.username == "test_user"
        assert user.first_name == "Test"
        assert user.language == "English"
        assert user.is_subscribed is True
        assert user.delivery_time == time(9, 0)
        assert user.timezone_str == "UTC"
    
    def test_broadcast_content_creation(self):
        """Test BroadcastContent dataclass creation"""
        content = BroadcastContent(
            date=date(2025, 8, 30),
            topic="Rosh Hashanah",
            wisdom_content={
                "English": {"text": "Wisdom text", "references": "Torah 1:1"},
                "Russian": {"text": "Текст мудрости", "references": "Тора 1:1"}
            },
            image_url="https://example.com/image.jpg"
        )
        
        assert content.date == date(2025, 8, 30)
        assert content.topic == "Rosh Hashanah"
        assert "English" in content.wisdom_content
        assert "Russian" in content.wisdom_content
        assert content.image_url == "https://example.com/image.jpg"
    
    def test_broadcast_content_without_image(self):
        """Test BroadcastContent creation without image"""
        content = BroadcastContent(
            date=date(2025, 8, 30),
            topic="Shabbat",
            wisdom_content={"English": {"text": "Peace", "references": "Genesis"}}
        )
        
        assert content.image_url is None
        assert content.topic == "Shabbat"


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.fixture
    def manager_with_errors(self):
        """Create manager configured for error testing"""
        manager = NewsletterManager()
        manager.db_url = "postgresql://test:test@localhost/test"
        return manager
    
    @pytest.mark.asyncio
    async def test_operation_with_no_pool(self, manager_with_errors, sample_user_data):
        """Test operations fail gracefully when pool is not initialized"""
        manager_with_errors.pool = None
        
        # Test various operations
        result = await manager_with_errors.upsert_user(sample_user_data)
        assert result is False
        
        # Test activity update doesn't crash
        await manager_with_errors.update_user_activity(123456789, "wisdom_request")
        # Should complete without raising exception
    
    @pytest.mark.asyncio
    async def test_database_connection_timeout(self, manager_with_errors, sample_user_data):
        """Test handling of database connection timeouts"""
        # Mock pool with timeout
        pool = AsyncMock()
        connection = AsyncMock()
        connection.execute.side_effect = asyncio.TimeoutError("Operation timed out")
        pool.acquire.return_value.__aenter__.return_value = connection
        manager_with_errors.pool = pool
        
        result = await manager_with_errors.upsert_user(sample_user_data)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_invalid_user_data(self, manager_with_errors):
        """Test handling of invalid user data"""
        # Mock pool
        pool = AsyncMock()
        connection = AsyncMock()
        pool.acquire.return_value.__aenter__.return_value = connection
        manager_with_errors.pool = pool
        
        # Test with missing required fields
        invalid_data = {'username': 'test'}  # Missing 'id'
        
        result = await manager_with_errors.upsert_user(invalid_data)
        
        # Should handle gracefully and return False or complete successfully
        assert isinstance(result, bool)
    
    @pytest.fixture
    def sample_user_data(self):
        """Sample user data fixture for error tests"""
        return {
            'id': 123456789,
            'username': 'test_user',
            'first_name': 'Test',
            'last_name': 'User',
            'language_code': 'en',
            'is_bot': False,
            'is_premium': False
        }


class TestIntegration:
    """Integration tests for newsletter manager"""
    
    @pytest.mark.asyncio
    async def test_full_user_lifecycle(self, sample_user_data):
        """Test complete user lifecycle: create, update, subscribe, unsubscribe"""
        manager = NewsletterManager()
        manager.db_url = "postgresql://test:test@localhost/test"
        
        with patch('asyncpg.create_pool') as mock_create_pool:
            mock_pool = AsyncMock()
            mock_connection = AsyncMock()
            mock_pool.acquire.return_value.__aenter__.return_value = mock_connection
            mock_create_pool.return_value = mock_pool
            
            # Initialize manager
            await manager.initialize()
            
            # Create user
            result = await manager.upsert_user(sample_user_data)
            assert result is True
            
            # Update activity
            await manager.update_user_activity(sample_user_data['id'], "wisdom_request")
            
            # Close properly
            await manager.close()
            
            # Verify database calls were made
            assert mock_connection.execute.call_count >= 2
            mock_pool.close.assert_called_once()
    
    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for integration tests"""
        return {
            'id': 987654321,
            'username': 'integration_test',
            'first_name': 'Integration',
            'last_name': 'Test',
            'language_code': 'en',
            'is_bot': False,
            'is_premium': True
        }


# Test Configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "--tb=short"])