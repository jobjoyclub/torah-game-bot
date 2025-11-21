#!/usr/bin/env python3
"""
Автотесты для новой системы генерации изображений
Тестирует интеграцию PromptLoader, адаптивные темы и качество промптов
"""
import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from torah_bot.prompt_loader import PromptLoader


class TestImageGenerationSystem(unittest.TestCase):
    """Тесты для улучшенной системы генерации изображений"""
    
    def setUp(self):
        """Инициализация тестовых данных"""
        self.prompt_loader = PromptLoader()
    
    def test_wisdom_image_prompt_loading(self):
        """Тест загрузки промпта для изображений из файла"""
        try:
            prompt = self.prompt_loader.get_wisdom_image_prompt(
                topic="family wisdom", 
                theme_elements="Family gathering elements"
            )
            
            # Проверяем что промпт содержит ключевые элементы
            self.assertIn("family wisdom", prompt)
            self.assertIn("Family gathering elements", prompt)
            self.assertIn("Pixar 3D", prompt)
            self.assertIn("no text", prompt)
            print("✅ PASSED: Wisdom image prompt loading")
            
        except Exception as e:
            print(f"❌ FAILED: Wisdom image prompt loading - {e}")
            raise
    
    def test_fallback_image_prompt(self):
        """Тест fallback промпта при недоступности файла"""
        # Mock файловая ошибка
        with patch.object(self.prompt_loader, 'load_prompt', side_effect=FileNotFoundError()):
            prompt = self.prompt_loader.get_wisdom_image_prompt("test topic")
            
            # Проверяем fallback промпт
            self.assertIn("test topic", prompt)
            self.assertIn("Pixar 3D style", prompt)
            self.assertIn("no text", prompt)
            print("✅ PASSED: Fallback image prompt system")
    
    def test_theme_elements_mapping_english(self):
        """Тест адаптивной тематики для английских тем"""
        test_cases = [
            ("family wisdom", "Family gathering around Shabbat table"),
            ("prayer guidance", "Tallit and tefillin"),
            ("work ethics", "Ancient craftsman's tools"),
            ("study habits", "Open books, scrolls, candlelit study room"),
            ("peace and harmony", "Dove with olive branch")
        ]
        
        for topic, expected_element in test_cases:
            elements = self.prompt_loader.get_theme_elements(topic)
            self.assertIn(expected_element.split(",")[0], elements)
            print(f"✅ PASSED: Theme mapping for '{topic}'")
    
    def test_theme_elements_mapping_russian(self):
        """Тест адаптивной тематики для русских тем"""
        test_cases = [
            ("добрые дела и помощь", "Hands giving charity"),
            ("семья и дети", "Семейный ужин в Шаббат"),
            ("мудрость предков", "Мудрый раввин с книгами"),
            ("молитва и духовность", "Талит и тфилин")
        ]
        
        for topic, expected_element in test_cases:
            elements = self.prompt_loader.get_theme_elements(topic)
            self.assertIn(expected_element.split(",")[0], elements)
            print(f"✅ PASSED: Russian theme mapping for '{topic}'")
    
    def test_default_theme_elements(self):
        """Тест дефолтных элементов для неопознанных тем"""
        unknown_topic = "completely unknown random topic xyz"
        elements = self.prompt_loader.get_theme_elements(unknown_topic)
        self.assertEqual(elements, "Traditional Jewish symbols, peaceful contemplative scene")
        print("✅ PASSED: Default theme elements for unknown topics")
    
    def test_prompt_file_structure(self):
        """Тест структуры файла промпта"""
        try:
            with open("src/torah_bot/prompts/wisdom_image.txt", 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Проверяем наличие ключевых секций
            self.assertIn("{topic}", content)
            self.assertIn("{theme_specific_elements}", content)
            self.assertIn("Pixar", content)
            self.assertIn("no text", content)
            self.assertIn("spiritual", content.lower())
            
            print("✅ PASSED: Prompt file structure validation")
            
        except FileNotFoundError:
            print("❌ FAILED: wisdom_image.txt file not found")
            raise
    
    def test_hd_quality_upgrade(self):
        """Тест что система использует HD качество"""
        # Мокаем OpenAI клиент для проверки параметров
        with patch('torah_bot.simple_bot.openai_client') as mock_client:
            mock_response = Mock()
            mock_response.data = [Mock()]
            mock_response.data[0].url = "https://test-image.com/image.jpg"
            mock_client.images.generate.return_value = mock_response
            
            # Импортируем и создаем экземпляр класса для тестирования
            from torah_bot.simple_bot import OptimizedRabbiModule
            from torah_bot.simple_bot import ProductionSessionManager, SmartLogger
            
            session_manager = ProductionSessionManager()
            analytics = SmartLogger()
            prompt_loader = PromptLoader()
            
            rabbi_module = OptimizedRabbiModule(session_manager, analytics, Mock(), prompt_loader)
            
            # Запускаем генерацию изображения
            import asyncio
            result = asyncio.run(rabbi_module.generate_image("test topic"))
            
            # Проверяем что вызов был с HD качеством
            mock_client.images.generate.assert_called_once()
            call_args = mock_client.images.generate.call_args
            self.assertEqual(call_args[1]['quality'], 'hd')
            self.assertEqual(call_args[1]['size'], '1024x1024')
            self.assertEqual(call_args[1]['model'], 'dall-e-3')
            
            print("✅ PASSED: HD quality and proper DALL-E parameters")


class TestPromptLoaderIntegration(unittest.TestCase):
    """Тесты интеграции PromptLoader с новыми методами"""
    
    def setUp(self):
        self.prompt_loader = PromptLoader()
    
    def test_cache_functionality(self):
        """Тест кеширования новых промптов"""
        # Первый вызов должен загрузить из файла
        prompt1 = self.prompt_loader.get_wisdom_image_prompt("test", "elements")
        
        # Второй вызов должен использовать кеш
        prompt2 = self.prompt_loader.get_wisdom_image_prompt("test", "elements")
        
        self.assertEqual(prompt1, prompt2)
        print("✅ PASSED: Image prompt caching")
    
    def test_cache_reload(self):
        """Тест очистки кеша"""
        # Загружаем промпт
        self.prompt_loader.get_wisdom_image_prompt("test", "elements")
        self.assertGreater(len(self.prompt_loader._cache), 0)
        
        # Очищаем кеш
        self.prompt_loader.reload_cache()
        self.assertEqual(len(self.prompt_loader._cache), 0)
        
        print("✅ PASSED: Cache reload functionality")


def run_image_generation_tests():
    """Запуск всех тестов генерации изображений"""
    print("\n🧪 RUNNING IMAGE GENERATION TESTS")
    print("=" * 50)
    
    # Создаем test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Добавляем тесты
    suite.addTests(loader.loadTestsFromTestCase(TestImageGenerationSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestPromptLoaderIntegration))
    
    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Возвращаем результат
    return result.wasSuccessful(), len(result.failures), len(result.errors)


if __name__ == "__main__":
    success, failures, errors = run_image_generation_tests()
    print(f"\n📊 TEST RESULTS: Success: {success}, Failures: {failures}, Errors: {errors}")
    sys.exit(0 if success else 1)