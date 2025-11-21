#!/usr/bin/env python3
"""
Service Container - Singleton pattern for managing shared instances
Prevents multiple initialization race conditions and ensures consistency
"""
import logging
import asyncio
from typing import Optional, Dict, Any
from threading import Lock

logger = logging.getLogger(__name__)

class ServiceContainer:
    """Singleton Service Container for managing shared instances"""
    
    _instance: Optional['ServiceContainer'] = None
    _lock = Lock()
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ServiceContainer, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Only initialize once
        if not ServiceContainer._initialized:
            self._services: Dict[str, Any] = {}
            self._initialization_lock = asyncio.Lock()
            ServiceContainer._initialized = True
            logger.info("🔧 ServiceContainer initialized")
    
    async def get_service(self, service_name: str, factory_func=None, *args, **kwargs):
        """Get or create a service with thread-safe singleton behavior"""
        async with self._initialization_lock:
            if service_name not in self._services:
                if factory_func is None:
                    raise ValueError(f"Service '{service_name}' not found and no factory provided")
                
                logger.info(f"🚀 Creating service: {service_name}")
                self._services[service_name] = await factory_func(*args, **kwargs)
                logger.info(f"✅ Service created: {service_name}")
            
            return self._services[service_name]
    
    def register_service(self, service_name: str, instance):
        """Register an already created service instance"""
        with self._lock:
            if service_name in self._services:
                logger.warning(f"⚠️ Service '{service_name}' already exists, replacing")
            self._services[service_name] = instance
            logger.info(f"📋 Service registered: {service_name}")
    
    def has_service(self, service_name: str) -> bool:
        """Check if service exists"""
        return service_name in self._services
    
    def get_service_sync(self, service_name: str):
        """Get service synchronously (if already exists)"""
        return self._services.get(service_name)
    
    def list_services(self) -> list:
        """List all registered services"""
        return list(self._services.keys())
    
    async def cleanup(self):
        """Cleanup all services"""
        logger.info("🧹 Cleaning up ServiceContainer...")
        async with self._initialization_lock:
            for service_name, service in self._services.items():
                if hasattr(service, 'cleanup'):
                    try:
                        await service.cleanup()
                    except Exception as e:
                        logger.error(f"❌ Error cleaning up {service_name}: {e}")
            
            self._services.clear()
            logger.info("✅ ServiceContainer cleaned up")

# Global instance
_container = ServiceContainer()

def get_container() -> ServiceContainer:
    """Get the global ServiceContainer instance"""
    return _container