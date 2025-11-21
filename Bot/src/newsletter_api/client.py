"""
Internal Newsletter API Client
Клиент для взаимодействия с внутренним Newsletter API Service
"""

import logging
from typing import Optional, Dict, Any
from .service import get_newsletter_service

logger = logging.getLogger(__name__)

class InternalNewsletterAPIClient:
    """Internal Newsletter API Client - direct service calls"""
    
    def __init__(self, telegram_client=None):
        self.service = None
        self.telegram_client = telegram_client
        
    async def _get_service(self):
        """Get newsletter service instance"""
        if not self.service:
            self.service = await get_newsletter_service(self.telegram_client)
        return self.service
    
    async def health_check(self) -> bool:
        """Check if newsletter service is available"""
        try:
            service = await self._get_service()
            return service is not None
        except Exception as e:
            logger.error(f"❌ Newsletter service health check failed ({type(e).__name__}): {e}")
            return False
    
    async def send_broadcast(
        self, 
        topic: Optional[str] = None, 
        language: str = "Russian", 
        user_name: str = "Друг"
    ) -> Dict[str, Any]:
        """
        Send broadcast via internal service
        
        Args:
            topic: Broadcast topic (if None, uses contextual)
            language: Broadcast language
            user_name: User name for personalization
            
        Returns:
            Broadcast result with statistics
        """
        try:
            logger.info(f"🚀 Internal API: Requesting broadcast - topic='{topic}', lang={language}")
            
            service = await self._get_service()
            result = await service.send_broadcast(topic=topic, language=language, user_name=user_name)
            
            if result['success']:
                logger.info(f"✅ Internal API broadcast: {result['sent_count']} sent, {result['failed_count']} failed")
            else:
                logger.error(f"❌ Internal API broadcast failed: {result['message']}")
            
            return result
                    
        except Exception as e:
            logger.error(f"❌ Internal API broadcast error ({type(e).__name__}): {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Internal API call failed: {str(e)}",
                "sent_count": 0,
                "failed_count": 0,
                "topic": topic or "unknown",
                "has_image": False
            }
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get newsletter statistics via internal service
        
        Returns:
            Newsletter statistics
        """
        try:
            logger.info("📊 Internal API: Requesting stats")
            
            service = await self._get_service()
            stats = await service.get_stats()
            
            logger.info(f"✅ Internal API stats: {stats['active_subscribers']} active subscribers")
            return stats
                    
        except Exception as e:
            logger.error(f"❌ Internal API stats error ({type(e).__name__}): {e}", exc_info=True)
            return {
                "total_subscribers": 0,
                "active_subscribers": 0,
                "language_breakdown": {},
                "last_broadcast_time": None,
                "total_broadcasts_sent": 0
            }

    async def send_quiz_broadcast(self, topic: Optional[str] = None, language: str = "Russian"):
        """Send quiz broadcast via internal service"""
        try:
            service = await self._get_service()
            return await service.send_quiz_broadcast(topic, language)
        except Exception as e:
            logger.error(f"❌ Internal API quiz broadcast error ({type(e).__name__}): {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Internal API call failed: {str(e)}",
                "sent_count": 0,
                "failed_count": 0,
                "topic": topic or "unknown",
                "quiz": True
            }

# Convenience functions for main bot integration

async def send_newsletter_broadcast(
    client: InternalNewsletterAPIClient,
    topic: Optional[str] = None
) -> bool:
    """
    Convenient function to send newsletter broadcast
    """
    result = await client.send_broadcast(topic=topic)
    return result.get('success', False)

async def get_newsletter_stats(client: InternalNewsletterAPIClient) -> str:
    """
    Get newsletter statistics as formatted string
    """
    stats = await client.get_stats()
    
    if stats['active_subscribers'] == 0:
        return "📊 Нет активных подписчиков"
    
    lang_breakdown = stats.get('language_breakdown', {})
    lang_text = ", ".join([f"{lang}: {count}" for lang, count in lang_breakdown.items()])
    
    return f"""📊 **Статистика Internal Newsletter API:**
👥 Всего подписчиков: {stats['total_subscribers']}
✅ Активных: {stats['active_subscribers']}
🌐 По языкам: {lang_text}
📨 Всего рассылок: {stats['total_broadcasts_sent']}"""

# Quiz admin testing method  
async def send_quiz_to_admin(client: InternalNewsletterAPIClient, admin_id: int):
    """Send test quiz to admin"""
    try:
        service = await client._get_service()
        return await service.send_quiz_to_admin(admin_id)
    except Exception as e:
        logger.error(f"❌ Newsletter API quiz test failed: {e}")
        return {"success": False, "message": str(e)}