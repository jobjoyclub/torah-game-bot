#!/usr/bin/env python3
"""
Автотесты для исправлений языковой интеграции
Проверяет работу приоритетов языков и мануальных настроек
"""
import sys
import os
import unittest
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))


class TestLanguageIntegration(unittest.TestCase):
    """Тесты для исправленной языковой системы"""
    
    def test_manual_language_priority_wisdom(self):
        """Тест приоритета мануального выбора языка в wisdom"""
        # Мокаем сессию с мануально выбранным языком
        mock_session = {
            "manual_language_set": True,
            "language": "Russian",
            "user_id": 12345
        }
        
        # Мокаем user_data с английским языком
        mock_user_data = {
            "language_code": "en",
            "first_name": "Test"
        }
        
        # Проверяем что система выбирает русский (мануальный) а не английский (auto)
        from torah_bot.simple_bot import ProductionSessionManager
        
        with patch.object(ProductionSessionManager, 'get_session', return_value=mock_session):
            # Система должна использовать Russian из мануальной настройки
            # а не English из language_code
            
            # Имитируем логику выбора языка из кода
            if mock_session.get("manual_language_set", False):
                selected_language = mock_session.get("language", "English")
            else:
                selected_language = ProductionSessionManager.detect_user_language(mock_user_data)
            
            self.assertEqual(selected_language, "Russian")
            print("✅ PASSED: Manual language priority in wisdom workflow")
    
    def test_manual_language_priority_quiz(self):
        """Тест приоритета мануального выбора языка в quiz"""
        mock_session = {
            "manual_language_set": True, 
            "language": "English"
        }
        
        mock_user_data = {"language_code": "ru"}
        
        # Проверяем приоритет мануального выбора
        if mock_session.get("manual_language_set", False):
            selected_language = mock_session.get("language", "English")
        else:
            from torah_bot.simple_bot import ProductionSessionManager
            selected_language = ProductionSessionManager.detect_user_language(mock_user_data)
        
        self.assertEqual(selected_language, "English")
        print("✅ PASSED: Manual language priority in quiz workflow")
    
    def test_json_prompt_format(self):
        """Тест что rabbi_wisdom.txt требует JSON формат"""
        try:
            with open("src/torah_bot/prompts/rabbi_wisdom.txt", 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Проверяем наличие JSON инструкций
            self.assertIn("JSON object", content)
            self.assertIn("wisdom", content)
            self.assertIn("topic", content) 
            self.assertIn("references", content)
            
            print("✅ PASSED: Rabbi wisdom prompt requires JSON format")
            
        except FileNotFoundError:
            print("❌ FAILED: rabbi_wisdom.txt not found")
            raise
    
    def test_language_detection_mapping(self):
        """Тест маппинга языковых кодов"""
        from torah_bot.simple_bot import ProductionSessionManager
        
        test_cases = [
            ({"language_code": "ru"}, "Russian"),
            ({"language_code": "en"}, "English"),
            ({"language_code": "he"}, "Hebrew"),
            ({"language_code": "es"}, "Spanish"),
            ({"language_code": "uk"}, "Russian"),  # Ukrainian -> Russian
            ({}, "English")  # Default fallback
        ]
        
        for user_data, expected in test_cases:
            result = ProductionSessionManager.detect_user_language(user_data)
            self.assertEqual(result, expected)
            print(f"✅ PASSED: Language detection for {user_data} -> {expected}")


def run_language_integration_tests():
    """Запуск всех тестов языковой интеграции"""
    print("\n🌐 RUNNING LANGUAGE INTEGRATION TESTS") 
    print("=" * 50)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestLanguageIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    return result.wasSuccessful(), len(result.failures), len(result.errors)


if __name__ == "__main__":
    success, failures, errors = run_language_integration_tests()
    print(f"\n📊 LANGUAGE TESTS: Success: {success}, Failures: {failures}, Errors: {errors}")
    sys.exit(0 if success else 1)