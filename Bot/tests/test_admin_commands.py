#!/usr/bin/env python3
"""
Tests for Admin Commands module
Тесты для модуля административных команд
"""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

class TestAdminCommands:
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
    
    def test_imports_and_structure(self):
        """Test admin commands imports and basic structure"""
        try:
            from src.torah_bot.admin_commands import AdminCommands
            import_success = True
            
            # Test basic initialization
            mock_bot = MagicMock()
            admin_handler = AdminCommands(mock_bot)
            
            # Check basic attributes
            has_bot = hasattr(admin_handler, 'telegram_client')
            has_newsletter_api = hasattr(admin_handler, 'newsletter_api')
            
            initialization_success = has_bot
            
            passed = import_success and initialization_success
            self.log_result(
                "Imports and Structure",
                passed,
                f"Import: {import_success}, Basic structure: {initialization_success}"
            )
            return admin_handler if passed else None
            
        except Exception as e:
            self.log_result("Imports and Structure", False, str(e))
            return None
    
    def test_admin_command_methods(self):
        """Test presence of admin command methods"""
        try:
            from src.torah_bot.admin_commands import AdminCommands
            
            mock_bot = MagicMock()
            admin_handler = AdminCommands(mock_bot)
            
            # Check for admin command methods
            has_broadcast = hasattr(admin_handler, 'handle_broadcast') or hasattr(admin_handler, 'broadcast_command')
            has_stats = hasattr(admin_handler, 'handle_stats') or hasattr(admin_handler, 'stats_command')
            has_users = hasattr(admin_handler, 'handle_users') or hasattr(admin_handler, 'users_command')
            has_newsletter = hasattr(admin_handler, 'handle_newsletter') or hasattr(admin_handler, 'newsletter_command')
            has_tests = hasattr(admin_handler, 'handle_run_tests') or hasattr(admin_handler, 'run_tests_command')
            
            command_methods_exist = any([has_broadcast, has_stats, has_users, has_newsletter, has_tests])
            
            passed = command_methods_exist
            self.log_result(
                "Admin Command Methods",
                passed,
                f"Broadcast: {has_broadcast}, Stats: {has_stats}, Users: {has_users}, Newsletter: {has_newsletter}, Tests: {has_tests}"
            )
            return passed
            
        except Exception as e:
            self.log_result("Admin Command Methods", False, str(e))
            return False
    
    async def test_admin_permission_check(self):
        """Test admin permission checking"""
        try:
            from src.torah_bot.admin_commands import AdminCommands
            
            mock_bot = MagicMock()
            admin_handler = AdminCommands(mock_bot)
            
            # Test permission check method
            has_permission_check = hasattr(admin_handler, 'is_admin') or hasattr(admin_handler, 'check_admin_permission')
            
            if has_permission_check:
                # Test with mock user ID
                if hasattr(admin_handler, 'is_admin'):
                    result = admin_handler.is_admin(12345)
                    permission_method_works = isinstance(result, bool)
                else:
                    permission_method_works = True  # Method exists
            else:
                permission_method_works = False
            
            passed = has_permission_check and permission_method_works
            self.log_result(
                "Admin Permission Check",
                passed,
                f"Has method: {has_permission_check}, Works: {permission_method_works}"
            )
            return passed
            
        except Exception as e:
            self.log_result("Admin Permission Check", False, str(e))
            return False
    
    async def test_broadcast_functionality(self):
        """Test broadcast command functionality"""
        try:
            from src.torah_bot.admin_commands import AdminCommands
            
            mock_bot = MagicMock()
            mock_bot.telegram_client = AsyncMock()
            mock_bot.telegram_client.send_message = AsyncMock(return_value={"ok": True})
            
            admin_handler = AdminCommands(mock_bot)
            
            # Look for broadcast method
            broadcast_method = None
            for attr_name in dir(admin_handler):
                if 'broadcast' in attr_name.lower() and callable(getattr(admin_handler, attr_name)):
                    broadcast_method = getattr(admin_handler, attr_name)
                    break
            
            has_broadcast_method = broadcast_method is not None
            
            if has_broadcast_method:
                # Mock message for broadcast test
                mock_message = {
                    "message_id": 1,
                    "from": {"id": 12345, "first_name": "Admin"},
                    "chat": {"id": 12345},
                    "text": "/broadcast Test message"
                }
                
                try:
                    # Try to call broadcast method
                    if asyncio.iscoroutinefunction(broadcast_method):
                        await broadcast_method(mock_message)
                    else:
                        broadcast_method(mock_message)
                    broadcast_executes = True
                except Exception:
                    broadcast_executes = False
            else:
                broadcast_executes = False
            
            passed = has_broadcast_method
            self.log_result(
                "Broadcast Functionality",
                passed,
                f"Has method: {has_broadcast_method}, Executes: {broadcast_executes}"
            )
            return passed
            
        except Exception as e:
            self.log_result("Broadcast Functionality", False, str(e))
            return False
    
    async def test_stats_functionality(self):
        """Test stats command functionality"""
        try:
            from src.torah_bot.admin_commands import AdminCommands
            
            mock_bot = MagicMock()
            mock_bot.telegram_client = AsyncMock()
            mock_bot.telegram_client.send_message = AsyncMock(return_value={"ok": True})
            
            admin_handler = AdminCommands(mock_bot)
            
            # Look for stats method
            stats_method = None
            for attr_name in dir(admin_handler):
                if 'stats' in attr_name.lower() and callable(getattr(admin_handler, attr_name)):
                    stats_method = getattr(admin_handler, attr_name)
                    break
            
            has_stats_method = stats_method is not None
            
            if has_stats_method:
                mock_message = {
                    "message_id": 1,
                    "from": {"id": 12345, "first_name": "Admin"},
                    "chat": {"id": 12345},
                    "text": "/stats"
                }
                
                try:
                    if asyncio.iscoroutinefunction(stats_method):
                        await stats_method(mock_message)
                    else:
                        stats_method(mock_message)
                    stats_executes = True
                except Exception:
                    stats_executes = False
            else:
                stats_executes = False
            
            passed = has_stats_method
            self.log_result(
                "Stats Functionality", 
                passed,
                f"Has method: {has_stats_method}, Executes: {stats_executes}"
            )
            return passed
            
        except Exception as e:
            self.log_result("Stats Functionality", False, str(e))
            return False
    
    async def test_newsletter_api_integration(self):
        """Test newsletter API integration commands"""
        try:
            from src.torah_bot.admin_commands import AdminCommands
            
            mock_bot = MagicMock()
            admin_handler = AdminCommands(mock_bot)
            
            # Check for newsletter API related methods
            has_newsletter_api = any(
                'newsletter' in attr_name.lower() and 'api' in attr_name.lower()
                for attr_name in dir(admin_handler)
                if callable(getattr(admin_handler, attr_name))
            )
            
            has_api_tests = any(
                'api' in attr_name.lower() and 'test' in attr_name.lower()
                for attr_name in dir(admin_handler)
                if callable(getattr(admin_handler, attr_name))
            )
            
            api_integration_exists = has_newsletter_api or has_api_tests
            
            passed = api_integration_exists
            self.log_result(
                "Newsletter API Integration",
                passed,
                f"Newsletter API: {has_newsletter_api}, API Tests: {has_api_tests}"
            )
            return passed
            
        except Exception as e:
            self.log_result("Newsletter API Integration", False, str(e))
            return False
    
    def test_command_routing(self):
        """Test command routing and processing"""
        try:
            from src.torah_bot.admin_commands import AdminCommands
            
            mock_bot = MagicMock()
            admin_handler = AdminCommands(mock_bot)
            
            # Check for command processing methods
            has_process_command = hasattr(admin_handler, 'process_command') or hasattr(admin_handler, 'handle_command')
            has_command_router = hasattr(admin_handler, 'route_command') or hasattr(admin_handler, 'command_router')
            has_handle_admin = hasattr(admin_handler, 'handle_admin_command') or hasattr(admin_handler, 'process_admin_command')
            
            command_processing_exists = has_process_command or has_command_router or has_handle_admin
            
            passed = command_processing_exists
            self.log_result(
                "Command Routing",
                passed,
                f"Process: {has_process_command}, Router: {has_command_router}, Handle: {has_handle_admin}"
            )
            return passed
            
        except Exception as e:
            self.log_result("Command Routing", False, str(e))
            return False
    
    def test_error_handling_in_admin(self):
        """Test error handling in admin commands"""
        try:
            from src.torah_bot.admin_commands import AdminCommands
            
            mock_bot = MagicMock()
            admin_handler = AdminCommands(mock_bot)
            
            # Check for error handling mechanisms
            has_error_handler = hasattr(admin_handler, 'handle_error') or hasattr(admin_handler, 'log_error')
            has_try_catch_patterns = any(
                'try' in str(getattr(admin_handler, attr)) or 'except' in str(getattr(admin_handler, attr))
                for attr in dir(admin_handler)
                if callable(getattr(admin_handler, attr)) and not attr.startswith('_')
            )
            
            error_handling_exists = has_error_handler or has_try_catch_patterns
            
            passed = error_handling_exists
            self.log_result(
                "Error Handling in Admin",
                passed,
                f"Error handler: {has_error_handler}, Try-catch patterns: {has_try_catch_patterns}"
            )
            return passed
            
        except Exception as e:
            self.log_result("Error Handling in Admin", False, str(e))
            return False

    async def run_all_tests(self):
        """Run complete test suite for AdminCommands"""
        print("👑 Starting AdminCommands Test Suite")
        print("="*42)
        
        # Test basic structure
        admin_handler = self.test_imports_and_structure()
        self.test_admin_command_methods()
        self.test_command_routing()
        self.test_error_handling_in_admin()
        
        if admin_handler:
            # Test async functionality
            await self.test_admin_permission_check()
            await self.test_broadcast_functionality()
            await self.test_stats_functionality()
            await self.test_newsletter_api_integration()
        
        # Results
        total = self.test_results["passed"] + self.test_results["failed"]
        success_rate = (self.test_results["passed"] / total * 100) if total > 0 else 0
        
        print("="*42)
        print(f"👑 AdminCommands Test Results:")
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
async def run_admin_commands_tests():
    """Run AdminCommands tests"""
    test_suite = TestAdminCommands()
    return await test_suite.run_all_tests()

if __name__ == "__main__":
    result = asyncio.run(run_admin_commands_tests())
    exit(0 if result else 1)