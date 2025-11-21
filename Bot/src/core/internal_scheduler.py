"""
Internal Scheduler - manages broadcasts when service is awake
Works in coordination with external wake-up calls from cron-job.org
"""

import asyncio
import logging
from datetime import datetime, timedelta, time as dt_time
from typing import Optional

logger = logging.getLogger(__name__)

class InternalScheduler:
    """Internal scheduler that manages broadcasts when service is active"""
    
    def __init__(self, container):
        self.container = container
        self.running = False
        self.last_check = None
        
        # Moscow time broadcast windows
        self.morning_window = (dt_time(6, 0), dt_time(12, 0))    # 06:00-12:00 MSK
        self.evening_window = (dt_time(18, 0), dt_time(22, 0))   # 18:00-22:00 MSK
        
        logger.info("🕒 Internal scheduler initialized")
    
    def get_moscow_time(self) -> datetime:
        """Get current Moscow time (UTC+3)"""
        utc_now = datetime.now()
        return utc_now + timedelta(hours=3)
    
    def is_in_window(self, current_time: datetime, window_start: dt_time, window_end: dt_time) -> bool:
        """Check if current time is within the specified window"""
        current_time_obj = current_time.time()
        return window_start <= current_time_obj <= window_end
    
    async def check_and_send_broadcasts(self):
        """Check time windows and send appropriate broadcasts if needed"""
        moscow_now = self.get_moscow_time()
        today = moscow_now.date()
        
        logger.info(f"🕒 Scheduler check at {moscow_now.strftime('%H:%M:%S MSK')}")
        
        newsletter_manager = self.container.get_service_sync('newsletter_manager')
        if not newsletter_manager:
            logger.error("❌ Newsletter manager not available")
            return
        
        # Check morning wisdom window (06:00-12:00 MSK)
        if self.is_in_window(moscow_now, *self.morning_window):
            logger.info("🌅 In morning window - checking wisdom broadcast")
            
            # Try to reserve wisdom slot
            wisdom_id = await newsletter_manager.reserve_broadcast_slot("wisdom")
            if wisdom_id:
                logger.info(f"✅ Reserved wisdom slot (ID: {wisdom_id}) - triggering broadcast")
                await self._trigger_wisdom_broadcast()
            else:
                logger.info("🔄 Wisdom already sent today")
        
        # Check evening quiz window (18:00-22:00 MSK)  
        elif self.is_in_window(moscow_now, *self.evening_window):
            logger.info("🌆 In evening window - checking quiz broadcast")
            
            # Try to reserve quiz slot
            quiz_id = await newsletter_manager.reserve_broadcast_slot("quiz")
            if quiz_id:
                logger.info(f"✅ Reserved quiz slot (ID: {quiz_id}) - triggering broadcast")
                await self._trigger_quiz_broadcast()
            else:
                logger.info("🔄 Quiz already sent today")
        
        else:
            logger.info(f"⏰ Outside broadcast windows - current time: {moscow_now.strftime('%H:%M MSK')}")
        
        self.last_check = moscow_now
    
    async def _trigger_wisdom_broadcast(self):
        """Trigger morning wisdom broadcast"""
        try:
            # Create newsletter API client directly
            from src.newsletter_api import InternalNewsletterAPIClient
            
            # Get telegram client from container
            telegram_client = self.container.get_service_sync('telegram_client')
            if telegram_client:
                newsletter_client = InternalNewsletterAPIClient(telegram_client)
                result = await newsletter_client.send_broadcast(
                    topic=None,  # Auto-select topic
                    language="Russian",
                    user_name="System"
                )
                logger.info(f"📧 Wisdom broadcast result: {result}")
            else:
                logger.error("❌ Telegram client not available for wisdom broadcast")
        except Exception as e:
            logger.error(f"❌ Failed to trigger wisdom broadcast: {e}")
    
    async def _trigger_quiz_broadcast(self):
        """Trigger evening quiz broadcast"""
        try:
            # Create newsletter API client directly
            from src.newsletter_api import InternalNewsletterAPIClient
            
            # Get telegram client from container
            telegram_client = self.container.get_service_sync('telegram_client')
            if telegram_client:
                newsletter_client = InternalNewsletterAPIClient(telegram_client)
                result = await newsletter_client.send_quiz_broadcast(
                    topic=None,  # Auto-select topic
                    language="Russian"
                )
                logger.info(f"🧠 Quiz broadcast result: {result}")
            else:
                logger.error("❌ Telegram client not available for quiz broadcast")
        except Exception as e:
            logger.error(f"❌ Failed to trigger quiz broadcast: {e}")
    
    def get_status(self) -> dict:
        """Get scheduler status for monitoring"""
        moscow_now = self.get_moscow_time()
        
        return {
            "running": self.running,
            "last_check": self.last_check.strftime('%H:%M:%S MSK') if self.last_check else None,
            "current_time": moscow_now.strftime('%H:%M:%S MSK'),
            "windows": {
                "morning": f"{self.morning_window[0].strftime('%H:%M')}-{self.morning_window[1].strftime('%H:%M')} MSK",
                "evening": f"{self.evening_window[0].strftime('%H:%M')}-{self.evening_window[1].strftime('%H:%M')} MSK"
            },
            "in_morning_window": self.is_in_window(moscow_now, *self.morning_window),
            "in_evening_window": self.is_in_window(moscow_now, *self.evening_window)
        }