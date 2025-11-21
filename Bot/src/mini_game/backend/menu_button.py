# Telegram Menu Button configuration for native WebApp integration
import logging
import json
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

class TelegramMenuButton:
    """Handle native Telegram menu button for WebApp"""
    
    def __init__(self, telegram_client):
        self.telegram_client = telegram_client
        self.menu_button_set = False
    
    async def set_webapp_menu_button(self, chat_id: Optional[int] = None):
        """Set native WebApp menu button for bot"""
        try:
            # Game URL for WebApp - AUTOSCALE DEPLOYMENT with HTTPS validation
            import os
            import time
            # UNIFIED DEPLOYMENT: Bot + Game in same deployment
            deployment_mode = os.environ.get("DEPLOYMENT_MODE", "development")
            if deployment_mode == "production" or os.environ.get("REPLIT_DEPLOYMENT"):
                # Autoscale: Unified deployment for bot + game
                base_url = "https://torah-project-jobjoyclub.replit.app"
            else:
                # Development: Use workspace URL
                repl_domain = os.environ.get("REPLIT_DEV_DOMAIN")
                if repl_domain:
                    base_url = f"https://{repl_domain}"
                else:
                    base_url = "https://torah-project-jobjoyclub.replit.app"
            
            # Use SHORT URL for BotFather compatibility (no query params)
            game_url = base_url
            
            logger.info(f"🎮 Setting menu button for {deployment_mode} mode: {game_url}")
            
            # Test URL accessibility before setting
            try:
                test_response = await self.telegram_client.session.get(game_url, timeout=10.0)
                if test_response.status_code >= 300:
                    logger.warning(f"⚠️  URL returns {test_response.status_code} for {game_url}")
            except Exception as test_e:
                logger.error(f"❌ URL test failed: {test_e}")
            
            menu_button = {
                "type": "web_app",
                "text": "🎮 Shabbat Runner: Kedusha Path",
                "web_app": {
                    "url": game_url
                }
            }
            
            # Prepare API call
            url = f"{self.telegram_client.base_url}/setChatMenuButton"
            data = {"menu_button": json.dumps(menu_button)}
            
            # Add chat_id if specified (for specific user)
            if chat_id:
                data["chat_id"] = str(chat_id)
            
            # Make API call
            if not self.telegram_client.session:
                self.telegram_client.session = httpx.AsyncClient(timeout=30.0)
            
            # Safe logging without token exposure
            safe_url = url.replace(self.telegram_client.base_url.split('bot')[1].split('/')[0], '[REDACTED]')
            logger.info(f"🔍 TELEGRAM API CALL: setChatMenuButton")
            logger.info(f"   Data keys: {list(data.keys())}")
            
            response = await self.telegram_client.session.post(url, data=data)
            result = response.json()
            
            logger.info(f"🔍 TELEGRAM API RESPONSE: Status {response.status_code}, OK: {result.get('ok', False)}")
            
            if result.get("ok"):
                target = f"user {chat_id}" if chat_id else "all users"
                logger.info(f"🎮 Native menu button set for {target}")
                self.menu_button_set = True
                return True
            else:
                logger.error(f"❌ Failed to set menu button: {result}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Menu button setup error: {e}")
            return False
    
    async def remove_menu_button(self, chat_id: Optional[int] = None):
        """Remove WebApp menu button and restore default"""
        try:
            menu_button = {"type": "default"}
            
            url = f"{self.telegram_client.base_url}/setChatMenuButton"
            data = {"menu_button": json.dumps(menu_button)}
            
            if chat_id:
                data["chat_id"] = str(chat_id)
            
            if not self.telegram_client.session:
                self.telegram_client.session = httpx.AsyncClient(timeout=30.0)
            
            response = await self.telegram_client.session.post(url, data=data)
            result = response.json()
            
            if result.get("ok"):
                target = f"user {chat_id}" if chat_id else "all users"
                logger.info(f"🔧 Menu button restored to default for {target}")
                return True
            else:
                logger.error(f"❌ Failed to restore menu button: {result}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Menu button removal error: {e}")
            return False