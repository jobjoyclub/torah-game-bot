#!/usr/bin/env python3
"""
Автотесты для улучшенной fallback системы генерации изображений
"""
import sys
import os
import unittest
import asyncio
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))


class TestImageFallbackSystem(unittest.TestCase):
    """Тесты для новой robust fallback системы изображений"""
    
    def setUp(self):
        """Настройка тестовой среды"""
        from torah_bot.simple_bot import OptimizedRabbiModule, ProductionSessionManager, SmartLogger
        from torah_bot.prompt_loader import PromptLoader
        
        self.session_manager = ProductionSessionManager()
        self.analytics = SmartLogger()
        self.prompt_loader = PromptLoader()
        self.telegram_client = Mock()
        
        self.rabbi_module = OptimizedRabbiModule(
            self.session_manager, 
            self.analytics, 
            self.telegram_client, 
            self.prompt_loader
        )
    
    def test_no_openai_client_fallback(self):
        """Тест fallback когда OpenAI клиент недоступен"""
        with patch('torah_bot.simple_bot.openai_client', None):
            result = asyncio.run(self.rabbi_module.generate_image("test topic"))
            self.assertIsNone(result)
            print("✅ PASSED: No OpenAI client fallback")
    
    def test_multiple_prompt_fallback(self):
        """Тест каскадной системы fallback промптов"""
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].url = "https://test-image.com/success.jpg"
        
        with patch('torah_bot.simple_bot.openai_client') as mock_client:
            # Первый промпт неудачен, второй успешен
            mock_client.images.generate.side_effect = [
                Exception("Content policy violation"),  # Первый промпт падает
                mock_response  # Второй промпт работает
            ]
            
            result = asyncio.run(self.rabbi_module.generate_image("test topic"))
            self.assertEqual(result, "https://test-image.com/success.jpg")
            self.assertEqual(mock_client.images.generate.call_count, 2)
            print("✅ PASSED: Multiple prompt fallback system")
    
    def test_content_policy_error_handling(self):
        """Тест обработки ошибок content policy"""
        with patch('torah_bot.simple_bot.openai_client') as mock_client:
            mock_client.images.generate.side_effect = Exception("content_policy violation detected")
            
            result = asyncio.run(self.rabbi_module.generate_image("inappropriate content"))
            self.assertIsNone(result)  # Должен попробовать все prompts и вернуть None
            print("✅ PASSED: Content policy error handling")
    
    def test_rate_limit_error_with_delay(self):
        """Тест обработки rate limit с задержкой"""
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].url = "https://test-image.com/delayed-success.jpg"
        
        with patch('torah_bot.simple_bot.openai_client') as mock_client:
            with patch('asyncio.sleep') as mock_sleep:
                mock_client.images.generate.side_effect = [
                    Exception("rate_limit exceeded"),  # Первый вызов - rate limit
                    mock_response  # Второй вызов успешен
                ]
                
                result = asyncio.run(self.rabbi_module.generate_image("test topic"))
                
                # Проверяем что была задержка при rate limit
                mock_sleep.assert_called_with(2)
                self.assertEqual(result, "https://test-image.com/delayed-success.jpg")
                print("✅ PASSED: Rate limit handling with delay")
    
    def test_quota_error_immediate_stop(self):
        """Тест немедленной остановки при quota/billing ошибках"""
        with patch('torah_bot.simple_bot.openai_client') as mock_client:
            mock_client.images.generate.side_effect = Exception("quota exceeded")
            
            result = asyncio.run(self.rabbi_module.generate_image("test topic"))
            
            # При quota ошибке должен остановиться немедленно
            self.assertIsNone(result)
            self.assertEqual(mock_client.images.generate.call_count, 1)  # Только один вызов
            print("✅ PASSED: Quota error immediate stop")
    
    def test_empty_response_handling(self):
        """Тест обработки пустых ответов от DALL-E"""
        mock_empty_response = Mock()
        mock_empty_response.data = []  # Пустой массив
        
        mock_success_response = Mock()
        mock_success_response.data = [Mock()]
        mock_success_response.data[0].url = "https://test-image.com/retry-success.jpg"
        
        with patch('torah_bot.simple_bot.openai_client') as mock_client:
            mock_client.images.generate.side_effect = [
                mock_empty_response,     # Первый ответ пустой
                mock_success_response    # Второй ответ успешный
            ]
            
            result = asyncio.run(self.rabbi_module.generate_image("test topic"))
            
            self.assertEqual(result, "https://test-image.com/retry-success.jpg")
            self.assertEqual(mock_client.images.generate.call_count, 2)
            print("✅ PASSED: Empty response handling")
    
    def test_enhanced_prompt_generation_fallback(self):
        """Тест fallback при ошибке генерации enhanced промпта"""
        # Мокаем ошибку в prompt loader
        with patch.object(self.prompt_loader, 'get_theme_elements', side_effect=Exception("File error")):
            with patch.object(self.prompt_loader, 'get_wisdom_image_prompt', side_effect=Exception("File error")):
                
                # Должен использовать internal fallback
                result = self.rabbi_module._get_enhanced_image_prompt("family wisdom")
                
                self.assertIn("family wisdom", result)
                self.assertIn("Pixar style", result)
                print("✅ PASSED: Enhanced prompt generation fallback")
    
    def test_quality_degradation_on_fallback(self):
        """Тест снижения качества на fallback промптах"""
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].url = "https://test-image.com/standard-quality.jpg"
        
        with patch('torah_bot.simple_bot.openai_client') as mock_client:
            # Первый (HD) промпт падает, второй (standard) работает
            mock_client.images.generate.side_effect = [
                Exception("HD generation failed"),  # HD промпт падает
                mock_response  # Standard промпт работает
            ]
            
            result = asyncio.run(self.rabbi_module.generate_image("test topic"))
            
            self.assertEqual(result, "https://test-image.com/standard-quality.jpg")
            
            # Проверяем что второй вызов был с standard качеством
            calls = mock_client.images.generate.call_args_list
            self.assertEqual(calls[0][1]['quality'], 'hd')        # Первый вызов - HD
            self.assertEqual(calls[1][1]['quality'], 'standard')  # Второй вызов - Standard
            print("✅ PASSED: Quality degradation on fallback")


def run_fallback_tests():
    """Запуск всех тестов fallback системы"""
    print("\n🛡️ RUNNING IMAGE FALLBACK SYSTEM TESTS")
    print("=" * 55)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestImageFallbackSystem))
    
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    return result.wasSuccessful(), len(result.failures), len(result.errors)


if __name__ == "__main__":
    success, failures, errors = run_fallback_tests()
    print(f"\n📊 FALLBACK TESTS: Success: {success}, Failures: {failures}, Errors: {errors}")
    sys.exit(0 if success else 1)