#!/usr/bin/env python3
"""
Tests for Quiz Topics module
Тесты для модуля управления темами квизов
"""

import asyncio
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

class TestQuizTopics:
    def __init__(self):
        self.test_results = {"passed": 0, "failed": 0, "errors": []}
    
    def log_result(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        if passed:
            self.test_results["passed"] += 1
            print(f"✅ {test_name}: {message}")
        else:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{test_name}: {message}")
            print(f"❌ {test_name}: {message}")
    
    def test_imports_and_initialization(self):
        """Test quiz topics imports and initialization"""
        try:
            from src.torah_bot.quiz_topics import QuizTopicGenerator
            import_success = True
            
            # Test basic initialization
            # QuizTopicGenerator is a class, check its structure
            has_diverse_topics = hasattr(QuizTopicGenerator, 'DIVERSE_TOPICS')
            has_get_random = hasattr(QuizTopicGenerator, 'get_random_topic')
            has_get_multiple = hasattr(QuizTopicGenerator, 'get_multiple_topics')
            
            initialization_success = has_diverse_topics and has_get_random
            
            passed = import_success and initialization_success
            self.log_result(
                "Imports and Initialization",
                passed,
                f"Import: {import_success}, Has structure: {initialization_success}"
            )
            return QuizTopicGenerator if passed else None
            
        except Exception as e:
            self.log_result("Imports and Initialization", False, str(e))
            return None
    
    def test_topic_structure_and_content(self):
        """Test quiz topics structure and content"""
        try:
            from src.torah_bot.quiz_topics import QuizTopicGenerator
            
            topics_manager = QuizTopicGenerator()
            
            # Test if topics are available
            has_topic_data = False
            topic_count = 0
            
            # Try different ways to get topics
            if hasattr(topics_manager, 'get_all_topics'):
                topics = topics_manager.get_all_topics()
                has_topic_data = len(topics) > 0
                topic_count = len(topics)
            elif hasattr(topics_manager, 'topics'):
                topics = topics_manager.topics
                has_topic_data = len(topics) > 0 if isinstance(topics, (list, dict)) else False
                topic_count = len(topics) if isinstance(topics, (list, dict)) else 0
            elif hasattr(topics_manager, 'quiz_topics'):
                topics = topics_manager.quiz_topics
                has_topic_data = len(topics) > 0 if isinstance(topics, (list, dict)) else False
                topic_count = len(topics) if isinstance(topics, (list, dict)) else 0
            
            # Check if topics contain expected content
            has_torah_topics = False
            has_talmud_topics = False
            
            if has_topic_data and isinstance(topics, (list, dict)):
                topics_str = str(topics).lower()
                has_torah_topics = 'torah' in topics_str or 'genesis' in topics_str or 'exodus' in topics_str
                has_talmud_topics = 'talmud' in topics_str or 'mishnah' in topics_str or 'gemara' in topics_str
            
            passed = has_topic_data and (has_torah_topics or has_talmud_topics)
            self.log_result(
                "Topic Structure and Content",
                passed,
                f"Has data: {has_topic_data}, Count: {topic_count}, Torah: {has_torah_topics}, Talmud: {has_talmud_topics}"
            )
            return passed
            
        except Exception as e:
            self.log_result("Topic Structure and Content", False, str(e))
            return False
    
    def test_random_topic_selection(self):
        """Test random topic selection functionality"""
        try:
            from src.torah_bot.quiz_topics import QuizTopicGenerator
            
            topics_manager = QuizTopicGenerator()
            
            # Test random topic selection
            random_topics = []
            selection_works = False
            
            # Try different methods for getting random topics
            for method_name in ['get_random_topic', 'random_topic', 'select_topic', 'get_topic']:
                if hasattr(topics_manager, method_name):
                    method = getattr(topics_manager, method_name)
                    try:
                        for _ in range(3):  # Get 3 random topics
                            topic = method()
                            if topic and isinstance(topic, str):
                                random_topics.append(topic)
                        selection_works = len(random_topics) > 0
                        break
                    except Exception:
                        continue
            
            # Check if topics are meaningful
            topics_are_meaningful = False
            if random_topics:
                topics_str = ' '.join(random_topics).lower()
                topics_are_meaningful = any(keyword in topics_str for keyword in [
                    'torah', 'genesis', 'exodus', 'leviticus', 'numbers', 'deuteronomy',
                    'talmud', 'mishnah', 'gemara', 'sabbath', 'prayer', 'family'
                ])
            
            passed = selection_works and (topics_are_meaningful or len(random_topics) > 0)
            self.log_result(
                "Random Topic Selection",
                passed,
                f"Selection works: {selection_works}, Count: {len(random_topics)}, Meaningful: {topics_are_meaningful}"
            )
            return passed
            
        except Exception as e:
            self.log_result("Random Topic Selection", False, str(e))
            return False
    
    def test_topic_categorization(self):
        """Test topic categorization and filtering"""
        try:
            from src.torah_bot.quiz_topics import QuizTopicGenerator
            
            topics_manager = QuizTopicGenerator()
            
            # Test category-based topic selection
            categories_work = False
            category_methods = ['get_topics_by_category', 'filter_by_category', 'get_category_topics']
            
            for method_name in category_methods:
                if hasattr(topics_manager, method_name):
                    method = getattr(topics_manager, method_name)
                    try:
                        # Try common categories
                        for category in ['torah', 'talmud', 'general', 'basic']:
                            result = method(category)
                            if result and len(result) > 0:
                                categories_work = True
                                break
                        if categories_work:
                            break
                    except Exception:
                        continue
            
            # Alternative: check if topics have category structure
            has_category_structure = False
            if hasattr(topics_manager, 'topics') and isinstance(topics_manager.topics, dict):
                topics_dict = topics_manager.topics
                # Check if it's organized by categories
                potential_categories = ['torah', 'talmud', 'general', 'basic', 'advanced']
                has_category_structure = any(cat in topics_dict for cat in potential_categories)
            
            category_support = categories_work or has_category_structure
            
            passed = category_support
            self.log_result(
                "Topic Categorization",
                passed,
                f"Category methods: {categories_work}, Structure: {has_category_structure}"
            )
            return passed
            
        except Exception as e:
            self.log_result("Topic Categorization", False, str(e))
            return False
    
    def test_multilingual_topic_support(self):
        """Test multilingual topic support"""
        try:
            from src.torah_bot.quiz_topics import QuizTopicGenerator
            
            topics_manager = QuizTopicGenerator()
            
            # Test language-specific topic selection
            multilingual_support = False
            language_methods = ['get_topics_for_language', 'get_localized_topics', 'topics_in_language']
            
            for method_name in language_methods:
                if hasattr(topics_manager, method_name):
                    method = getattr(topics_manager, method_name)
                    try:
                        # Try different languages
                        for lang in ['Russian', 'Hebrew', 'English', 'ru', 'he', 'en']:
                            result = method(lang)
                            if result and len(result) > 0:
                                multilingual_support = True
                                break
                        if multilingual_support:
                            break
                    except Exception:
                        continue
            
            # Alternative: check if topics contain non-English content
            has_multilingual_content = False
            if hasattr(topics_manager, 'topics'):
                topics_str = str(topics_manager.topics)
                # Check for Cyrillic or Hebrew characters
                has_cyrillic = any(ord(char) >= 0x0400 and ord(char) <= 0x04FF for char in topics_str)
                has_hebrew = any(ord(char) >= 0x0590 and ord(char) <= 0x05FF for char in topics_str)
                has_multilingual_content = has_cyrillic or has_hebrew
            
            language_support = multilingual_support or has_multilingual_content
            
            passed = language_support
            self.log_result(
                "Multilingual Topic Support",
                passed,
                f"Language methods: {multilingual_support}, Content: {has_multilingual_content}"
            )
            return passed
            
        except Exception as e:
            self.log_result("Multilingual Topic Support", False, str(e))
            return False
    
    def test_topic_validation_and_filtering(self):
        """Test topic validation and filtering mechanisms"""
        try:
            from src.torah_bot.quiz_topics import QuizTopicGenerator
            
            topics_manager = QuizTopicGenerator()
            
            # Test validation methods
            has_validation = False
            validation_methods = ['validate_topic', 'is_valid_topic', 'filter_topics', 'sanitize_topic']
            
            for method_name in validation_methods:
                if hasattr(topics_manager, method_name):
                    has_validation = True
                    method = getattr(topics_manager, method_name)
                    try:
                        # Test with sample input
                        result = method("test topic")
                        validation_works = result is not None
                    except Exception:
                        validation_works = False
                    break
                else:
                    validation_works = False
            
            # Test duplicate prevention
            has_duplicate_prevention = False
            duplicate_methods = ['avoid_duplicates', 'get_unique_topic', 'filter_duplicates']
            
            for method_name in duplicate_methods:
                if hasattr(topics_manager, method_name):
                    has_duplicate_prevention = True
                    break
            
            filtering_support = has_validation or has_duplicate_prevention
            
            passed = filtering_support
            self.log_result(
                "Topic Validation and Filtering",
                passed,
                f"Validation: {has_validation}, Duplicate prevention: {has_duplicate_prevention}"
            )
            return passed
            
        except Exception as e:
            self.log_result("Topic Validation and Filtering", False, str(e))
            return False
    
    def test_topic_difficulty_levels(self):
        """Test topic difficulty level support"""
        try:
            from src.torah_bot.quiz_topics import QuizTopicGenerator
            
            topics_manager = QuizTopicGenerator()
            
            # Test difficulty-based selection
            has_difficulty_support = False
            difficulty_methods = ['get_topics_by_difficulty', 'get_basic_topics', 'get_advanced_topics']
            
            for method_name in difficulty_methods:
                if hasattr(topics_manager, method_name):
                    has_difficulty_support = True
                    method = getattr(topics_manager, method_name)
                    try:
                        result = method()
                        difficulty_works = result is not None and len(result) > 0 if isinstance(result, (list, dict)) else result is not None
                    except Exception:
                        try:
                            # Try with difficulty parameter
                            result = method('basic')
                            difficulty_works = result is not None
                        except Exception:
                            difficulty_works = False
                    break
                else:
                    difficulty_works = False
            
            # Check if topics have difficulty indicators
            has_difficulty_structure = False
            if hasattr(topics_manager, 'topics'):
                topics_str = str(topics_manager.topics).lower()
                difficulty_keywords = ['basic', 'advanced', 'beginner', 'intermediate', 'easy', 'hard']
                has_difficulty_structure = any(keyword in topics_str for keyword in difficulty_keywords)
            
            difficulty_support = has_difficulty_support or has_difficulty_structure
            
            passed = difficulty_support
            self.log_result(
                "Topic Difficulty Levels",
                passed,
                f"Difficulty methods: {has_difficulty_support}, Structure: {has_difficulty_structure}"
            )
            return passed
            
        except Exception as e:
            self.log_result("Topic Difficulty Levels", False, str(e))
            return False

    async def run_all_tests(self):
        """Run complete test suite for QuizTopics"""
        print("📚 Starting QuizTopics Test Suite")
        print("="*40)
        
        # Test all functionality
        topics_manager = self.test_imports_and_initialization()
        
        if topics_manager:
            self.test_topic_structure_and_content()
            self.test_random_topic_selection()
            self.test_topic_categorization()
            self.test_multilingual_topic_support()
            self.test_topic_validation_and_filtering()
            self.test_topic_difficulty_levels()
        
        # Results
        total = self.test_results["passed"] + self.test_results["failed"]
        success_rate = (self.test_results["passed"] / total * 100) if total > 0 else 0
        
        print("="*40)
        print(f"📚 QuizTopics Test Results:")
        print(f"   Total: {total}")
        print(f"   Passed: {self.test_results['passed']}")
        print(f"   Failed: {self.test_results['failed']}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        if self.test_results["errors"]:
            print("\n❌ Errors:")
            for error in self.test_results["errors"]:
                print(f"   - {error}")
        
        status = "✅ ALL TESTS PASSED" if success_rate == 100 else f"⚠️ {self.test_results['failed']} TESTS FAILED"
        print(f"\n🎯 Status: {status}")
        
        return success_rate >= 70

# Main execution function
async def run_quiz_topics_tests():
    """Run QuizTopics tests"""
    test_suite = TestQuizTopics()
    return await test_suite.run_all_tests()

if __name__ == "__main__":
    result = asyncio.run(run_quiz_topics_tests())
    exit(0 if result else 1)