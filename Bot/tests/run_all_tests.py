#!/usr/bin/env python3
"""
Комплексный запуск всех автотестов для Torah Bot
"""
import sys
import os
import unittest
import time
from io import StringIO

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

def run_all_tests():
    """Запуск всех тестов с детальным отчетом"""
    print("🧪 TORAH BOT - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print(f"⏰ Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    # Захватываем вывод для детального анализа
    test_output = StringIO()
    
    # Список всех тестовых модулей
    test_modules = [
        'test_image_generation',
        'test_language_integration'
    ]
    
    total_tests = 0
    total_failures = 0
    total_errors = 0
    total_success = 0
    
    results = {}
    
    for module_name in test_modules:
        print(f"📋 TESTING MODULE: {module_name}")
        print("-" * 40)
        
        try:
            # Импорт модуля
            module = __import__(module_name)
            
            # Создаем test suite
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(module)
            
            # Запуск тестов с захватом вывода
            runner = unittest.TextTestRunner(stream=test_output, verbosity=2)
            result = runner.run(suite)
            
            # Подсчет результатов
            module_tests = result.testsRun
            module_failures = len(result.failures)
            module_errors = len(result.errors)
            module_success = module_tests - module_failures - module_errors
            
            total_tests += module_tests
            total_failures += module_failures
            total_errors += module_errors
            total_success += module_success
            
            results[module_name] = {
                'tests': module_tests,
                'success': module_success,
                'failures': module_failures,
                'errors': module_errors,
                'passed': result.wasSuccessful()
            }
            
            # Вывод результатов модуля
            status = "✅ PASSED" if result.wasSuccessful() else "❌ FAILED"
            print(f"{status} - {module_success}/{module_tests} tests passed")
            
            if module_failures > 0:
                print(f"  ⚠️ Failures: {module_failures}")
            if module_errors > 0:
                print(f"  💥 Errors: {module_errors}")
                
        except Exception as e:
            print(f"❌ MODULE IMPORT ERROR: {e}")
            total_errors += 1
            results[module_name] = {'error': str(e)}
        
        print("")
    
    # Финальный отчет
    print("📊 FINAL TEST REPORT")
    print("=" * 60)
    
    for module, result in results.items():
        if 'error' in result:
            print(f"❌ {module}: IMPORT ERROR - {result['error']}")
        else:
            status = "✅" if result['passed'] else "❌"
            print(f"{status} {module}: {result['success']}/{result['tests']} passed")
    
    print("")
    print(f"📈 OVERALL STATISTICS:")
    print(f"   Total Tests: {total_tests}")
    print(f"   ✅ Success: {total_success}")
    print(f"   ⚠️ Failures: {total_failures}")
    print(f"   💥 Errors: {total_errors}")
    
    success_rate = (total_success / total_tests * 100) if total_tests > 0 else 0
    print(f"   📊 Success Rate: {success_rate:.1f}%")
    
    overall_passed = total_failures == 0 and total_errors == 0
    
    print("")
    if overall_passed:
        print("🎉 ALL TESTS PASSED! System ready for deployment.")
    else:
        print("⚠️ Some tests failed. Review and fix issues before deployment.")
    
    print(f"⏱️ Completed: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return overall_passed, results


if __name__ == "__main__":
    success, detailed_results = run_all_tests()
    sys.exit(0 if success else 1)