#!/usr/bin/env python3
"""
Torah Bot Newsletter Management System
Handles subscriptions, broadcasts, and admin functionality
"""
import os
import asyncio
import logging
import json
import asyncpg
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, time, timezone
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class NewsletterUser:
    telegram_user_id: int
    username: str
    first_name: str
    language: str
    is_subscribed: bool
    delivery_time: time
    timezone_str: str

@dataclass
class BroadcastContent:
    date: date
    topic: str
    wisdom_content: Dict[str, Dict[str, str]]  # {language: {text, references}}
    image_url: Optional[str] = None

class NewsletterManager:
    """Manages newsletter subscriptions and broadcasts"""
    
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        self.pool: Optional[asyncpg.Pool] = None
        
    async def initialize(self):
        """Initialize database connection pool with retry logic"""
        import asyncio
        
        if not self.db_url:
            raise ValueError("DATABASE_URL not found in environment")
        
        # Retry logic with exponential backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.pool = await asyncpg.create_pool(
                    self.db_url,
                    min_size=0,
                    max_size=4,
                    command_timeout=30
                )
                logger.info("Newsletter database pool initialized")
                return
            except Exception as e:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️ Database pool initialization failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"❌ Database pool initialization failed after {max_retries} attempts: {e}")
                    raise
    
    async def close(self):
        """Close database connections"""
        if self.pool:
            await self.pool.close()
    
    # ===================================================================
    # USER MANAGEMENT
    # ===================================================================
    
    async def upsert_user(self, user_data: Dict[str, Any]) -> bool:
        """Create or update user in database"""
        try:
            if not self.pool:
                raise ValueError("Database pool not initialized")
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO users (
                        telegram_user_id, username, first_name, last_name, 
                        language_code, is_bot, is_premium, user_data
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (telegram_user_id) 
                    DO UPDATE SET
                        username = EXCLUDED.username,
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        language_code = EXCLUDED.language_code,
                        is_premium = EXCLUDED.is_premium,
                        user_data = EXCLUDED.user_data,
                        last_interaction = NOW()
                """, 
                    user_data.get('id'),
                    user_data.get('username'),
                    user_data.get('first_name'),
                    user_data.get('last_name'),
                    user_data.get('language_code', 'en'),
                    user_data.get('is_bot', False),
                    user_data.get('is_premium', False),
                    json.dumps(user_data)
                )
                
                logger.info(f"✅ User {user_data.get('id')} upserted successfully")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to upsert user {user_data.get('id')}: {e}")
            return False
    
    async def update_user_activity(self, telegram_user_id: int, activity_type: str):
        """Update user activity statistics"""
        try:
            if not self.pool:
                raise ValueError("Database pool not initialized")
            async with self.pool.acquire() as conn:
                if activity_type == "wisdom_request":
                    await conn.execute("""
                        UPDATE users 
                        SET total_wisdom_requests = total_wisdom_requests + 1,
                            last_interaction = NOW()
                        WHERE telegram_user_id = $1
                    """, telegram_user_id)
                elif activity_type == "quiz_attempt":
                    await conn.execute("""
                        UPDATE users 
                        SET total_quiz_attempts = total_quiz_attempts + 1,
                            last_interaction = NOW()
                        WHERE telegram_user_id = $1
                    """, telegram_user_id)
                    
        except Exception as e:
            logger.error(f"Failed to update user activity for {telegram_user_id}: {e}")
    
    # ===================================================================
    # SUBSCRIPTION MANAGEMENT
    # ===================================================================
    
    async def subscribe_user(self, telegram_user_id: int, language: str = "English", 
                           delivery_time: str = "09:00", timezone_str: str = "UTC") -> bool:
        """Subscribe user to newsletter"""
        try:
            if not self.pool:
                raise ValueError("Database pool not initialized")
            async with self.pool.acquire() as conn:
                # Convert string time to TIME object if needed
                if isinstance(delivery_time, str):
                    from datetime import time
                    time_parts = delivery_time.split(':')
                    if len(time_parts) == 2:
                        delivery_time_obj = time(int(time_parts[0]), int(time_parts[1]), 0)
                    elif len(time_parts) == 3:
                        delivery_time_obj = time(int(time_parts[0]), int(time_parts[1]), int(time_parts[2]))
                    else:
                        delivery_time_obj = time(9, 0, 0)  # Default 9:00 AM
                else:
                    delivery_time_obj = delivery_time
                
                await conn.execute("""
                    INSERT INTO newsletter_subscriptions 
                    (user_id, language, delivery_time, timezone, is_active)
                    VALUES ($1, $2, $3, $4, TRUE)
                    ON CONFLICT (user_id) 
                    DO UPDATE SET
                        is_active = TRUE,
                        language = EXCLUDED.language,
                        delivery_time = EXCLUDED.delivery_time,
                        timezone = EXCLUDED.timezone,
                        unsubscribed_at = NULL
                """, telegram_user_id, language, delivery_time_obj, timezone_str)
                
                logger.info(f"📧 User {telegram_user_id} subscribed to newsletter ({language})")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to subscribe user {telegram_user_id}: {e}")
            return False
    
    async def unsubscribe_user(self, telegram_user_id: int) -> bool:
        """Unsubscribe user from newsletter"""
        try:
            if not self.pool:
                raise ValueError("Database pool not initialized")
            async with self.pool.acquire() as conn:
                result = await conn.execute("""
                    UPDATE newsletter_subscriptions 
                    SET is_active = FALSE, unsubscribed_at = NOW()
                    WHERE user_id = $1 AND is_active = TRUE
                """, telegram_user_id)
                
                if result == "UPDATE 1":
                    logger.info(f"📧 User {telegram_user_id} unsubscribed from newsletter")
                    return True
                else:
                    logger.warning(f"⚠️ User {telegram_user_id} was not subscribed")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Failed to unsubscribe user {telegram_user_id}: {e}")
            return False
    
    async def get_subscriber_count(self) -> Dict[str, int]:
        """Get subscriber statistics"""
        try:
            if not self.pool:
                raise ValueError("Database pool not initialized")
            async with self.pool.acquire() as conn:
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_subscribers,
                        COUNT(*) FILTER (WHERE u.last_interaction > NOW() - INTERVAL '30 days') as active_30d,
                        COUNT(*) FILTER (WHERE u.last_interaction > NOW() - INTERVAL '7 days') as active_7d
                    FROM newsletter_subscriptions ns
                    JOIN users u ON u.telegram_user_id = ns.user_id
                    WHERE ns.is_active = TRUE
                """)
                
                return {
                    'total_subscribers': stats['total_subscribers'],
                    'active_30_days': stats['active_30d'],
                    'active_7_days': stats['active_7d']
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get subscriber count: {e}")
            return {'total_subscribers': 0, 'active_30_days': 0, 'active_7_days': 0}
    
    async def get_subscribers_by_language(self) -> Dict[str, int]:
        """Get subscriber count by language"""
        try:
            if not self.pool:
                raise ValueError("Database pool not initialized")
            async with self.pool.acquire() as conn:
                results = await conn.fetch("""
                    SELECT language, COUNT(*) as count
                    FROM newsletter_subscriptions
                    WHERE is_active = TRUE
                    GROUP BY language
                    ORDER BY count DESC
                """)
                
                return {row['language']: row['count'] for row in results}
                
        except Exception as e:
            logger.error(f"❌ Failed to get subscribers by language: {e}")
            return {}
    
    # ===================================================================
    # BROADCAST MANAGEMENT
    # ===================================================================
    
    async def create_broadcast_content(self, broadcast_date: date, content: BroadcastContent, 
                                     created_by: str = "system") -> Optional[int]:
        """Create new broadcast content"""
        try:
            if not self.pool:
                raise ValueError("Database pool not initialized")
            async with self.pool.acquire() as conn:
                broadcast_id = await conn.fetchval("""
                    INSERT INTO newsletter_broadcasts 
                    (broadcast_date, wisdom_content, image_url, created_by, status)
                    VALUES ($1, $2, $3, $4, 'ready')
                    RETURNING id
                """, 
                    broadcast_date,
                    json.dumps(content.wisdom_content),
                    content.image_url,
                    created_by
                )
                
                logger.info(f"📝 Created broadcast content for {broadcast_date} (ID: {broadcast_id})")
                return broadcast_id
                
        except Exception as e:
            logger.error(f"❌ Failed to create broadcast content: {e}")
            return None
    
    async def reserve_broadcast_slot(self, content_type: str) -> Optional[int]:
        """
        Atomically reserve a broadcast slot for today to prevent duplicate broadcasts.
        Returns broadcast_id if successfully reserved, None if already exists for today.
        """
        try:
            if not self.pool:
                raise ValueError("Database pool not initialized")
                
            from datetime import datetime, timedelta, date
            
            # Calculate MSK date (UTC+3)
            utc_now = datetime.now()
            moscow_now = utc_now + timedelta(hours=3)
            today_msk = moscow_now.date()
            
            async with self.pool.acquire() as conn:
                # Atomic INSERT with ON CONFLICT DO NOTHING
                broadcast_id = await conn.fetchval("""
                    INSERT INTO newsletter_broadcasts 
                    (broadcast_date, broadcast_type, created_at, status, created_by)
                    VALUES ($1, $2, NOW(), 'reserved', 'auto_scheduler')
                    ON CONFLICT (broadcast_date, broadcast_type) DO NOTHING
                    RETURNING id
                """, today_msk, content_type)
                
                if broadcast_id:
                    logger.info(f"✅ RESERVED {content_type} broadcast slot for {today_msk} (ID: {broadcast_id})")
                    return broadcast_id
                else:
                    logger.info(f"🔄 {content_type.title()} broadcast already sent today ({today_msk}) - skipping")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Failed to reserve broadcast slot: {e}")
            return None
    
    async def get_broadcast_for_date(self, target_date: date) -> Optional[Dict]:
        """Get broadcast content for specific date"""
        try:
            if not self.pool:
                raise ValueError("Database pool not initialized")
            async with self.pool.acquire() as conn:
                broadcast = await conn.fetchrow("""
                    SELECT id, broadcast_date, wisdom_content, image_url, status, 
                           total_recipients, successful_deliveries, failed_deliveries
                    FROM newsletter_broadcasts
                    WHERE broadcast_date = $1
                """, target_date)
                
                if broadcast:
                    return {
                        'id': broadcast['id'],
                        'date': broadcast['broadcast_date'],
                        'content': json.loads(broadcast['wisdom_content']),
                        'image_url': broadcast['image_url'],
                        'status': broadcast['status'],
                        'stats': {
                            'total_recipients': broadcast['total_recipients'],
                            'successful_deliveries': broadcast['successful_deliveries'],
                            'failed_deliveries': broadcast['failed_deliveries']
                        }
                    }
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to get broadcast for {target_date}: {e}")
            return None
    
    # ===================================================================
    # ADMIN FUNCTIONALITY
    # ===================================================================
    
    async def is_admin(self, telegram_user_id: int) -> bool:
        """Check if user is admin with retry logic for race conditions and comprehensive fallback protection"""
        
        # FALLBACK PROTECTION: Hardcoded admin IDs as safety net
        FALLBACK_ADMIN_IDS = {6630727156, 7057240608}  # @torah_support, @zohan
        
        try:
            # CRITICAL FIX: Retry logic for pool initialization race condition
            max_retries = 3
            for attempt in range(max_retries):
                if not self.pool:
                    if attempt < max_retries - 1:
                        logger.warning(f"Pool not ready, retrying... (attempt {attempt + 1})")
                        await asyncio.sleep(0.1)  # Wait 100ms
                        continue
                    else:
                        logger.error("Pool not initialized after retries - using fallback")
                        # Fallback to hardcoded list if DB unavailable
                        fallback_result = telegram_user_id in FALLBACK_ADMIN_IDS
                        logger.info(f"🔒 Fallback admin check for {telegram_user_id}: {fallback_result}")
                        return fallback_result
                
                async with self.pool.acquire() as conn:
                    admin = await conn.fetchrow("""
                        SELECT id FROM admin_users 
                        WHERE telegram_user_id = $1 AND is_active = TRUE
                    """, telegram_user_id)
                    
                    is_admin_result = admin is not None
                    logger.info(f"✅ Database admin check for {telegram_user_id}: {is_admin_result}")
                    
                    # ENHANCED FALLBACK: If database is empty but user is in fallback list, use fallback
                    if not is_admin_result and telegram_user_id in FALLBACK_ADMIN_IDS:
                        # Check if admin_users table is completely empty (production DB scenario)
                        admin_count = await conn.fetchval("SELECT COUNT(*) FROM admin_users WHERE is_active = TRUE")
                        if admin_count == 0:
                            logger.warning(f"🔒 Production DB empty - using fallback for {telegram_user_id}")
                            return True
                    
                    return is_admin_result
                    
            # Fallback if loop completes without return
            logger.warning(f"🔒 Unexpected path in is_admin for {telegram_user_id} - using fallback")
            return telegram_user_id in FALLBACK_ADMIN_IDS
            
        except Exception as e:
            logger.error(f"❌ Failed to check admin status for {telegram_user_id}: {e}")
            # Fallback to hardcoded list if DB error occurs
            fallback_result = telegram_user_id in FALLBACK_ADMIN_IDS
            logger.info(f"🔒 Exception fallback admin check for {telegram_user_id}: {fallback_result}")
            return fallback_result
    
    async def get_admin_permissions(self, telegram_user_id: int) -> Dict[str, bool]:
        """Get admin permissions with fallback support"""
        
        # FALLBACK ADMIN IDs
        FALLBACK_ADMIN_IDS = {6630727156, 7057240608}  # @torah_support, @zohan
        
        # Default full permissions for fallback admins
        FALLBACK_PERMISSIONS = {
            "can_send_broadcasts": True,
            "can_test_broadcasts": True, 
            "can_manage_users": True,
            "can_view_stats": True,
            "can_manage_schedule": True
        }
        
        try:
            if not self.pool:
                if telegram_user_id in FALLBACK_ADMIN_IDS:
                    logger.info(f"🔒 Fallback permissions for {telegram_user_id} (no pool)")
                    return FALLBACK_PERMISSIONS
                return {}
                
            async with self.pool.acquire() as conn:
                admin = await conn.fetchrow("""
                    SELECT permissions FROM admin_users 
                    WHERE telegram_user_id = $1 AND is_active = TRUE
                """, telegram_user_id)
                
                if admin and admin['permissions']:
                    return json.loads(admin['permissions'])
                
                # ENHANCED FALLBACK: Check if DB is empty and user is fallback admin
                if telegram_user_id in FALLBACK_ADMIN_IDS:
                    admin_count = await conn.fetchval("SELECT COUNT(*) FROM admin_users WHERE is_active = TRUE")
                    if admin_count == 0:
                        logger.info(f"🔒 Fallback permissions for {telegram_user_id} (empty DB)")
                        return FALLBACK_PERMISSIONS
                
                return {}
                
        except Exception as e:
            logger.error(f"❌ Failed to get admin permissions for {telegram_user_id}: {e}")
            # Fallback for exceptions
            if telegram_user_id in FALLBACK_ADMIN_IDS:
                logger.info(f"🔒 Exception fallback permissions for {telegram_user_id}")
                return FALLBACK_PERMISSIONS
            return {}
    
    async def create_test_broadcast(self, admin_id: int, test_content: Dict, 
                                  image_url: Optional[str] = None, 
                                  target_languages: Optional[List[str]] = None) -> Optional[int]:
        """Create test broadcast for admin"""
        try:
            if target_languages is None:
                target_languages = ["English", "Russian"]
                
            if not self.pool:
                raise ValueError("Database pool not initialized")
            async with self.pool.acquire() as conn:
                test_id = await conn.fetchval("""
                    INSERT INTO test_broadcasts 
                    (admin_id, test_content, test_image_url, target_languages, status)
                    VALUES ($1, $2, $3, $4, 'ready')
                    RETURNING id
                """, admin_id, json.dumps(test_content), image_url, target_languages)
                
                logger.info(f"🧪 Created test broadcast for admin {admin_id} (ID: {test_id})")
                return test_id
                
        except Exception as e:
            logger.error(f"❌ Failed to create test broadcast: {e}")
            return None
    
    # ===================================================================
    # ANALYTICS
    # ===================================================================
    
    async def get_newsletter_analytics(self) -> Dict[str, Any]:
        """Get comprehensive newsletter analytics"""
        try:
            if not self.pool:
                raise ValueError("Database pool not initialized")
            async with self.pool.acquire() as conn:
                # Basic stats
                basic_stats = await conn.fetchrow("""
                    SELECT 
                        (SELECT COUNT(*) FROM users) as total_users,
                        (SELECT COUNT(*) FROM newsletter_subscriptions WHERE is_active = TRUE) as subscribers,
                        (SELECT COUNT(*) FROM newsletter_broadcasts WHERE status = 'completed') as completed_broadcasts,
                        (SELECT COUNT(*) FROM delivery_log WHERE status = 'sent' AND delivered_at > NOW() - INTERVAL '30 days') as deliveries_30d
                """)
                
                # Language breakdown
                language_stats = await conn.fetch("""
                    SELECT * FROM active_subscribers_by_language
                """)
                
                # Recent broadcast performance
                recent_broadcasts = await conn.fetch("""
                    SELECT * FROM broadcast_statistics
                    WHERE broadcast_date >= CURRENT_DATE - INTERVAL '7 days'
                    ORDER BY broadcast_date DESC
                """)
                
                return {
                    'overview': {
                        'total_users': basic_stats['total_users'],
                        'active_subscribers': basic_stats['subscribers'],
                        'completed_broadcasts': basic_stats['completed_broadcasts'],
                        'deliveries_last_30d': basic_stats['deliveries_30d']
                    },
                    'languages': [
                        {
                            'language': row['language'],
                            'subscribers': row['subscriber_count'],
                            'active_30d': row['active_users_30d'],
                            'active_7d': row['active_users_7d']
                        }
                        for row in language_stats
                    ],
                    'recent_broadcasts': [
                        {
                            'date': row['broadcast_date'],
                            'status': row['status'],
                            'recipients': row['total_recipients'],
                            'delivery_rate': float(row['delivery_rate_percent']) if row['delivery_rate_percent'] else 0,
                            'open_rate': float(row['open_rate_percent']) if row['open_rate_percent'] else 0
                        }
                        for row in recent_broadcasts
                    ]
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get newsletter analytics: {e}")
            return {'overview': {}, 'languages': [], 'recent_broadcasts': []}

# Global instance
newsletter_manager = NewsletterManager()