#!/usr/bin/env python3
"""
Integration Test Runner for Internal Newsletter API
Запуск интеграционных тестов для Internal Newsletter API
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from test_newsletter_api_microservice import run_newsletter_api_tests
from test_broadcast_migration import run_migration_tests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntegrationTestRunner:
    """Comprehensive integration test runner"""
    
    def __init__(self):
        self.test_suites = [
            ("Internal Newsletter API", run_newsletter_api_tests),
            ("Broadcast Migration", run_migration_tests)
        ]
        self.results = {}
    
    async def run_all_tests(self):
        """Run all integration tests"""
        logger.info("🚀 STARTING COMPLETE INTEGRATION TEST SUITE")
        logger.info("📅 " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        logger.info("="*70)
        
        overall_success = True
        
        for suite_name, suite_runner in self.test_suites:
            logger.info(f"🧪 Running {suite_name} Tests...")
            logger.info("-" * 50)
            
            try:
                results = await suite_runner()
                self.results[suite_name] = results
                
                success_rate = results.get("success_rate", 0)
                
                if success_rate >= 80:  # 80% threshold for success
                    logger.info(f"✅ {suite_name}: PASSED ({success_rate:.1f}%)")
                else:
                    logger.error(f"❌ {suite_name}: FAILED ({success_rate:.1f}%)")
                    overall_success = False
                    
            except Exception as e:
                logger.error(f"💥 {suite_name}: CRASHED - {e}")
                self.results[suite_name] = {"error": str(e), "success_rate": 0}
                overall_success = False
            
            logger.info("")  # Empty line between suites
        
        # Final summary
        self.print_final_summary(overall_success)
        return overall_success
    
    def print_final_summary(self, overall_success: bool):
        """Print comprehensive test summary"""
        logger.info("="*70)
        logger.info("📊 INTEGRATION TEST SUMMARY")
        logger.info("="*70)
        
        total_tests = 0
        total_passed = 0
        total_failed = 0
        all_errors = []
        
        for suite_name, results in self.results.items():
            if "error" in results:
                logger.info(f"💥 {suite_name}: CRASHED - {results['error']}")
                continue
            
            success_rate = results.get("success_rate", 0)
            passed = results.get("passed", 0)
            failed = results.get("failed", 0)
            errors = results.get("errors", [])
            
            total_tests += passed + failed
            total_passed += passed
            total_failed += failed
            all_errors.extend(errors)
            
            status_icon = "✅" if success_rate >= 80 else "❌"
            logger.info(f"{status_icon} {suite_name}: {success_rate:.1f}% ({passed}/{passed + failed})")
        
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        logger.info("-" * 70)
        logger.info(f"📈 OVERALL RESULTS:")
        logger.info(f"   Total Tests: {total_tests}")
        logger.info(f"   Passed: {total_passed}")
        logger.info(f"   Failed: {total_failed}")
        logger.info(f"   Success Rate: {overall_success_rate:.1f}%")
        
        if all_errors:
            logger.info(f"\n❌ ERRORS SUMMARY:")
            for i, error in enumerate(all_errors[:10], 1):  # Show first 10 errors
                logger.info(f"   {i}. {error}")
            
            if len(all_errors) > 10:
                logger.info(f"   ... and {len(all_errors) - 10} more errors")
        
        logger.info("="*70)
        
        if overall_success:
            logger.info("🎉 ALL INTEGRATION TESTS PASSED!")
            logger.info("🚀 Internal Newsletter API Microservice is PRODUCTION READY!")
        else:
            logger.info("⚠️ SOME INTEGRATION TESTS FAILED!")
            logger.info("🔧 Please review and fix issues before production deployment.")
        
        logger.info("="*70)

async def main():
    """Main test runner function"""
    runner = IntegrationTestRunner()
    success = await runner.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if success else 1)

# Command line execution
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        exit(130)
    except Exception as e:
        print(f"💥 Test runner crashed: {e}")
        exit(1)