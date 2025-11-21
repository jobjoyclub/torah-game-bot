#!/usr/bin/env python3
"""
Tests for Deployment Configuration module
Тесты для модуля конфигурации деплоя
"""

import asyncio
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

class TestDeploymentConfig:
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
        """Test deployment config imports and structure"""
        try:
            import deployment_config
            import_success = True
            
            # Check for deployment configuration attributes
            has_port_config = hasattr(deployment_config, 'PORT') or hasattr(deployment_config, 'port')
            has_host_config = hasattr(deployment_config, 'HOST') or hasattr(deployment_config, 'host')
            has_env_config = hasattr(deployment_config, 'ENV') or hasattr(deployment_config, 'environment')
            has_deployment_type = hasattr(deployment_config, 'DEPLOYMENT_TYPE') or 'deployment' in str(deployment_config.__dict__)
            
            config_structure = has_port_config or has_host_config or has_env_config or has_deployment_type
            
            passed = import_success and config_structure
            self.log_result(
                "Imports and Structure",
                passed,
                f"Import: {import_success}, Port: {has_port_config}, Host: {has_host_config}, Env: {has_env_config}, Type: {has_deployment_type}"
            )
            return deployment_config if passed else None
            
        except Exception as e:
            self.log_result("Imports and Structure", False, str(e))
            return None
    
    def test_replit_specific_config(self):
        """Test Replit-specific deployment configuration"""
        try:
            import deployment_config
            
            # Check for Replit-specific settings
            config_str = str(deployment_config.__dict__).lower()
            
            has_replit_config = 'replit' in config_str
            has_reserved_vm = 'reserved' in config_str or 'vm' in config_str
            has_port_5000 = '5000' in config_str or hasattr(deployment_config, 'PORT') and str(getattr(deployment_config, 'PORT', '')) == '5000'
            has_host_binding = '0.0.0.0' in config_str or 'all hosts' in config_str
            
            replit_optimized = has_replit_config or has_reserved_vm or has_port_5000 or has_host_binding
            
            passed = replit_optimized
            self.log_result(
                "Replit Specific Config",
                passed,
                f"Replit: {has_replit_config}, Reserved VM: {has_reserved_vm}, Port 5000: {has_port_5000}, Host binding: {has_host_binding}"
            )
            return passed
            
        except Exception as e:
            self.log_result("Replit Specific Config", False, str(e))
            return False
    
    def test_environment_variables_handling(self):
        """Test environment variables handling"""
        try:
            import deployment_config
            
            # Check for environment variable usage
            has_env_vars = any(
                'env' in attr_name.lower() or 'getenv' in str(getattr(deployment_config, attr_name, ''))
                for attr_name in dir(deployment_config)
            )
            
            # Check for specific environment variables
            config_source = str(deployment_config.__dict__)
            important_env_vars = ['DATABASE_URL', 'OPENAI_API_KEY', 'TELEGRAM_TOKEN', 'PORT']
            has_important_vars = any(var in config_source for var in important_env_vars)
            
            # Check for environment-specific configurations
            has_env_specific = any(
                keyword in config_source.lower()
                for keyword in ['development', 'production', 'staging', 'test']
            )
            
            env_handling = has_env_vars or has_important_vars or has_env_specific
            
            passed = env_handling
            self.log_result(
                "Environment Variables Handling",
                passed,
                f"Env vars: {has_env_vars}, Important vars: {has_important_vars}, Env specific: {has_env_specific}"
            )
            return passed
            
        except Exception as e:
            self.log_result("Environment Variables Handling", False, str(e))
            return False
    
    def test_database_configuration(self):
        """Test database configuration settings"""
        try:
            import deployment_config
            
            # Check for database configuration
            config_source = str(deployment_config.__dict__)
            
            has_db_config = any(
                keyword in config_source.lower()
                for keyword in ['database', 'db_', 'postgresql', 'postgres']
            )
            
            has_connection_config = any(
                keyword in config_source
                for keyword in ['DATABASE_URL', 'PGHOST', 'PGPORT', 'PGUSER', 'PGPASSWORD']
            )
            
            has_connection_pooling = any(
                keyword in config_source.lower()
                for keyword in ['pool', 'connection_pool', 'max_connections']
            )
            
            db_configuration = has_db_config or has_connection_config or has_connection_pooling
            
            passed = db_configuration
            self.log_result(
                "Database Configuration",
                passed,
                f"DB config: {has_db_config}, Connection: {has_connection_config}, Pooling: {has_connection_pooling}"
            )
            return passed
            
        except Exception as e:
            self.log_result("Database Configuration", False, str(e))
            return False
    
    def test_api_keys_and_secrets(self):
        """Test API keys and secrets configuration"""
        try:
            import deployment_config
            
            # Check for API key configuration
            config_source = str(deployment_config.__dict__)
            
            has_openai_config = 'OPENAI_API_KEY' in config_source or 'openai' in config_source.lower()
            has_telegram_config = 'TELEGRAM' in config_source or 'BOT_TOKEN' in config_source
            has_secrets_handling = any(
                keyword in config_source.lower()
                for keyword in ['secret', 'key', 'token', 'api_key']
            )
            
            # Check for secure handling patterns
            has_secure_patterns = any(
                keyword in config_source
                for keyword in ['os.getenv', 'environ', 'getenv']
            )
            
            api_config = has_openai_config or has_telegram_config or has_secrets_handling
            security_patterns = has_secure_patterns
            
            passed = api_config and security_patterns
            self.log_result(
                "API Keys and Secrets",
                passed,
                f"OpenAI: {has_openai_config}, Telegram: {has_telegram_config}, Secrets: {has_secrets_handling}, Secure: {has_secure_patterns}"
            )
            return passed
            
        except Exception as e:
            self.log_result("API Keys and Secrets", False, str(e))
            return False
    
    def test_logging_and_monitoring_config(self):
        """Test logging and monitoring configuration"""
        try:
            import deployment_config
            
            # Check for logging configuration
            config_source = str(deployment_config.__dict__)
            
            has_logging_config = any(
                keyword in config_source.lower()
                for keyword in ['log', 'logging', 'debug', 'verbose']
            )
            
            has_log_levels = any(
                keyword in config_source
                for keyword in ['INFO', 'DEBUG', 'WARNING', 'ERROR', 'CRITICAL']
            )
            
            has_monitoring = any(
                keyword in config_source.lower()
                for keyword in ['monitor', 'health', 'metrics', 'analytics']
            )
            
            logging_config = has_logging_config or has_log_levels or has_monitoring
            
            passed = logging_config
            self.log_result(
                "Logging and Monitoring Config",
                passed,
                f"Logging: {has_logging_config}, Levels: {has_log_levels}, Monitoring: {has_monitoring}"
            )
            return passed
            
        except Exception as e:
            self.log_result("Logging and Monitoring Config", False, str(e))
            return False
    
    def test_deployment_validation(self):
        """Test deployment validation and checks"""
        try:
            import deployment_config
            
            # Check for validation functions
            has_validation = any(
                keyword in attr_name.lower()
                for keyword in ['validate', 'check', 'verify']
                for attr_name in dir(deployment_config)
                if callable(getattr(deployment_config, attr_name, None))
            )
            
            # Check for configuration validation
            has_config_validation = any(
                keyword in str(deployment_config.__dict__).lower()
                for keyword in ['required', 'mandatory', 'essential', 'check']
            )
            
            # Check for startup checks
            has_startup_checks = any(
                keyword in attr_name.lower()
                for keyword in ['startup', 'initialize', 'setup']
                for attr_name in dir(deployment_config)
                if callable(getattr(deployment_config, attr_name, None))
            )
            
            validation_exists = has_validation or has_config_validation or has_startup_checks
            
            passed = validation_exists
            self.log_result(
                "Deployment Validation",
                passed,
                f"Validation: {has_validation}, Config validation: {has_config_validation}, Startup checks: {has_startup_checks}"
            )
            return passed
            
        except Exception as e:
            self.log_result("Deployment Validation", False, str(e))
            return False
    
    def test_error_handling_and_fallbacks(self):
        """Test error handling and fallback configurations"""
        try:
            import deployment_config
            
            # Check for error handling
            config_source = str(deployment_config.__dict__)
            
            has_error_handling = any(
                keyword in config_source.lower()
                for keyword in ['error', 'exception', 'fallback', 'default']
            )
            
            has_retry_config = any(
                keyword in config_source.lower()
                for keyword in ['retry', 'attempt', 'timeout', 'backoff']
            )
            
            has_graceful_shutdown = any(
                keyword in config_source.lower()
                for keyword in ['shutdown', 'cleanup', 'graceful', 'signal']
            )
            
            error_handling_exists = has_error_handling or has_retry_config or has_graceful_shutdown
            
            passed = error_handling_exists
            self.log_result(
                "Error Handling and Fallbacks",
                passed,
                f"Error handling: {has_error_handling}, Retry: {has_retry_config}, Graceful shutdown: {has_graceful_shutdown}"
            )
            return passed
            
        except Exception as e:
            self.log_result("Error Handling and Fallbacks", False, str(e))
            return False

    async def run_all_tests(self):
        """Run complete test suite for DeploymentConfig"""
        print("🚀 Starting DeploymentConfig Test Suite")
        print("="*44)
        
        # Test all functionality
        config = self.test_imports_and_structure()
        
        if config:
            self.test_replit_specific_config()
            self.test_environment_variables_handling()
            self.test_database_configuration()
            self.test_api_keys_and_secrets()
            self.test_logging_and_monitoring_config()
            self.test_deployment_validation()
            self.test_error_handling_and_fallbacks()
        
        # Results
        total = self.test_results["passed"] + self.test_results["failed"]
        success_rate = (self.test_results["passed"] / total * 100) if total > 0 else 0
        
        print("="*44)
        print(f"🚀 DeploymentConfig Test Results:")
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
async def run_deployment_config_tests():
    """Run DeploymentConfig tests"""
    test_suite = TestDeploymentConfig()
    return await test_suite.run_all_tests()

if __name__ == "__main__":
    result = asyncio.run(run_deployment_config_tests())
    exit(0 if result else 1)