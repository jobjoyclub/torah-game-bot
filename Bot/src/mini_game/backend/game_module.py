# Mini Game integration module for Torah Bot
import logging
from typing import Dict, Any, Optional, List
import json
import asyncio

logger = logging.getLogger(__name__)

class MiniGameModule:
    """Safe integration of Shabbat Runner mini game with Torah Bot"""
    
    def __init__(self, telegram_client, session_manager, analytics=None):
        self.telegram_client = telegram_client
        self.session_manager = session_manager
        self.analytics = analytics
        
        # Game analytics storage
        self.game_scores = {}  # user_id -> [scores]
        self.game_stats = {
            "total_games": 0,
            "total_players": set(),
            "average_score": 0,
            "best_score": 0,
            "today_games": 0
        }
        
        # Native menu button setup
        self._menu_button_users = set()  # Track users with menu button
    
    async def handle_game_command(self, chat_id: int, user_id: int, user_data: Optional[Dict] = None):
        """Handle request to start mini game"""
        try:
            # Get user language for localized messages
            session = self.session_manager.get_session(user_id, user_data)
            language = session.get("language", "English")
            
            # Localized game messages
            game_messages = {
                "English": {
                    "title": "🎮 Shabbat Runner: Kedusha Path",
                    "description": "🕯️ Collect Shabbat items and avoid forbidden objects!\n\n🎯 <b>How to play:</b>\n• TAP to collect items\n• Don't tap to avoid forbidden objects\n• 45 seconds to get the highest score!\n\n🏆 Ready for the challenge?",
                    "button": "🚀 Play Game"
                },
                "Russian": {
                    "title": "🎮 Shabbat Runner: Путь Кдуши",
                    "description": "🕯️ Нет ничего прекраснее, чем изучать святость Шаббата через игру, дорогой мой!\n\n✨ <b>Мудрость игры проста:</b>\n• Прикасайся к святым предметам - они приносят благословение\n• Оберегайся от запрещённого - это путь к мудрости\n• 45 секунд, чтобы собрать искры кдуши!\n\n🌟 Помни: каждое правильное действие добавляет света в мир. Готов познать радость Шаббата?",
                    "button": "🕯️ Игра Shabbat Runner"
                },
                "Hebrew": {
                    "title": "🎮 Shabbat Runner: נתיב הקדושה",
                    "description": "🕯️ אספו חפצי שבת והימנעו מפריטים אסורים!\n\n🎯 <b>איך לשחק:</b>\n• הקישו כדי לאסוף פריטים\n• אל תקישו כדי להימנע מאסורים\n• 45 שניות להשיג הציון הגבוה ביותר!\n\n🏆 מוכנים לאתגר?",
                    "button": "🚀 שחק"
                }
            }
            
            message_data = game_messages.get(language, game_messages["English"])
            
            # Set native menu button globally AND for this user (critical fix)
            await self._setup_native_menu_button(None)  # Global setting
            await self._setup_native_menu_button(user_id)  # User-specific
            
            # Create game URL with user parameters  
            # Autoscale deployment URL - FIXED
            import os
            # AUTOSCALE MODE: Use same deployment for bot + game
            deployment_mode = os.environ.get("DEPLOYMENT_MODE", "development")
            if deployment_mode == "production" or os.environ.get("REPLIT_DEPLOYMENT"):
                # Autoscale: Use same deployment URL for bot + game
                base_url = "https://torah-project-jobjoyclub.replit.app"
            else:
                # Development: Use workspace URL
                repl_domain = os.environ.get("REPLIT_DEV_DOMAIN")
                if repl_domain:
                    base_url = f"https://{repl_domain}"
                else:
                    base_url = "https://torah-project-jobjoyclub.replit.app"
            # Pre-warm the Autoscale deployment with health check
            import time
            import asyncio
            import httpx
            
            try:
                # Wake up the game server proactively
                async with httpx.AsyncClient(timeout=3.0) as client:
                    await client.get(f"{base_url}/health")
                logger.info("🔥 Game server pre-warmed successfully")
            except Exception as e:
                logger.warning(f"⚠️ Pre-warming failed (normal on cold start): {e}")
            
            # AGGRESSIVE cache-busting to force Telegram refresh after deployment
            cache_version = int(time.time())  # Changes every second - FORCES refresh
            deployment_version = "v2_sept1"  # Manual version bump after changes
            
            # Extract username from user_data for analytics
            username = user_data.get("username", "unknown") if user_data else "unknown"
            
            # CRITICAL FIX: Add username to URL for proper game analytics
            game_url = f"{base_url}/game?v={cache_version}&deploy={deployment_version}&user_id={user_id}&username={username}&lang={language.lower()}"
            
            # Create inline keyboard with Web App button
            keyboard = {
                "inline_keyboard": [
                    [
                        {
                            "text": message_data["button"],
                            "web_app": {"url": game_url}
                        }
                    ],
                    [
                        {
                            "text": "🔙 Back to Menu" if language == "English" else "🔙 Назад в меню" if language == "Russian" else "🔙 חזור לתפריט",
                            "callback_data": "main_menu"
                        }
                    ]
                ]
            }
            
            # Send game invitation with rabbi photo from web URL
            try:
                photo_url = f"{base_url}/game_rabbi_with_torah.png"
                await self.telegram_client.send_photo(
                    chat_id,
                    photo_url,
                    caption=f"<b>{message_data['title']}</b>\n\n{message_data['description']}",
                    reply_markup=keyboard
                )
                logger.info(f"📸 Game invitation with web photo sent to user {user_id}")
            except Exception as photo_error:
                logger.warning(f"⚠️ Web photo failed, sending text only: {photo_error}")
                # Fallback to text-only message
                await self.telegram_client.send_message(
                    chat_id,
                    f"<b>{message_data['title']}</b>\n\n{message_data['description']}",
                    reply_markup=keyboard
                )
            
            # Analytics tracking
            if self.analytics:
                self.analytics.smart_logger.business_log(
                    "GAME_INVITE_SENT",
                    user_id,
                    username=user_data.get("username", "unknown") if user_data else "unknown",
                    language=language
                )
                
            logger.info(f"🎮 Game invitation sent to user {user_id} in {language}")
            
        except Exception as e:
            logger.error(f"❌ Failed to handle game command for user {user_id}: {e}")
            # Fallback message
            await self.telegram_client.send_message(
                chat_id,
                "🎮 Game temporarily unavailable. Please try again later!"
            )
    
    async def handle_game_stats(self, chat_id: int, user_id: int, user_data: Optional[Dict] = None):
        """Show user's game statistics"""
        session = self.session_manager.get_session(user_id, user_data)
        language = session.get("language", "English")
        
        user_scores = self.game_scores.get(user_id, [])
        
        if not user_scores:
            no_games_messages = {
                "English": "🎮 You haven't played Shabbat Runner yet!\n\nStart your first game to see your stats here.",
                "Russian": "🎮 Вы ещё не играли в Shabbat Runner!\n\nСыграйте первую игру, чтобы увидеть статистику.",
                "Hebrew": "🎮 עדיין לא שיחקת ב-Shabbat Runner!\n\nהתחל את המשחק הראשון כדי לראות את הסטטיסטיקה."
            }
            message = no_games_messages.get(language, no_games_messages["English"])
        else:
            best_score = max(user_scores)
            avg_score = sum(user_scores) / len(user_scores)
            total_games = len(user_scores)
            
            stats_messages = {
                "English": f"🏆 <b>Your Shabbat Runner Stats</b>\n\n🎯 Best Score: <b>{best_score}</b>\n📊 Average: <b>{avg_score:.1f}</b>\n🎮 Games Played: <b>{total_games}</b>\n\n🌟 Keep collecting those Shabbat items!",
                "Russian": f"🏆 <b>Ваша статистика Shabbat Runner</b>\n\n🎯 Лучший результат: <b>{best_score}</b>\n📊 Средний: <b>{avg_score:.1f}</b>\n🎮 Игр сыграно: <b>{total_games}</b>\n\n🌟 Продолжайте собирать предметы Шаббата!",
                "Hebrew": f"🏆 <b>הסטטיסטיקה שלך ב-Shabbat Runner</b>\n\n🎯 הציון הטוב ביותר: <b>{best_score}</b>\n📊 ממוצע: <b>{avg_score:.1f}</b>\n🎮 משחקים ששוחקו: <b>{total_games}</b>\n\n🌟 תמשיכו לאסוף פריטי שבת!"
            }
            message = stats_messages.get(language, stats_messages["English"])
        
        keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": "🎮 Play Game" if language == "English" else "🎮 Играть" if language == "Russian" else "🎮 שחק",
                        "callback_data": "mini_game"
                    }
                ],
                [
                    {
                        "text": "🔙 Back to Menu" if language == "English" else "🔙 Назад в меню" if language == "Russian" else "🔙 חזור לתפריט",
                        "callback_data": "main_menu"
                    }
                ]
            ]
        }
        
        await self.telegram_client.send_message(chat_id, message, reply_markup=keyboard)
    
    def record_game_score(self, user_id: int, score: int, user_data: Optional[Dict] = None):
        """Record game score for analytics (called from web app)"""
        try:
            if user_id not in self.game_scores:
                self.game_scores[user_id] = []
            
            self.game_scores[user_id].append(score)
            
            # Update global stats
            self.game_stats["total_games"] += 1
            self.game_stats["total_players"].add(user_id)
            self.game_stats["today_games"] += 1
            
            if score > self.game_stats["best_score"]:
                self.game_stats["best_score"] = score
            
            # Recalculate average
            all_scores = []
            for scores in self.game_scores.values():
                all_scores.extend(scores)
            if all_scores:
                self.game_stats["average_score"] = sum(all_scores) / len(all_scores)
            
            # Enhanced business analytics with detailed game data
            if self.analytics:
                # Use new game_session_event method for detailed logging
                self.analytics.smart_logger.game_session_event(
                    "GAME_COMPLETED",
                    user_id,
                    username=user_data.get("username", "unknown") if user_data else "unknown",
                    language=user_data.get("language", "unknown") if user_data else "unknown",
                    score=score,
                    duration=45.0,  # Standard game duration
                    items_collected=max(0, score // 2),  # Estimate items from score
                    mistakes=max(0, 3 - (score // 5)),  # Estimate mistakes
                    after_tutorial=False  # Backend doesn't know tutorial status
                )
                
                # Also log for backward compatibility
                self.analytics.smart_logger.business_log(
                    "GAME_SCORE_RECORDED",
                    user_id,
                    username=user_data.get("username", "unknown") if user_data else "unknown",
                    score=score,
                    best_score=max(self.game_scores[user_id]),
                    games_played=len(self.game_scores[user_id])
                )
            
            logger.info(f"🎮 Game score recorded: user {user_id} scored {score}")
            
            # Check for achievement rewards
            self.check_achievements(user_id, score)
            
        except Exception as e:
            logger.error(f"❌ Failed to record game score: {e}")
    
    def check_achievements(self, user_id: int, score: int):
        """Check if user earned any achievement rewards with enhanced analytics"""
        user_scores = self.game_scores.get(user_id, [])
        
        # Achievement triggers with smart analytics
        if score >= 20:
            # High score achievement
            logger.info(f"🏆 User {user_id} achieved high score: {score}")
            
            # Send achievement analytics
            if self.analytics:
                self.analytics.smart_logger.game_achievement_event(
                    "high_score",
                    user_id,
                    username="unknown",  # Will be filled from session data
                    language="unknown",
                    score=score
                )
        
        if score >= 25:
            # Shabbat master achievement
            logger.info(f"🌟 User {user_id} achieved Shabbat Master status: {score}")
            
            if self.analytics:
                self.analytics.smart_logger.game_achievement_event(
                    "shabbat_master", 
                    user_id,
                    username="unknown",
                    language="unknown",
                    score=score
                )
        
        if len(user_scores) >= 5:
            # Frequent player achievement  
            logger.info(f"🎯 User {user_id} is a frequent player: {len(user_scores)} games")
            
            if self.analytics:
                self.analytics.smart_logger.game_achievement_event(
                    "frequent_player",
                    user_id,
                    username="unknown",
                    language="unknown",
                    games_played=len(user_scores)
                )
        
        # Personal best
        if score == max(user_scores):
            logger.info(f"🏆 User {user_id} set new personal best: {score}")
            
            if self.analytics:
                self.analytics.smart_logger.game_achievement_event(
                    "personal_best",
                    user_id,
                    username="unknown",
                    language="unknown",
                    score=score,
                    previous_best=max(user_scores[:-1]) if len(user_scores) > 1 else 0
                )
    
    def get_game_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get top players leaderboard"""
        leaderboard = []
        
        for user_id, scores in self.game_scores.items():
            best_score = max(scores)
            total_games = len(scores)
            avg_score = sum(scores) / len(scores)
            
            leaderboard.append({
                "user_id": user_id,
                "best_score": best_score,
                "total_games": total_games,
                "avg_score": avg_score
            })
        
        # Sort by best score
        leaderboard.sort(key=lambda x: x["best_score"], reverse=True)
        return leaderboard[:limit]
    
    async def _setup_native_menu_button(self, user_id: Optional[int]):
        """Set up native Telegram menu button for user (one-time)"""
        try:
            # Skip if already set for this user
            if user_id in self._menu_button_users:
                return
            
            # Game URL for WebApp - ALWAYS use production autoscale domain for Telegram
            import os
            
            # For Menu Button, always use the production autoscale domain
            # because Telegram needs external access, not development domain
            base_url = "https://torah-project-jobjoyclub.replit.app"
            
            # Use SHORT URL for BotFather menu button
            game_url = base_url
            
            menu_button = {
                "type": "web_app",
                "text": "🎮 Shabbat Game",
                "web_app": {
                    "url": game_url
                }
            }
            
            # Use bot's _make_request method for consistency  
            data: Dict[str, Any] = {"menu_button": menu_button}
            
            # Add chat_id only if specified (for user-specific button)
            if user_id is not None:
                data["chat_id"] = user_id
                
            # Use the telegram client's _make_request for consistency
            if hasattr(self.telegram_client, '_make_request'):
                result = await self.telegram_client._make_request("setChatMenuButton", data)
                
                if result.get("ok"):
                    logger.info(f"🎮 Native menu button set for user {user_id}")
                    # Only add to set if user_id is not None
                    if user_id is not None:
                        self._menu_button_users.add(user_id)
                    return True
                else:
                    logger.warning(f"⚠️ Menu button setup failed for user {user_id}: {result}")
                    return False
            else:
                logger.warning("⚠️ Telegram client _make_request not available")
                return False
            
        except Exception as e:
            logger.error(f"❌ Native menu button setup error: {e}")
            return False