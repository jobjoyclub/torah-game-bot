#!/usr/bin/env python3
"""
Scheduled Broadcast System with Internal Newsletter API Integration
Система запланированных рассылок с интеграцией внутреннего Newsletter API
"""

import asyncio
import logging
import schedule
import time
from datetime import datetime, date
from typing import Optional, List, Dict, Any

# Internal Newsletter API integration
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.newsletter_api import InternalNewsletterAPIClient
from src.core.db_advisory_locks import get_advisory_lock_manager

logger = logging.getLogger(__name__)

class ScheduledBroadcastSystem:
    """Scheduled broadcast system using Internal Newsletter API"""
    
    def __init__(self, telegram_client=None):
        self.newsletter_api = InternalNewsletterAPIClient(telegram_client)
        self.is_running = False
    
    def _format_error_breakdown(self, error_breakdown):
        """Format detailed error breakdown for display"""
        if not error_breakdown or all(count == 0 for count in error_breakdown.values()):
            return "None"
        
        error_messages = []
        error_names = {
            "403_blocked": "🚫 User blocked bot",
            "429_rate_limit": "⏱️ Rate limited", 
            "400_bad_request": "❌ Bad request",
            "network_error": "🌐 Network error",
            "no_client": "📞 No client",
            "unknown_error": "❓ Unknown error"
        }
        
        for error_type, count in error_breakdown.items():
            if count > 0:
                name = error_names.get(error_type, error_type)
                error_messages.append(f"{name}: {count}")
        
        return "\n".join(error_messages) if error_messages else "None"
        
    async def start_scheduler(self):
        """Start the scheduled broadcast system"""
        logger.info("🕒 Starting Internal API scheduled broadcast system")
        
        # Check API health
        api_health = await self.newsletter_api.health_check()
        if not api_health:
            logger.error("❌ Internal Newsletter API unavailable - scheduler disabled")
            return False
        
        # Schedule daily broadcasts at 06:00 UTC (09:00 Moscow time) - Morning wisdom
        schedule.every().day.at("06:00").do(
            lambda: asyncio.create_task(self.send_scheduled_broadcast(topic=None))
        )
        
        # Schedule daily quiz broadcasts at 18:00 UTC (21:00 Moscow time) - Daily quiz
        schedule.every().day.at("18:00").do(
            lambda: asyncio.create_task(self.send_scheduled_quiz())
        )
        
        logger.info("✅ Internal API scheduler started - morning wisdom at 06:00 UTC (09:00 MSK), daily quiz at 18:00 UTC (21:00 MSK)")
        self.is_running = True
        
        # Run scheduler loop
        while self.is_running:
            schedule.run_pending()
            await asyncio.sleep(60)  # Check every minute
        
        return True
    
    async def send_scheduled_broadcast(self, topic: Optional[str] = None):
        """Send scheduled broadcast via Internal API with duplicate prevention"""
        try:
            # Get current date for lock
            current_date = date.today().strftime('%Y-%m-%d')
            logger.info(f"🚀 Executing scheduled wisdom broadcast for {current_date} via Internal Newsletter API")
            
            # Acquire advisory lock to prevent duplicate broadcasts  
            lock_manager = get_advisory_lock_manager()
            async with lock_manager.advisory_lock(f"broadcast:wisdom:{current_date}") as lock_acquired:
                if not lock_acquired:
                    logger.warning(f"🔒 Wisdom broadcast already in progress for {current_date} - skipping duplicate")
                    return False
                
                # Check API health
                api_health = await self.newsletter_api.health_check()
                if not api_health:
                    logger.error("❌ Scheduled broadcast failed - Internal API unavailable")
                    return False
            
                # Get current stats before broadcast
                pre_stats = await self.newsletter_api.get_stats()
                logger.info(f"📊 Pre-broadcast: {pre_stats['active_subscribers']} active subscribers")
                
                # Send broadcast
                result = await self.newsletter_api.send_broadcast(
                    topic=topic,
                    language="Russian",
                    user_name="Друг"
                )
                
                if result['success']:
                    broadcast_stats = f"""✅ Scheduled wisdom broadcast complete via Internal API:
📤 Sent: {result['sent_count']}
❌ Failed: {result['failed_count']} 
🎯 Topic: {result['topic']}
🖼️ Image: {'✅' if result['has_image'] else '❌'}
🔒 Date Lock: {current_date}"""
                    logger.info(broadcast_stats)
                
                    # Send broadcast statistics to Torah Logs chat
                    try:
                        # Get telegram client from newsletter api
                        if hasattr(self.newsletter_api, 'telegram_client') and self.newsletter_api.telegram_client:
                            torah_logs_chat_id = int(os.environ.get("TORAH_LOGS_CHAT_ID", "-1003025527880"))
                            success_rate = (result['sent_count'] / (result['sent_count'] + result['failed_count'])) * 100
                            
                            error_breakdown_text = self._format_error_breakdown(result.get('error_breakdown', {}))
                            
                            stats_message = f"""📊 <b>Wisdom Broadcast Statistics</b>
                            
📤 <b>Sent:</b> {result['sent_count']}
❌ <b>Failed:</b> {result['failed_count']}
📊 <b>Error Details:</b>
{error_breakdown_text}
📈 <b>Success Rate:</b> {success_rate:.1f}%
🎯 <b>Topic:</b> {result['topic']}
🖼️ <b>Image:</b> {'Included' if result['has_image'] else 'Text only'}
🔒 <b>Date Lock:</b> {current_date}
⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"""

                            await self.newsletter_api.telegram_client.send_message(
                                chat_id=torah_logs_chat_id,
                                text=stats_message,
                                parse_mode="HTML"
                            )
                            logger.info(f"📊 Wisdom broadcast statistics sent to logs chat")
                    except Exception as e:
                        logger.error(f"❌ Failed to send broadcast statistics to logs: {e}")
                
                    return True
                else:
                    logger.error(f"❌ Scheduled wisdom broadcast failed: {result['message']}")
                    return False
                
        except Exception as e:
            logger.error(f"❌ Scheduled broadcast error: {e}")
            return False
    
    async def send_scheduled_quiz(self):
        """Send scheduled quiz broadcast via Internal API with duplicate prevention"""
        try:
            # Get current date for lock
            current_date = date.today().strftime('%Y-%m-%d')
            logger.info(f"🧠 Executing scheduled quiz broadcast for {current_date} via Internal Newsletter API")
            
            # Acquire advisory lock to prevent duplicate quiz broadcasts
            lock_manager = get_advisory_lock_manager()
            async with lock_manager.advisory_lock(f"broadcast:quiz:{current_date}") as lock_acquired:
                if not lock_acquired:
                    logger.warning(f"🔒 Quiz broadcast already in progress for {current_date} - skipping duplicate")
                    return False
                
                # Check API health
                api_health = await self.newsletter_api.health_check()
                if not api_health:
                    logger.error("❌ Scheduled quiz broadcast failed - Internal API unavailable")
                    return False
            
                # Get current stats before broadcast
                pre_stats = await self.newsletter_api.get_stats()
                logger.info(f"📊 Pre-quiz broadcast: {pre_stats['active_subscribers']} active subscribers")
                
                # Send quiz broadcast
                result = await self.newsletter_api.send_quiz_broadcast(
                    topic=None,  # Random topic
                    language="Russian"
                )
            
                if result['success']:
                    quiz_stats = f"""✅ Scheduled quiz broadcast complete via Internal API:
📤 Sent: {result['sent_count']}
❌ Failed: {result['failed_count']} 
🧠 Topic: {result['topic']}
🔒 Date Lock: {current_date}"""
                    logger.info(quiz_stats)
                
                    # Send quiz statistics to Torah Logs chat
                    try:
                        # Get telegram client from newsletter api
                        if hasattr(self.newsletter_api, 'telegram_client') and self.newsletter_api.telegram_client:
                            torah_logs_chat_id = int(os.environ.get("TORAH_LOGS_CHAT_ID", "-1003025527880"))
                            success_rate = (result['sent_count'] / (result['sent_count'] + result['failed_count'])) * 100
                            
                            error_breakdown_text = self._format_error_breakdown(result.get('error_breakdown', {}))
                            
                            stats_message = f"""🧠 <b>Quiz Broadcast Statistics</b>
                            
📤 <b>Sent:</b> {result['sent_count']}
❌ <b>Failed:</b> {result['failed_count']}
📊 <b>Error Details:</b>
{error_breakdown_text}
📈 <b>Success Rate:</b> {success_rate:.1f}%
🧠 <b>Topic:</b> {result['topic']}
🔒 <b>Date Lock:</b> {current_date}
⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"""
                            
                            await self.newsletter_api.telegram_client.send_message(
                                chat_id=torah_logs_chat_id,
                                text=stats_message,
                                parse_mode="HTML"
                            )
                            logger.info("📊 Quiz broadcast stats sent to Torah Logs chat")
                            
                    except Exception as stats_error:
                        logger.warning(f"⚠️ Could not send quiz stats to logs chat: {stats_error}")
                
                    return True
                else:
                    logger.error(f"❌ Scheduled quiz broadcast failed: {result['message']}")
                    return False
                
        except Exception as e:
            logger.error(f"❌ Scheduled quiz broadcast error: {e}")
            return False

    async def send_manual_broadcast(self, topic: Optional[str] = None):
        """Send manual broadcast via Internal API - auto-detects time for content type with duplicate prevention"""
        from datetime import datetime, timezone, timedelta
        
        # Get Moscow time
        moscow_tz = timezone(timedelta(hours=3))
        moscow_time = datetime.now(moscow_tz)
        moscow_hour = moscow_time.hour
        
        # Create timestamp-based lock for manual broadcasts
        timestamp_str = moscow_time.strftime('%Y-%m-%d-%H')
        
        logger.info(f"🕒 Manual broadcast triggered at {moscow_time.strftime('%H:%M')} MSK")
        
        # Acquire advisory lock to prevent simultaneous manual broadcasts
        lock_manager = get_advisory_lock_manager()
        async with lock_manager.advisory_lock(f"broadcast:manual:{timestamp_str}") as lock_acquired:
            if not lock_acquired:
                logger.warning(f"🔒 Manual broadcast already in progress for hour {timestamp_str} - skipping duplicate")
                return False
        
            # Simple time-based logic: morning = wisdom, late day = quiz
            if moscow_hour >= 18:  # 18:00+ MSK = daily quiz time
                logger.info(f"🧠 Quiz time ({moscow_hour}:XX MSK) - sending quiz broadcast")
                return await self.send_scheduled_quiz()
            else:  # Morning/day = wisdom time
                logger.info(f"🌅 Morning time ({moscow_hour}:XX MSK) - sending wisdom broadcast")
                return await self.send_scheduled_broadcast(topic=topic)
    
    def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """Get list of all scheduled jobs"""
        jobs = []
        for job in schedule.jobs:
            job_info = {
                "next_run": job.next_run.strftime('%Y-%m-%d %H:%M:%S UTC') if job.next_run else "Not scheduled",
                "interval": f"Every day at {job.start_day}" if hasattr(job, 'start_day') else "Daily",
                "job_func": str(job.job_func),
                "tags": list(getattr(job, 'tags', set()))
            }
            
            # Determine job type based on function name
            if "send_scheduled_quiz" in str(job.job_func):
                job_info.update({
                    "type": "Quiz Broadcast",
                    "description": "Evening Torah Quiz at 21:00 Moscow time",
                    "time_utc": "18:00 UTC",
                    "time_moscow": "21:00 MSK"
                })
            elif "send_scheduled_broadcast" in str(job.job_func):
                job_info.update({
                    "type": "Wisdom Broadcast", 
                    "description": "Morning Torah Wisdom at 09:00 Moscow time",
                    "time_utc": "06:00 UTC",
                    "time_moscow": "09:00 MSK"
                })
            else:
                job_info.update({
                    "type": "Unknown",
                    "description": "Unknown scheduled task"
                })
                
            jobs.append(job_info)
        
        return jobs

    def stop_scheduler(self):
        """Stop the scheduled broadcast system"""
        logger.info("🛑 Stopping Internal API scheduled broadcast system")
        self.is_running = False
        schedule.clear()

# Global scheduler instance
_scheduler_instance = None

async def get_scheduler(telegram_client=None):
    """Get or create scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = ScheduledBroadcastSystem(telegram_client)
    return _scheduler_instance

async def start_scheduled_broadcasts():
    """Start scheduled broadcast system"""
    scheduler = await get_scheduler()
    return await scheduler.start_scheduler()

async def send_manual_broadcast(topic: Optional[str] = None, telegram_client=None):
    """Send manual broadcast now"""
    scheduler = await get_scheduler(telegram_client)
    return await scheduler.send_manual_broadcast(topic)

async def stop_scheduled_broadcasts():
    """Stop scheduled broadcast system"""
    global _scheduler_instance
    if _scheduler_instance:
        _scheduler_instance.stop_scheduler()
        _scheduler_instance = None