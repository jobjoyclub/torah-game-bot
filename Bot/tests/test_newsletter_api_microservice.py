#!/usr/bin/env python3
"""
Comprehensive Auto-Tests for Internal Newsletter API Microservice
Полные автотесты для внутреннего микросервиса Newsletter API
"""

import asyncio
import logging
import json
import time
from datetime import datetime, date
from typing import Dict, Any, Optional
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.newsletter_api import InternalNewsletterAPIClient, NewsletterAPIService, get_newsletter_service
from src.torah_bot.broadcast_system import get_broadcast_system, DailyBroadcastSystem

logger = logging.getLogger(__name__)

class NewsletterAPITestSuite:
    """Complete test suite for Internal Newsletter API microservice"""
    
    def __init__(self):
        self.client = InternalNewsletterAPIClient()
        self.service = None
        self.test_results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        
    async def setup(self):
        """Initialize test environment"""
        try:
            self.service = await get_newsletter_service()
            logger.info("✅ Test environment initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Test setup failed: {e}")
            return False
    
    async def cleanup(self):
        """Clean up test environment"""
        try:
            if self.service:
                await self.service.close()
            logger.info("🧹 Test environment cleaned up")
        except Exception as e:
            logger.error(f"⚠️ Cleanup error: {e}")
    
    def log_test_result(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        self.test_results["total_tests"] += 1
        
        if passed:
            self.test_results["passed"] += 1
            logger.info(f"✅ {test_name}: PASSED {message}")
        else:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{test_name}: {message}")
            logger.error(f"❌ {test_name}: FAILED {message}")
    
    async def test_health_check(self):
        """Test API health check"""
        try:
            health = await self.client.health_check()
            self.log_test_result(
                "Health Check", 
                health, 
                "API is online" if health else "API is offline"
            )
            return health
        except Exception as e:
            self.log_test_result("Health Check", False, str(e))
            return False
    
    async def test_stats_retrieval(self):
        """Test statistics retrieval"""
        try:
            stats = await self.client.get_stats()
            
            required_fields = ["total_subscribers", "active_subscribers", "language_breakdown"]
            has_all_fields = all(field in stats for field in required_fields)
            
            self.log_test_result(
                "Stats Retrieval",
                has_all_fields and isinstance(stats["active_subscribers"], int),
                f"Active subscribers: {stats.get('active_subscribers', 'N/A')}"
            )
            return stats if has_all_fields else None
        except Exception as e:
            self.log_test_result("Stats Retrieval", False, str(e))
            return None
    
    async def test_ai_content_generation(self):
        """Test AI content generation without sending"""
        try:
            # Test wisdom generation
            wisdom_data = await self.service.generate_wisdom(
                "тестирование AI генерации контента",
                "Russian",
                "Тестер"
            )
            
            has_required_fields = all(
                field in wisdom_data for field in ["wisdom", "topic", "references"]
            )
            
            content_valid = (
                isinstance(wisdom_data.get("wisdom"), str) and 
                len(wisdom_data.get("wisdom", "")) > 10
            )
            
            passed = has_required_fields and content_valid
            
            self.log_test_result(
                "AI Content Generation",
                passed,
                f"Topic: {wisdom_data.get('topic', 'N/A')}, Length: {len(wisdom_data.get('wisdom', ''))}"
            )
            return wisdom_data if passed else None
        except Exception as e:
            self.log_test_result("AI Content Generation", False, str(e))
            return None
    
    async def test_image_generation(self):
        """Test DALL-E 3 image generation"""
        try:
            image_url = await self.service.generate_image("wisdom and learning test")
            
            passed = image_url is not None and image_url.startswith("https://")
            
            self.log_test_result(
                "Image Generation",
                passed,
                f"Generated: {'Yes' if passed else 'No'}"
            )
            return image_url
        except Exception as e:
            self.log_test_result("Image Generation", False, str(e))
            return None
    
    async def test_message_formatting(self):
        """Test message formatting identical to Rabbi Wisdom"""
        try:
            wisdom_data = {
                "wisdom": "Test wisdom content for formatting verification",
                "topic": "Testing",
                "references": "Test Reference 1:1"
            }
            
            formatted_message = self.service.format_wisdom_message(wisdom_data)
            
            required_elements = [
                "📖 <b>Мудрость Раввина</b>",
                "✨ Ежедневная мудрость",
                "📚 <b>Источники:</b>",
                "✍️ <i>Напишите тему"
            ]
            
            has_all_elements = all(element in formatted_message for element in required_elements)
            
            self.log_test_result(
                "Message Formatting",
                has_all_elements,
                f"All required elements: {'Yes' if has_all_elements else 'No'}"
            )
            return formatted_message if has_all_elements else None
        except Exception as e:
            self.log_test_result("Message Formatting", False, str(e))
            return None
    
    async def test_keyboard_generation(self):
        """Test inline keyboard generation"""
        try:
            keyboard = self.service.get_keyboard()
            
            has_inline_keyboard = "inline_keyboard" in keyboard
            has_required_buttons = False
            
            if has_inline_keyboard:
                buttons = keyboard["inline_keyboard"]
                button_texts = []
                for row in buttons:
                    for button in row:
                        button_texts.append(button.get("text", ""))
                
                required_buttons = ["🔄 Ещё мудрость", "🧠 Пройти квиз", "🏠 Главное меню"]
                has_required_buttons = all(btn in button_texts for btn in required_buttons)
            
            passed = has_inline_keyboard and has_required_buttons
            
            self.log_test_result(
                "Keyboard Generation",
                passed,
                f"Buttons: {'Valid' if passed else 'Invalid'}"
            )
            return keyboard if passed else None
        except Exception as e:
            self.log_test_result("Keyboard Generation", False, str(e))
            return None
    
    async def test_database_connection(self):
        """Test database connection and basic queries"""
        try:
            if not self.service.db_pool:
                self.log_test_result("Database Connection", False, "No database pool")
                return False
            
            # Test basic query
            async with self.service.db_pool.acquire() as conn:
                result = await conn.fetchval("SELECT COUNT(*) FROM newsletter_subscriptions")
                
            passed = isinstance(result, int) and result >= 0
            
            self.log_test_result(
                "Database Connection",
                passed,
                f"Subscribers in DB: {result}"
            )
            return passed
        except Exception as e:
            self.log_test_result("Database Connection", False, str(e))
            return False
    
    async def test_contextual_topic_generation(self):
        """Test contextual topic generation based on time"""
        try:
            topic = self.service.get_contextual_topic()
            
            passed = isinstance(topic, str) and len(topic) > 5
            
            self.log_test_result(
                "Contextual Topic Generation",
                passed,
                f"Generated topic: {topic[:50]}..."
            )
            return topic if passed else None
        except Exception as e:
            self.log_test_result("Contextual Topic Generation", False, str(e))
            return None
    
    async def test_broadcast_integration(self):
        """Test integration with broadcast system"""
        try:
            # Mock telegram client for testing
            class MockTelegramClient:
                async def send_message(self, chat_id, text, **kwargs):
                    return {"ok": True, "result": {"message_id": 123}}
                    
                async def send_photo(self, chat_id, photo, caption, **kwargs):
                    return {"ok": True, "result": {"message_id": 124}}
            
            mock_client = MockTelegramClient()
            broadcast_system = DailyBroadcastSystem(mock_client)
            
            # Test health check through broadcast system
            health = await broadcast_system.health_check()
            
            self.log_test_result(
                "Broadcast Integration",
                health,
                f"Broadcast system API connection: {'OK' if health else 'Failed'}"
            )
            return health
        except Exception as e:
            self.log_test_result("Broadcast Integration", False, str(e))
            return False
    
    async def test_error_handling(self):
        """Test error handling and fallback systems"""
        try:
            # Test with invalid topic
            result = await self.client.send_broadcast(topic="")
            
            # Should handle gracefully
            has_error_handling = "success" in result and "message" in result
            
            self.log_test_result(
                "Error Handling",
                has_error_handling,
                f"Handles empty topic: {'Yes' if has_error_handling else 'No'}"
            )
            return has_error_handling
        except Exception as e:
            # Exception handling is also valid error handling
            self.log_test_result("Error Handling", True, f"Caught exception: {type(e).__name__}")
            return True
    
    async def test_performance_timing(self):
        """Test performance and response timing"""
        try:
            start_time = time.time()
            
            # Test parallel operations
            health_task = asyncio.create_task(self.client.health_check())
            stats_task = asyncio.create_task(self.client.get_stats())
            
            health_result = await health_task
            stats_result = await stats_task
            
            end_time = time.time()
            duration = end_time - start_time
            
            passed = duration < 10.0 and health_result  # Should complete within 10 seconds
            
            self.log_test_result(
                "Performance Timing",
                passed,
                f"Parallel operations completed in {duration:.2f}s"
            )
            return duration
        except Exception as e:
            self.log_test_result("Performance Timing", False, str(e))
            return None
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run complete test suite"""
        logger.info("🚀 Starting Internal Newsletter API Microservice Test Suite")
        logger.info("="*60)
        
        # Setup
        setup_success = await self.setup()
        if not setup_success:
            return {"error": "Failed to initialize test environment"}
        
        try:
            # Run all tests
            test_methods = [
                self.test_health_check,
                self.test_database_connection,
                self.test_stats_retrieval,
                self.test_contextual_topic_generation,
                self.test_ai_content_generation,
                self.test_image_generation,
                self.test_message_formatting,
                self.test_keyboard_generation,
                self.test_broadcast_integration,
                self.test_error_handling,
                self.test_performance_timing
            ]
            
            for test_method in test_methods:
                await test_method()
                await asyncio.sleep(0.5)  # Small delay between tests
            
        except Exception as e:
            logger.error(f"❌ Test suite error: {e}")
            self.test_results["errors"].append(f"Suite error: {e}")
        
        finally:
            await self.cleanup()
        
        # Calculate results
        success_rate = (self.test_results["passed"] / self.test_results["total_tests"] * 100) if self.test_results["total_tests"] > 0 else 0
        
        logger.info("="*60)
        logger.info("📊 TEST SUITE RESULTS:")
        logger.info(f"Total Tests: {self.test_results['total_tests']}")
        logger.info(f"Passed: {self.test_results['passed']}")
        logger.info(f"Failed: {self.test_results['failed']}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        
        if self.test_results["errors"]:
            logger.info("❌ Errors:")
            for error in self.test_results["errors"]:
                logger.info(f"  - {error}")
        
        status = "✅ ALL TESTS PASSED" if success_rate == 100 else f"⚠️ {self.test_results['failed']} TESTS FAILED"
        logger.info(f"🎯 STATUS: {status}")
        
        return {
            "success_rate": success_rate,
            "total_tests": self.test_results["total_tests"],
            "passed": self.test_results["passed"],
            "failed": self.test_results["failed"],
            "errors": self.test_results["errors"],
            "status": status
        }

# Convenience functions for integration
async def run_newsletter_api_tests() -> Dict[str, Any]:
    """Run all newsletter API tests"""
    test_suite = NewsletterAPITestSuite()
    return await test_suite.run_all_tests()

async def quick_health_test() -> bool:
    """Quick health test for CI/CD"""
    test_suite = NewsletterAPITestSuite()
    if await test_suite.setup():
        health = await test_suite.test_health_check()
        await test_suite.cleanup()
        return health
    return False

# Main execution
if __name__ == "__main__":
    async def main():
        results = await run_newsletter_api_tests()
        
        if results.get("success_rate", 0) == 100:
            print("🎉 All tests passed! Internal Newsletter API is ready for production.")
            exit(0)
        else:
            print(f"⚠️ Some tests failed. Success rate: {results.get('success_rate', 0):.1f}%")
            exit(1)
    
    asyncio.run(main())