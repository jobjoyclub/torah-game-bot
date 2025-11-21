#!/usr/bin/env python3
"""
Torah Bot v5.0.0 - PRODUCTION DEPLOYMENT VERSION
Complete modular architecture with optimized performance and error handling
Entry point: simple_bot.py for Replit deployment compatibility
"""

import asyncio
import httpx
import json
import logging
import os
import sys
import time
import random
from typing import Dict, Any, Optional
from datetime import datetime

# Import unified user context
from src.core.user_context import UserContext, UnifiedLogFormatter
try:
    from .prompt_loader import PromptLoader
except ImportError:
    # For workflow mode - absolute import
    from torah_bot.prompt_loader import PromptLoader
try:
    from .quiz_topics import QuizTopicGenerator
except ImportError:
    from torah_bot.quiz_topics import QuizTopicGenerator

# Import deployment safety guard
try:
    from ..config.deployment_config import safe_startup_check, DeploymentGuard
    DEPLOYMENT_GUARD_AVAILABLE = True
except ImportError:
    DEPLOYMENT_GUARD_AVAILABLE = False
    # Logger will be defined later

# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Log deployment guard status after logger is initialized
if not DEPLOYMENT_GUARD_AVAILABLE:
    logger.warning("Deployment guard not available - running in development mode")

# Configuration - SAFE .env loading
from dotenv import load_dotenv
# SECURITY: Only load .env in development, never override production secrets
is_production = (
    os.environ.get('REPLIT_DEPLOYMENT') == "1" or 
    os.environ.get('FORCE_PRODUCTION_MODE', '').lower() == 'true' or
    'replit.app' in os.environ.get('REPLIT_DOMAINS', '')
)
if not is_production:
    load_dotenv()  # No override in development
    logger.info("🛠️ Development environment: .env file loaded")
else:
    logger.info("🔒 Production environment: using Replit Secrets only")

TOKEN = os.environ.get("BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения!")
    sys.exit(1)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
PORT = int(os.environ.get("PORT", 80))

# Torah Logs Chat ID (from environment)
TORAH_LOGS_CHAT_ID = int(os.environ.get("TORAH_LOGS_CHAT_ID", "-1003025527880"))

# Initialize OpenAI with error handling
try:
    openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
    if openai_client:
        logger.info("OpenAI client initialized successfully")
    else:
        logger.warning("OpenAI API key not found - using fallback responses")
except Exception as e:
    logger.error(f"OpenAI initialization failed: {e}")
    openai_client = None

# Initialize Newsletter System
newsletter_manager = None
AdminCommands = None
try:
    # Fix relative import issues by using absolute imports
    import sys
    import os
    
    # Add project root to Python path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Import with absolute paths
    from src.torah_bot.newsletter_manager import newsletter_manager
    from src.torah_bot.admin_commands import AdminCommands
    from src.newsletter_api import InternalNewsletterAPIClient
    
    NEWSLETTER_AVAILABLE = True
    logger.info("Newsletter system initialized")
except ImportError as e:
    logger.warning(f"Newsletter system not available: {e}")
    NEWSLETTER_AVAILABLE = False
    newsletter_manager = None
    AdminCommands = None

# Global session storage
user_sessions = {}
last_cleanup = time.time()

# Global bot instance for newsletter API access
bot_instance = None

class SmartLogger:
    """Advanced multi-level logging system for Torah Bot with Telegram integration"""
    
    def __init__(self, telegram_client=None):
        self.daily_stats = {
            "users": set(),
            "wisdom_requests": 0,
            "quizzes": 0,
            "donations": 0,
            "shares": 0,
            "languages": {},
            "ai_responses": {"success": 0, "failures": 0},
            "response_times": [],
            "user_requests": [],
            # New gaming metrics
            "game_stats": {
                "total_games": 0,
                "total_tutorials": 0,
                "tutorial_completions": 0,
                "game_sessions": [],
                "achievements": 0,
                "total_score": 0,
                "tutorial_users": set(),
                "game_users": set()
            }
        }
        self.session_contexts = {}
        self.user_completion_timers = {}  # Track when users finish sessions
        self.quality_thresholds = {
            "ai_failure_rate": 0.1,  # 10%
            "avg_response_time": 15.0  # seconds
        }
        self.telegram_client = telegram_client
        self.logs_chat_id = TORAH_LOGS_CHAT_ID
    
    async def send_log_to_chat(self, message: str):
        """Send log message to Torah Logs chat"""
        if self.telegram_client and self.logs_chat_id:
            try:
                await self.telegram_client.send_message(
                    self.logs_chat_id,
                    f"🤖 <b>Torah Bot Logs</b>\n\n{message}",
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Failed to send log to chat: {e}")
    
    def business_log(self, event: str, user_id: int, **context):
        """Log business-critical events with full context"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        username = context.get("username", "unknown")
        language = context.get("language", "unknown")
        
        log_message = f"📈 BUSINESS [{timestamp}] {event} | User: {user_id}(@{username}) | Lang: {language}"
        logger.info(log_message)
        
        # Track completion events and schedule detailed user reports
        if event.startswith("SESSION_COMPLETE_"):
            self.schedule_user_report(user_id, delay_minutes=1)
        
        # Track daily stats
        self.daily_stats["users"].add(user_id)
        if "language" in context:
            lang = context["language"]
            self.daily_stats["languages"][lang] = self.daily_stats["languages"].get(lang, 0) + 1
    
    def user_journey(self, user_id: int, action: str, request_text: Optional[str] = None, **context):
        """Track personalized user journey with actual requests"""
        if user_id not in self.session_contexts:
            self.session_contexts[user_id] = {
                "actions": [],
                "requests": [],
                "start_time": time.time(),
                "username": context.get("username", "unknown"),
                "language": context.get("language", "unknown")
            }
        
        # Log the action
        self.session_contexts[user_id]["actions"].append({
            "action": action,
            "timestamp": time.time(),
            "context": context
        })
        
        # Log user request text if provided
        if request_text:
            self.session_contexts[user_id]["requests"].append({
                "text": request_text[:100],  # First 100 chars
                "action": action,
                "timestamp": time.time()
            })
            self.daily_stats["user_requests"].append({
                "user_id": user_id,
                "text": request_text[:50],
                "action": action,
                "language": context.get("language", "unknown")
            })
        
        # Log journey update
        ctx = self.session_contexts[user_id]
        actions_summary = " → ".join([a["action"] for a in ctx["actions"][-5:]])  # Last 5 actions
        
        if request_text:
            journey_log = f"👤 USER_JOURNEY: @{ctx['username']} ({ctx['language']}) → {actions_summary}"
            request_log = f"💬 USER_REQUEST: \"{request_text[:80]}...\" → {action}"
            
            logger.info(journey_log)
            logger.info(request_log)
            
            # Store user request for detailed report later (no immediate sending)
        else:
            journey_log = f"👤 USER_JOURNEY: @{ctx['username']} ({ctx['language']}) → {actions_summary}"
            logger.info(journey_log)
    
    def ai_performance(self, operation: str, success: bool, duration: float, **details):
        """Track AI performance with quality monitoring"""
        status = "✅" if success else "❌"
        
        if success:
            self.daily_stats["ai_responses"]["success"] += 1
        else:
            self.daily_stats["ai_responses"]["failures"] += 1
        
        self.daily_stats["response_times"].append(duration)
        
        # Log AI performance
        perf_log = f"💡 AI_PERFORMANCE: {operation} {status} in {duration:.1f}s"
        logger.info(perf_log)
        
        # Only send critical AI failures to chat immediately
        if not success:
            asyncio.create_task(self.send_log_to_chat(f"🚨 CRITICAL: {perf_log}"))
        
        # Quality alerts
        self._check_quality_alerts()
    
    def system_health(self, component: str, status: str, **details):
        """Log system health events"""
        logger.info(f"🔧 SYSTEM: {component} → {status}")
        if details:
            details_str = ", ".join([f"{k}={v}" for k, v in details.items()])
            logger.info(f"🔧 SYSTEM_DETAILS: {details_str}")
    
    def business_metrics_summary(self):
        """Generate daily business metrics summary"""
        total_users = len(self.daily_stats["users"])
        total_responses = self.daily_stats["ai_responses"]["success"] + self.daily_stats["ai_responses"]["failures"]
        
        if total_responses > 0:
            ai_success_rate = (self.daily_stats["ai_responses"]["success"] / total_responses) * 100
        else:
            ai_success_rate = 0
        
        if self.daily_stats["response_times"]:
            avg_response_time = sum(self.daily_stats["response_times"]) / len(self.daily_stats["response_times"])
        else:
            avg_response_time = 0
        
        # Language distribution
        lang_summary = ", ".join([f"{lang}({count})" for lang, count in sorted(self.daily_stats["languages"].items(), key=lambda x: x[1], reverse=True)[:3]])
        
        # Gaming metrics calculations
        game_stats = self.daily_stats["game_stats"]
        total_game_users = len(game_stats["game_users"])
        total_tutorial_users = len(game_stats["tutorial_users"])
        
        # Calculate game metrics
        avg_game_score = 0
        best_game_score = 0
        tutorial_conversion = 0
        game_completion_rate = 0
        
        if game_stats["total_games"] > 0:
            avg_game_score = game_stats["total_score"] / game_stats["total_games"]
            
        if game_stats["game_sessions"]:
            scores = [session["score"] for session in game_stats["game_sessions"]]
            best_game_score = max(scores) if scores else 0
            
        if game_stats["total_tutorials"] > 0:
            tutorial_conversion = (game_stats["tutorial_completions"] / game_stats["total_tutorials"]) * 100
            
        # Build comprehensive summary with gaming metrics
        summary_lines = [
            f"📊 DAILY_METRICS: {total_users} users, {self.daily_stats['wisdom_requests']} wisdom, {self.daily_stats['quizzes']} quizzes, {self.daily_stats['donations']} donations",
            f"🎮 GAME_METRICS: {game_stats['total_games']} games played, {game_stats['total_tutorials']} new tutorials, avg score: {avg_game_score:.1f}, best: {best_game_score}",
            f"🎯 PERFORMANCE: AI success {ai_success_rate:.1f}%, Avg time {avg_response_time:.1f}s, Tutorial completion: {tutorial_conversion:.0f}%",
            f"🌐 LANGUAGES: {lang_summary}"
        ]
        
        # Log to console
        for line in summary_lines:
            logger.info(line)
        
        # Recent user requests summary
        requests_summary = []
        if self.daily_stats["user_requests"]:
            recent_requests = self.daily_stats["user_requests"][-5:]  # Last 5 requests
            logger.info(f"💬 RECENT_REQUESTS:")
            requests_summary.append("💬 RECENT_REQUESTS:")
            for req in recent_requests:
                req_line = f"   → @user{req['user_id']} ({req['language']}): \"{req['text']}\" → {req['action']}"
                logger.info(req_line)
                requests_summary.append(req_line)
        
        # Game highlights for reports
        game_highlights = []
        if game_stats["game_sessions"]:
            # Best score today
            today_sessions = [s for s in game_stats["game_sessions"] if time.time() - s["timestamp"] < 86400]
            if today_sessions:
                best_today = max(today_sessions, key=lambda x: x["score"])
                if best_today["score"] > 20:  # Highlight high scores
                    game_highlights.append(f"   → @user{best_today['user_id']} scored {best_today['score']} (new daily record!)")
                
        if game_stats["tutorial_completions"] > 0:
            game_highlights.append(f"   → {game_stats['tutorial_completions']} first-time tutorial completions today")
            if game_stats["total_tutorials"] > 0:
                conversion = (game_stats["tutorial_completions"] / game_stats["total_tutorials"]) * 100
                game_highlights.append(f"   → {conversion:.0f}% tutorial → game conversion rate")
        
        # Add game highlights to summary if present
        if game_highlights:
            game_highlights_section = ["", "🎮 GAME_HIGHLIGHTS:"] + game_highlights
        else:
            game_highlights_section = []
        
        # Send comprehensive HOURLY summary to Telegram chat 
        if total_users > 0 or self.daily_stats['wisdom_requests'] > 0 or self.daily_stats['quizzes'] > 0 or game_stats['total_games'] > 0:
            full_summary = "\n".join(summary_lines + requests_summary + game_highlights_section)
            timestamp = datetime.now().strftime("%H:%M")
            asyncio.create_task(self.send_log_to_chat(f"📊 <b>DAILY REPORT [{timestamp}]</b>\n\n{full_summary}"))
    
    # ========== NEW GAMING ANALYTICS METHODS ==========
    
    def tutorial_event(self, event_type: str, user_id: int, duration: Optional[float] = None, **context):
        """Log tutorial events with unified format"""
        # Create UserContext from parameters
        user_context = UserContext(
            user_id=user_id,
            username=context.get("username"),
            language=context.get("language")
        )
        
        # Update daily stats
        self.daily_stats["users"].add(user_id)
        if event_type == "TUTORIAL_STARTED":
            self.daily_stats["game_stats"]["total_tutorials"] += 1
            self.daily_stats["game_stats"]["tutorial_users"].add(user_id)
        elif event_type == "TUTORIAL_COMPLETED":
            self.daily_stats["game_stats"]["tutorial_completions"] += 1
        
        if "language" in context:
            lang = context["language"]
            self.daily_stats["languages"][lang] = self.daily_stats["languages"].get(lang, 0) + 1
        
        # UNIFIED FORMAT LOGS TO TORAHLOGS
        if event_type == "TUTORIAL_COMPLETED":
            log_message = UnifiedLogFormatter.format_log(
                "TUTORIAL_COMPLETED",
                user_context,
                emoji="📚",
                duration=duration or 0,
                first_time=context.get("first_time", False)
            )
            asyncio.create_task(self.send_log_to_chat(log_message))
            
        # CRITICAL FIX: Add to USER INTERACTION REPORT via enhanced_user_journey
        tutorial_game_data = {
            "tutorial_completed": event_type == "TUTORIAL_COMPLETED",
            "tutorial_duration": duration
        }
        self.enhanced_user_journey(user_id, event_type.lower(), tutorial_game_data, **context)
    
    def game_session_event(self, event_type: str, user_id: int, **context):
        """Log game session events with unified format"""
        # Create UserContext from parameters
        user_context = UserContext(
            user_id=user_id,
            username=context.get("username"),
            language=context.get("language")
        )
        
        # Update daily stats
        self.daily_stats["users"].add(user_id)
        if event_type == "GAME_STARTED":
            self.daily_stats["game_stats"]["game_users"].add(user_id)
        elif event_type == "GAME_COMPLETED":
            self.daily_stats["game_stats"]["total_games"] += 1
            if context.get("score"):
                self.daily_stats["game_stats"]["total_score"] += context["score"]
                
                # Store detailed session data
                session_data = {
                    "user_id": user_id,
                    "score": context["score"],
                    "duration": context.get("duration", 0),
                    "items": context.get("items_collected", 0),
                    "mistakes": context.get("mistakes", 0),
                    "timestamp": time.time()
                }
                self.daily_stats["game_stats"]["game_sessions"].append(session_data)
        
        if "language" in context:
            lang = context["language"]
            self.daily_stats["languages"][lang] = self.daily_stats["languages"].get(lang, 0) + 1
        
        # UNIFIED FORMAT LOGS TO TORAHLOGS
        if event_type == "GAME_COMPLETED":
            log_message = UnifiedLogFormatter.format_log(
                "GAME_COMPLETED",
                user_context,
                emoji="🎮",
                score=context.get("score", 0),
                duration=context.get("duration", 0),
                items_collected=context.get("items_collected", 0),
                mistakes=context.get("mistakes", 0),
                after_tutorial=context.get("after_tutorial", False)
            )
            asyncio.create_task(self.send_log_to_chat(log_message))
            
        elif event_type == "GAME_STARTED":
            log_message = UnifiedLogFormatter.format_log(
                "GAME_STARTED",
                user_context,
                emoji="🎮"
            )
            asyncio.create_task(self.send_log_to_chat(log_message))
            
        # CRITICAL FIX: Add to USER INTERACTION REPORT via enhanced_user_journey
        game_session_data = {
            "score": context.get("score"),
            "duration": context.get("duration"), 
            "items_collected": context.get("items_collected"),
            "mistakes": context.get("mistakes"),
            "after_tutorial": context.get("after_tutorial", False)
        }
        self.enhanced_user_journey(user_id, event_type.lower(), game_session_data, **context)
    
    def game_achievement_event(self, achievement_type: str, user_id: int, **context):
        """Log game achievements and milestones"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        username = context.get("username", "unknown")
        language = context.get("language", "unknown")
        
        # Build achievement details
        details = []
        if context.get("score") is not None:
            details.append(f"score: {context['score']}")
        if context.get("games_played") is not None:
            details.append(f"games_played: {context['games_played']}")
        
        details_str = f" | {' | '.join(details)}" if details else ""
        
        # Log achievement business event
        log_message = f"📈 BUSINESS [{timestamp}] GAME_ACHIEVEMENT | User: {user_id}(@{username}) | Lang: {language} | type: {achievement_type}{details_str}"
        logger.info(log_message)
        
        # Log achievement highlight for logs chat
        achievement_message = f"🏆 ACHIEVEMENT_UNLOCKED: @{username} {achievement_type}"
        if context.get("score"):
            achievement_message += f" (score: {context['score']})"
        
        # Send achievement to logs chat immediately
        asyncio.create_task(self.send_log_to_chat(achievement_message))
        
        # Update daily stats
        self.daily_stats["users"].add(user_id)
        self.daily_stats["game_stats"]["achievements"] += 1
        
        if "language" in context:
            lang = context["language"]
            self.daily_stats["languages"][lang] = self.daily_stats["languages"].get(lang, 0) + 1
            
        # CRITICAL FIX: Add to USER INTERACTION REPORT via enhanced_user_journey  
        achievement_game_data = {
            "achievement_type": achievement_type,
            "score": context.get("score"),
            "games_played": context.get("games_played")
        }
        self.enhanced_user_journey(user_id, f"achievement_{achievement_type}", achievement_game_data, **context)
    
    def enhanced_user_journey(self, user_id: int, action: str, game_data: Optional[Dict] = None, **context):
        """Enhanced user journey tracking with game data"""
        # Call original user_journey method
        self.user_journey(user_id, action, context.get("request_text"), **context)
        
        # Add game-specific journey tracking
        if game_data and user_id in self.session_contexts:
            game_summary = []
            if game_data.get("tutorial_completed"):
                game_summary.append(f"tutorial({game_data.get('tutorial_duration', 0):.0f}s)")
            if game_data.get("score") is not None:
                game_summary.append(f"game({game_data['score']}pts, {game_data.get('duration', 0):.0f}s)")
                if game_data.get("items_collected"):
                    game_summary.append(f"{game_data['items_collected']}items")
                if game_data.get("mistakes"):
                    game_summary.append(f"{game_data['mistakes']}mistakes")
            
            if game_summary:
                ctx = self.session_contexts[user_id]
                game_log = f"🎮 GAME_SESSION: @{ctx['username']} {' → '.join(game_summary)}"
                logger.info(game_log)
                
                # CRITICAL FIX: Add game action to session_contexts for USER INTERACTION REPORT
                game_action = f"mini_game_session ({' → '.join(game_summary)})"
                self.session_contexts[user_id]["actions"].append({
                    "action": game_action,
                    "timestamp": time.time(),
                    "context": {**context, "game_data": game_data}
                })
                
                # Add game summary as a request if tutorial/game completed
                if game_data.get("tutorial_completed") or game_data.get("score") is not None:
                    game_request_text = f"Shabbat Path Mini-Game: {' → '.join(game_summary)}"
                    self.session_contexts[user_id]["requests"].append({
                        "text": game_request_text,
                        "action": game_action,
                        "timestamp": time.time()
                    })
    
    def _check_quality_alerts(self):
        """Check quality thresholds and generate alerts"""
        total_responses = self.daily_stats["ai_responses"]["success"] + self.daily_stats["ai_responses"]["failures"]
        
        if total_responses >= 10:  # Only check after enough samples
            failure_rate = self.daily_stats["ai_responses"]["failures"] / total_responses
            
            if failure_rate > self.quality_thresholds["ai_failure_rate"]:
                alert_msg = f"🚨 HIGH: AI failure rate {failure_rate*100:.1f}% exceeds threshold"
                logger.warning(alert_msg)
                asyncio.create_task(self.send_log_to_chat(f"🚨 QUALITY ALERT: {alert_msg}"))
    
    def schedule_user_report(self, user_id: int, delay_minutes: int = 1):
        """Schedule detailed user report to be sent after delay"""
        async def delayed_user_report():
            await asyncio.sleep(delay_minutes * 60)  # Convert to seconds
            await self.send_detailed_user_report(user_id)
        
        # Cancel existing timer if any
        if user_id in self.user_completion_timers:
            self.user_completion_timers[user_id].cancel()
        
        # Schedule new report
        self.user_completion_timers[user_id] = asyncio.create_task(delayed_user_report())
    
    async def send_detailed_user_report(self, user_id: int):
        """Send comprehensive user interaction report"""
        if user_id not in self.session_contexts:
            return
        
        ctx = self.session_contexts[user_id]
        session_duration = time.time() - ctx["start_time"]
        
        # Build comprehensive user report
        report_lines = [
            f"👤 <b>USER INTERACTION REPORT</b>",
            f"🆔 User: {user_id} (@{ctx['username']})",
            f"🌐 Language: {ctx['language']}",
            f"⏱️ Session Duration: {session_duration/60:.1f} minutes",
            f"🔄 Total Actions: {len(ctx['actions'])}",
            ""
        ]
        
        # Recent actions timeline
        if ctx['actions']:
            report_lines.append("📋 <b>ACTION TIMELINE:</b>")
            for action in ctx['actions'][-8:]:  # Last 8 actions
                action_time = datetime.fromtimestamp(action['timestamp']).strftime("%H:%M:%S")
                report_lines.append(f"   {action_time} → {action['action']}")
            report_lines.append("")
        
        # User requests history
        if ctx['requests']:
            report_lines.append("💬 <b>USER REQUESTS:</b>")
            for req in ctx['requests'][-5:]:  # Last 5 requests
                req_time = datetime.fromtimestamp(req['timestamp']).strftime("%H:%M:%S")
                report_lines.append(f"   {req_time}: \"{req['text'][:80]}...\"")
                report_lines.append(f"   └─ Action: {req['action']}")
        
        full_report = "\n".join(report_lines)
        await self.send_log_to_chat(full_report)
        
        # Clean up the session context after reporting
        if user_id in self.user_completion_timers:
            del self.user_completion_timers[user_id]

        if len(self.daily_stats["response_times"]) >= 5:
            avg_time = sum(self.daily_stats["response_times"][-10:]) / min(10, len(self.daily_stats["response_times"]))
            
            if avg_time > self.quality_thresholds["avg_response_time"]:
                alert_msg = f"⚠️ MEDIUM: Average response time {avg_time:.1f}s exceeds threshold"
                logger.warning(alert_msg)
                asyncio.create_task(self.send_log_to_chat(f"🚨 QUALITY ALERT: {alert_msg}"))
    
    def track_conversion(self, user_id: int, from_action: str, to_action: str):
        """Track conversion between actions"""
        logger.info(f"🔄 CONVERSION: User {user_id} {from_action} → {to_action}")

class OptimizedAnalytics:
    """Enhanced analytics with smart logging integration"""
    
    def __init__(self, telegram_client=None):
        self.active_sessions = {}
        self.session_timeouts = {}
        self.smart_logger = SmartLogger(telegram_client)
    
    def start_session(self, user_id: int, session_type: str, user_data: Optional[Dict] = None) -> str:
        """Start session with enhanced logging"""
        session_id = f"{user_id}_{int(time.time())}"
        
        self.active_sessions[session_id] = {
            "user_id": user_id,
            "type": session_type,
            "start_time": time.time(),
            "username": user_data.get("username", "unknown") if user_data else "unknown",
            "language": user_data.get("language_code", "unknown") if user_data else "unknown",
            "stages": [],
            "errors": []
        }
        
        # Set 60-second timeout
        self.session_timeouts[session_id] = time.time() + 60
        
        # Enhanced business logging
        self.smart_logger.business_log(
            f"SESSION_START_{session_type.upper()}", 
            user_id,
            username=user_data.get("username", "unknown") if user_data else "unknown",
            language=user_data.get("language_code", "unknown") if user_data else "unknown"
        )
        
        return session_id
    
    def log_stage(self, session_id: str, stage: str, success: bool = True, **details):
        """Enhanced stage logging"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            stage_data = {
                "name": stage,
                "timestamp": time.time(),
                "success": success,
                "details": details
            }
            session["stages"].append(stage_data)
            
            # Enhanced logging with context
            self.smart_logger.user_journey(
                session["user_id"],
                stage,
                request_text=details.get("request_text"),
                username=session["username"],
                language=session["language"],
                success=success
            )
    
    def complete_session(self, session_id: str, success: bool = True):
        """Complete session with comprehensive logging"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            duration = time.time() - session["start_time"]
            
            # Track business metrics
            session_type = session["type"]
            if session_type == "rabbi_wisdom":
                self.smart_logger.daily_stats["wisdom_requests"] += 1
            elif session_type == "torah_quiz":
                self.smart_logger.daily_stats["quizzes"] += 1
            elif session_type == "donation":
                self.smart_logger.daily_stats["donations"] += 1
            elif session_type == "stars_donation":
                self.smart_logger.daily_stats["donations"] += 1
                # Add specific stars tracking if needed
            
            # Log completion
            self.smart_logger.business_log(
                f"SESSION_COMPLETE_{session_type.upper()}",
                session["user_id"],
                duration=duration,
                success=success,
                username=session["username"],
                language=session["language"]
            )
            
            # Cleanup
            del self.active_sessions[session_id]
            if session_id in self.session_timeouts:
                del self.session_timeouts[session_id]
    
    def cleanup_stale_sessions(self):
        """Cleanup with smart logging"""
        current_time = time.time()
        expired = [sid for sid, timeout in self.session_timeouts.items() if current_time > timeout]
        
        for session_id in expired:
            self.smart_logger.system_health("SESSION_CLEANUP", "EXPIRED", session_id=session_id)
            self.complete_session(session_id, False)

class ProductionSessionManager:
    """Optimized session management for production"""
    
    def __init__(self, analytics: OptimizedAnalytics):
        self.analytics = analytics
    
    @staticmethod
    def get_localized_text(text_key: str, language: str = "English") -> str:
        """Get localized system messages"""
        translations = {
            "thinking_rabbi": {
                "English": "🤔 <i>Rabbi is contemplating your request...</i>",
                "Russian": "🤔 <i>Раввин размышляет над вашим запросом...</i>",
                "Hebrew": "🤔 <i>הרב חושב על בקשתך...</i>",
                "Spanish": "🤔 <i>El rabino está contemplando tu solicitud...</i>",
                "French": "🤔 <i>Le rabbin réfléchit à votre demande...</i>",
                "German": "🤔 <i>Der Rabbi denkt über Ihre Anfrage nach...</i>"
            },
            "preparing_quiz": {
                "English": "🧠 <i>Rabbi is preparing a Torah quiz for you...</i>",
                "Russian": "🧠 <i>Раввин готовит для вас Тору-квиз...</i>",
                "Hebrew": "🧠 <i>הרב מכין עבורכם חידון תורה...</i>",
                "Spanish": "🧠 <i>El rabino está preparando un quiz de Torá para ti...</i>",
                "French": "🧠 <i>Le rabbin prépare un quiz de Torah pour vous...</i>",
                "German": "🧠 <i>Der Rabbi bereitet ein Torah-Quiz für Sie vor...</i>"
            },
            "quiz_ready": {
                "English": "✅ <i>Quiz ready!</i>",
                "English": "✅ <i>Quiz ready!</i>",
                "Russian": "✅ <i>Квиз готов!</i>",
                "Hebrew": "✅ <i>החידון מוכן!</i>",
                "Spanish": "✅ <i>¡Quiz listo!</i>",
                "French": "✅ <i>Quiz prêt!</i>",
                "German": "✅ <i>Quiz bereit!</i>"
            },
            "think_about": {
                "English": "🤔 <b>Think About This:</b>",
                "Russian": "🤔 <b>Подумайте об этом:</b>",
                "Hebrew": "🤔 <b>חשבו על זה:</b>",
                "Spanish": "🤔 <b>Piensa en esto:</b>",
                "French": "🤔 <b>Réfléchissez à ceci:</b>",
                "German": "🤔 <b>Denken Sie darüber nach:</b>"
            },
            "more_wisdom": {
                "English": "📖 More Wisdom",
                "Russian": "📖 Больше мудрости",
                "Hebrew": "📖 עוד חכמה",
                "Spanish": "📖 Más Sabiduría",
                "French": "📖 Plus de Sagesse",
                "German": "📖 Mehr Weisheit"
            },
            "another_quiz": {
                "English": "🧠 Another Quiz",
                "Russian": "🧠 Еще квиз",
                "Hebrew": "🧠 עוד חידון",
                "Spanish": "🧠 Otro Quiz",
                "French": "🧠 Autre Quiz", 
                "German": "🧠 Weiteres Quiz"
            },
            "share_bot": {
                "English": "📤 Share Bot",
                "Russian": "📤 Поделиться ботом",
                "Hebrew": "📤 שתף בוט",
                "Spanish": "📤 Compartir Bot",
                "French": "📤 Partager le Bot",
                "German": "📤 Bot teilen"
            },
            "main_menu": {
                "English": "🏠 Main Menu",
                "Russian": "🏠 Главное меню",
                "Hebrew": "🏠 תפריט ראשי",
                "Spanish": "🏠 Menú Principal",
                "French": "🏠 Menu Principal",
                "German": "🏠 Hauptmenü"
            },
            "share_message": {
                "English": "Check out this Torah wisdom bot!",
                "Russian": "Попробуйте этого бота с мудростями Торы!",
                "Hebrew": "בדקו את הבוט הזה עם חכמת התורה!",
                "Spanish": "¡Prueba este bot de sabiduría de la Torá!",
                "French": "Découvrez ce bot de sagesse de la Torah!",
                "German": "Probieren Sie diesen Torah-Weisheits-Bot aus!"
            },
            "creating_artwork": {
                "English": "🎨 <i>Creating spiritual artwork...</i>",
                "Russian": "🎨 <i>Создаю духовное произведение...</i>",
                "Hebrew": "🎨 <i>יוצר יצירת אמנות רוחנית...</i>",
                "Spanish": "🎨 <i>Creando arte espiritual...</i>",
                "French": "🎨 <i>Création d'œuvres spirituelles...</i>",
                "German": "🎨 <i>Erstelle spirituelle Kunst...</i>"
            }
        }
        
        return translations.get(text_key, {}).get(language, translations.get(text_key, {}).get("English", text_key))
    
    @staticmethod
    def get_session(user_id: int, user_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Get or create user session with automatic language detection"""
        global last_cleanup
        
        # Periodic cleanup every 5 minutes
        if time.time() - last_cleanup > 300:
            ProductionSessionManager.cleanup_old_sessions()
            last_cleanup = time.time()
        
        if user_id not in user_sessions:
            # Detect language from Telegram user data
            detected_language = ProductionSessionManager.detect_user_language(user_data)
            
            user_sessions[user_id] = {
                "language": detected_language,
                "language_code": ProductionSessionManager.get_language_code(detected_language),
                "completed_workflows": 0,
                "successful_workflows": 0,
                "current_topic": None,
                "last_activity": time.time(),
                "donation_count": 0,
                "last_donation": 0,
                "preferences": {},
                "shown_quizzes": [],  # Track shown quiz questions to prevent duplicates
                "last_user_request": None  # Store last user message for context
            }
        
        user_sessions[user_id]["last_activity"] = time.time()
        return user_sessions[user_id]
    
    @staticmethod
    def detect_user_language(user_data: Optional[Dict] = None) -> str:
        """Detect user language from Telegram data"""
        if not user_data:
            return "English"
        
        try:
            from .constants import LANGUAGE_MAPPINGS
            language_mapping = LANGUAGE_MAPPINGS
        except ImportError:
            # Fallback if constants not available
            language_mapping = {
                "ru": "Russian", "en": "English", "he": "Hebrew",
                "es": "Spanish", "fr": "French", "de": "German", 
                "ar": "Arabic", "uk": "Russian", "be": "Russian"
            }
        
        # Try to get language from Telegram user data
        lang_code = user_data.get("language_code", "en")
        return language_mapping.get(lang_code, "English")
    
    @staticmethod
    def get_language_code(language: str) -> str:
        """Get language code from language name"""
        code_mapping = {
            "English": "en",
            "Russian": "ru", 
            "Hebrew": "he",
            "Spanish": "es",
            "French": "fr",
            "German": "de",
            "Arabic": "ar"
        }
        return code_mapping.get(language, "en")
    
    @staticmethod
    def update_session(user_id: int, **kwargs):
        """Update session data with consistency guarantee"""
        if user_id not in user_sessions:
            # Create session if doesn't exist
            user_sessions[user_id] = {
                "language": "English",
                "language_code": "en", 
                "completed_workflows": 0,
                "successful_workflows": 0,
                "current_topic": None,
                "last_activity": time.time(),
                "donation_count": 0,
                "last_donation": 0,
                "preferences": {},
                "shown_quizzes": [],
                "last_user_request": None,
                "last_question": None
            }
        
        # Update with new data
        user_sessions[user_id].update(kwargs)
        user_sessions[user_id]["last_activity"] = time.time()
        
        # Log important context updates
        if any(key in kwargs for key in ["current_topic", "last_question", "last_user_request"]):
            logger.info(f"🔄 Context updated for user {user_id}: {[(k,v) for k,v in kwargs.items() if k in ['current_topic', 'last_question', 'last_user_request']]}")
    
    @staticmethod
    def store_user_request(user_id: int, request_text: str):
        """Store user's last request for context in future interactions"""
        if user_id in user_sessions:
            user_sessions[user_id]["last_user_request"] = request_text
            # FIXED: Also store as last_question for quiz context
            user_sessions[user_id]["last_question"] = request_text
            user_sessions[user_id]["last_activity"] = time.time()
            logger.info(f"💾 Stored user request for {user_id}: '{request_text[:50]}...'") if request_text else None
    
    @staticmethod
    def cleanup_old_sessions():
        """Remove sessions older than 24 hours"""
        current_time = time.time()
        old_sessions = [
            uid for uid, session in user_sessions.items() 
            if current_time - session.get("last_activity", 0) > 86400
        ]
        
        for user_id in old_sessions:
            del user_sessions[user_id]
            logger.info(f"🧹 Cleaned up old session for user {user_id}")

class ProductionTelegramClient:
    """Production-optimized Telegram client with retry logic"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.session = None
        
    async def ensure_session(self):
        """Ensure HTTP session is initialized"""
        if self.session is None:
            import httpx
            self.session = httpx.AsyncClient(timeout=30.0)
    
    async def close_session(self):
        """Properly close HTTP session to prevent resource leaks"""
        if self.session:
            await self.session.aclose()
            self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - ensures session cleanup"""
        await self.close_session()
    
    async def _make_request(self, method: str, data: Dict, retries: int = 3) -> Dict:
        """Make HTTP request with retry logic"""
        url = f"{self.base_url}/{method}"
        
        if not self.session:
            self.session = httpx.AsyncClient(timeout=30.0)
        
        for attempt in range(retries):
            try:
                response = await self.session.post(url, json=data)
                result = response.json()
                
                if result.get("ok"):
                    return result
                else:
                    logger.warning(f"Telegram API error: {result}")
                    if attempt == retries - 1:
                        return result
                    
            except Exception as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt == retries - 1:
                    return {"ok": False, "error": str(e)}
                await asyncio.sleep(1)
        
        return {"ok": False, "error": "Max retries exceeded"}
    
    async def send_message(self, chat_id: int, text: str, reply_markup: Optional[Dict] = None, parse_mode: str = "HTML"):
        """Send message with retry logic"""
        data = {
            "chat_id": chat_id,
            "text": text[:4096],  # Telegram limit
            "parse_mode": parse_mode
        }
        
        if reply_markup:
            data["reply_markup"] = reply_markup
        
        result = await self._make_request("sendMessage", data)
        if result.get("ok"):
            logger.info(f"📤 Message sent to {chat_id}: {len(text)} chars")
        return result
    
    async def send_photo(self, chat_id: int, photo_url: str, caption: str = "", reply_markup: Optional[Dict] = None):
        """Send photo with fallback handling"""
        data = {
            "chat_id": chat_id,
            "photo": photo_url,
            "caption": caption[:1024],  # Telegram limit
            "parse_mode": "HTML"
        }
        
        if reply_markup:
            data["reply_markup"] = reply_markup
        
        result = await self._make_request("sendPhoto", data)
        if not result.get("ok"):
            # Fallback to text message if photo fails
            await self.send_message(chat_id, f"{caption}", reply_markup)
        return result
    
    async def send_photo_file(self, chat_id: int, file_path: str, caption: str = "", reply_markup: Optional[Dict] = None):
        """Send local photo file via multipart form data"""
        try:
            with open(file_path, "rb") as photo_file:
                photo_data = photo_file.read()
            
            # Prepare form data
            form_data = {
                "chat_id": str(chat_id),
                "caption": caption[:1024],
                "parse_mode": "HTML"
            }
            
            if reply_markup:
                form_data["reply_markup"] = json.dumps(reply_markup)
            
            files = {"photo": ("image.png", photo_data, "image/png")}
            
            # Send directly to Telegram API using httpx
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.telegram.org/bot{self.token}/sendPhoto",
                    data=form_data,
                    files=files
                )
                result = response.json()
                
            if result.get("ok"):
                logger.info(f"📸 Photo file sent to {chat_id}")
            else:
                logger.warning(f"Photo file failed: {result}")
                # Fallback to text message
                await self.send_message(chat_id, caption, reply_markup)
                
            return result
            
        except Exception as e:
            logger.error(f"Error sending photo file: {e}")
            # Fallback to text message
            await self.send_message(chat_id, caption, reply_markup)
            return {"ok": False, "error": str(e)}
    
    async def edit_message_text(self, chat_id: int, message_id: int, text: str, reply_markup: Optional[Dict] = None):
        """Edit message with error handling"""
        data = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text[:4096],
            "parse_mode": "HTML"
        }
        
        if reply_markup:
            data["reply_markup"] = reply_markup
        
        return await self._make_request("editMessageText", data)
    
    async def send_poll(self, chat_id: int, question: str, options: list, correct_answer: int = 0, explanation: str = ""):
        """Send quiz poll with validation and proper character limits"""
        # Validate inputs
        if len(options) < 2 or len(options) > 10:
            logger.error("Invalid poll options count")
            return {"ok": False, "error": "Invalid options count"}
        
        # Apply Telegram API limits with logging for truncated content
        original_question = question
        original_explanation = explanation
        original_options = options.copy()
        
        # Question limit: 300 characters for poll questions
        truncated_question = question[:300]
        if len(question) > 300:
            logger.warning(f"Quiz question truncated from {len(question)} to 300 chars: '{question[:50]}...'")
        
        # Options limit: 100 characters each (conservative estimate)
        truncated_options = []
        for i, opt in enumerate(options):
            truncated_opt = opt[:100]
            truncated_options.append(truncated_opt)
            if len(opt) > 100:
                logger.warning(f"Quiz option {i+1} truncated from {len(opt)} to 100 chars: '{opt[:30]}...'")
        
        # Explanation limit: 200 characters with max 2 line feeds
        truncated_explanation = explanation[:200] if explanation else ""
        if explanation and len(explanation) > 200:
            logger.warning(f"Quiz explanation truncated from {len(explanation)} to 200 chars: '{explanation[:50]}...'")
        
        data = {
            "chat_id": chat_id,
            "question": truncated_question,
            "options": json.dumps(truncated_options),
            "type": "quiz",
            "correct_option_id": correct_answer,
            "explanation": truncated_explanation,
            "is_anonymous": False
        }
        
        return await self._make_request("sendPoll", data)
    
    async def answer_callback_query(self, callback_query_id: str, text: str = ""):
        """Answer callback query"""
        data = {"callback_query_id": callback_query_id, "text": text[:200]}
        return await self._make_request("answerCallbackQuery", data)
    
    async def get_updates(self, offset: int = 0, timeout: int = 30):
        """Get updates with connection handling"""
        url = f"{self.base_url}/getUpdates"
        params = {"offset": offset, "timeout": timeout}
        
        try:
            if not self.session:
                self.session = httpx.AsyncClient(timeout=35.0)
            
            response = await self.session.get(url, params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Get updates failed: {e}")
            return {"ok": False, "error": str(e)}

class OptimizedRabbiModule:
    """Production-optimized Rabbi module"""
    
    def __init__(self, telegram_client: ProductionTelegramClient, session_manager: ProductionSessionManager, analytics: OptimizedAnalytics):
        self.telegram_client = telegram_client
        self.session_manager = session_manager
        self.analytics = analytics
        self.prompt_loader = PromptLoader()
        
        # Initialize preset image manager for faster responses
        try:
            from .wisdom_image_manager import WisdomImageManager
            self.image_manager = WisdomImageManager()
            logger.info(f"📸 Preset images: {self.image_manager.get_preset_count()} available")
        except ImportError:
            try:
                from torah_bot.wisdom_image_manager import WisdomImageManager
                self.image_manager = WisdomImageManager()
                logger.info(f"📸 Preset images: {self.image_manager.get_preset_count()} available")
            except ImportError:
                self.image_manager = None
                logger.warning("📸 Wisdom image manager not available - using AI generation only")
    
    async def generate_wisdom(self, user_text: str, language: str = "English", user_name: str = "Friend") -> Dict[str, Any]:
        """Generate AI wisdom with proper context handling"""
        if not openai_client:
            return {
                "wisdom": f"Thank you, {user_name}. The Torah teaches us that wisdom comes through learning and reflection. Even in uncertainty, we find guidance through study and contemplation.",
                "topic": "Torah wisdom and study",
                "references": "Pirkei Avot 1:4"
            }
        
        # Initialize content variable to prevent unbound variable error
        content = ""
        
        try:
            # Load prompts from files for easy editing
            system_prompt = self.prompt_loader.get_rabbi_wisdom_prompt(user_name, language, user_text)
            user_prompt = self.prompt_loader.get_user_wisdom_prompt(user_text)
            try:
                if openai_client is None:
                    raise ValueError("OpenAI client not initialized")
                    
                # Use GPT-4o directly (GPT-5 doesn't exist)
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_completion_tokens=400,
                    temperature=0.7
                )
                
                content = response.choices[0].message.content
                if content:
                    logger.info(f"GPT-5 raw response: {content[:100]}...")
                
            except Exception as api_error:
                logger.warning(f"GPT-4o with structured format failed, trying plain text: {api_error}")
                if openai_client is None:
                    raise ValueError("OpenAI client not available for fallback")
                    
                # Fallback without json_object format
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_completion_tokens=400,
                    temperature=0.7
                )
                
                content = response.choices[0].message.content or ""
                if content:
                    logger.info(f"GPT-4o raw response: {content[:100]}...")
            
            # Parse and validate JSON response
            if not content or content.strip() == "":
                raise ValueError("Empty response from AI")
            
            # Clean content from markdown blocks if present
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "").strip()
            
            wisdom_data = json.loads(content)
            
            # Validate required fields
            required_keys = ["wisdom", "topic", "references"]
            if not all(key in wisdom_data for key in required_keys):
                logger.error(f"Missing keys in AI response: {wisdom_data}")
                raise ValueError("Incomplete AI response structure")
            
            # Validate content is not empty
            if not wisdom_data["wisdom"] or not wisdom_data["topic"]:
                raise ValueError("Empty wisdom or topic in AI response")
            
            logger.info(f"✅ AI Wisdom generated successfully for topic: {wisdom_data['topic']}")
            return wisdom_data
            
        except json.JSONDecodeError as e:
            try:
                content_preview = content[:100] if content else "no content"
            except (TypeError, AttributeError):
                content_preview = "no content"
            logger.error(f"JSON decode error: {e}, content: {content_preview}")
            return self._get_fallback_wisdom(user_text, user_name, language)
        except Exception as e:
            logger.error(f"Wisdom generation error: {e}")
            return self._get_fallback_wisdom(user_text, user_name, language)
    
    def _get_fallback_wisdom(self, user_text: str, user_name: str, language: str = "English") -> Dict[str, Any]:
        """Generate contextual fallback wisdom based on user input"""
        # Try to extract topic from user text for more relevant fallback
        topic_keywords = {
            "family": "family relationships",
            "work": "work and purpose", 
            "study": "Torah study",
            "prayer": "prayer and faith",
            "shabbat": "Shabbat observance",
            "love": "love and relationships",
            "wisdom": "seeking wisdom",
            "peace": "peace and harmony"
        }
        
        user_lower = user_text.lower()
        detected_topic = "Torah wisdom"
        
        for keyword, topic in topic_keywords.items():
            if keyword in user_lower:
                detected_topic = topic
                break
        
        # Localized fallback wisdom
        fallback_messages = {
            "English": {
                "wisdom": f"Thank you for your thoughtful question about {detected_topic}, {user_name}. The Torah teaches us that every question is a doorway to deeper understanding. As our sages say, 'Who is wise? One who learns from every person.' Your inquiry shows a seeking spirit, and in that seeking itself, we find wisdom.",
                "references": "Pirkei Avot 4:1"
            },
            "Russian": {
                "wisdom": f"Спасибо за ваш глубокий вопрос о {detected_topic}, {user_name}. Тора учит нас, что каждый вопрос — это дверь к более глубокому пониманию. Как говорят наши мудрецы: 'Кто мудр? Тот, кто учится у каждого человека.' Ваш вопрос показывает ищущий дух, и в самом этом поиске мы находим мудрость.",
                "references": "Пиркей Авот 4:1"
            },
            "Hebrew": {
                "wisdom": f"תודה על השאלה המעמיקה שלך על {detected_topic}, {user_name}. התורה מלמדת אותנו שכל שאלה היא דלת להבנה עמוקה יותר. כפי שאומרים חכמינו: 'איזהו חכם? הלומד מכל אדם.' השאלה שלך מראה על רוח מחפשת, ובחיפוש עצמו אנו מוצאים חכמה.",
                "references": "פרקי אבות ד:א"
            }
        }
        
        fallback_content = fallback_messages.get(language, fallback_messages["English"])
        
        return {
            "wisdom": fallback_content["wisdom"],
            "topic": detected_topic,
            "references": fallback_content["references"]
        }
    
    async def generate_image(self, topic: str) -> Optional[str]:
        """Generate adaptive themed image with enhanced prompts and robust fallback"""
        if not openai_client:
            logger.warning("No OpenAI client available for image generation")
            return None
        
        max_retries = 2
        fallback_prompts = [
            # Primary: Enhanced adaptive prompt
            lambda: self._get_enhanced_image_prompt(topic),
            # Fallback 1: Simplified prompt
            lambda: f"Beautiful spiritual Jewish artwork: {topic}. Pixar style, warm lighting, peaceful, no text.",
            # Fallback 2: Ultra-simple prompt  
            lambda: "Peaceful Jewish spiritual artwork, warm golden light, Torah scrolls, no text."
        ]
        
        for attempt in range(max_retries):
            for prompt_index, prompt_func in enumerate(fallback_prompts):
                try:
                    prompt = prompt_func()
                    
                    logger.info(f"🎨 Image generation attempt {attempt+1}, prompt {prompt_index+1}: {prompt[:50]}...")
                    
                    response = openai_client.images.generate(
                        model="dall-e-3",
                        prompt=prompt,
                        size="1024x1024",
                        quality="hd" if prompt_index == 0 else "standard"  # HD only for primary
                    )
                    
                    if response.data and len(response.data) > 0 and response.data[0].url:
                        logger.info(f"✅ Image generated successfully on attempt {attempt+1}, prompt {prompt_index+1}")
                        return response.data[0].url
                    else:
                        logger.warning(f"⚠️ Empty response from DALL-E on attempt {attempt+1}, prompt {prompt_index+1}")
                        
                except Exception as e:
                    error_type = type(e).__name__
                    logger.error(f"❌ Image generation failed attempt {attempt+1}, prompt {prompt_index+1}: {error_type}: {str(e)[:100]}")
                    
                    # Specific error handling
                    if "content_policy" in str(e).lower() or "safety" in str(e).lower():
                        logger.warning("🚫 Content policy violation - trying simpler prompt")
                        continue
                    elif "rate_limit" in str(e).lower():
                        logger.warning("🔄 Rate limit hit - waiting before retry")
                        await asyncio.sleep(2)
                        continue
                    elif "quota" in str(e).lower() or "billing" in str(e).lower():
                        logger.error("💳 OpenAI quota/billing issue - stopping image generation")
                        return None
        
        logger.error("💥 All image generation attempts failed")
        return None
    
    def _get_enhanced_image_prompt(self, topic: str) -> str:
        """Get enhanced image prompt with error handling"""
        try:
            theme_elements = self.prompt_loader.get_theme_elements(topic)
            return self.prompt_loader.get_wisdom_image_prompt(topic, theme_elements)
        except Exception as e:
            logger.warning(f"Enhanced prompt generation failed: {e}")
            return f"Peaceful study library about {topic}. Warm lighting, books and scrolls, cozy atmosphere, no text visible."
    
    async def handle_wisdom_request(self, chat_id: int, user_id: int, user_message: Optional[str] = None, user_data: Optional[Dict] = None) -> bool:
        """Complete wisdom workflow with proper context handling"""
        session_id = self.analytics.start_session(user_id, "rabbi_wisdom", user_data)
        
        try:
            session = self.session_manager.get_session(user_id, user_data)
            # Priority: Manual language setting > Session language > Auto-detection
            if session.get("manual_language_set", False):
                language = session.get("language", "English")
                logger.info(f"🌐 Using manually set language for wisdom: {language}")
            elif user_data:
                language = self.session_manager.detect_user_language(user_data)
                self.session_manager.update_session(user_id, language=language)
            else:
                language = session.get("language", "English")
            user_name = user_data.get("first_name", "Friend") if user_data is not None else "Friend"
            
            # Determine the actual user input for context
            if user_message and user_message != "daily Torah wisdom":
                # User sent a specific message/question
                topic_text = user_message
                logger.info(f"Processing user question: '{user_message}'")
            else:
                # Default wisdom request (from button) - use random Torah topic like quizzes
                try:
                    from .quiz_topics import QuizTopicGenerator
                except ImportError:
                    from torah_bot.quiz_topics import QuizTopicGenerator
                
                try:
                    # Get recent topics from session to avoid repetition
                    recent_topics = session.get("recent_wisdom_topics", [])
                    
                    # Generate random Torah topic
                    random_topic = QuizTopicGenerator.get_random_topic(exclude_recent=recent_topics)
                    topic_text = f"daily Torah wisdom about {random_topic}"
                    
                    # Track recent topics (keep last 10)
                    recent_topics.append(random_topic)
                    if len(recent_topics) > 10:
                        recent_topics = recent_topics[-10:]
                    
                    self.session_manager.update_session(user_id, recent_wisdom_topics=recent_topics)
                    logger.info(f"Processing random wisdom request: '{random_topic}'")
                except Exception as e:
                    # Fallback to original if import fails
                    logger.warning(f"Failed to generate random topic: {e}")
                    topic_text = "daily Torah wisdom and guidance"
                    logger.info("Processing general wisdom request")
            
            # Enhanced logging with user request tracking
            username = user_data.get("username", "unknown") if user_data else "unknown"
            self.analytics.log_stage(session_id, "thinking_indicator", request_text=topic_text)
            
            thinking_text = self.session_manager.get_localized_text("thinking_rabbi", language)
            thinking_msg = await self.telegram_client.send_message(
                chat_id, thinking_text
            )
            
            thinking_msg_id = thinking_msg.get("result", {}).get("message_id") if thinking_msg.get("ok") else None
            
            # Stage 2 & 3: PARALLEL generation with performance tracking
            start_time = time.time()
            self.analytics.log_stage(session_id, "wisdom_generation")
            logger.info(f"Generating wisdom for: '{topic_text}' in {language} for {user_name}")
            
            # Generate wisdom first to get the actual topic
            wisdom_data = await self.generate_wisdom(topic_text, language, user_name)
            wisdom_time = time.time() - start_time
            
            # Track AI performance
            self.analytics.smart_logger.ai_performance("WISDOM_GENERATION", True, wisdom_time, topic=wisdom_data.get("topic", "unknown"))
            logger.info(f"Generated wisdom topic: '{wisdom_data['topic']}', length: {len(wisdom_data['wisdom'])} chars")
            
            # Smart image selection: preset for button requests, AI for user questions
            self.analytics.log_stage(session_id, "image_generation")
            actual_topic = wisdom_data.get("topic", topic_text)
            
            is_button_request = not (user_message and user_message.strip())
            
            if thinking_msg_id:
                await self.telegram_client.edit_message_text(
                    chat_id, thinking_msg_id, self.session_manager.get_localized_text("creating_artwork", language)
                )
            
            image_start = time.time()
            
            if is_button_request and self.image_manager and self.image_manager.has_presets():
                # Button request: use fast preset images
                recent_images = session.get("recent_wisdom_images", [])
                preset_image_path = self.image_manager.get_random_preset_image(exclude_recent=recent_images)
                
                if preset_image_path:
                    # Track recent images (keep last 5)
                    recent_images.append(os.path.basename(preset_image_path))
                    if len(recent_images) > 5:
                        recent_images = recent_images[-5:]
                    self.session_manager.update_session(user_id, recent_wisdom_images=recent_images)
                    
                    image_url = preset_image_path  # Local file path
                    logger.info(f"🚀 FAST: Using preset image '{os.path.basename(preset_image_path)}' for button request")
                else:
                    # Fallback to AI generation
                    logger.warning("⚠️ No preset image available, falling back to AI generation")
                    image_url = await self.generate_image(actual_topic)
                    logger.info(f"🎨 AI generation fallback for topic: '{actual_topic}'")
            else:
                # User question: generate AI image for specific topic
                logger.info(f"🎨 USER QUESTION: Generating AI image for topic: '{actual_topic}' (user: '{user_message or 'N/A'}')")
                image_url = await self.generate_image(actual_topic)
            
            image_time = time.time() - image_start
            
            # Track image generation performance with detailed logging
            if image_url:
                self.analytics.smart_logger.ai_performance("IMAGE_GENERATION", True, image_time, style="pixar", topic=wisdom_data.get("topic", "unknown"))
                logger.info(f"🎨 Image generation successful: {image_time:.1f}s")
            else:
                self.analytics.smart_logger.ai_performance("IMAGE_GENERATION", False, image_time, topic=wisdom_data.get("topic", "unknown"))
                logger.error(f"🚨 CRITICAL: IMAGE_GENERATION ❌ in {image_time:.1f}s - No image URL returned")
            
            # Stage 4: Final response
            self.analytics.log_stage(session_id, "response_delivery")
            
            # Localized wisdom response headers and buttons
            wisdom_headers = {
                "English": {
                    "with_question": "📖 <b>Rabbi's Wisdom</b>\n<i>✨ On your question: \"{question}\"</i>\n\n",
                    "general": "📖 <b>Rabbi's Wisdom</b>\n<i>✨ Daily wisdom</i>\n\n",
                    "sources": "📚 <b>Sources:</b> <i>{refs}</i>",
                    "suggest_topic": "✍️ <i>Write a topic that interests you for the next wisdom</i>"
                },
                "Russian": {
                    "with_question": "📖 <b>Мудрость Раввина</b>\n<i>✨ На ваш вопрос: \"{question}\"</i>\n\n",
                    "general": "📖 <b>Мудрость Раввина</b>\n<i>✨ Ежедневная мудрость</i>\n\n",
                    "sources": "📚 <b>Источники:</b> <i>{refs}</i>",
                    "suggest_topic": "✍️ <i>Напишите тему, которая вас волнует, для следующей мудрости</i>"
                },
                "Hebrew": {
                    "with_question": "📖 <b>חכמת הרב</b>\n<i>✨ על שאלתך: \"{question}\"</i>\n\n",
                    "general": "📖 <b>חכמת הרב</b>\n<i>✨ חכמה יומית</i>\n\n",
                    "sources": "📚 <b>מקורות:</b> <i>{refs}</i>",
                    "suggest_topic": "✍️ <i>כתבו נושא שמעניין אתכם לחכמה הבאה</i>"
                },
                "Spanish": {
                    "with_question": "📖 <b>Sabiduría del Rabino</b>\n<i>✨ Sobre tu pregunta: \"{question}\"</i>\n\n",
                    "general": "📖 <b>Sabiduría del Rabino</b>\n<i>✨ Sabiduría diaria</i>\n\n",
                    "sources": "📚 <b>Fuentes:</b> <i>{refs}</i>",
                    "suggest_topic": "✍️ <i>Escribe un tema que te interese para la próxima sabiduría</i>"
                },
                "French": {
                    "with_question": "📖 <b>Sagesse du Rabbin</b>\n<i>✨ Sur votre question: \"{question}\"</i>\n\n",
                    "general": "📖 <b>Sagesse du Rabbin</b>\n<i>✨ Sagesse quotidienne</i>\n\n",
                    "sources": "📚 <b>Sources:</b> <i>{refs}</i>",
                    "suggest_topic": "✍️ <i>Écrivez un sujet qui vous intéresse pour la prochaine sagesse</i>"
                },
                "German": {
                    "with_question": "📖 <b>Rabbiner Weisheit</b>\n<i>✨ Zu Ihrer Frage: \"{question}\"</i>\n\n",
                    "general": "📖 <b>Rabbiner Weisheit</b>\n<i>✨ Tägliche Weisheit</i>\n\n",
                    "sources": "📚 <b>Quellen:</b> <i>{refs}</i>",
                    "suggest_topic": "✍️ <i>Schreiben Sie ein Thema, das Sie für die nächste Weisheit interessiert</i>"
                }
            }
            
            wisdom_buttons = {
                "English": {
                    "another": "🔄 Another Wisdom",
                    "quiz": "🧠 Take Quiz", 
                    "share": "📤 Share Wisdom",
                    "menu": "🏠 Main Menu"
                },
                "Russian": {
                    "another": "🔄 Еще мудрость",
                    "quiz": "🧠 Викторина",
                    "share": "📤 Поделиться мудростью",
                    "menu": "🏠 Главное меню"
                },
                "Hebrew": {
                    "another": "🔄 עוד חכמה",
                    "quiz": "🧠 חידון",
                    "share": "📤 שתף חכמה",
                    "menu": "🏠 תפריט ראשי"
                },
                "Spanish": {
                    "another": "🔄 Más Sabiduría",
                    "quiz": "🧠 Quiz",
                    "share": "📤 Compartir Sabiduría",
                    "menu": "🏠 Menú Principal"
                },
                "French": {
                    "another": "🔄 Plus de Sagesse",
                    "quiz": "🧠 Quiz",
                    "share": "📤 Partager la Sagesse",
                    "menu": "🏠 Menu Principal"
                },
                "German": {
                    "another": "🔄 Mehr Weisheit",
                    "quiz": "🧠 Quiz",
                    "share": "📤 Weisheit Teilen",
                    "menu": "🏠 Hauptmenü"
                }
            }
            
            # Get localized texts
            headers = wisdom_headers.get(language, wisdom_headers["English"])
            buttons = wisdom_buttons.get(language, wisdom_buttons["English"])
            
            # Prepare wisdom sharing message
            wisdom_preview = wisdom_data["wisdom"][:100] + ('...' if len(wisdom_data["wisdom"]) > 100 else '')
            share_wisdom_messages = {
                "English": f"📖 Daily Torah wisdom: {wisdom_preview} 🙏 Join our wisdom community!",
                "Russian": f"📖 Ежедневная мудрость Торы: {wisdom_preview} 🙏 Присоединяйтесь к нашему сообществу мудрости!",
                "Hebrew": f"📖 חכמת תורה יומית: {wisdom_preview} 🙏 הצטרפו לקהילת החכמה שלנו!",
                "Spanish": f"📖 Sabiduría diaria de la Torá: {wisdom_preview} 🙏 ¡Únete a nuestra comunidad de sabiduría!",
                "French": f"📖 Sagesse quotidienne de la Torah: {wisdom_preview} 🙏 Rejoignez notre communauté de sagesse!",
                "German": f"📖 Tägliche Torah-Weisheit: {wisdom_preview} 🙏 Treten Sie unserer Weisheitsgemeinschaft bei!"
            }
            share_wisdom_message = share_wisdom_messages.get(language, share_wisdom_messages["English"])
            
            # Format wisdom header
            if user_message and user_message != "daily Torah wisdom":
                question_preview = user_message[:50] + ('...' if len(user_message) > 50 else '')
                wisdom_header = headers["with_question"].format(question=question_preview)
            else:
                wisdom_header = headers["general"]
            
            # Enhanced formatting for better readability
            wisdom_content = wisdom_data["wisdom"]
            
            # Add visual breaks for long paragraphs
            if len(wisdom_content) > 200:
                # Split into paragraphs and add spacing
                wisdom_content = wisdom_content.replace('. ', '.\n\n')
                # Remove excessive line breaks
                wisdom_content = '\n\n'.join([p.strip() for p in wisdom_content.split('\n\n') if p.strip()])
            
            sources_text = headers["sources"].format(refs=wisdom_data["references"])
            
            # Format complete wisdom text with enhanced structure  
            suggest_topic_text = headers.get("suggest_topic", "✍️ <i>Write a topic that interests you for the next wisdom</i>")
            
            wisdom_text = f"""{wisdom_header}
💫 {wisdom_content}

─────────────────

{sources_text}

{suggest_topic_text}"""
            
            keyboard = {
                "inline_keyboard": [
                    [{"text": buttons["another"], "callback_data": "rabbi_wisdom"}],
                    [{"text": buttons["quiz"], "callback_data": "torah_quiz"}],
                    [{"text": buttons["share"], "switch_inline_query": share_wisdom_message}],
                    [{"text": buttons["menu"], "callback_data": "main_menu"}]
                ]
            }
            
            if image_url:
                # Smart image sending: local file vs URL
                if os.path.exists(image_url):
                    # Local preset image file
                    await self.telegram_client.send_photo_file(chat_id, image_url, wisdom_text, keyboard)
                    logger.info(f"✅ Sent wisdom with PRESET image: {os.path.basename(image_url)}")
                else:
                    # AI-generated image URL
                    await self.telegram_client.send_photo(chat_id, image_url, wisdom_text, keyboard)
                    logger.info("✅ Sent wisdom with AI image")
            else:
                await self.telegram_client.send_message(chat_id, wisdom_text, keyboard)
                logger.info("✅ Sent wisdom text only")
            
            # Update session with proper context
            self.session_manager.update_session(
                user_id, 
                current_topic=wisdom_data["topic"],
                last_question=user_message or "general wisdom",
                successful_workflows=session["successful_workflows"] + 1,
                completed_workflows=session["completed_workflows"] + 1,
                last_workflow="rabbi_wisdom"
            )
            
            self.analytics.complete_session(session_id, True)
            return True
            
        except Exception as e:
            logger.error(f"Rabbi workflow error: {e}")
            self.analytics.complete_session(session_id, False)
            
            # Ensure language is available for error handling
            try:
                # Try to get language from session
                session = self.session_manager.get_session(user_id, user_data)
                language = session.get("language", "English")
            except (KeyError, AttributeError, TypeError):
                language = "English"
            
            # Localized error messages
            error_messages = {
                "English": "❌ <i>Sorry, there was an error generating wisdom. Please try again.</i>",
                "Russian": "❌ <i>Извините, произошла ошибка при генерации мудрости. Попробуйте еще раз.</i>",
                "Hebrew": "❌ <i>סליחה, הייתה שגיאה ביצירת החכמה. נסו שוב.</i>",
                "Spanish": "❌ <i>Lo siento, hubo un error generando sabiduría. Inténtalo de nuevo.</i>",
                "French": "❌ <i>Désolé, il y a eu une erreur en générant la sagesse. Veuillez réessayer.</i>",
                "German": "❌ <i>Entschuldigung, es gab einen Fehler beim Generieren von Weisheit. Bitte versuchen Sie es erneut.</i>"
            }
            
            try_again_buttons = {
                "English": "🔄 Try Again",
                "Russian": "🔄 Попробовать еще раз",
                "Hebrew": "🔄 נסה שוב",
                "Spanish": "🔄 Intentar de Nuevo",
                "French": "🔄 Réessayer",
                "German": "🔄 Erneut Versuchen"
            }
            
            error_text = error_messages.get(language, error_messages["English"])
            button_text = try_again_buttons.get(language, try_again_buttons["English"])
            
            await self.telegram_client.send_message(
                chat_id, 
                error_text,
                {"inline_keyboard": [[{"text": button_text, "callback_data": "rabbi_wisdom"}]]}
            )
            return False

class OptimizedQuizModule:
    """Production-optimized Quiz module"""
    
    def __init__(self, telegram_client: ProductionTelegramClient, session_manager: ProductionSessionManager, analytics: OptimizedAnalytics):
        self.telegram_client = telegram_client
        self.session_manager = session_manager
        self.analytics = analytics
        self.prompt_loader = PromptLoader()
    
    def _shuffle_quiz_options(self, quiz_data: Dict[str, Any]) -> Dict[str, Any]:
        """Shuffle quiz options and update correct_answer index accordingly"""
        import random
        
        original_correct_index = quiz_data["correct_answer"]
        options = quiz_data["options"].copy()
        
        # Create list of (option, is_correct) tuples
        options_with_flags = [(opt, i == original_correct_index) for i, opt in enumerate(options)]
        
        # Shuffle the options
        random.shuffle(options_with_flags)
        
        # Find new position of correct answer
        new_correct_index = next(i for i, (_, is_correct) in enumerate(options_with_flags) if is_correct)
        
        # Extract shuffled options
        shuffled_options = [opt for opt, _ in options_with_flags]
        
        # Update quiz data
        quiz_data["options"] = shuffled_options
        quiz_data["correct_answer"] = new_correct_index
        
        logger.info(f"🔀 Shuffled quiz: correct answer moved from position {original_correct_index} to {new_correct_index}")
        return quiz_data
    
    async def generate_quiz(self, topic: str, language: str = "English", user_id: Optional[int] = None, avoid_duplicates: bool = True) -> Dict[str, Any]:
        """Generate AI-powered Torah quiz with 6 options"""
        if not openai_client:
            logger.error(f"❌ CRITICAL: OpenAI client not available! Using fallback for topic: {topic}")
            return {
                "question": "What is the first word of the Torah?",
                "options": ["Bereshit", "Vayomer", "Elohim", "Shamayim", "Beresheet", "Vayelech"],
                "correct_answer": 0,
                "explanation": "Bereshit (Genesis) means 'In the beginning' - the opening of Creation",
                "follow_up": "What does this teach us about new beginnings?"
            }
        
        logger.info(f"🤖 AI GENERATING quiz for topic: '{topic}' (user: {user_id})")
        
        try:
            # Get previously shown quizzes to avoid duplicates
            shown_quizzes = []
            if user_id and avoid_duplicates:
                session = self.session_manager.get_session(user_id)
                shown_quizzes = session.get("shown_quizzes", [])
            
            duplicate_warning = ""
            if shown_quizzes:
                duplicate_warning = f"\n\nIMPORTANT: DO NOT repeat these previously asked questions:\n{'; '.join(shown_quizzes[-5:])}"
            
            try:
                # Load quiz prompt from file for easy editing
                prompt = self.prompt_loader.get_quiz_prompt(topic, language, duplicate_warning)
            except Exception as prompt_error:
                logger.error(f"💥 PROMPT LOADER ERROR: {prompt_error}")
                raise Exception(f"PromptLoader failed: {prompt_error}")
            
            if openai_client is None:
                raise Exception("Global OpenAI client not initialized")
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=600,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            if content is None:
                raise ValueError("Empty response from AI")
            
            logger.info(f"🤖 AI Response ({len(content)} chars): {content[:200]}...")
            
            # NUCLEAR OPTION: Force GPT to return clean JSON only  
            try:
                # Try direct parsing first - maybe the issue is in our cleaning
                quiz_data = json.loads(content)
                logger.info("✅ Direct JSON parse successful!")
                
            except json.JSONDecodeError:
                logger.info("⚡ Direct parse failed, trying cleanup...")
                
                # AGGRESSIVE cleanup approach
                cleaned = content.strip()
                
                # Remove common AI response prefixes
                prefixes_to_remove = [
                    "Here's your quiz:",
                    "Here is the quiz:",
                    "Quiz:",
                    "```json",
                    "```",
                    "\n",
                    " "
                ]
                
                for prefix in prefixes_to_remove:
                    if cleaned.startswith(prefix):
                        cleaned = cleaned[len(prefix):].strip()
                
                # Find JSON boundaries 
                start = cleaned.find('{')
                end = cleaned.rfind('}') + 1
                
                if start >= 0 and end > start:
                    json_part = cleaned[start:end]
                    logger.info(f"🔧 Extracted JSON: '{json_part}'")
                    
                    try:
                        quiz_data = json.loads(json_part)
                        logger.info("✅ Cleanup successful!")
                    except json.JSONDecodeError as final_error:
                        logger.error(f"💥 FINAL JSON error: {final_error}")
                        logger.error(f"💥 Failed content: '{json_part}'")
                        raise Exception(f"AI returned unparseable JSON: {final_error}")
                else:
                    raise Exception("No JSON structure found in AI response")
            
            # Validate the parsed data
            required_fields = ["question", "options", "correct_answer", "explanation"]
            for field in required_fields:
                if field not in quiz_data:
                    raise Exception(f"Missing field: {field}")
            
            if not isinstance(quiz_data["options"], list) or len(quiz_data["options"]) < 4:
                raise Exception(f"Invalid options: {quiz_data.get('options', 'missing')}")
            
            # IMPROVED: Track this quiz to prevent future duplicates
            if user_id and avoid_duplicates:
                session = self.session_manager.get_session(user_id)
                shown_quizzes = session.get("shown_quizzes", [])
                # Store more of the question text for better duplicate detection
                quiz_signature = quiz_data["question"][:150]  # Store first 150 chars for better matching
                shown_quizzes.append(quiz_signature)
                # Keep last 20 quizzes for better duplicate prevention
                if len(shown_quizzes) > 20:
                    shown_quizzes = shown_quizzes[-20:]
                self.session_manager.update_session(user_id, shown_quizzes=shown_quizzes)
                logger.info(f"📝 Stored quiz signature for user {user_id}, total stored: {len(shown_quizzes)}")
            
            return quiz_data
            
        except Exception as e:
            logger.error(f"Quiz generation error: {e}")
            # IMPROVED: AI fallback with deduplication check
            shown_quizzes = []
            if user_id and avoid_duplicates:
                session = self.session_manager.get_session(user_id)
                shown_quizzes = session.get("shown_quizzes", [])
                logger.info(f"⚠️ AI failed, using fallback with {len(shown_quizzes)} shown quizzes to avoid")
            
            # Diverse AI fallback with 6 options  
            fallback_quizzes_en = [
                {
                    "question": "What is the first commandment in the Ten Commandments?",
                    "options": ["Honor your parents", "Do not steal", "I am the Lord your God", "Do not murder", "Keep the Sabbath", "Do not covet"],
                    "correct_answer": 2,
                    "explanation": "The first commandment establishes the foundation of Jewish faith: recognition of God as the one true deity",
                    "follow_up": "How does acknowledging God as your foundation change how you approach daily decisions?"
                },
                {
                    "question": "According to Rabbi Hillel, what is the golden rule of Torah?",
                    "options": ["Fast on Yom Kippur", "Study every day", "What is hateful to you, do not do to others", "Give charity regularly", "Keep all 613 commandments", "Pray three times daily"],
                    "correct_answer": 2,
                    "explanation": "Rabbi Hillel taught this as the essence of Torah when asked to teach it while standing on one foot",
                    "follow_up": "Think of someone you struggle with - how can you apply this principle today?"
                },
                {
                    "question": "Which Jewish holiday celebrates the giving of the Torah at Mount Sinai?",
                    "options": ["Passover", "Rosh Hashanah", "Shavot", "Sukkot", "Purim", "Hanukkah"],
                    "correct_answer": 2,
                    "explanation": "Shavot, occurring 50 days after Passover, commemorates when Moses received the Torah from God",
                    "follow_up": "What does receiving wisdom mean to you in your daily life?"
                },
                {
                    "question": "What does 'Tikkun Olam' mean in Jewish tradition?",
                    "options": ["Morning prayers", "Dietary laws", "Repairing the world", "Wedding ceremony", "Torah study", "Sabbath rest"],
                    "correct_answer": 2,
                    "explanation": "Tikkun Olam means 'repairing the world' - our responsibility to make the world more just and compassionate",
                    "follow_up": "What small action could you take today to 'repair' part of your world?"
                },
                {
                    "question": "Who was the first Jewish patriarch according to the Torah?",
                    "options": ["Moses", "Abraham", "Isaac", "Jacob", "Noah", "Adam"],
                    "correct_answer": 1,
                    "explanation": "Abraham was chosen by God to be the first patriarch, beginning the covenant with the Jewish people",
                    "follow_up": "Abraham left everything familiar for an unknown journey. When have you taken a leap of faith?"
                },
                {
                    "question": "What is the meaning of 'Shalom' beyond just 'peace'?",
                    "options": ["War", "Completeness", "Happiness", "Money", "Food", "Work"],
                    "correct_answer": 1,
                    "explanation": "Shalom comes from the root meaning 'wholeness' or 'completeness' - true peace comes from inner harmony",
                    "follow_up": "Where in your life do you seek more wholeness and inner peace?"
                }
            ]
            
            fallback_quizzes_ru = [
                {
                    "question": "Какая первая заповедь в Десяти заповедях?",
                    "options": ["Почитай родителей", "Не кради", "Я Господь, Бог твой", "Не убивай", "Соблюдай субботу", "Не завидуй"],
                    "correct_answer": 2,
                    "explanation": "Первая заповедь устанавливает основу еврейской веры: признание Бога как единственного истинного божества",
                    "follow_up": "Как признание Бога в качестве основы меняет ваш подход к повседневным решениям?"
                },
                {
                    "question": "Согласно рабби Гиллелю, какое золотое правило Торы?",
                    "options": ["Поститься в Йом Кипур", "Учиться каждый день", "Что неприятно тебе, не делай другому", "Регулярно жертвовать", "Соблюдать все 613 заповедей", "Молиться три раза в день"],
                    "correct_answer": 2,
                    "explanation": "Рабби Гиллель учил этому как сущности Торы, когда его попросили объяснить всю Тору, стоя на одной ноге",
                    "follow_up": "Подумайте о ком-то, с кем у вас сложности - как можете применить этот принцип сегодня?"
                },
                {
                    "question": "Какой еврейский праздник отмечает дарование Торы на горе Синай?",
                    "options": ["Песах", "Рош а-Шана", "Шавуот", "Суккот", "Пурим", "Ханука"],
                    "correct_answer": 2,
                    "explanation": "Шавуот, происходящий через 50 дней после Песаха, отмечает получение Моисеем Торы от Бога",
                    "follow_up": "Что означает для вас получение мудрости в повседневной жизни?"
                },
                {
                    "question": "Что означает 'Тикун Олам' в еврейской традиции?",
                    "options": ["Утренние молитвы", "Законы кашрута", "Исправление мира", "Свадебная церемония", "Изучение Торы", "Субботний покой"],
                    "correct_answer": 2,
                    "explanation": "Тикун Олам означает 'исправление мира' - наша ответственность сделать мир более справедливым и сострадательным",
                    "follow_up": "Какое маленькое действие вы могли бы предпринять сегодня, чтобы 'исправить' часть своего мира?"
                },
                {
                    "question": "Кто был первым еврейским патриархом согласно Торе?",
                    "options": ["Моисей", "Авраам", "Исаак", "Иаков", "Ной", "Адам"],
                    "correct_answer": 1,
                    "explanation": "Авраам был избран Богом стать первым патриархом, начав завет с еврейским народом",
                    "follow_up": "Авраам оставил все знакомое ради неизвестного пути. Когда вы совершали прыжок веры?"
                },
                {
                    "question": "Что означает 'Шалом' помимо просто 'мир'?",
                    "options": ["Война", "Целостность", "Счастье", "Деньги", "Еда", "Работа"],
                    "correct_answer": 1,
                    "explanation": "Шалом происходит от корня, означающего 'целостность' или 'завершенность' - истинный мир приходит из внутренней гармонии",
                    "follow_up": "Где в вашей жизни вы ищете больше целостности и внутреннего мира?"
                }
            ]
            
            # Choose fallback based on language
            if language == "Russian":
                fallback_quizzes = fallback_quizzes_ru
            else:
                fallback_quizzes = fallback_quizzes_en
            
            # SMART deduplication for fallback quizzes
            if user_id and avoid_duplicates and shown_quizzes:
                # Try to find quiz not in shown_quizzes
                available_quizzes = []
                for quiz in fallback_quizzes:
                    quiz_sig = quiz["question"][:150]
                    if not any(quiz_sig in shown for shown in shown_quizzes):
                        available_quizzes.append(quiz)
                
                if available_quizzes:
                    selected_quiz = random.choice(available_quizzes) 
                    logger.info(f"📝 Selected non-duplicate fallback quiz: {selected_quiz['question'][:50]}...")
                else:
                    # All fallback quizzes shown, reset and pick any
                    selected_quiz = random.choice(fallback_quizzes)
                    logger.info(f"🔄 All fallback quizzes shown, reset and selected: {selected_quiz['question'][:50]}...")
                    # Clear shown quizzes to start fresh
                    self.session_manager.update_session(user_id, shown_quizzes=[])
            else:
                selected_quiz = random.choice(fallback_quizzes)
            
            # IMPORTANT: Also track fallback quizzes in deduplication
            if user_id and avoid_duplicates:
                session = self.session_manager.get_session(user_id)
                shown_quizzes = session.get("shown_quizzes", [])
                quiz_signature = selected_quiz["question"][:150] 
                shown_quizzes.append(quiz_signature)
                if len(shown_quizzes) > 20:
                    shown_quizzes = shown_quizzes[-20:]
                self.session_manager.update_session(user_id, shown_quizzes=shown_quizzes)
                logger.info(f"📝 Stored fallback quiz signature, total: {len(shown_quizzes)}")
            
            return selected_quiz
    
    async def handle_quiz_request(self, chat_id: int, user_id: int, user_data: Optional[Dict] = None) -> bool:
        """Complete optimized quiz workflow with loader"""
        session_id = self.analytics.start_session(user_id, "torah_quiz", user_data)
        
        try:
            session = self.session_manager.get_session(user_id, user_data)
            # Priority: Manual language setting > Session language > Auto-detection
            if session.get("manual_language_set", False):
                language = session.get("language", "English")
                logger.info(f"🌐 Using manually set language: {language}")
            elif user_data:
                language = self.session_manager.detect_user_language(user_data)
                self.session_manager.update_session(user_id, language=language)
            else:
                language = session.get("language", "English")
            
            # FIXED: Use user's context correctly for quiz generation
            user_request = session.get("last_user_request")
            current_topic = session.get("current_topic") 
            last_question = session.get("last_question")  # Added this key field
            
            # Determine quiz topic based on user context (prioritize user's actual request)
            if last_question and last_question.strip().lower() not in ['daily torah wisdom', '/start', 'start', 'general wisdom']:
                # User made a specific request, use exact question for quiz topic
                topic = last_question
                logger.info(f"🎯 Quiz using user's specific question: {last_question}")
            elif user_request and user_request.strip().lower() not in ['daily torah wisdom', '/start', 'start']:
                # Fallback to last user request
                topic = user_request
                logger.info(f"🎯 Quiz using user request: {user_request}")
            elif current_topic and current_topic != "None" and current_topic != "Torah wisdom":
                # Use current session topic if it's specific
                topic = current_topic
                logger.info(f"🎯 Quiz using current topic: {current_topic}")
            else:
                # SYSTEM FIX: Generate diverse random topics instead of same default
                recent_topics = session.get("recent_quiz_topics", [])
                topic = QuizTopicGenerator.get_random_topic(exclude_recent=recent_topics[-5:])
                
                # Track recent topics for diversity
                recent_topics.append(topic)
                if len(recent_topics) > 10:  # Keep last 10 topics
                    recent_topics = recent_topics[-10:]
                self.session_manager.update_session(user_id, recent_quiz_topics=recent_topics)
                
                logger.info(f"🎯 Quiz using diverse random topic: {topic}")
            
            # Stage 1: Show thinking loader
            thinking_text = self.session_manager.get_localized_text("preparing_quiz", language)
            thinking_msg = await self.telegram_client.send_message(
                chat_id, thinking_text
            )
            
            # Generate quiz with AI
            self.analytics.log_stage(session_id, "quiz_generation")
            quiz_data = await self.generate_quiz(topic, language, user_id)
            
            # CRITICAL FIX: Shuffle quiz options so correct answer isn't always first
            quiz_data = self._shuffle_quiz_options(quiz_data)
            
            # Clean up loader message
            try:
                if thinking_msg.get("ok") and thinking_msg.get("result"):
                    message_id = thinking_msg["result"]["message_id"]
                    ready_text = self.session_manager.get_localized_text("quiz_ready", language)
                    await self.telegram_client.edit_message_text(
                        chat_id, message_id, ready_text
                    )
                    await asyncio.sleep(1)
            except Exception:
                pass
            
            self.analytics.log_stage(session_id, "quiz_delivery")
            await self.telegram_client.send_poll(
                chat_id,
                quiz_data["question"],
                quiz_data["options"],
                quiz_data["correct_answer"],
                quiz_data["explanation"]
            )
            
            # REMOVED follow-up question, only topic prompt for next quiz
            quiz_prompt_text = "💬 <i>Напишите тему для следующего квиза</i>" if language == "Russian" else "💬 <i>Write a topic for your next quiz</i>"
            
            follow_up_text = f"{quiz_prompt_text}"
            
            more_wisdom_text = self.session_manager.get_localized_text("more_wisdom", language)
            another_quiz_text = self.session_manager.get_localized_text("another_quiz", language)
            main_menu_text = self.session_manager.get_localized_text("main_menu", language)
            
            # Localized quiz sharing button and message
            share_quiz_text = "📤 Поделиться квизом" if language == "Russian" else "📤 Share Quiz"
            share_quiz_message = f"🧠 Интересный квиз по еврейской мудрости: {quiz_data['question'][:50]}... Попробуйте ответить!" if language == "Russian" else f"🧠 Interesting Torah quiz: {quiz_data['question'][:50]}... Try to answer!"
            
            keyboard = {
                "inline_keyboard": [
                    [{"text": more_wisdom_text, "callback_data": "rabbi_wisdom"}],
                    [{"text": another_quiz_text, "callback_data": "torah_quiz"}],
                    [{"text": share_quiz_text, "switch_inline_query": share_quiz_message}],
                    [{"text": main_menu_text, "callback_data": "main_menu"}]
                ]
            }
            
            await self.telegram_client.send_message(chat_id, follow_up_text, keyboard)
            
            # Update session with quiz workflow marker
            self.session_manager.update_session(
                user_id,
                successful_workflows=session["successful_workflows"] + 1,
                completed_workflows=session["completed_workflows"] + 1,
                last_workflow="torah_quiz"
            )
            
            self.analytics.complete_session(session_id, True)
            return True
            
        except Exception as e:
            logger.error(f"Quiz workflow error: {e}")
            self.analytics.complete_session(session_id, False)
            return False

class SmartDonationModule:
    """Production donation system with intelligent triggers and Telegram Stars support"""
    
    def __init__(self, telegram_client: ProductionTelegramClient, session_manager: ProductionSessionManager, analytics: Optional[OptimizedAnalytics] = None):
        self.telegram_client = telegram_client
        self.session_manager = session_manager
        self.analytics = analytics
        
        # Telegram Stars payment configuration
        self.stars_options = {
            100: {"title": "Torah Wisdom Support", "description": "Support Torah learning with 100 Stars"},
            300: {"title": "Enhanced Torah Support", "description": "Enhanced support for Torah wisdom - 300 Stars"},
            500: {"title": "Premium Torah Support", "description": "Premium support for Torah education - 500 Stars"}
        }
        
        self.donation_messages = {
            "English": [
                {
                    "text": "🌟 Enjoying your Torah learning journey?",
                    "wisdom": "\"The world stands on three things: Torah, service, and loving kindness\" - Pirkei Avot 1:2"
                },
                {
                    "text": "💖 Help us spread Jewish wisdom worldwide!",
                    "wisdom": "\"Much have I learned from teachers, more from colleagues, most from students\" - Taanit 7a"
                },
                {
                    "text": "🙏 Your support preserves ancient wisdom",
                    "wisdom": "\"Who is rich? One satisfied with their portion\" - Pirkei Avot 4:1"
                }
            ],
            "Russian": [
                {
                    "text": "🌟 Нравится ваше путешествие в изучении Торы?",
                    "wisdom": "\"Мир стоит на трех вещах: Торе, служении и добрых делах\" - Пиркей Авот 1:2"
                },
                {
                    "text": "💖 Помогите распространить еврейскую мудрость по всему миру!",
                    "wisdom": "\"Много я изучил у учителей, больше у коллег, но больше всего у учеников\" - Таанит 7а"
                },
                {
                    "text": "🙏 Ваша поддержка сохраняет древнюю мудрость",
                    "wisdom": "\"Кто богат? Тот, кто доволен своей долей\" - Пиркей Авот 4:1"
                }
            ],
            "Hebrew": [
                {
                    "text": "🌟 נהנים מהמסע שלכם בלימוד התורה?",
                    "wisdom": "\"על שלושה דברים העולם עומד: על התורה ועל העבודה ועל גמילות חסדים\" - פרקי אבות א:ב"
                },
                {
                    "text": "💖 עזרו לנו להפיץ חכמה יהודית ברחבי העולם!",
                    "wisdom": "\"הרבה למדתי מרבותי, יותר מחברי, ויותר מכולם מתלמידי\" - תענית ז'"
                },
                {
                    "text": "🙏 התמיכה שלכם משמרת חכמה עתיקה",
                    "wisdom": "\"איזהו עשיר? השמח בחלקו\" - פרקי אבות ד:א"
                }
            ]
        }
    
    def should_show_donation(self, user_id: int) -> bool:
        """Smart donation trigger logic"""
        session = self.session_manager.get_session(user_id)
        
        successful_workflows = session.get("successful_workflows", 0)
        last_donation = session.get("last_donation", 0)
        time_since_last = time.time() - last_donation
        
        # Show if: 2+ successful workflows AND 10+ minutes since last donation
        return successful_workflows >= 2 and time_since_last > 600
    
    async def show_donation(self, chat_id: int, user_id: int):
        """Display smart donation prompt with localization"""
        session = self.session_manager.get_session(user_id)
        language = session.get("language", "English")
        
        # Get localized messages or fallback to English
        messages = self.donation_messages.get(language, self.donation_messages["English"])
        donation_data = random.choice(messages)
        
        # Localized footer messages
        footer_messages = {
            "English": "🤝 Every contribution helps preserve and share Torah wisdom with seekers worldwide.",
            "Russian": "🤝 Каждый вклад помогает сохранить и поделиться мудростью Торы с ищущими по всему миру.",
            "Hebrew": "🤝 כל תרומה עוזרת לשמר ולחלוק חכמת תורה עם מחפשים ברחבי העולם."
        }
        
        footer = footer_messages.get(language, footer_messages["English"])
        
        # Combine image and text in one message
        full_text = f"""{donation_data["text"]}

💎 <i>{donation_data["wisdom"]}</i>

{footer}"""
        
        # Localized button texts with Jewish spirit and Stars support
        button_texts = {
            "English": {
                "stars_100": "⭐ 100 Stars",
                "stars_300": "⭐ 300 Stars", 
                "stars_500": "⭐ 500 Stars",
                "support_ton": "🪙 Give Tzedakah (TON)",
                "share": "🤝 Share with Friends", 
                "continue": "🔄 Continue Learning",
                "share_text": "Join me in discovering ancient Torah wisdom that transforms modern life! 📖✨"
            },
            "Russian": {
                "stars_100": "⭐ 100 Stars",
                "stars_300": "⭐ 300 Stars", 
                "stars_500": "⭐ 500 Stars",
                "support_ton": "🪙 Дать Цдаку (TON)",
                "share": "🤝 Поделиться с друзьями",
                "continue": "🔄 Продолжить обучение",
                "share_text": "Присоединяйтесь ко мне в изучении древней мудрости Торы, которая меняет современную жизнь! 📖✨"
            },
            "Hebrew": {
                "stars_100": "⭐ 100 Stars",
                "stars_300": "⭐ 300 Stars", 
                "stars_500": "⭐ 500 Stars",
                "support_ton": "🪙 לתת צדקה (TON)",
                "share": "🤝 שתף עם חברים",
                "continue": "🔄 המשך ללמוד",
                "share_text": "הצטרפו אלי לגילוי חכמת תורה עתיקה המשנה את החיים המודרניים! 📖✨"
            }
        }
        
        buttons = button_texts.get(language, button_texts["English"])
        
        keyboard = {
            "inline_keyboard": [
                [{"text": buttons["stars_100"], "callback_data": "stars_100"}],
                [{"text": buttons["stars_300"], "callback_data": "stars_300"}, 
                 {"text": buttons["stars_500"], "callback_data": "stars_500"}],
                [{"text": buttons["support_ton"], "url": "https://tonviewer.com/EQBi_54Asf14msdW1xwKLuAHp5YBouFC7QKu_WZUs4oFnmJm"}],
                [{"text": buttons["share"], "switch_inline_query": buttons["share_text"]}],
                [{"text": buttons["continue"], "callback_data": "main_menu"}]
            ]
        }
        
        # Send rabbi support image with combined text AND buttons
        try:
            await self.telegram_client.send_photo_file(
                chat_id=chat_id,
                file_path="src/images/rabbi_support.png",
                caption=full_text,
                reply_markup=keyboard
            )
        except Exception as e:
            logger.warning(f"Could not send support image: {e}")
            # Fallback to text-only message with buttons if image fails
            await self.telegram_client.send_message(chat_id, full_text, keyboard)
        
        # Update donation tracking
        self.session_manager.update_session(
            user_id,
            last_donation=time.time(),
            donation_count=self.session_manager.get_session(user_id).get("donation_count", 0) + 1
        )
    
    async def send_stars_invoice(self, chat_id: int, user_id: int, stars_amount: int):
        """Send Telegram Stars invoice"""
        try:
            if stars_amount not in self.stars_options:
                logger.error(f"Invalid stars amount: {stars_amount}")
                return False
            
            session = self.session_manager.get_session(user_id)
            language = session.get("language", "English")
            
            # Get localized text for the invoice
            option = self.stars_options[stars_amount]
            
            # Rabbi-style titles and descriptions with wisdom and humor
            localized_content = {
                "English": {
                    "title": f"✨ Torah Wisdom Support - {stars_amount} Stars",
                    "description": f"Like King Solomon said: 'Cast your bread upon the waters...' Today, cast {stars_amount} Stars to help spread ancient wisdom to modern hearts! 📚⭐"
                },
                "Russian": {
                    "title": f"✨ Поддержка мудрости Торы - {stars_amount} Stars",
                    "description": f"Как говорил царь Соломон: 'Отпускай хлеб твой по водам...' Сегодня отправьте {stars_amount} Stars, чтобы помочь распространить древнюю мудрость в современные сердца! 📚⭐"
                },
                "Hebrew": {
                    "title": f"✨ תמיכה בחכמת התורה - {stars_amount} Stars",
                    "description": f"כמו שאמר המלך שלמה: 'שלח לחמך על פני המים...' היום שלחו {stars_amount} Stars כדי לעזור להפיץ חכמה עתיקה ללבבות מודרניים! 📚⭐"
                }
            }
            
            content = localized_content.get(language, localized_content["English"])
            
            # Create invoice data for Telegram Stars
            invoice_data = {
                "chat_id": chat_id,
                "title": content["title"],
                "description": content["description"],
                "payload": f"stars_donation_{stars_amount}_{user_id}_{int(time.time())}",  # Unique payload
                "provider_token": "",  # Empty for Telegram Stars
                "currency": "XTR",  # Telegram Stars currency
                "prices": [{"label": f"{stars_amount} Stars", "amount": stars_amount}],
                "start_parameter": f"stars_{stars_amount}",
                "need_name": False,
                "need_phone_number": False,
                "need_email": False,
                "need_shipping_address": False,
                "send_phone_number_to_provider": False,
                "send_email_to_provider": False,
                "is_flexible": False
            }
            
            # Send invoice via Telegram API
            response = await self.telegram_client._make_request("sendInvoice", invoice_data)
            
            if response and response.get("ok"):
                logger.info(f"✅ Stars invoice sent: {stars_amount} stars to user {user_id}")
                return True
            else:
                logger.error(f"❌ Failed to send stars invoice: {response}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending stars invoice: {e}")
            return False
    
    async def handle_pre_checkout_query(self, pre_checkout_query):
        """Handle pre-checkout query for Telegram Stars"""
        try:
            query_id = pre_checkout_query["id"]
            currency = pre_checkout_query.get("currency")
            total_amount = pre_checkout_query.get("total_amount")
            invoice_payload = pre_checkout_query.get("invoice_payload", "")
            
            # Validate Stars payment
            if currency == "XTR" and invoice_payload.startswith("stars_donation_"):
                # Extract amount from payload
                parts = invoice_payload.split("_")
                if len(parts) >= 3:
                    expected_amount = int(parts[2])
                    if total_amount == expected_amount and expected_amount in self.stars_options:
                        # Approve the payment
                        await self.telegram_client._make_request("answerPreCheckoutQuery", {
                            "pre_checkout_query_id": query_id,
                            "ok": True
                        })
                        logger.info(f"✅ Pre-checkout approved: {total_amount} stars")
                        return True
            
            # Reject invalid payment
            await self.telegram_client._make_request("answerPreCheckoutQuery", {
                "pre_checkout_query_id": query_id,
                "ok": False,
                "error_message": "Invalid payment amount or currency"
            })
            logger.warning(f"❌ Pre-checkout rejected: {currency} {total_amount}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Pre-checkout query error: {e}")
            return False
    
    async def handle_successful_payment(self, successful_payment, user_id: int, chat_id: int):
        """Handle successful Telegram Stars payment"""
        try:
            currency = successful_payment.get("currency")
            total_amount = successful_payment.get("total_amount")
            invoice_payload = successful_payment.get("invoice_payload", "")
            telegram_payment_charge_id = successful_payment.get("telegram_payment_charge_id")
            
            if currency == "XTR" and invoice_payload.startswith("stars_donation_"):
                # Parse payment details
                parts = invoice_payload.split("_")
                stars_amount = int(parts[2]) if len(parts) >= 3 else total_amount
                
                # Update user session with successful donation
                session = self.session_manager.get_session(user_id)
                language = session.get("language", "English")
                
                self.session_manager.update_session(
                    user_id,
                    donation_count=session.get("donation_count", 0) + 1,
                    stars_donated=session.get("stars_donated", 0) + stars_amount,
                    last_donation=time.time(),
                    last_stars_payment_id=telegram_payment_charge_id
                )
                
                # Rabbi-style thank you messages with wisdom and warmth
                thank_you_messages = {
                    "English": f"🌟 <b>Ah, my dear friend! Your heart shines brighter than {stars_amount} Stars!</b>\n\n🧙‍♂️ <i>You know, the Talmud says: \"When someone gives even a small coin to charity, they become a partner with the Almighty.\" And you? You've just become a business partner with the Creator of the Universe! Not bad for a Tuesday!</i>\n\n✨ Your {stars_amount} Stars will help Torah wisdom reach souls across the globe - from Brooklyn to Bangkok, from Miami to Moscow!\n\n🙏 <b>May your generosity return to you sevenfold, your coffee always be the perfect temperature, and your WiFi never disconnect during important calls!</b>\n\n<i>\"Cast your bread upon the waters, for you will find it after many days\" - Ecclesiastes 11:1</i>\n\n💫 <i>P.S. The angels are updating their books right now. ⭐</i>",
                    "Russian": f"🌟 <b>Ах, мой дорогой друг! Ваше сердце сияет ярче {stars_amount} звёзд!</b>\n\n🧙‍♂️ <i>Знаете, Талмуд говорит: \"Когда кто-то жертвует даже маленькую монетку, он становится партнёром Всевышнего.\" А вы? Вы только что стали деловым партнёром Творца Вселенной! Неплохо для вторника!</i>\n\n✨ Ваши {stars_amount} Stars помогут мудрости Торы достичь душ по всему миру - от Бруклина до Бангкока, от Майами до Москвы!\n\n🙏 <b>Пусть ваша щедрость вернётся к вам семикратно, кофе всегда будет идеальной температуры, а интернет никогда не отключится во время важных звонков!</b>\n\n<i>\"Отпускай хлеб твой по водам, потому что по прошествии многих дней опять найдешь его\" - Екклесиаст 11:1</i>\n\n💫 <i>P.S. Ангелы прямо сейчас обновляют свои книги. ⭐</i>",
                    "Hebrew": f"🌟 <b>אח, ידידי היקר! הלב שלך זוהר יותר מ-{stars_amount} כוכבים!</b>\n\n🧙‍♂️ <i>אתם יודעים, התלמוד אומר: \"כשמישהו נותן אפילו מטבע קטן לצדקה, הוא נעשה שותף עם הקב\"ה.\" ואתם? זה עתה הפכתם לשותפים עסקיים עם בורא העולם! לא רע ליום שלישי!</i>\n\n✨ ה-{stars_amount} Stars שלכם יעזרו לחכמת התורה להגיע לנשמות ברחבי העולם - מברוקלין לבנגקוק, ממיאמי למוסקבה!\n\n🙏 <b>יהי רצון שהנדיבות שלכם תחזור אליכם פי שבעה, הקפה תמיד יהיה בטמפרטורה המושלמת, והאינטרנט אף פעם לא ינותק בזמן שיחות חשובות!</b>\n\n<i>\"שלח לחמך על פני המים כי ברב הימים תמצאנו\" - קהלת יא:א</i>\n\n💫 <i>נ.ב. המלאכים מעדכנים את הספרים שלהם עכשיו. ⭐</i>"
                }
                
                thank_you_text = thank_you_messages.get(language, thank_you_messages["English"])
                
                await self.telegram_client.send_message(chat_id, thank_you_text, parse_mode="HTML")
                
                # Log successful donation and update analytics
                logger.info(f"💰 STARS DONATION: User {user_id} donated {stars_amount} stars (ID: {telegram_payment_charge_id})")
                
                # Analytics tracking
                if self.analytics:
                    session_id = f"stars_donation_{user_id}_{int(time.time())}"
                    self.analytics.start_session(user_id, "stars_donation", {"stars_amount": stars_amount})
                    self.analytics.complete_session(session_id, True)
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Successful payment handling error: {e}")
            return False

class ProductionStartupScreen:
    """Optimized startup screen"""
    
    def __init__(self, telegram_client: ProductionTelegramClient):
        self.telegram_client = telegram_client
        # Cache welcome messages to avoid recreating them each time
        self._welcome_messages_cache = None
        # Cache welcome photo to avoid reading file each time
        self._welcome_photo_cache = None
    
    def _get_welcome_messages_cache(self):
        """Get cached welcome messages"""
        if self._welcome_messages_cache is None:
            self._welcome_messages_cache = {
                "Russian": {
                "text": """👋 <b>Шалом! Я ваш помощник-раввин.</b>

Поделюсь теплыми мудростями из еврейской традиции, расскажу истории наших мудрецов и помогу понять, как древние учения применимы к современной жизни. Есть вопросы о семье, работе, вере или учебе? Каждый разговор - возможность узнать что-то важное.

<b>Выберите что интересует:</b> 📖 Мудрость Раввина • 🧠 Викторина • 💝 Поддержать • 🌐 Язык""",
                "buttons": [
                    [{"text": "📖 Мудрость Раввина", "callback_data": "rabbi_wisdom"}],
                    [{"text": "🧠 Викторина по Торе", "callback_data": "torah_quiz"}],
                    [{"text": "🎮 Игра Shabbat Runner", "callback_data": "mini_game"}],
                    [{"text": "💝 Поддержать проект", "callback_data": "donation"}],
                    [{"text": "🌐 Язык", "callback_data": "language_menu"}]
                ]
            },
            "English": {
                "text": """👋 <b>Shalom! I'm your Rabbi assistant.</b>

I'll share warm wisdom from Jewish tradition, tell stories of our sages, and help you discover how ancient teachings apply to modern life. Whether you have questions about family, work, faith, or study - every conversation is a chance to learn something meaningful.

<b>Choose what interests you:</b> 📖 Rabbi Wisdom • 🧠 Torah Quiz • 💝 Support Project • 🌐 Language""",
                "buttons": [
                    [{"text": "📖 Rabbi Wisdom", "callback_data": "rabbi_wisdom"}],
                    [{"text": "🧠 Torah Quiz", "callback_data": "torah_quiz"}],
                    [{"text": "🎮 Shabbat Game", "callback_data": "mini_game"}],
                    [{"text": "💝 Support Project", "callback_data": "donation"}],
                    [{"text": "🌐 Language", "callback_data": "language_menu"}]
                ]
            },
            "Hebrew": {
                "text": """👋 <b>שלום! אני הרב העוזר שלכם.</b>

אשתף איתכם חכמות חמות מהמסורת היהודית, אספר סיפורי חכמינו ואעזור לכם להבין איך תורות עתיקות רלוונטיות לחיים המודרניים. יש לכם שאלות על משפחה, עבודה, אמונה או לימוד? כל שיחה היא הזדמנות ללמוד משהו משמעותי.

<b>בחרו מה מעניין אתכם:</b> 📖 חכמת הרב • 🧠 חידון תורה • 💝 תמיכה • 🌐 שפה""",
                "buttons": [
                    [{"text": "📖 חכמת הרב", "callback_data": "rabbi_wisdom"}],
                    [{"text": "🧠 חידון תורה", "callback_data": "torah_quiz"}],
                    [{"text": "🎮 משחק שבת", "callback_data": "mini_game"}],
                    [{"text": "💝 תמיכה בפרויקט", "callback_data": "donation"}],
                    [{"text": "🌐 שפה", "callback_data": "language_menu"}]
                ]
            },
            "Spanish": {
                "text": """👋 <b>¡Shalom! Soy tu asistente rabino.</b>

Compartiré sabiduría cálida de la tradición judía, te contaré historias de nuestros sabios y te ayudaré a descubrir cómo las enseñanzas antiguas se aplican a la vida moderna. ¿Tienes preguntas sobre familia, trabajo, fe o estudio? Cada conversación es una oportunidad de aprender algo significativo.

<b>Elige lo que te interesa:</b> 📖 Sabiduría del Rabino • 🧠 Quiz de Torá • 💝 Apoyar • 🌐 Idioma""",
                "buttons": [
                    [{"text": "📖 Sabiduría del Rabino", "callback_data": "rabbi_wisdom"}],
                    [{"text": "🧠 Quiz de Torá", "callback_data": "torah_quiz"}],
                    [{"text": "🎮 Juego de Shabat", "callback_data": "mini_game"}],
                    [{"text": "💝 Apoyar Proyecto", "callback_data": "donation"}],
                    [{"text": "🌐 Idioma", "callback_data": "language_menu"}]
                ]
            },
            "French": {
                "text": """👋 <b>Shalom! Je suis votre assistant rabbin.</b>

Je partagerai avec vous une sagesse chaleureuse de la tradition juive, vous raconterai les histoires de nos sages et vous aiderai à découvrir comment les enseignements anciens s'appliquent à la vie moderne. Vous avez des questions sur la famille, le travail, la foi ou les études? Chaque conversation est une opportunité d'apprendre quelque chose de significatif.

<b>Choisissez ce qui vous intéresse:</b> 📖 Sagesse du Rabbin • 🧠 Quiz Torah • 💝 Soutenir • 🌐 Langue""",
                "buttons": [
                    [{"text": "📖 Sagesse du Rabbin", "callback_data": "rabbi_wisdom"}],
                    [{"text": "🧠 Quiz Torah", "callback_data": "torah_quiz"}],
                    [{"text": "🎮 Jeu de Sabbat", "callback_data": "mini_game"}],
                    [{"text": "💝 Soutenir le Projet", "callback_data": "donation"}],
                    [{"text": "🌐 Langue", "callback_data": "language_menu"}]
                ]
            },
            "German": {
                "text": """👋 <b>Shalom! Ich bin Ihr Rabbiner-Assistent.</b>

Ich teile warme Weisheiten aus der jüdischen Tradition mit Ihnen, erzähle Geschichten unserer Weisen und helfe Ihnen zu entdecken, wie alte Lehren im modernen Leben anwendbar sind. Haben Sie Fragen zu Familie, Arbeit, Glauben oder Studium? Jedes Gespräch ist eine Gelegenheit, etwas Bedeutsames zu lernen.

<b>Wählen Sie was Sie interessiert:</b> 📖 Rabbiner Weisheit • 🧠 Torah Quiz • 💝 Unterstützen • 🌐 Sprache""",
                "buttons": [
                    [{"text": "📖 Rabbiner Weisheit", "callback_data": "rabbi_wisdom"}],
                    [{"text": "🧠 Torah Quiz", "callback_data": "torah_quiz"}],
                    [{"text": "🎮 Sabbat Spiel", "callback_data": "mini_game"}],
                    [{"text": "💝 Projekt Unterstützen", "callback_data": "donation"}],
                    [{"text": "🌐 Sprache", "callback_data": "language_menu"}]
                ]
            }
        }
        return self._welcome_messages_cache
    
    async def show_main_menu(self, chat_id: int, user_id: Optional[int] = None, user_data: Optional[Dict] = None):
        """Display localized main menu based on user language"""
        # Get user language preference
        if user_id is not None:
            session = ProductionSessionManager.get_session(user_id, user_data)
            language = session.get("language", "English")
        else:
            language = ProductionSessionManager.detect_user_language(user_data)
        
        # Get cached welcome messages
        welcome_messages = self._get_welcome_messages_cache()
        
        # Get localized content or fallback to English
        content = welcome_messages.get(language, welcome_messages["English"])
        
        keyboard = {"inline_keyboard": content["buttons"]}
        
        # Send welcome photo with message
        try:
            # Cache photo data for faster subsequent loads
            if self._welcome_photo_cache is None:
                try:
                    with open("rabbi_welcome.png", "rb") as photo_file:
                        self._welcome_photo_cache = photo_file.read()
                        logger.info("📸 Welcome photo cached for faster loading")
                except FileNotFoundError:
                    logger.warning("📸 Welcome photo not found - using text fallback")
                    self._welcome_photo_cache = False  # Mark as unavailable
            
            if self._welcome_photo_cache:
                data = {
                    "chat_id": chat_id,
                    "caption": content["text"],
                    "parse_mode": "HTML",
                    "reply_markup": json.dumps(keyboard)
                }
                if not self.telegram_client.session:
                    self.telegram_client.session = httpx.AsyncClient(timeout=30.0)
                
                # Use BytesIO for proper file handling
                from io import BytesIO
                photo_bytes = self._welcome_photo_cache if isinstance(self._welcome_photo_cache, bytes) else b""
                photo_io = BytesIO(photo_bytes)
                photo_io.name = "rabbi_welcome.png"
                
                response = await self.telegram_client.session.post(
                    f"{self.telegram_client.base_url}/sendPhoto", 
                    data=data, 
                    files={"photo": photo_io}
                )
                result = response.json()
                
                if result.get("ok"):
                    logger.info(f"📸 Welcome photo sent to {chat_id}")
                    return
                else:
                    logger.warning(f"Photo send failed: {result}")
            else:
                # Photo not available, use text fallback
                logger.info("📸 Photo cache unavailable, using text fallback")
                    
        except Exception as e:
            logger.warning(f"Welcome photo error: {e}")
        
        # Fallback to text message if photo fails
        await self.telegram_client.send_message(chat_id, content["text"], keyboard)

class LanguageModule:
    """Optimized language selection"""
    
    def __init__(self, telegram_client: ProductionTelegramClient, session_manager: ProductionSessionManager):
        self.telegram_client = telegram_client
        self.session_manager = session_manager
    
    async def show_language_menu(self, chat_id: int, user_id: Optional[int] = None, user_data: Optional[Dict] = None):
        """Show language options with localization"""
        # Get current user language
        if user_id:
            session = self.session_manager.get_session(user_id, user_data)
            current_language = session.get("language", "English")
        else:
            current_language = self.session_manager.detect_user_language(user_data) if user_data else "English"
        
        # Localized menu headers
        language_headers = {
            "English": "🌐 <b>Choose Language</b>\n\n<i>Select your preferred language:</i>",
            "Russian": "🌐 <b>Выберите язык</b>\n\n<i>Выберите предпочитаемый язык:</i>",
            "Hebrew": "🌐 <b>בחירת שפה</b>\n\n<i>בחרו את השפה המועדפת עליכם:</i>",
            "Spanish": "🌐 <b>Elegir idioma</b>\n\n<i>Selecciona tu idioma preferido:</i>",
            "French": "🌐 <b>Choisir la langue</b>\n\n<i>Sélectionnez votre langue préférée:</i>",
            "German": "🌐 <b>Sprache wählen</b>\n\n<i>Wählen Sie Ihre bevorzugte Sprache:</i>"
        }
        
        # Localized back buttons
        back_buttons = {
            "English": "🔙 Back",
            "Russian": "🔙 Назад",
            "Hebrew": "🔙 חזור",
            "Spanish": "🔙 Atrás",
            "French": "🔙 Retour",
            "German": "🔙 Zurück"
        }
        
        header_text = language_headers.get(current_language, language_headers["English"])
        back_text = back_buttons.get(current_language, back_buttons["English"])
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "🇺🇸 English", "callback_data": "lang_en"}, {"text": "🇷🇺 Русский", "callback_data": "lang_ru"}],
                [{"text": "🇮🇱 עברית", "callback_data": "lang_he"}, {"text": "🇪🇸 Español", "callback_data": "lang_es"}],
                [{"text": "🇫🇷 Français", "callback_data": "lang_fr"}, {"text": "🇩🇪 Deutsch", "callback_data": "lang_de"}],
                [{"text": back_text, "callback_data": "main_menu"}]
            ]
        }
        
        await self.telegram_client.send_message(
            chat_id,
            header_text,
            keyboard
        )
    
    async def set_language(self, chat_id: int, user_id: int, lang_code: str):
        """Set user language"""
        languages = {
            "en": "English", "ru": "Russian", "he": "Hebrew",
            "es": "Spanish", "fr": "French", "de": "German"
        }
        
        language_name = languages.get(lang_code, "English")
        self.session_manager.update_session(user_id, language=language_name, manual_language_set=True)
        
        # Localized confirmation messages
        confirmation_messages = {
            "English": f"✅ Language set to <b>{language_name}</b>",
            "Russian": f"✅ Язык установлен: <b>Русский</b>",
            "Hebrew": f"✅ השפה הוגדרה: <b>עברית</b>",
            "Spanish": f"✅ Idioma establecido: <b>Español</b>",
            "French": f"✅ Langue définie: <b>Français</b>",
            "German": f"✅ Sprache eingestellt: <b>Deutsch</b>"
        }
        
        confirmation_text = confirmation_messages.get(language_name, confirmation_messages["English"])
        
        await self.telegram_client.send_message(
            chat_id,
            confirmation_text
        )
        
        # Return to main menu
        await asyncio.sleep(1)
        startup = ProductionStartupScreen(self.telegram_client)
        await startup.show_main_menu(chat_id, user_id)

class TorahBotFinal:
    """Final production Torah Bot with centralized language management"""
    
    def __init__(self):
        self.telegram_client = ProductionTelegramClient(TOKEN)
        self.analytics = OptimizedAnalytics(self.telegram_client)
        self.session_manager = ProductionSessionManager(self.analytics)
        
        # Initialize optimized modules
        self.startup_screen = ProductionStartupScreen(self.telegram_client)
        self.rabbi_module = OptimizedRabbiModule(self.telegram_client, self.session_manager, self.analytics)
        
        # Newsletter system attributes
        self.admin_commands: Optional[Any] = None
        self.newsletter_manager: Optional[Any] = None  # Direct reference for ServiceContainer
        self.newsletter_initialized = False
        self.quiz_module = OptimizedQuizModule(self.telegram_client, self.session_manager, self.analytics)
        self.donation_module = SmartDonationModule(self.telegram_client, self.session_manager)
        self.language_module = LanguageModule(self.telegram_client, self.session_manager)
        
        # Initialize mini game module (safe import)
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
            from src.mini_game.backend.game_module import MiniGameModule
            self.game_module = MiniGameModule(self.telegram_client, self.session_manager, self.analytics)
            self.mini_game_module = self.game_module  # Backward compatibility
            logger.info("🎮 Mini game module initialized")
        except ImportError as e:
            self.game_module = None
            self.mini_game_module = None
            logger.warning(f"🎮 Mini game module not available: {e}")
    
    async def initialize(self):
        """Initialize the bot for production mode"""
        # Initialize newsletter system if available
        if NEWSLETTER_AVAILABLE and newsletter_manager and AdminCommands:
            try:
                await newsletter_manager.initialize()
                self.newsletter_manager = newsletter_manager  # Store for ServiceContainer
                self.admin_commands = AdminCommands(self.telegram_client, newsletter_manager)
                self.newsletter_initialized = True
                logger.info("📧 Newsletter system initialized successfully")
                
                # ВНУТРЕННИЙ SCHEDULER ОТКЛЮЧЕН - ИСПОЛЬЗУЕМ GITHUB ACTIONS
                # from src.torah_bot.scheduled_broadcast import ScheduledBroadcastSystem
                # self.scheduler = ScheduledBroadcastSystem(self.telegram_client)
                # asyncio.create_task(self.scheduler.start_scheduler())
                logger.info("🔒 Internal scheduler DISABLED - using GitHub Actions external scheduler")
            except Exception as e:
                logger.error(f"Newsletter initialization failed: {e}")
                self.newsletter_initialized = False
                self.admin_commands = None
    
    async def initialize_webhook_mode(self):
        """Initialize bot for webhook mode only - no polling"""
        # CRITICAL FIX: Force AdminCommands initialization for webhook mode
        try:
            # Initialize newsletter system
            if newsletter_manager:
                await newsletter_manager.initialize()
                self.newsletter_manager = newsletter_manager  # Store for ServiceContainer
                logger.info("📧 Newsletter manager initialized for webhook mode")
                
            # Force create AdminCommands regardless of NEWSLETTER_AVAILABLE flag
            if AdminCommands:
                self.admin_commands = AdminCommands(self.telegram_client, newsletter_manager)
                self.newsletter_initialized = True
                logger.info("✅ AdminCommands initialized for webhook mode - admin access enabled")
            else:
                logger.error("❌ AdminCommands not available - admin access disabled")
                self.newsletter_initialized = False
                
        except Exception as e:
            logger.error(f"Newsletter/Admin initialization failed: {e}")
            self.newsletter_initialized = False
            self.admin_commands = None
        
        # Initialize game module menu button for webhook
        if self.game_module:
            try:
                await asyncio.sleep(1)  # Wait for initialization
                result = await self.game_module._setup_native_menu_button(None)
                if result:
                    logger.info("🎮 Menu button initialized for webhook mode")
                else:
                    logger.warning("⚠️ Menu button initialization returned False")
            except Exception as e:
                logger.error(f"❌ Menu button initialization failed: {e}")
        
        logger.info("📡 Bot initialized for webhook mode - ready for Telegram requests")
    
    async def cleanup(self):
        """Cleanup resources gracefully"""
        logger.info("🔄 Cleaning up Torah Bot resources...")
        try:
            # Session manager cleanup - safe fallback
            logger.info("🧹 Session manager cleanup completed")
            if hasattr(self.analytics, 'cleanup_stale_sessions'):
                self.analytics.cleanup_stale_sessions()
            logger.info("✅ Torah Bot cleanup completed")
        except Exception as e:
            logger.error(f"❌ Cleanup error: {e}")
    
    async def run_production_mode(self):
        """Run the bot in production mode with polling loop"""
        offset = 0
        error_count = 0
        max_errors = 10
        
        logger.info("🚀 Starting production polling loop...")
        
        # Main polling loop
        metrics_counter = 0
        while True:
            try:
                # Cleanup analytics periodically
                self.analytics.cleanup_stale_sessions()
                
                # Generate DAILY business metrics summary every 2880 iterations (every ~24 hours with 30s timeout)
                metrics_counter += 1
                if metrics_counter % 2880 == 0:
                    self.analytics.smart_logger.business_metrics_summary()
                
                # Get updates
                result = await self.telegram_client.get_updates(offset=offset, timeout=30)
                
                if not result.get("ok"):
                    error_count += 1
                    logger.error(f"API Error ({error_count}/{max_errors}): {result}")
                    
                    if error_count >= max_errors:
                        logger.error("Too many consecutive errors, restarting...")
                        await asyncio.sleep(60)
                        error_count = 0
                        continue
                    
                    await asyncio.sleep(5)
                    continue
                
                # Reset error count on success
                error_count = 0
                
                # Process updates
                if result.get("result"):
                    for update in result["result"]:
                        offset = update["update_id"] + 1
                        
                        try:
                            if "callback_query" in update:
                                await self.handle_callback(update["callback_query"])
                            elif "message" in update:
                                await self.handle_message(update["message"])
                            elif "pre_checkout_query" in update:
                                await self.donation_module.handle_pre_checkout_query(update["pre_checkout_query"])
                            elif "message" in update and "successful_payment" in update["message"]:
                                payment_data = update["message"]["successful_payment"]
                                chat_id = update["message"]["chat"]["id"]
                                user_id = update["message"]["from"]["id"]
                                await self.donation_module.handle_successful_payment(payment_data, user_id, chat_id)
                        except Exception as e:
                            logger.error(f"Update processing error: {e}")
                            continue
                            
            except KeyboardInterrupt:
                logger.info("Bot stopped by user")
                break
            except Exception as e:
                error_count += 1
                logger.error(f"Main loop error ({error_count}): {e}")
                
                if error_count >= max_errors:
                    logger.error("Too many errors, restarting...")
                    await asyncio.sleep(60)
                    error_count = 0
                else:
                    await asyncio.sleep(1)

    def ensure_language_consistency(self, user_id: int, user_data: Optional[Dict] = None) -> str:
        """Centralized language management - ensures all modules use same language"""
        session = self.session_manager.get_session(user_id, user_data)
        
        # Force re-detection if user_data is fresh (new interaction)
        if user_data and "language_code" in user_data:
            detected_language = self.session_manager.detect_user_language(user_data)
            if session.get("language") != detected_language and not session.get("manual_language_set", False):
                # Update language if it's different and wasn't manually set
                self.session_manager.update_session(user_id, language=detected_language)
                session = self.session_manager.get_session(user_id)
        
        return session.get("language", "English")
    
    async def handle_callback(self, callback_query: Dict[str, Any]):
        """Optimized callback handling with language consistency"""
        callback_id = callback_query["id"]
        callback_data = callback_query["data"]
        chat_id = callback_query["message"]["chat"]["id"]  # ✅ ИСПРАВЛЕНО: правильный chat_id
        user_id = callback_query["from"]["id"]
        user_data = callback_query["from"]
        
        # Always answer callback first
        await self.telegram_client.answer_callback_query(callback_id)
        
        # Ensure language consistency across all modules
        language = self.ensure_language_consistency(user_id, user_data)
        
        try:
            # Route to appropriate module
            if callback_data == "main_menu":
                await self.startup_screen.show_main_menu(chat_id, user_id, user_data)
            elif callback_data == "rabbi_wisdom":
                await self.rabbi_module.handle_wisdom_request(chat_id, user_id, user_data=user_data)
            elif callback_data == "torah_quiz":
                # CRITICAL FIX: Handle repeated quiz requests properly
                session = self.session_manager.get_session(user_id, user_data)
                last_workflow = session.get("last_workflow", "")
                current_topic = session.get("current_topic")
                
                # If this is a repeated quiz request (last workflow was also quiz)
                if last_workflow == "torah_quiz":
                    # Clear current_topic to force random topic selection
                    self.session_manager.update_session(user_id, current_topic=None)
                    logger.info(f"🔄 REPEATED QUIZ: Cleared topic for user {user_id}, will use random topic")
                else:
                    # First quiz after wisdom - keep current_topic
                    logger.info(f"🎯 FIRST QUIZ: User {user_id} topic: '{current_topic}' from previous workflow: {last_workflow}")
                
                await self.quiz_module.handle_quiz_request(chat_id, user_id, user_data)
            elif callback_data == "donation":
                await self.donation_module.show_donation(chat_id, user_id)
            elif callback_data.startswith("stars_"):
                # Handle Stars donation
                stars_amount = int(callback_data.replace("stars_", ""))
                await self.donation_module.send_stars_invoice(chat_id, user_id, stars_amount)
            elif callback_data == "language_menu":
                await self.language_module.show_language_menu(chat_id, user_id, user_data)
            elif callback_data.startswith("lang_"):
                lang_code = callback_data.split("_")[1]
                await self.language_module.set_language(chat_id, user_id, lang_code)
            elif callback_data == "mini_game":
                # Handle mini game request
                if self.mini_game_module:
                    await self.mini_game_module.handle_game_command(chat_id, user_id, user_data)
                else:
                    await self.telegram_client.send_message(chat_id, "🎮 Game temporarily unavailable")
            elif callback_data == "game_stats":
                # Handle game stats request
                if self.mini_game_module:
                    await self.mini_game_module.handle_game_stats(chat_id, user_id, user_data)
                else:
                    await self.telegram_client.send_message(chat_id, "📊 Stats temporarily unavailable")
            else:
                logger.warning(f"Unknown callback: {callback_data}")
            
            # Removed automatic donation trigger - only manual donations via button
                    
        except Exception as e:
            logger.error(f"Callback handling error: {e}")
    
    async def handle_message(self, message: Dict[str, Any]):
        """Optimized message handling with language consistency"""
        text = message.get("text", "")
        chat_id = message["chat"]["id"]
        user_id = message["from"]["id"]
        user_data = message["from"]
        
        # Ensure language consistency at entry point
        language = self.ensure_language_consistency(user_id, user_data)
        
        # Handle admin commands first
        if (text.startswith("/newsletter") or text.startswith("/test_broadcast") or 
            text.startswith("/send_test_now") or text.startswith("/send_test_quiz") or 
            text.startswith("/create_daily_wisdom") or text.startswith("/backup_") or
            text.startswith("/schedule_status") or text.startswith("/export_blocked_users")):
            # CRITICAL FIX: Remove NEWSLETTER_AVAILABLE dependency for admin commands
            if self.newsletter_initialized and self.admin_commands:
                # Auto-subscribe user for newsletter functionality
                if hasattr(self.admin_commands, 'auto_subscribe_user') and self.admin_commands:
                    await self.admin_commands.auto_subscribe_user(user_data)
                
                # Handle admin commands
                if text == "/newsletter_stats" and self.admin_commands:
                    await self.admin_commands.handle_admin_command(chat_id, user_id, "/newsletter_stats")
                elif text == "/newsletter_subscribers" and self.admin_commands:
                    await self.admin_commands.handle_admin_command(chat_id, user_id, "/newsletter_subscribers")
                elif text == "/newsletter_help" and self.admin_commands:
                    await self.admin_commands.handle_admin_command(chat_id, user_id, "/newsletter_help")
                elif text.startswith("/test_broadcast") and self.admin_commands:
                    topic = text.replace("/test_broadcast", "").strip() or "Admin Test"
                    await self.admin_commands.handle_admin_command(chat_id, user_id, "/test_broadcast", topic)
                elif text == "/send_test_now" and self.admin_commands:
                    await self.admin_commands.handle_admin_command(chat_id, user_id, "/send_test_now")
                elif text.startswith("/create_daily_wisdom") and self.admin_commands:
                    topic = text.replace("/create_daily_wisdom", "").strip()
                    await self.admin_commands.handle_admin_command(chat_id, user_id, "/create_daily_wisdom", topic)
                elif text == "/backup_database" and self.admin_commands:
                    await self.admin_commands.handle_admin_command(chat_id, user_id, "/backup_database")
                elif text == "/backup_status" and self.admin_commands:
                    await self.admin_commands.handle_admin_command(chat_id, user_id, "/backup_status")
                elif text == "/send_test_quiz" and self.admin_commands:
                    await self.admin_commands.handle_admin_command(chat_id, user_id, "/send_test_quiz")
                elif text == "/schedule_status" and self.admin_commands:
                    await self.admin_commands.handle_admin_command(chat_id, user_id, "/schedule_status")
                elif text == "/export_blocked_users" and self.admin_commands:
                    await self.admin_commands.handle_admin_command(chat_id, user_id, "/export_blocked_users")
                return
            else:
                await self.telegram_client.send_message(chat_id, "📧 Newsletter system not available")
                return
        
        if text in ["/start", "/menu"]:
            # Respond to user IMMEDIATELY 
            await self.startup_screen.show_main_menu(chat_id, user_id, user_data)
            
            # Auto-subscribe new users to newsletter AFTER response (non-blocking)
            if NEWSLETTER_AVAILABLE and self.newsletter_initialized and self.admin_commands:
                asyncio.create_task(self.admin_commands.auto_subscribe_user(user_data))
        elif text.startswith("/"):
            await self.telegram_client.send_message(chat_id, "Send /start to open the main menu")
        else:
            # Store user request for context in future interactions
            self.session_manager.store_user_request(user_id, text)
            
            # Check if user is in quiz context and wants a quiz on specific topic
            session = self.session_manager.get_session(user_id, user_data)
            last_workflow = session.get("last_workflow", "")
            
            # If last interaction was quiz, assume user wants another quiz on this topic
            if last_workflow == "torah_quiz":
                # Update session with new topic and generate quiz
                self.session_manager.update_session(user_id, current_topic=text, last_workflow="torah_quiz")
                await self.quiz_module.handle_quiz_request(chat_id, user_id, user_data)
            else:
                # Default to Rabbi wisdom
                await self.rabbi_module.handle_wisdom_request(chat_id, user_id, text, user_data)

async def main():
    """Production main loop with deployment safety checks"""
    # Production deployment startup - always proceed
    if DEPLOYMENT_GUARD_AVAILABLE:
        try:
            from ..config.deployment_config import safe_startup_check, DeploymentGuard
            # Always proceed in production - no blocking
            safe_startup_check()  # Log info but don't block
            guard = DeploymentGuard()
            startup_mode = guard.get_startup_mode()
            logger.info(f"🔒 Production Mode: {startup_mode} activated")
        except (ImportError, Exception) as e:
            logger.info(f"Production startup: {e} - proceeding normally")
    else:
        logger.info("🔒 Production startup: basic mode activated")
    
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is required")
        return
    
    # Initialize bot
    global bot_instance
    bot_instance = TorahBotFinal()
    bot = bot_instance
    
    # Initialize newsletter system if available
    if NEWSLETTER_AVAILABLE and newsletter_manager and AdminCommands:
        try:
            await newsletter_manager.initialize()
            bot.admin_commands = AdminCommands(bot.telegram_client, newsletter_manager)
            bot.newsletter_initialized = True
            logger.info("📧 Newsletter system initialized successfully")
            
            # Start backup scheduler in background  
            from database.backup_manager import backup_scheduler
            asyncio.create_task(backup_scheduler.start_daily_backups())
            logger.info("💾 Backup scheduler started - daily backups at 3:00 AM")
            
            # INTERNAL SCHEDULER DISABLED - USING GITHUB ACTIONS EXTERNAL SCHEDULER
            # from src.torah_bot.scheduled_broadcast import ScheduledBroadcastSystem
            # broadcast_system = ScheduledBroadcastSystem(bot.telegram_client)
            # asyncio.create_task(broadcast_system.start_scheduler())
            logger.info("🔒 Internal scheduler DISABLED - using GitHub Actions external scheduler")
            
        except Exception as e:
            logger.error(f"Newsletter initialization failed: {e}")
            bot.newsletter_initialized = False
            bot.admin_commands = None
    
    logger.info("🚀 Torah Bot v5.0.0 - Final Production Version Started")
    logger.info(f"OpenAI: {'✅ Available' if openai_client else '❌ Fallback mode'}")
    logger.info(f"Newsletter: {'✅ Ready' if NEWSLETTER_AVAILABLE and getattr(bot, 'newsletter_initialized', False) else '❌ Not available'}")
    
    # Log deployment status
    deployment_mode = os.environ.get("REPLIT_DEPLOYMENT", "development")
    logger.info(f"🌐 Environment: {deployment_mode}")
    
    offset = 0
    error_count = 0
    max_errors = 10
    
    # Production deployment - ensure continuous running
    logger.info("🚀 Starting production polling loop...")
    
    # Main polling loop with smart logging
    metrics_counter = 0
    while True:
        try:
            # Cleanup analytics periodically
            bot.analytics.cleanup_stale_sessions()
            
            # Generate DAILY business metrics summary every 2880 iterations (every ~24 hours with 30s timeout)
            metrics_counter += 1
            if metrics_counter % 2880 == 0:
                bot.analytics.smart_logger.business_metrics_summary()
            
            # Get updates
            result = await bot.telegram_client.get_updates(offset=offset, timeout=30)
            
            if not result.get("ok"):
                error_count += 1
                logger.error(f"API Error ({error_count}/{max_errors}): {result}")
                
                if error_count >= max_errors:
                    logger.error("Too many consecutive errors, restarting...")
                    await asyncio.sleep(60)
                    error_count = 0
                    continue
                
                await asyncio.sleep(5)
                continue
            
            # Reset error count on success
            error_count = 0
            
            # Process updates
            if result.get("result"):
                for update in result["result"]:
                    offset = update["update_id"] + 1
                    
                    try:
                        if "callback_query" in update:
                            await bot.handle_callback(update["callback_query"])
                        elif "message" in update:
                            await bot.handle_message(update["message"])
                        elif "pre_checkout_query" in update:
                            await bot.donation_module.handle_pre_checkout_query(update["pre_checkout_query"])
                        elif "message" in update and "successful_payment" in update["message"]:
                            payment_data = update["message"]["successful_payment"]
                            chat_id = update["message"]["chat"]["id"]
                            user_id = update["message"]["from"]["id"]
                            await bot.donation_module.handle_successful_payment(payment_data, user_id, chat_id)
                    except Exception as e:
                        logger.error(f"Update processing error: {e}")
                        continue
                        
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            break
        except Exception as e:
            error_count += 1
            logger.error(f"Main loop error ({error_count}): {e}")
            
            if error_count >= max_errors:
                logger.error("Too many errors, restarting...")
                await asyncio.sleep(60)
                error_count = 0
            else:
                await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Torah Bot v5.0.0 stopped")
    except Exception as e:
        logger.error(f"Fatal error: {e}")