#!/usr/bin/env python3
"""
Tests for PromptLoader module
Тесты для модуля загрузки промптов
"""

import asyncio
import os
import tempfile
import shutil
from unittest.mock import patch
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

try:
    from src.torah_bot.prompt_loader import PromptLoader
except ImportError:
    PromptLoader = None

class TestPromptLoader:
    def __init__(self):
        self.test_results = {"passed": 0, "failed": 0, "errors": []}
        self.temp_dir = None
        
    def setup_test_environment(self):
        """Create temporary directory with test prompt files"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test prompt files
        test_prompts = {
            "rabbi_wisdom.txt": "Rabbi wisdom template: {user_name} in {language} about {user_text}",
            "user_prompt_wisdom.txt": "User prompt for: {user_text}",  
            "torah_quiz.txt": "Quiz template: {topic} in {language}. Variety: {variety_instruction}. Warning: {duplicate_warning}",
            "quiz_variety_elements.txt": "Element 1\nElement 2\nElement 3\n",
            "wisdom_image.txt": "Image prompt: {topic} with elements: {theme_specific_elements}"
        }
        
        for filename, content in test_prompts.items():
            filepath = os.path.join(self.temp_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                
        return self.temp_dir
    
    def cleanup_test_environment(self):
        """Clean up temporary directory"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def log_result(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        if passed:
            self.test_results["passed"] += 1
            print(f"✅ {test_name}: {message}")
        else:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{test_name}: {message}")
            print(f"❌ {test_name}: {message}")
    
    def test_initialization(self):
        """Test PromptLoader initialization"""
        try:
            # Test with custom directory
            loader1 = PromptLoader(self.temp_dir)
            has_custom_dir = loader1.prompts_dir == self.temp_dir
            
            # Test with default directory
            loader2 = PromptLoader()
            has_default_dir = "prompts" in loader2.prompts_dir
            
            passed = has_custom_dir and has_default_dir
            self.log_result(
                "Initialization", 
                passed,
                f"Custom dir: {has_custom_dir}, Default dir: {has_default_dir}"
            )
            return loader1  # Return loader for other tests
            
        except Exception as e:
            self.log_result("Initialization", False, str(e))
            return None
    
    def test_load_prompt(self, loader):
        """Test basic prompt loading"""
        try:
            # Test successful loading
            content = loader.load_prompt("rabbi_wisdom.txt")
            content_loaded = len(content) > 0 and "Rabbi wisdom template" in content
            
            # Test caching (second load should be from cache)
            content2 = loader.load_prompt("rabbi_wisdom.txt") 
            cache_works = content == content2
            
            # Test file not found
            file_not_found_handled = False
            try:
                loader.load_prompt("nonexistent.txt")
            except FileNotFoundError:
                file_not_found_handled = True
            
            passed = content_loaded and cache_works and file_not_found_handled
            self.log_result(
                "Load Prompt",
                passed,
                f"Content: {content_loaded}, Cache: {cache_works}, Error handling: {file_not_found_handled}"
            )
            return passed
            
        except Exception as e:
            self.log_result("Load Prompt", False, str(e))
            return False
    
    def test_rabbi_wisdom_prompt(self, loader):
        """Test rabbi wisdom prompt generation"""
        try:
            prompt = loader.get_rabbi_wisdom_prompt(
                user_name="TestUser",
                language="English", 
                user_text="test topic"
            )
            
            has_all_params = all(param in prompt for param in ["TestUser", "English", "test topic"])
            is_formatted = "Rabbi wisdom template:" in prompt
            
            passed = has_all_params and is_formatted
            self.log_result(
                "Rabbi Wisdom Prompt",
                passed,
                f"All parameters: {has_all_params}, Formatted: {is_formatted}"
            )
            return passed
            
        except Exception as e:
            self.log_result("Rabbi Wisdom Prompt", False, str(e))
            return False
    
    def test_quiz_prompt(self, loader):
        """Test quiz prompt generation with variety"""
        try:
            prompt = loader.get_quiz_prompt(
                topic="Torah study",
                language="Russian",
                duplicate_warning="No duplicates"
            )
            
            has_topic = "Torah study" in prompt
            has_language = "Russian" in prompt
            has_variety = len(prompt) > 50  # Should include variety element
            has_warning = "No duplicates" in prompt
            
            passed = has_topic and has_language and has_variety and has_warning
            self.log_result(
                "Quiz Prompt",
                passed, 
                f"Topic: {has_topic}, Language: {has_language}, Variety: {has_variety}, Warning: {has_warning}"
            )
            return passed
            
        except Exception as e:
            self.log_result("Quiz Prompt", False, str(e))
            return False
    
    def test_theme_elements(self, loader):
        """Test theme elements mapping"""
        try:
            # Test known themes
            family_theme = loader.get_theme_elements("family dinner")
            wisdom_theme = loader.get_theme_elements("ancient wisdom") 
            unknown_theme = loader.get_theme_elements("unknown_topic_xyz")
            
            has_family = "Family gathering" in family_theme
            has_wisdom = "Ancient sage" in wisdom_theme or "tree of knowledge" in wisdom_theme
            has_default = "Traditional Jewish symbols" in unknown_theme
            
            passed = has_family and has_wisdom and has_default
            self.log_result(
                "Theme Elements",
                passed,
                f"Family: {has_family}, Wisdom: {has_wisdom}, Default: {has_default}"
            )
            return passed
            
        except Exception as e:
            self.log_result("Theme Elements", False, str(e))
            return False
    
    def test_cache_reload(self, loader):
        """Test cache clearing functionality"""
        try:
            # Load a prompt to cache it
            loader.load_prompt("rabbi_wisdom.txt")
            has_cache_before = len(loader._cache) > 0
            
            # Clear cache
            loader.reload_cache()
            cache_cleared = len(loader._cache) == 0
            
            passed = has_cache_before and cache_cleared
            self.log_result(
                "Cache Reload",
                passed,
                f"Had cache: {has_cache_before}, Cleared: {cache_cleared}"
            )
            return passed
            
        except Exception as e:
            self.log_result("Cache Reload", False, str(e))
            return False

    async def run_all_tests(self):
        """Run complete test suite for PromptLoader"""
        print("🧪 Starting PromptLoader Test Suite")
        print("="*40)
        
        # Setup test environment
        self.setup_test_environment()
        
        try:
            # Initialize loader
            loader = self.test_initialization()
            
            if loader:
                # Run all tests
                test_methods = [
                    (self.test_load_prompt, loader),
                    (self.test_rabbi_wisdom_prompt, loader),
                    (self.test_quiz_prompt, loader),
                    (self.test_theme_elements, loader),
                    (self.test_cache_reload, loader)
                ]
                
                for test_method, test_loader in test_methods:
                    test_method(test_loader)
                    
        finally:
            self.cleanup_test_environment()
        
        # Results
        total = self.test_results["passed"] + self.test_results["failed"]
        success_rate = (self.test_results["passed"] / total * 100) if total > 0 else 0
        
        print("="*40)
        print(f"📊 PromptLoader Test Results:")
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
        
        return success_rate >= 90

# Main execution function
async def run_prompt_loader_tests():
    """Run PromptLoader tests"""
    test_suite = TestPromptLoader()
    return await test_suite.run_all_tests()

if __name__ == "__main__":
    result = asyncio.run(run_prompt_loader_tests())
    exit(0 if result else 1)