#!/usr/bin/env python3
"""
Torah Bot Daily Broadcast System - MIGRATED TO INTERNAL API
Fully integrated with Internal Newsletter API microservice
"""
import asyncio
import logging
import json
import os
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any

# Internal Newsletter API integration
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.newsletter_api import InternalNewsletterAPIClient
from .newsletter_manager import newsletter_manager, BroadcastContent

logger = logging.getLogger(__name__)

class DailyBroadcastSystem:
    """Manages daily wisdom broadcast creation and delivery via Internal API"""
    
    def __init__(self, telegram_client):
        self.telegram_client = telegram_client
        self.newsletter_api = InternalNewsletterAPIClient()
        self.supported_languages = [
            "English", "Russian", "Hebrew", "Spanish", "French", "German", "Arabic"
        ]
        
    async def health_check(self) -> bool:
        """Check if Internal Newsletter API is available"""
        return await self.newsletter_api.health_check()
        
    async def get_api_stats(self) -> Dict[str, Any]:
        """Get statistics from Internal API"""
        return await self.newsletter_api.get_stats()
    
    async def create_daily_broadcast(self, target_date: date = None, topic: str = None) -> Optional[int]:
        """Create and send daily broadcast via Internal API"""
        if target_date is None:
            target_date = date.today()
            
        logger.info(f"📅 Creating daily broadcast for {target_date} via Internal API")
        
        try:
            # Check API health
            if not await self.health_check():
                logger.error("Internal Newsletter API unavailable")
                return None
            
            # Send broadcast via Internal API
            result = await self.newsletter_api.send_broadcast(
                topic=topic,
                language="Russian",  # Primary language
                user_name="Друг"
            )
            
            if result['success']:
                logger.info(f"""✅ Daily broadcast sent via Internal API:
📤 Sent: {result['sent_count']}
❌ Failed: {result['failed_count']} 
🎯 Topic: {result['topic']}
🖼️ Image: {'✅' if result['has_image'] else '❌'}""")
                
                # Create broadcast record in database for tracking
                broadcast_content = BroadcastContent(
                    date=target_date,
                    topic=result['topic'],
                    wisdom_content={"Russian": {"text": "Generated via Internal API", "topic": result['topic']}},
                    image_url=None  # Image handled by API
                )
                
                broadcast_id = await newsletter_manager.create_broadcast_content(
                    broadcast_date=target_date,
                    content=broadcast_content,
                    created_by="internal_api"
                )
                
                return broadcast_id
            else:
                logger.error(f"Internal API broadcast failed: {result['message']}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create daily broadcast via Internal API: {e}")
            return None
    
    async def send_test_broadcast_to_admin(self, admin_chat_id: int, topic: Optional[str] = None) -> bool:
        """Send test broadcast to admin via Internal API"""
        try:
            logger.info(f"🧪 Sending test broadcast to admin {admin_chat_id} via Internal API")
            
            # Check API health
            if not await self.health_check():
                logger.error("Internal Newsletter API unavailable for test broadcast")
                return False
            
            # Get API stats for admin info
            stats = await self.get_api_stats()
            
            # Send admin notification
            admin_message = f"""🧪 <b>TEST BROADCAST VIA INTERNAL API</b>

🚀 <b>API Status:</b> ✅ Online
📊 <b>Subscribers:</b> {stats['active_subscribers']} active
💾 <b>Database:</b> ✅ Connected

🎯 <b>Topic:</b> {topic or 'Contextual daily wisdom'}

⏳ <b>Sending test broadcast...</b>

This will be followed by the actual broadcast content identical to what subscribers receive."""

            await self.telegram_client.send_message(
                admin_chat_id,
                admin_message,
                parse_mode="HTML"
            )
            
            # Generate test content for admin only (not broadcast to all users)
            from src.newsletter_api.service import NewsletterAPIService
            test_service = NewsletterAPIService()
            
            # Generate wisdom content
            wisdom_data = await test_service.generate_wisdom_using_main_bot(
                topic or test_service.get_contextual_topic(),
                "Russian", 
                "Admin"
            )
            
            # Generate image
            image_url = await test_service.generate_image(wisdom_data['topic'])
            
            # Format message EXACTLY like main bot
            wisdom_text = test_service.format_wisdom_message(wisdom_data, "Russian")
            keyboard = test_service.get_keyboard("Russian", wisdom_data["wisdom"])
            
            # Send ONLY to admin (not all users)
            if image_url:
                response = await self.telegram_client.send_photo(
                    chat_id=admin_chat_id,
                    photo_url=image_url,
                    caption=wisdom_text,
                    reply_markup=keyboard
                )
            else:
                response = await self.telegram_client.send_message(
                    chat_id=admin_chat_id,
                    text=wisdom_text,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
            
            # Create result object
            result = {
                'success': response and response.get('ok', False),
                'sent_count': 1 if response and response.get('ok') else 0,
                'failed_count': 0 if response and response.get('ok') else 1,
                'topic': wisdom_data['topic'],
                'has_image': bool(image_url),
                'message': 'Test sent to admin only'
            }
            
            # Send result summary to admin
            if result['success']:
                summary = f"""✅ <b>TEST BROADCAST COMPLETED</b>

📈 <b>Results:</b>
• Successfully sent: {result['sent_count']}
• Failed: {result['failed_count']}
• Topic: {result['topic']}
• Image generated: {'✅ Yes' if result['has_image'] else '❌ No'}

🎯 <b>Service:</b> Internal Newsletter API
💡 <b>Status:</b> System ready for production broadcasts"""
            else:
                summary = f"""❌ <b>TEST BROADCAST FAILED</b>

⚠️ <b>Error:</b> {result['message']}
🔧 <b>Action needed:</b> Check Internal API service status"""

            await self.telegram_client.send_message(
                admin_chat_id,
                summary,
                parse_mode="HTML"
            )
            
            return result['success']
            
        except Exception as e:
            logger.error(f"Error sending test broadcast via Internal API: {e}")
            
            # Send error notification to admin
            await self.telegram_client.send_message(
                admin_chat_id,
                f"❌ <b>TEST BROADCAST ERROR</b>\n\n🔧 Internal API error: {str(e)}",
                parse_mode="HTML"
            )
            return False
    
    async def send_scheduled_broadcast(self, topic: Optional[str] = None) -> bool:
        """Send scheduled broadcast via Internal API"""
        try:
            logger.info("⏰ Executing scheduled broadcast via Internal API")
            
            # Check API health
            if not await self.health_check():
                logger.error("Internal Newsletter API unavailable for scheduled broadcast")
                return False
            
            # Send broadcast
            result = await self.newsletter_api.send_broadcast(
                topic=topic,
                language="Russian",
                user_name="Друг"
            )
            
            if result['success']:
                logger.info(f"""✅ Scheduled broadcast complete via Internal API:
📤 Sent: {result['sent_count']}
❌ Failed: {result['failed_count']} 
🎯 Topic: {result['topic']}
🖼️ Image: {'✅' if result['has_image'] else '❌'}""")
                return True
            else:
                logger.error(f"Scheduled broadcast failed: {result['message']}")
                return False
                
        except Exception as e:
            logger.error(f"Scheduled broadcast error: {e}")
            return False

    # Legacy method compatibility - redirects to Internal API
    async def generate_daily_wisdom(self, target_date: date, topic: str = None) -> Dict[str, Dict[str, str]]:
        """Legacy method - redirects to Internal API"""
        logger.warning("generate_daily_wisdom called - redirecting to Internal API")
        
        result = await self.newsletter_api.send_broadcast(
            topic=topic,
            language="Russian",
            user_name="System"
        )
        
        if result['success']:
            return {
                "Russian": {
                    "text": f"Generated via Internal API - Topic: {result['topic']}",
                    "topic": result['topic'],
                    "references": "Internal API Generated",
                    "date": target_date.isoformat()
                }
            }
        else:
            return {"Russian": {"text": "Internal API generation failed", "topic": "Error", "references": "N/A", "date": target_date.isoformat()}}

    # Legacy method compatibility
    async def generate_wisdom_image(self, topic: str, date: date) -> Optional[str]:
        """Legacy method - handled by Internal API"""
        logger.warning("generate_wisdom_image called - handled by Internal API")
        return None  # Image generation handled by Internal API

# Global instance
broadcast_system = None

def get_broadcast_system(telegram_client):
    """Get or create broadcast system instance"""
    global broadcast_system
    if broadcast_system is None:
        broadcast_system = DailyBroadcastSystem(telegram_client)
    return broadcast_system