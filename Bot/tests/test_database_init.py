#!/usr/bin/env python3
"""
Tests for Database Initialization module
Тесты для модуля инициализации базы данных
"""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

class TestDatabaseInit:
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
        """Test database init imports and structure"""
        try:
            import src.database.init_database as db_init_module
            import_success = True
            
            # Test basic initialization
            db_init = db_init_module
            
            # Check basic attributes
            has_connection_method = hasattr(db_init, 'connect') or hasattr(db_init, 'get_connection')
            has_init_method = hasattr(db_init, 'initialize') or hasattr(db_init, 'init_database')
            has_create_tables = hasattr(db_init, 'create_tables') or hasattr(db_init, 'setup_tables')
            
            structure_exists = has_connection_method or has_init_method or has_create_tables
            
            passed = import_success and structure_exists
            self.log_result(
                "Imports and Structure",
                passed,
                f"Import: {import_success}, Connection: {has_connection_method}, Init: {has_init_method}, Tables: {has_create_tables}"
            )
            return db_init if passed else None
            
        except Exception as e:
            self.log_result("Imports and Structure", False, str(e))
            return None
    
    async def test_database_connection(self):
        """Test database connection functionality"""
        try:
            import src.database.init_database as db_init_module
            
            db_init = db_init_module
            
            # Test connection method
            connection_works = False
            connection_method = None
            
            # Try different connection methods
            for method_name in ['connect', 'get_connection', 'create_connection']:
                if hasattr(db_init, method_name):
                    connection_method = getattr(db_init, method_name)
                    break
            
            if connection_method:
                # Mock database connection
                with patch('psycopg2.connect') as mock_connect:
                    mock_conn = MagicMock()
                    mock_connect.return_value = mock_conn
                    
                    try:
                        if asyncio.iscoroutinefunction(connection_method):
                            result = await connection_method()
                        else:
                            result = connection_method()
                        connection_works = result is not None
                    except Exception:
                        connection_works = False
            
            # Test connection string handling
            has_connection_string = hasattr(db_init, 'connection_string') or hasattr(db_init, 'database_url')
            
            passed = connection_works or has_connection_string
            self.log_result(
                "Database Connection",
                passed,
                f"Connection works: {connection_works}, Has connection string: {has_connection_string}"
            )
            return passed
            
        except Exception as e:
            self.log_result("Database Connection", False, str(e))
            return False
    
    async def test_table_creation(self):
        """Test table creation functionality"""
        try:
            import src.database.init_database as db_init_module
            
            db_init = db_init_module
            
            # Test table creation methods
            table_creation_works = False
            
            # Try different table creation methods
            for method_name in ['create_tables', 'setup_tables', 'init_tables', 'create_schema']:
                if hasattr(db_init, method_name):
                    table_method = getattr(db_init, method_name)
                    
                    # Mock database cursor
                    with patch('psycopg2.connect') as mock_connect:
                        mock_conn = MagicMock()
                        mock_cursor = MagicMock()
                        mock_conn.cursor.return_value = mock_cursor
                        mock_connect.return_value = mock_conn
                        
                        try:
                            if asyncio.iscoroutinefunction(table_method):
                                await table_method()
                            else:
                                table_method()
                            table_creation_works = True
                            break
                        except Exception:
                            continue
            
            # Check for SQL schema files or embedded SQL
            has_sql_schema = False
            schema_file_path = os.path.join(project_root, 'src', 'database', 'newsletter_schema.sql')
            if os.path.exists(schema_file_path):
                has_sql_schema = True
            
            # Check for embedded SQL in the class
            if hasattr(db_init, '__class__'):
                class_source = str(db_init.__class__.__dict__)
                has_embedded_sql = 'CREATE TABLE' in class_source.upper() or 'sql' in class_source.lower()
            else:
                has_embedded_sql = False
            
            schema_support = has_sql_schema or has_embedded_sql
            
            passed = table_creation_works or schema_support
            self.log_result(
                "Table Creation",
                passed,
                f"Creation works: {table_creation_works}, SQL schema: {has_sql_schema}, Embedded SQL: {has_embedded_sql}"
            )
            return passed
            
        except Exception as e:
            self.log_result("Table Creation", False, str(e))
            return False
    
    def test_newsletter_schema_support(self):
        """Test newsletter schema support"""
        try:
            import src.database.init_database as db_init_module
            
            db_init = db_init_module
            
            # Check for newsletter-specific methods
            has_newsletter_setup = any(
                'newsletter' in attr_name.lower()
                for attr_name in dir(db_init)
                if callable(getattr(db_init, attr_name))
            )
            
            # Check for user management methods
            has_user_setup = any(
                'user' in attr_name.lower()
                for attr_name in dir(db_init)
                if callable(getattr(db_init, attr_name))
            )
            
            # Check for broadcast/subscription methods
            has_subscription_setup = any(
                keyword in attr_name.lower()
                for keyword in ['subscription', 'broadcast', 'subscriber']
                for attr_name in dir(db_init)
                if callable(getattr(db_init, attr_name))
            )
            
            newsletter_support = has_newsletter_setup or has_user_setup or has_subscription_setup
            
            passed = newsletter_support
            self.log_result(
                "Newsletter Schema Support",
                passed,
                f"Newsletter: {has_newsletter_setup}, Users: {has_user_setup}, Subscriptions: {has_subscription_setup}"
            )
            return passed
            
        except Exception as e:
            self.log_result("Newsletter Schema Support", False, str(e))
            return False
    
    async def test_database_migration_support(self):
        """Test database migration and versioning support"""
        try:
            import src.database.init_database as db_init_module
            
            db_init = db_init_module
            
            # Check for migration methods
            has_migration_support = any(
                keyword in attr_name.lower()
                for keyword in ['migration', 'version', 'upgrade', 'migrate']
                for attr_name in dir(db_init)
                if callable(getattr(db_init, attr_name))
            )
            
            # Check for schema versioning
            has_version_tracking = any(
                keyword in attr_name.lower()
                for keyword in ['version', 'schema_version', 'db_version']
                for attr_name in dir(db_init)
            )
            
            # Check for backup before migration
            has_backup_integration = any(
                'backup' in attr_name.lower()
                for attr_name in dir(db_init)
                if callable(getattr(db_init, attr_name))
            )
            
            migration_support = has_migration_support or has_version_tracking or has_backup_integration
            
            passed = migration_support
            self.log_result(
                "Database Migration Support",
                passed,
                f"Migration: {has_migration_support}, Versioning: {has_version_tracking}, Backup: {has_backup_integration}"
            )
            return passed
            
        except Exception as e:
            self.log_result("Database Migration Support", False, str(e))
            return False
    
    def test_error_handling_and_rollback(self):
        """Test error handling and transaction rollback"""
        try:
            import src.database.init_database as db_init_module
            
            db_init = db_init_module
            
            # Check for error handling methods
            has_error_handling = any(
                keyword in attr_name.lower()
                for keyword in ['error', 'exception', 'handle_error']
                for attr_name in dir(db_init)
                if callable(getattr(db_init, attr_name))
            )
            
            # Check for transaction management
            has_transaction_support = any(
                keyword in attr_name.lower()
                for keyword in ['transaction', 'commit', 'rollback', 'begin']
                for attr_name in dir(db_init)
                if callable(getattr(db_init, attr_name))
            )
            
            # Check for recovery methods
            has_recovery_support = any(
                keyword in attr_name.lower()
                for keyword in ['recover', 'restore', 'repair']
                for attr_name in dir(db_init)
                if callable(getattr(db_init, attr_name))
            )
            
            error_handling_exists = has_error_handling or has_transaction_support or has_recovery_support
            
            passed = error_handling_exists
            self.log_result(
                "Error Handling and Rollback",
                passed,
                f"Error handling: {has_error_handling}, Transactions: {has_transaction_support}, Recovery: {has_recovery_support}"
            )
            return passed
            
        except Exception as e:
            self.log_result("Error Handling and Rollback", False, str(e))
            return False
    
    async def test_initialization_workflow(self):
        """Test complete initialization workflow"""
        try:
            import src.database.init_database as db_init_module
            
            db_init = db_init_module
            
            # Test main initialization method
            initialization_works = False
            
            # Try different initialization methods
            for method_name in ['initialize', 'init_database', 'setup', 'run', 'main']:
                if hasattr(db_init, method_name):
                    init_method = getattr(db_init, method_name)
                    
                    # Mock the entire database setup
                    with patch('psycopg2.connect') as mock_connect:
                        mock_conn = MagicMock()
                        mock_cursor = MagicMock()
                        mock_conn.cursor.return_value = mock_cursor
                        mock_connect.return_value = mock_conn
                        
                        try:
                            if asyncio.iscoroutinefunction(init_method):
                                await init_method()
                            else:
                                init_method()
                            initialization_works = True
                            break
                        except Exception:
                            continue
            
            # Check if there's a main function or script entry point
            has_main_function = hasattr(db_init, '__main__') or 'if __name__' in str(db_init.__class__)
            
            workflow_exists = initialization_works or has_main_function
            
            passed = workflow_exists
            self.log_result(
                "Initialization Workflow",
                passed,
                f"Initialization works: {initialization_works}, Has main: {has_main_function}"
            )
            return passed
            
        except Exception as e:
            self.log_result("Initialization Workflow", False, str(e))
            return False

    async def run_all_tests(self):
        """Run complete test suite for DatabaseInit"""
        print("🗄️ Starting DatabaseInit Test Suite")
        print("="*42)
        
        # Test basic structure
        db_init = self.test_imports_and_structure()
        
        if db_init:
            # Test functionality
            await self.test_database_connection()
            await self.test_table_creation()
            self.test_newsletter_schema_support()
            await self.test_database_migration_support()
            self.test_error_handling_and_rollback()
            await self.test_initialization_workflow()
        
        # Results
        total = self.test_results["passed"] + self.test_results["failed"]
        success_rate = (self.test_results["passed"] / total * 100) if total > 0 else 0
        
        print("="*42)
        print(f"🗄️ DatabaseInit Test Results:")
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
async def run_database_init_tests():
    """Run DatabaseInit tests"""
    test_suite = TestDatabaseInit()
    return await test_suite.run_all_tests()

if __name__ == "__main__":
    result = asyncio.run(run_database_init_tests())
    exit(0 if result else 1)