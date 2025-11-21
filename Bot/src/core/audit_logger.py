#!/usr/bin/env python3
"""
Audit Logging System for Admin Operations
Comprehensive logging of all administrative actions for security and compliance
"""
import json
import logging
import asyncio
import asyncpg
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class AuditEventType(Enum):
    """Types of auditable events"""
    ADMIN_LOGIN = "admin_login"
    MANUAL_BROADCAST = "manual_broadcast"
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    SCHEDULER_ACTION = "scheduler_action"
    DATABASE_ACCESS = "database_access"
    SECURITY_EVENT = "security_event"
    USER_DATA_ACCESS = "user_data_access"
    API_KEY_USAGE = "api_key_usage"

@dataclass
class AuditEvent:
    """Audit event data structure"""
    timestamp: datetime
    event_type: AuditEventType
    user_identifier: str
    action: str
    resource: str
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit event to dictionary for JSON serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['event_type'] = self.event_type.value
        return data

class AuditLogger:
    """Comprehensive audit logging system"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        self._connection_pool = None
        self._audit_queue = asyncio.Queue(maxsize=1000)  # Buffer for high-throughput logging
        self._processing_task = None
        self._torah_logs_chat_id = int(os.environ.get("TORAH_LOGS_CHAT_ID", "-1003025527880"))
        
    async def initialize(self):
        """Initialize audit logging system"""
        try:
            # Initialize database connection pool
            if self.database_url:
                self._connection_pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=1,
                    max_size=5,
                    command_timeout=30
                )
                
                # Ensure audit_log table exists
                await self._ensure_audit_table()
                
                logger.info("🔍 Audit logging database initialized")
            
            # Start background processing task
            self._processing_task = asyncio.create_task(self._process_audit_queue())
            logger.info("🔍 Audit logging system initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize audit logging: {e}")
    
    async def _ensure_audit_table(self):
        """Create audit_log table if it doesn't exist"""
        try:
            if not self._connection_pool:
                return
            async with self._connection_pool.acquire() as conn:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS audit_log (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMPTZ NOT NULL,
                        event_type VARCHAR(50) NOT NULL,
                        user_identifier VARCHAR(255) NOT NULL,
                        action VARCHAR(255) NOT NULL,
                        resource VARCHAR(255) NOT NULL,
                        details JSONB,
                        ip_address INET,
                        user_agent TEXT,
                        success BOOLEAN NOT NULL DEFAULT true,
                        error_message TEXT,
                        session_id VARCHAR(255),
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
                    CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_log(event_type);
                    CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_identifier);
                    CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_log(resource);
                """)
                logger.info("🔍 Audit log table ensured")
        except Exception as e:
            logger.error(f"❌ Failed to create audit log table: {e}")
    
    async def log_event(
        self, 
        event_type: AuditEventType,
        user_identifier: str,
        action: str,
        resource: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """Log an audit event"""
        try:
            event = AuditEvent(
                timestamp=datetime.now(timezone.utc),
                event_type=event_type,
                user_identifier=user_identifier,
                action=action,
                resource=resource,
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                error_message=error_message,
                session_id=session_id
            )
            
            # Add to queue for async processing
            try:
                self._audit_queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning("🔍 Audit queue full, dropping event")
                # Log to file as fallback
                await self._log_to_file(event)
                
        except Exception as e:
            logger.error(f"❌ Failed to log audit event: {e}")
    
    async def _process_audit_queue(self):
        """Background task to process audit events"""
        while True:
            try:
                event = await self._audit_queue.get()
                
                # Process event (database + notifications)
                await self._store_event(event)
                
                # Send critical events to Torah Logs chat
                if event.event_type in [
                    AuditEventType.SECURITY_EVENT, 
                    AuditEventType.MANUAL_BROADCAST,
                    AuditEventType.SYSTEM_CONFIG_CHANGE
                ]:
                    await self._notify_critical_event(event)
                
                self._audit_queue.task_done()
                
            except Exception as e:
                logger.error(f"❌ Error processing audit event: {e}")
                await asyncio.sleep(1)  # Prevent tight loop on persistent errors
    
    async def _store_event(self, event: AuditEvent):
        """Store audit event in database"""
        try:
            if not self._connection_pool:
                await self._log_to_file(event)
                return
                
            async with self._connection_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO audit_log (
                        timestamp, event_type, user_identifier, action, 
                        resource, details, ip_address, user_agent, 
                        success, error_message, session_id
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                """, 
                    event.timestamp,
                    event.event_type.value,
                    event.user_identifier,
                    event.action,
                    event.resource,
                    json.dumps(event.details),
                    event.ip_address,
                    event.user_agent,
                    event.success,
                    event.error_message,
                    event.session_id
                )
                
        except Exception as e:
            logger.error(f"❌ Failed to store audit event in database: {e}")
            # Fallback to file logging
            await self._log_to_file(event)
    
    async def _log_to_file(self, event: AuditEvent):
        """Fallback logging to file"""
        try:
            audit_file = "audit.log"
            with open(audit_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event.to_dict()) + "\n")
        except Exception as e:
            logger.error(f"❌ Failed to log audit event to file: {e}")
    
    async def _notify_critical_event(self, event: AuditEvent):
        """Send critical audit events to Torah Logs chat"""
        try:
            # Import here to avoid circular imports
            from src.core.service_container import get_container
            
            container = get_container()
            telegram_client = container.get_service_sync('telegram_client')
            
            if not telegram_client:
                return
                
            # Format event for Telegram
            status_emoji = "✅" if event.success else "❌"
            event_emoji = {
                AuditEventType.SECURITY_EVENT: "🚨",
                AuditEventType.MANUAL_BROADCAST: "📢",
                AuditEventType.SYSTEM_CONFIG_CHANGE: "⚙️"
            }.get(event.event_type, "🔍")
            
            message = f"""🔍 <b>Audit Log - Critical Event</b>
            
{event_emoji} <b>Type:</b> {event.event_type.value}
{status_emoji} <b>Status:</b> {'Success' if event.success else 'Failed'}
👤 <b>User:</b> {event.user_identifier}
🎯 <b>Action:</b> {event.action}
📋 <b>Resource:</b> {event.resource}
🌐 <b>IP:</b> {event.ip_address or 'Unknown'}
⏰ <b>Time:</b> {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC"""

            if event.details:
                details_str = json.dumps(event.details, indent=2)[:500]  # Limit size
                message += f"\n📊 <b>Details:</b>\n<code>{details_str}</code>"
                
            if event.error_message:
                message += f"\n❌ <b>Error:</b> {event.error_message}"
            
            await telegram_client.send_message(
                chat_id=self._torah_logs_chat_id,
                text=message,
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to notify critical audit event: {e}")
    
    async def get_audit_history(
        self, 
        user_identifier: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        hours: int = 24,
        limit: int = 100
    ) -> list:
        """Retrieve audit history"""
        try:
            if not self._connection_pool:
                return []
                
            query = """
                SELECT * FROM audit_log 
                WHERE timestamp >= NOW() - INTERVAL $1 || ' hours'
            """
            params: list = [str(hours)]
            
            if user_identifier:
                query += " AND user_identifier = $" + str(len(params) + 1)
                params.append(user_identifier)
                
            if event_type:
                query += " AND event_type = $" + str(len(params) + 1) 
                params.append(event_type.value)
                
            query += " ORDER BY timestamp DESC LIMIT $" + str(len(params) + 1)
            params.append(str(limit))
            
            async with self._connection_pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"❌ Failed to retrieve audit history: {e}")
            return []
    
    async def cleanup(self):
        """Clean up audit logging system"""
        try:
            if self._processing_task:
                self._processing_task.cancel()
                
            if self._connection_pool:
                await self._connection_pool.close()
                
            logger.info("🔍 Audit logging system cleaned up")
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup audit logging: {e}")

# Global audit logger instance
_audit_logger = None

async def get_audit_logger() -> AuditLogger:
    """Get or create global audit logger"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
        await _audit_logger.initialize()
    return _audit_logger

# Convenience functions for common audit events
async def log_admin_action(
    user_identifier: str,
    action: str,
    resource: str,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    success: bool = True,
    error_message: Optional[str] = None
):
    """Log admin action with audit trail"""
    audit_logger = await get_audit_logger()
    await audit_logger.log_event(
        event_type=AuditEventType.MANUAL_BROADCAST,
        user_identifier=user_identifier,
        action=action,
        resource=resource,
        details=details,
        ip_address=ip_address,
        success=success,
        error_message=error_message
    )

async def log_security_event(
    event_description: str,
    user_identifier: str = "system",
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
):
    """Log security event"""
    audit_logger = await get_audit_logger()
    await audit_logger.log_event(
        event_type=AuditEventType.SECURITY_EVENT,
        user_identifier=user_identifier,
        action="security_event",
        resource="system",
        details={"description": event_description, **(details or {})},
        ip_address=ip_address
    )