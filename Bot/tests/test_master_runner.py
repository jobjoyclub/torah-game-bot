#!/usr/bin/env python3
"""
Master Test Runner - All Missing Module Tests
Главный запускатель тестов для всех недостающих модулей
"""

import asyncio
import os
import sys
import importlib

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

class MasterTestRunner:
    def __init__(self):
        self.total_results = {"passed": 0, "failed": 0, "total_tests": 0, "test_suites": 0}
        self.suite_results = []
    
    async def run_test_suite(self, test_module_name: str, test_function_name: str):
        """Run individual test suite"""
        try:
            print(f"\n{'='*50}")
            print(f"🧪 RUNNING: {test_module_name}")
            print(f"{'='*50}")
            
            # Import test module
            test_module = importlib.import_module(f"tests.{test_module_name}")
            test_function = getattr(test_module, test_function_name)
            
            # Run test
            success = await test_function()
            
            # Extract results if available
            if hasattr(test_module, 'TestPromptLoader'):
                test_class = getattr(test_module, 'TestPromptLoader')
            elif hasattr(test_module, 'TestSimpleBot'):
                test_class = getattr(test_module, 'TestSimpleBot')
            elif hasattr(test_module, 'TestAdminCommands'):
                test_class = getattr(test_module, 'TestAdminCommands')
            elif hasattr(test_module, 'TestQuizTopics'):
                test_class = getattr(test_module, 'TestQuizTopics')
            elif hasattr(test_module, 'TestDatabaseInit'):
                test_class = getattr(test_module, 'TestDatabaseInit')
            elif hasattr(test_module, 'TestDeploymentConfig'):
                test_class = getattr(test_module, 'TestDeploymentConfig')
            else:
                test_class = None
            
            # Record results
            suite_result = {
                "name": test_module_name,
                "success": success,
                "passed": 0,
                "failed": 0,
                "total": 0
            }
            
            if test_class and hasattr(test_class, '__init__'):
                # Try to get test results
                test_instance = test_class()
                if hasattr(test_instance, 'test_results'):
                    results = test_instance.test_results
                    suite_result["passed"] = results.get("passed", 0)
                    suite_result["failed"] = results.get("failed", 0)
                    suite_result["total"] = suite_result["passed"] + suite_result["failed"]
            
            self.suite_results.append(suite_result)
            self.total_results["test_suites"] += 1
            
            if success:
                print(f"✅ {test_module_name}: SUCCESS")
            else:
                print(f"❌ {test_module_name}: FAILED")
                
            return success
            
        except Exception as e:
            print(f"💥 {test_module_name}: EXCEPTION - {str(e)}")
            self.suite_results.append({
                "name": test_module_name,
                "success": False,
                "error": str(e),
                "passed": 0,
                "failed": 1,
                "total": 1
            })
            self.total_results["test_suites"] += 1
            return False
    
    async def run_all_missing_tests(self):
        """Run all missing module tests"""
        print("🚀 STARTING COMPREHENSIVE TEST SUITE")
        print("All Missing Module Tests")
        print("="*60)
        
        # Test suites to run
        test_suites = [
            ("test_prompt_loader", "run_prompt_loader_tests"),
            ("test_simple_bot", "run_simple_bot_tests"),
            ("test_admin_commands", "run_admin_commands_tests"),
            ("test_quiz_topics", "run_quiz_topics_tests"),
            ("test_database_init", "run_database_init_tests"),
            ("test_deployment_config", "run_deployment_config_tests")
        ]
        
        # Run each test suite
        results = []
        for test_module, test_function in test_suites:
            result = await self.run_test_suite(test_module, test_function)
            results.append(result)
        
        # Compile final results
        successful_suites = sum(1 for r in results if r)
        failed_suites = len(results) - successful_suites
        
        total_passed = sum(suite["passed"] for suite in self.suite_results)
        total_failed = sum(suite["failed"] for suite in self.suite_results)
        total_tests = total_passed + total_failed
        
        overall_success_rate = (successful_suites / len(results) * 100) if results else 0
        test_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        # Print comprehensive results
        print("\n" + "="*60)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("="*60)
        
        print(f"\n🧪 TEST SUITE SUMMARY:")
        print(f"   Total Suites: {len(results)}")
        print(f"   Successful: {successful_suites}")
        print(f"   Failed: {failed_suites}")
        print(f"   Suite Success Rate: {overall_success_rate:.1f}%")
        
        print(f"\n🎯 INDIVIDUAL TEST SUMMARY:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {total_passed}")
        print(f"   Failed: {total_failed}")
        print(f"   Test Success Rate: {test_success_rate:.1f}%")
        
        print(f"\n📋 DETAILED RESULTS:")
        for suite in self.suite_results:
            status = "✅" if suite["success"] else "❌"
            if "error" in suite:
                print(f"   {status} {suite['name']}: ERROR - {suite['error']}")
            else:
                print(f"   {status} {suite['name']}: {suite['passed']}/{suite['total']} tests passed")
        
        # Final status
        if overall_success_rate >= 80 and test_success_rate >= 70:
            final_status = "🎉 EXCELLENT - Ready for production!"
        elif overall_success_rate >= 60 and test_success_rate >= 60:
            final_status = "✅ GOOD - Acceptable test coverage"
        elif overall_success_rate >= 40:
            final_status = "⚠️ FAIR - Needs improvement"
        else:
            final_status = "❌ POOR - Requires significant work"
        
        print(f"\n🏆 FINAL STATUS: {final_status}")
        print(f"📈 Overall Success: {overall_success_rate:.1f}% | Test Success: {test_success_rate:.1f}%")
        
        return overall_success_rate >= 60

# Main execution
async def run_comprehensive_test_suite():
    """Main function to run all tests"""
    runner = MasterTestRunner()
    return await runner.run_all_missing_tests()

if __name__ == "__main__":
    try:
        result = asyncio.run(run_comprehensive_test_suite())
        exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⏸️ Test execution interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        exit(1)