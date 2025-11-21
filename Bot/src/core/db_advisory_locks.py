#!/usr/bin/env python3
"""
Database Advisory Locks for preventing duplicate broadcasts
Предотвращает дублирование рассылок в multi-instance environments
"""
import asyncio
import logging
import asyncpg
import os
from contextlib import asynccontextmanager
from typing import Optional
import hashlib

logger = logging.getLogger(__name__)

class DBAdvisoryLockManager:
    """PostgreSQL advisory lock manager for broadcast deduplication"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        self._connection_pool = None
    
    async def get_connection_pool(self):
        """Get or create connection pool"""
        if not self._connection_pool:
            if not self.database_url:
                raise ValueError("DATABASE_URL environment variable not set")
            
            self._connection_pool = await asyncpg.create_pool(
                self.database_url,
                min_size=1,
                max_size=3,
                command_timeout=60
            )
            logger.info("🔒 Advisory lock database pool created")
        
        return self._connection_pool
    
    def _generate_lock_id(self, resource_name: str) -> int:
        """
        Generate consistent integer lock ID from resource name
        PostgreSQL advisory locks use bigint (int64) IDs
        """
        # Create hash of resource name for consistent ID generation
        hash_obj = hashlib.md5(resource_name.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()
        
        # Take first 8 bytes (16 hex chars) and convert to signed 64-bit integer
        lock_id = int(hash_hex[:16], 16)
        
        # Ensure it fits in PostgreSQL bigint range (-2^63 to 2^63-1)
        if lock_id > 2**63 - 1:
            lock_id = lock_id - 2**64
            
        return lock_id
    
    @asynccontextmanager
    async def advisory_lock(self, resource_name: str, timeout: int = 30):
        """
        Acquire PostgreSQL advisory lock with automatic release
        
        Args:
            resource_name: Unique resource name (e.g., "broadcast:wisdom:2025-09-26")
            timeout: Maximum time to wait for lock acquisition in seconds
            
        Yields:
            bool: True if lock was acquired, False if timeout/error
        """
        lock_id = self._generate_lock_id(resource_name)
        pool = await self.get_connection_pool()
        
        connection = None
        lock_acquired = False
        
        try:
            connection = await pool.acquire()
            logger.info(f"🔒 Attempting to acquire advisory lock: {resource_name} (ID: {lock_id})")
            
            # Try to acquire lock with timeout
            try:
                # Use pg_try_advisory_lock for non-blocking attempt
                result = await asyncio.wait_for(
                    connection.fetchval("SELECT pg_try_advisory_lock($1)", lock_id),
                    timeout=timeout
                )
                
                if result:
                    lock_acquired = True
                    logger.info(f"✅ Advisory lock acquired: {resource_name}")
                else:
                    logger.warning(f"🔒 Advisory lock already held by another process: {resource_name}")
                
            except asyncio.TimeoutError:
                logger.warning(f"⏱️ Advisory lock timeout after {timeout}s: {resource_name}")
                result = False
            
            yield lock_acquired
            
        except Exception as e:
            logger.error(f"❌ Advisory lock error for {resource_name}: {e}")
            yield False
        
        finally:
            # Always release lock if acquired
            if lock_acquired and connection:
                try:
                    await connection.execute("SELECT pg_advisory_unlock($1)", lock_id)
                    logger.info(f"🔓 Advisory lock released: {resource_name}")
                except Exception as release_error:
                    logger.error(f"❌ Failed to release advisory lock {resource_name}: {release_error}")
            
            # Return connection to pool
            if connection and pool:
                try:
                    await pool.release(connection)
                except Exception as pool_error:
                    logger.error(f"❌ Failed to return connection to pool: {pool_error}")
    
    async def is_locked(self, resource_name: str) -> bool:
        """
        Check if a resource is currently locked (non-blocking)
        
        Args:
            resource_name: Resource name to check
            
        Returns:
            bool: True if resource is locked, False otherwise
        """
        lock_id = self._generate_lock_id(resource_name)
        pool = await self.get_connection_pool()
        
        try:
            async with pool.acquire() as connection:
                # Check if lock is currently held using pg_try_advisory_lock
                # This will return False if already locked by another session
                can_acquire = await connection.fetchval("SELECT pg_try_advisory_lock($1)", lock_id)
                
                if can_acquire:
                    # We got the lock, so it wasn't held - release it immediately
                    await connection.execute("SELECT pg_advisory_unlock($1)", lock_id)
                    return False  # Was not locked
                else:
                    return True  # Is locked by another session
                    
        except Exception as e:
            logger.error(f"❌ Error checking lock status for {resource_name}: {e}")
            return False  # Assume not locked on error
    
    async def list_active_locks(self) -> list:
        """
        List all currently active advisory locks (for debugging)
        
        Returns:
            List of active lock information
        """
        pool = await self.get_connection_pool()
        
        try:
            async with pool.acquire() as connection:
                rows = await connection.fetch("""
                    SELECT 
                        objid as lock_id,
                        classid,
                        objsubid,
                        pid,
                        mode,
                        granted,
                        fastpath
                    FROM pg_locks 
                    WHERE locktype = 'advisory'
                    ORDER BY objid
                """)
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"❌ Error listing active advisory locks: {e}")
            return []
    
    async def cleanup_connection_pool(self):
        """Clean up connection pool on shutdown"""
        if self._connection_pool:
            try:
                await self._connection_pool.close()
                logger.info("🔒 Advisory lock connection pool closed")
            except Exception as e:
                logger.error(f"❌ Error closing advisory lock pool: {e}")

# Global lock manager instance
_lock_manager = None

def get_advisory_lock_manager() -> DBAdvisoryLockManager:
    """Get or create global advisory lock manager"""
    global _lock_manager
    if _lock_manager is None:
        _lock_manager = DBAdvisoryLockManager()
    return _lock_manager

# Convenience functions for common broadcast lock patterns
async def broadcast_lock(broadcast_type: str, date_str: str, timeout: int = 30):
    """
    Acquire broadcast lock for specific type and date
    
    Args:
        broadcast_type: Type of broadcast ("wisdom", "quiz", "manual")
        date_str: Date string (YYYY-MM-DD format)
        timeout: Lock timeout in seconds
        
    Returns:
        Context manager for advisory lock
    """
    resource_name = f"broadcast:{broadcast_type}:{date_str}"
    manager = get_advisory_lock_manager()
    return manager.advisory_lock(resource_name, timeout)

async def daily_wisdom_lock(date_str: str):
    """Acquire lock for daily wisdom broadcast"""
    return broadcast_lock("wisdom", date_str)

async def daily_quiz_lock(date_str: str):
    """Acquire lock for daily quiz broadcast"""
    return broadcast_lock("quiz", date_str)

async def manual_broadcast_lock(timestamp_str: str):
    """Acquire lock for manual broadcast (uses timestamp for uniqueness)"""
    return broadcast_lock("manual", timestamp_str)