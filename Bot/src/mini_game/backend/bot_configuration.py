# Bot configuration for Telegram Mini App Store listing
import logging
import json
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

class BotStoreConfiguration:
    """Configure bot for Telegram Mini App Store featuring"""
    
    def __init__(self, telegram_client):
        self.telegram_client = telegram_client
    
    async def setup_bot_for_app_store(self):
        """Configure bot settings for app store visibility"""
        try:
            # Bot description for app store (visible in bot profile)
            bot_description = {
                "description": "🎮 Torah Bot: AI-powered Jewish wisdom education with interactive Shabbat Runner Mini App game. Learn Torah with AI Rabbi, take quizzes, and play educational games. Perfect for Jewish learning and Shabbat preparation!"
            }
            
            # Bot short description for listings
            short_description = {
                "short_description": "🕯️ AI Torah wisdom + Shabbat Runner game 🎮"
            }
            
            # Bot commands for better discoverability
            bot_commands = [
                {"command": "start", "description": "🏠 Start Torah Bot"},
                {"command": "wisdom", "description": "🧠 Get AI Torah wisdom"},
                {"command": "quiz", "description": "❓ Take Torah quiz"},
                {"command": "game", "description": "🎮 Play Shabbat Runner"},
                {"command": "help", "description": "❓ Get help"},
                {"command": "language", "description": "🌍 Change language"}
            ]
            
            # Set bot description (shows in profile)
            await self._set_bot_description(bot_description["description"])
            
            # Set bot short description (shows in search)
            await self._set_bot_short_description(short_description["short_description"])
            
            # Set bot commands for auto-complete
            await self._set_bot_commands(bot_commands)
            
            logger.info("✅ Bot configured for app store featuring")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to configure bot for app store: {e}")
            return False
    
    async def _set_bot_description(self, description: str):
        """Set bot description visible in profile"""
        try:
            url = f"{self.telegram_client.base_url}/setMyDescription"
            data = {"description": description}
            
            if not self.telegram_client.session:
                self.telegram_client.session = httpx.AsyncClient(timeout=30.0)
            
            response = await self.telegram_client.session.post(url, data=data)
            result = response.json()
            
            if result.get("ok"):
                logger.info("📝 Bot description set successfully")
            else:
                logger.warning(f"⚠️ Failed to set description: {result}")
                
        except Exception as e:
            logger.error(f"❌ Description setting error: {e}")
    
    async def _set_bot_short_description(self, short_description: str):
        """Set bot short description for search listings"""
        try:
            url = f"{self.telegram_client.base_url}/setMyShortDescription"
            data = {"short_description": short_description}
            
            if not self.telegram_client.session:
                self.telegram_client.session = httpx.AsyncClient(timeout=30.0)
            
            response = await self.telegram_client.session.post(url, data=data)
            result = response.json()
            
            if result.get("ok"):
                logger.info("📄 Bot short description set successfully")
            else:
                logger.warning(f"⚠️ Failed to set short description: {result}")
                
        except Exception as e:
            logger.error(f"❌ Short description setting error: {e}")
    
    async def _set_bot_commands(self, commands: list):
        """Set bot commands for auto-complete menu"""
        try:
            url = f"{self.telegram_client.base_url}/setMyCommands"
            data = {"commands": json.dumps(commands)}
            
            if not self.telegram_client.session:
                self.telegram_client.session = httpx.AsyncClient(timeout=30.0)
            
            response = await self.telegram_client.session.post(url, data=data)
            result = response.json()
            
            if result.get("ok"):
                logger.info(f"⚡ Bot commands set successfully ({len(commands)} commands)")
            else:
                logger.warning(f"⚠️ Failed to set commands: {result}")
                
        except Exception as e:
            logger.error(f"❌ Commands setting error: {e}")
    
    async def enable_inline_mode(self):
        """Enable inline mode for better app integration"""
        try:
            # Note: Inline mode must be enabled via @BotFather
            # This is a placeholder for future inline query handling
            logger.info("📱 Inline mode configuration reminder: enable via @BotFather")
            return True
            
        except Exception as e:
            logger.error(f"❌ Inline mode setup error: {e}")
            return False