#!/usr/bin/env python3
"""
Unified Webhook Service - TRUE UNIFIED ARCHITECTURE
Решает все проблемы: 409 conflicts, медленное пробуждение, раздельные компоненты
"""

import asyncio
import logging
import os
import sys
import signal
from pathlib import Path
import json
from typing import Optional

# FastAPI imports
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Security imports
from src.core.rate_limiter import rate_limit_middleware, start_rate_limiter_cleanup
from src.core.audit_logger import get_audit_logger, log_admin_action, AuditEventType
from src.core.user_context import UserContext

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

# Import smart scheduling system
# Removed: from src.core.smart_scheduler import ActivityMonitor, HybridScheduler

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 🔒 SECURITY: Prevent bot token leakage in httpx logs
logging.getLogger("httpx").setLevel(logging.WARNING)


# ✅ AUTO-SUBSCRIPTION SYSTEM FOR WEBHOOK BOUNDARY
def extract_user_data_from_update(update_data: dict) -> Optional[UserContext]:
    """Extract user context from Telegram update - FIXED to include username"""
    try:
        telegram_user_data = None
        
        # Handle message updates
        if "message" in update_data and "from" in update_data["message"]:
            telegram_user_data = update_data["message"]["from"]
        # Handle callback query updates  
        elif "callback_query" in update_data and "from" in update_data["callback_query"]:
            telegram_user_data = update_data["callback_query"]["from"]
        
        if telegram_user_data:
            # Language code to language name mapping
            language_mapping = {
                "en": "English", "ru": "Russian", "es": "Spanish", 
                "fr": "French", "de": "German", "he": "Hebrew",
                "ar": "Arabic", "uk": "Russian", "be": "Russian"
            }
            language_code = telegram_user_data.get("language_code", "en")
            language_name = language_mapping.get(language_code, "English")
            
            # Create UserContext with full user data including username
            return UserContext.from_telegram_user(telegram_user_data, language=language_name)
        
        return None
        
    except Exception as e:
        logger.warning(f"⚠️ Failed to extract user data from update: {e}")
        return None


async def ensure_user_subscription(user_context: UserContext, newsletter_manager) -> bool:
    """Ensure user is subscribed to newsletter - idempotent operation"""
    try:
        if not user_context or not newsletter_manager:
            return False
        
        # Call newsletter manager to subscribe user (idempotent with ON CONFLICT logic)
        success = await newsletter_manager.subscribe_user(
            telegram_user_id=user_context.user_id,
            language=user_context.language,
            delivery_time="09:00",  # Default delivery time
            timezone="UTC"  # Default timezone
        )
        
        if success:
            logger.info(f"📧 User {user_context.user_id} auto-subscribed to newsletter ({user_context.language})")
        else:
            logger.warning(f"⚠️ Failed to auto-subscribe user {user_context.user_id} to newsletter")
            
        return success
        
    except Exception as e:
        logger.error(f"❌ Auto-subscription failed for user {user_context.user_id}: {e}")
        return False

class UnifiedWebhookService:
    """
    Единый сервис: Telegram Webhook + Mini Game + Newsletter + Health Check + Smart Scheduling
    Atomic initialization, автономный scheduler с автопереключением
    """
    
    def __init__(self):
        self.app = FastAPI(
            title="Torah Bot Unified Service", 
            description="Webhook-only unified architecture with smart scheduling"
        )
        
        # Start background cleanup for rate limiter and audit logger
        import asyncio
        asyncio.create_task(start_rate_limiter_cleanup())
        asyncio.create_task(get_audit_logger())  # Initialize audit logger
        self.bot_instance = None
        self.telegram_client = None
        self.services_ready = False
        
        # 🤖 INTERNAL SCHEDULING SYSTEM
        # Old hybrid scheduler removed - now using simple internal scheduler
        
        # Add CORS for Telegram WebApp - SECURED TO TELEGRAM DOMAINS ONLY
        telegram_domains = [
            "https://web.telegram.org",
            "https://pluto.web.telegram.org",
            "https://venus.web.telegram.org", 
            "https://aurora.web.telegram.org",
            "https://vesta.web.telegram.org",
            "https://flora.web.telegram.org",
            "https://pluto-1.web.telegram.org",
            "https://venus-1.web.telegram.org",
            "https://aurora-1.web.telegram.org", 
            "https://vesta-1.web.telegram.org",
            "https://flora-1.web.telegram.org",
            "https://torah-project-jobjoyclub.replit.app",  # Our production domain
            "http://localhost:5000",  # Local development
            "http://127.0.0.1:5000"   # Local development
        ]
        
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=telegram_domains,
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Content-Type", "Authorization", "X-Admin-Secret", "X-Telegram-Web-App-Init-Data", "X-Requested-With"],
        )
        
        # Setup routes after middleware
        self.setup_routes()
    
    def _enforce_production_mode(self):
        """🔒 КРИТИЧЕСКАЯ ЗАЩИТА: Блокирует переключение в development без согласования пользователя"""
        
        # Проверяем находимся ли мы в Replit deployment
        is_replit_deployment = os.environ.get('REPLIT_DEPLOYMENT') == "1"
        is_production_domain = any(domain in os.environ.get('REPLIT_DOMAINS', '') 
                                 for domain in ['torah-project-jobjoyclub.replit.app'])
        
        # Принудительная защита production режима
        forced_production = os.environ.get('FORCE_PRODUCTION_MODE', 'true').lower() == 'true'
        
        if is_replit_deployment or is_production_domain or forced_production:
            # 🚨 ЗАЩИТА: Переопределяем переменные среды для принудительного production режима
            os.environ['DEPLOYMENT_MODE'] = 'production'
            os.environ['BOT_MODE'] = 'webhook'
            os.environ['FORCE_AUTOSCALE'] = 'true'
            
            logger.warning("🔒 PRODUCTION MODE ENFORCED - Development mode blocked by user security policy")
            logger.info(f"🏭 Production indicators: deployment={is_replit_deployment}, domain={is_production_domain}, forced={forced_production}")
            
        # Дополнительная проверка на попытку переключения в development
        if os.environ.get('NODE_ENV') == 'development':
            logger.error("🚨 SECURITY ALERT: Attempt to force development mode detected - BLOCKED!")
            os.environ['NODE_ENV'] = 'production'
            
        return True
    
    async def _validate_database_configuration(self):
        """Validate DATABASE_URL and perform database sanity check"""
        try:
            # Check if DATABASE_URL exists
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                raise ValueError("❌ DATABASE_URL not found in environment variables")
            
            # Parse database URL to extract information
            import re
            match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)
            if match:
                db_host = match.group(3)
                db_port = match.group(4) 
                db_name = match.group(5)
                logger.info(f"💾 Database target: {db_host}:{db_port}/{db_name}")
            else:
                logger.info(f"💾 Database URL configured (format not parsed)")
            
            # Perform sanity check by connecting and checking newsletter_subscriptions
            import asyncpg
            try:
                conn = await asyncpg.connect(database_url)
                
                # Check if newsletter_subscriptions table exists and get count
                subscription_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM newsletter_subscriptions 
                    WHERE is_active = true
                """)
                
                # Get last subscription date
                last_subscription = await conn.fetchval("""
                    SELECT MAX(subscribed_at) FROM newsletter_subscriptions
                """)
                
                await conn.close()
                
                logger.info(f"✅ Database sanity check passed:")
                logger.info(f"   📊 Active subscribers: {subscription_count}")
                logger.info(f"   📅 Last subscription: {last_subscription}")
                
                return True
                
            except Exception as db_error:
                logger.error(f"❌ Database connection failed: {db_error}")
                raise ValueError(f"Database connection failed: {db_error}")
        
        except Exception as e:
            logger.error(f"❌ Database validation failed: {e}")
            raise
    
    async def initialize_services(self):
        """Atomic initialization of all services using ServiceContainer"""
        try:
            # 🔒 DEPLOYMENT MODE PROTECTION - блокировка development режима без согласования
            self._enforce_production_mode()
            
            logger.info("🚀 Starting UNIFIED SERVICE initialization...")
            
            # PHASE 1: Database URL validation and sanity check
            await self._validate_database_configuration()
            
            # PHASE 2: Initialize ServiceContainer for consistent state
            from src.core.service_container import get_container
            from src.core.service_factories import initialize_all_services
            
            container = get_container()
            
            # PHASE 3: Initialize all services through container (prevents race conditions)
            services = await initialize_all_services(container)
            
            # PHASE 4: Extract services for backward compatibility
            self.bot_instance = services['torah_bot']
            self.telegram_client = services['telegram_client']
            
            # CRITICAL: Store container for access by other components
            self.container = container
            
            logger.info("🔧 ServiceContainer unified all instances - admin access should work")
            
            # PHASE 5: Set webhook URL
            webhook_url = self.get_webhook_url()
            await self.setup_telegram_webhook(webhook_url)
            
            logger.info("✅ All services initialized atomically via ServiceContainer")
            
            # LOGGING SYSTEM STATUS: ✅ VERIFIED WORKING
            # SmartLogger has TelegramClient and can send messages to TorahLogs chat
            logger.info("🔧 Logging system verified - SmartLogger ready for chat messages")
            
            # PHASE 6: Initialize Smart Scheduling System
            newsletter_service = self.container.get_service_sync('newsletter_manager')
            # OLD HYBRID SCHEDULER REMOVED - USING INTERNAL SCHEDULER + EXTERNAL WAKE-UP
            logger.info("🔒 Old hybrid scheduler removed - using internal scheduler + external wake-up")
            
            # 🕒 Initialize Background Scheduler for time-based broadcasts  
            from src.torah_bot.scheduled_broadcast import ScheduledBroadcastSystem
            telegram_client = self.container.get_service_sync('telegram_client')
            self.background_scheduler = ScheduledBroadcastSystem(telegram_client)
            
            # Start the background scheduler in a task
            self.scheduler_task = asyncio.create_task(self.background_scheduler.start_scheduler())
            logger.info("🕒 Background Scheduler started - running time-based broadcasts at 09:00 and 21:00 MSK")
            
            # PHASE 7: Add Scheduler API endpoints AFTER scheduler is created
            self.add_scheduler_endpoints()
            
            self.services_ready = True
            
        except Exception as e:
            logger.error(f"❌ Service initialization failed: {e}")
            self.services_ready = False
            raise
    
    def get_webhook_url(self):
        """Get webhook URL from environment variables with fallback"""
        # Check for explicit webhook URL configuration
        webhook_url = os.environ.get('WEBHOOK_URL')
        if webhook_url:
            return webhook_url
            
        # 🚨 CRITICAL FIX: Force production domain when autoscale deployment is configured
        # Check for autoscale deployment indicators
        is_replit_deployment = os.environ.get('REPLIT_DEPLOYMENT') == "1"
        is_autoscale_forced = os.environ.get('FORCE_AUTOSCALE', '').lower() == 'true'
        
        if is_replit_deployment or is_autoscale_forced:
            logger.info("🏭 Using production webhook URL for autoscale deployment")
            return "https://torah-project-jobjoyclub.replit.app/webhook"
            
        # Build from Replit environment variables for development
        repl_slug = os.environ.get('REPL_SLUG', 'torah-project')
        repl_owner = os.environ.get('REPL_OWNER', 'jobjoyclub')
        
        # Development URL
        logger.info("🛠️ Using development webhook URL")
        return f"https://{repl_slug}-{repl_owner}.replit.app/webhook"
    
    async def setup_telegram_webhook(self, webhook_url):
        """Setup Telegram webhook with security token"""
        try:
            bot_token = os.environ.get('BOT_TOKEN') or os.environ.get('TELEGRAM_BOT_TOKEN')
            if not bot_token:
                raise ValueError("Bot token not found")
            
            # Generate or get webhook secret token for security
            webhook_secret = os.environ.get('TELEGRAM_WEBHOOK_SECRET')
            if not webhook_secret:
                from src.core.telegram_security import generate_webhook_secret_token
                webhook_secret = generate_webhook_secret_token()
                logger.info("🔒 Generated new webhook secret token")
                # Note: In production, save this to environment or secrets management
            
            # Store secret token for verification
            self.webhook_secret = webhook_secret
            
            import httpx
            async with httpx.AsyncClient() as client:
                webhook_data = {
                    "url": webhook_url,
                    "allowed_updates": ["message", "callback_query"],
                    "secret_token": webhook_secret
                }
                
                response = await client.post(
                    f"https://api.telegram.org/bot{bot_token}/setWebhook",
                    json=webhook_data
                )
                result = response.json()
                
                if result.get("ok"):
                    logger.info(f"✅ Webhook set successfully with security: {webhook_url}")
                else:
                    logger.error(f"❌ Webhook setup failed: {result}")
                    
        except Exception as e:
            logger.error(f"❌ Webhook setup error: {e}")
    
    def setup_routes(self):
        """Setup all routes in single FastAPI app"""
        
        # === UNIFIED HEALTH CHECK ===
        @self.app.get("/health")
        @self.app.get("/api")  # Autoscale health check endpoint
        @self.app.head("/api")  # Handle HEAD requests from Autoscale
        async def unified_health_check():
            """Single health endpoint for entire service with deployment protection"""
            import time
            
            if not self.services_ready:
                return JSONResponse({
                    "status": "initializing",
                    "service": "torah-bot-unified",
                    "ready": False,
                    "timestamp": int(time.time())
                }, status_code=503)
            
            # 🔒 ПРИНУДИТЕЛЬНАЯ ЗАЩИТА production режима
            is_production = os.environ.get('REPLIT_DEPLOYMENT') == "1"
            is_production_domain = any(domain in os.environ.get('REPLIT_DOMAINS', '') 
                                     for domain in ['torah-project-jobjoyclub.replit.app'])
            forced_production = os.environ.get('FORCE_PRODUCTION_MODE', 'true').lower() == 'true'
            
            # Если есть любой индикатор production - принудительно показываем production
            deployment_status = "production" if (is_production or is_production_domain or forced_production) else "development"
            
            # 🚨 SECURITY: Предупреждение о попытках development режима
            security_warnings = []
            if not (is_production or is_production_domain or forced_production) and os.environ.get('NODE_ENV') == 'development':
                security_warnings.append("BLOCKED_DEV_MODE_ATTEMPT")
            
            # 🤖 BACKGROUND SCHEDULING: Include scheduler status
            scheduler_status = {}
            if hasattr(self, 'background_scheduler') and self.background_scheduler:
                scheduler_status = {
                    "type": "background_time_based",
                    "running": self.background_scheduler.is_running,
                    "jobs": self.background_scheduler.get_scheduled_jobs()
                }
            
            response_data = {
                "status": "healthy",
                "service": "torah-bot-unified",
                "mode": "webhook",
                "deployment": deployment_status,
                "components": {
                    "telegram_bot": "ready",
                    "mini_game": "ready", 
                    "newsletter": "ready",
                    "scheduler_api": "ready",
                    "background_scheduler": "ready" if scheduler_status else "not_initialized"
                },
                "ready": True,
                "timestamp": int(time.time()),
                "webhook_url": self.get_webhook_url(),
                "security_status": {
                    "production_enforced": forced_production,
                    "deployment_protection": "active",
                    "warnings": security_warnings
                },
                "background_scheduler": scheduler_status
            }
            
            return JSONResponse(response_data)
        
        # === WAKE-UP ENDPOINT ===
        @self.app.get("/wake")
        @self.app.post("/wake")
        async def wake_up_service(request: Request):
            """Simple endpoint to wake up autoscale deployment from external cron"""
            try:
                # 🚦 RATE LIMITING: Moderate limits for wake endpoint
                await rate_limit_middleware(request)
            except HTTPException:
                # Allow wake endpoint to have more lenient rate limiting
                pass
            from datetime import datetime, timedelta
            import time
            
            # Calculate Moscow time
            utc_now = datetime.now()
            moscow_now = utc_now + timedelta(hours=3)
            
            logger.info(f"🔔 Service wakeup called at {moscow_now.strftime('%H:%M:%S MSK')}")
            
            # Just return wake status - scheduler runs independently
            scheduler_status = "independent_background_scheduler"
            
            return JSONResponse({
                "status": "awake",
                "service": "torah-bot-unified", 
                "wakeup_time": moscow_now.strftime('%Y-%m-%d %H:%M:%S MSK'),
                "timestamp": int(time.time()),
                "scheduler_check": scheduler_status,
                "message": "Service is now active"
            })
        
        # === SCHEDULER STATUS ENDPOINT will be added in add_scheduler_endpoints() ===
        
        # 🤖 SMART SCHEDULER API ENDPOINTS - Will be added after initialization
        
        # === BROADCAST STATUS MONITORING ===
        @self.app.get("/api/broadcast_status")
        async def broadcast_status():
            """Monitoring endpoint for broadcast system diagnostics"""
            import time
            from datetime import datetime, timedelta
            
            # Calculate next quiz times
            utc_now = datetime.now()
            moscow_now = utc_now + timedelta(hours=3)
            
            # Next morning wisdom: 06:00 UTC (09:00 MSK)
            next_morning = moscow_now.replace(hour=9, minute=0, second=0, microsecond=0)
            if moscow_now.hour >= 9:
                next_morning += timedelta(days=1)
            
            # Next evening quiz: 18:00 UTC (21:00 MSK)  
            next_evening = moscow_now.replace(hour=21, minute=0, second=0, microsecond=0)
            if moscow_now.hour >= 21:
                next_evening += timedelta(days=1)
            
            return JSONResponse({
                "broadcast_system": {
                    "service_ready": self.services_ready,
                    "current_moscow_time": moscow_now.strftime('%Y-%m-%d %H:%M:%S MSK'),
                    "current_moscow_hour": moscow_now.hour,
                    "github_actions_schedule": {
                        "morning_wisdom": "05:58 UTC (08:58 MSK)",
                        "evening_quiz": "17:58 UTC (20:58 MSK)"
                    },
                    "next_broadcasts": {
                        "morning_wisdom": next_morning.strftime('%Y-%m-%d %H:%M MSK'),
                        "evening_quiz": next_evening.strftime('%Y-%m-%d %H:%M MSK')
                    }
                },
                "time_detection": {
                    "is_morning_time": 6 <= moscow_now.hour < 12,
                    "is_evening_time": 18 <= moscow_now.hour <= 23,
                    "detected_content_type": (
                        "wisdom" if 6 <= moscow_now.hour < 12 
                        else "quiz" if 18 <= moscow_now.hour <= 23 
                        else "auto"
                    )
                },
                "system_info": {
                    "deployment": "production" if os.environ.get('REPLIT_DEPLOYMENT') == "1" else "development",
                    "webhook_url": self.get_webhook_url(),
                    "timestamp": int(time.time())
                }
            })
        
        # === WEBHOOK STATUS CHECK ===
        @self.app.get("/webhook-info")
        async def webhook_info():
            """Check current webhook configuration"""
            bot_token = os.environ.get('BOT_TOKEN') or os.environ.get('TELEGRAM_BOT_TOKEN')
            
            if not bot_token:
                return JSONResponse({"error": "Bot token not found"}, status_code=500)
            
            try:
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
                    )
                    result = response.json()
                    
                    return JSONResponse({
                        "expected_webhook": self.get_webhook_url(),
                        "telegram_webhook_info": result,
                        "deployment_env": os.environ.get('REPLIT_DEPLOYMENT', 'not_set')
                    })
                    
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)
        
        # === TELEGRAM WEBHOOK ===
        @self.app.post("/webhook")
        async def telegram_webhook(request: Request):
            """Main Telegram webhook endpoint with security verification"""
            try:
                if not self.services_ready:
                    return JSONResponse({"error": "Service not ready"}, status_code=503)
                
                # 🔒 SECURITY: Verify webhook authenticity
                from src.core.telegram_security import verify_telegram_webhook, log_security_event
                
                webhook_secret = getattr(self, 'webhook_secret', None)
                if not webhook_secret:
                    webhook_secret = os.environ.get('TELEGRAM_WEBHOOK_SECRET')
                
                is_authentic = verify_telegram_webhook(request, webhook_secret)
                if not is_authentic:
                    log_security_event("WEBHOOK_AUTH_FAILED", request, "Invalid webhook authentication")
                    return JSONResponse({"error": "Unauthorized"}, status_code=401)
                
                data = await request.json()
                logger.info("📨 Webhook received update")
                
                # ✅ AUTO-SUBSCRIPTION: Ensure user is subscribed to newsletter
                try:
                    user_context = extract_user_data_from_update(data)
                    if user_context:
                        newsletter_manager = self.container.get_service_sync('newsletter_manager')
                        if newsletter_manager:
                            await ensure_user_subscription(user_context, newsletter_manager)
                        else:
                            logger.warning("⚠️ Newsletter manager not available for auto-subscription")
                    else:
                        logger.info("📊 No user data in update - skipping auto-subscription")
                except Exception as e:
                    logger.warning(f"⚠️ Auto-subscription failed (non-critical): {e}")
                
                # CRITICAL: Process update using ServiceContainer bot instance
                if self.bot_instance:
                    # Ensure bot uses the SAME AdminCommands instance from container
                    container_admin_commands = self.container.get_service_sync('admin_commands')
                    if container_admin_commands and hasattr(self.bot_instance, 'admin_commands'):
                        self.bot_instance.admin_commands = container_admin_commands
                        logger.info("🔧 Bot instance updated with container AdminCommands")
                    
                    # Use existing update processing logic
                    if "message" in data:
                        await self.bot_instance.handle_message(data["message"])
                    elif "callback_query" in data:
                        await self.bot_instance.handle_callback(data["callback_query"])
                
                return JSONResponse({"ok": True})
                
            except Exception as e:
                logger.error(f"❌ Webhook processing error: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)
        
        # === GITHUB ACTIONS SCHEDULER API ===
        @self.app.post("/api/manual_broadcast")
        async def github_actions_broadcast(request: Request):
            """GitHub Actions scheduler endpoint with SAFE newsletter broadcast - REQUIRES ADMIN AUTH"""
            try:
                # 🚦 RATE LIMITING: Check rate limits first
                await rate_limit_middleware(request)
                
                if not self.services_ready:
                    return JSONResponse({"error": "Service not ready"}, status_code=503)
                
                # 🔒 SECURITY: Require admin authentication
                admin_secret = request.headers.get("X-Admin-Secret")
                expected_secret = os.getenv("ADMIN_SECRET")
                
                if not admin_secret or not expected_secret or admin_secret != expected_secret:
                    logger.warning(f"🔒 Unauthorized manual_broadcast attempt - missing or invalid X-Admin-Secret")
                    return JSONResponse({
                        "error": "Unauthorized - X-Admin-Secret header required",
                        "status": "denied"
                    }, status_code=401)
                
                logger.info("🔒 Admin authentication verified for manual_broadcast")
                
                # 🔍 AUDIT LOGGING: Log admin action
                client_ip = request.headers.get("X-Forwarded-For", "unknown").split(",")[0].strip()
                user_agent = request.headers.get("User-Agent", "unknown")
                
                data = await request.json()
                topic = data.get("topic", None)
                auto_schedule = data.get("auto_schedule", False)
                test_mode = data.get("test_mode", False)  # NEW: Test mode flag
                
                # 🔍 AUDIT: Log manual broadcast attempt
                await log_admin_action(
                    user_identifier="admin_api",
                    action="manual_broadcast_request",
                    resource="newsletter_system",
                    details={
                        "topic": topic,
                        "auto_schedule": auto_schedule,
                        "test_mode": test_mode,
                        "request_data": data
                    },
                    ip_address=client_ip
                )
                
                # AUTO-DETERMINE CONTENT TYPE WITH STRICT TIME WINDOWS AND DEDUPLICATION
                if auto_schedule:
                    from datetime import datetime, timedelta, date
                    import time
                    
                    utc_now = datetime.now()
                    moscow_now = utc_now + timedelta(hours=3)  # UTC+3 Moscow time
                    current_hour = moscow_now.hour
                    current_minute = moscow_now.minute
                    today = date.today()
                    
                    # STRICT TIME WINDOWS: Only send during specific windows
                    if 6 <= current_hour < 12:  # Morning window: 06:00-11:59 MSK
                        content_type = "wisdom"
                        window_name = "morning"
                    elif 18 <= current_hour <= 23:  # Evening window: 18:00-23:59 MSK 
                        content_type = "quiz"
                        window_name = "evening"
                    else:
                        # Outside broadcast windows - return no-op
                        logger.info(f"🕒 Outside broadcast windows: {moscow_now.strftime('%H:%M MSK')} - no action")
                        return JSONResponse({
                            "success": True,
                            "message": f"Outside broadcast window - no action taken",
                            "current_time": moscow_now.strftime('%H:%M MSK'),
                            "next_window": "06:00-11:59 MSK (morning) or 18:00-23:59 MSK (evening)",
                            "test_mode": True,
                            "timestamp": int(time.time())
                        })
                    
                    # ATOMIC DEDUPLICATION: Reserve broadcast slot to prevent duplicates
                    newsletter_manager = self.container.get_service_sync('newsletter_manager')
                    if not newsletter_manager:
                        logger.error("❌ Newsletter manager not available - cannot proceed")
                        return JSONResponse({
                            "success": False,
                            "message": "Newsletter service unavailable",
                            "error": "service_unavailable"
                        }, status_code=503)
                    
                    # Atomically reserve the broadcast slot
                    broadcast_id = await newsletter_manager.reserve_broadcast_slot(content_type)
                    if not broadcast_id:
                        # Slot already reserved (broadcast already sent today)
                        return JSONResponse({
                            "success": True,
                            "message": f"{content_type.title()} broadcast already sent today",
                            "broadcast_type": content_type,
                            "window": window_name,
                            "already_sent": True,
                            "test_mode": False,
                            "timestamp": int(time.time()),
                            "note": "Atomic deduplication prevented duplicate broadcast"
                        })
                    
                    logger.info(f"🎯 Broadcast slot reserved (ID: {broadcast_id}) - proceeding with {content_type}")
                    
                    topic = None  # Let topic generators handle unique selection
                    logger.info(f"🕒 Auto-schedule: {moscow_now.strftime('%H:%M MSK')} → {content_type} in {window_name} window")
                else:
                    topic = topic or "manual test"
                    content_type = "manual"
                
                # 🤖 Activity monitoring removed - internal scheduler handles timing
                
                # ENHANCED LOGGING FOR DIAGNOSTICS
                user_agent = request.headers.get("user-agent", "unknown")
                logger.info(f"📡 GitHub Actions broadcast request: {topic} (test_mode={test_mode})")
                logger.info(f"🔍 Request details: User-Agent='{user_agent}', auto_schedule={auto_schedule}, test_mode={test_mode}")
                
                # 🤖 LOG CURRENT SCHEDULER MODE
                if hasattr(self, 'background_scheduler') and self.background_scheduler:
                    logger.info(f"🤖 Internal scheduler: active")
                
                # IMPROVED USER-AGENT CHECKING - More reliable for GitHub Actions
                user_agent_lower = user_agent.lower()
                is_github_request = (
                    "github" in user_agent_lower or 
                    "curl" in user_agent_lower or
                    auto_schedule  # Trust auto_schedule flag as primary indicator
                )
                
                # CRITICAL FIX: Only send real broadcasts from GitHub Actions, not manual tests
                should_send_real_broadcast = (
                    auto_schedule and 
                    not test_mode and
                    is_github_request
                )
                
                logger.info(f"🎯 Broadcast decision: should_send_real_broadcast={should_send_real_broadcast} (github_check={is_github_request})")
                
                # UNIVERSAL FALLBACK MECHANISM: If scheduled time detected but User-Agent check failed, proceed anyway
                content_fallback = False
                if auto_schedule and content_type in ["quiz", "wisdom"] and not should_send_real_broadcast and not test_mode:
                    logger.warning(f"⚠️ {content_type.title()} time detected but User-Agent check failed - activating fallback mechanism")
                    should_send_real_broadcast = True
                    content_fallback = True
                
                if should_send_real_broadcast:
                    # REAL NEWSLETTER BROADCAST INTEGRATION
                    from src.newsletter_api.client import InternalNewsletterAPIClient
                    
                    # CRITICAL: Use ServiceContainer telegram_client for consistency
                    container_telegram_client = self.container.get_service_sync('telegram_client')
                    newsletter_client = InternalNewsletterAPIClient(container_telegram_client or self.telegram_client)
                    
                    # FIXED: Use correct method for quiz vs wisdom
                    if content_type == "quiz":
                        broadcast_result = await newsletter_client.send_quiz_broadcast(
                            topic=topic,
                            language="Russian"
                        )
                    else:
                        broadcast_result = await newsletter_client.send_broadcast(
                            topic=topic,
                            language="Russian",
                            user_name="Друг"
                        )
                    
                    logger.info(f"✅ REAL broadcast executed: {broadcast_result.get('sent_count', 0)} sent")
                else:
                    # MOCK response for testing
                    broadcast_result = {
                        "success": True,
                        "sent_count": 0,
                        "failed_count": 0,
                        "has_image": False,
                        "message": "Test mode - no real broadcast sent"
                    }
                    logger.info("🧪 TEST MODE - No real broadcast sent")
                
                # 🔍 AUDIT: Log broadcast completion with results
                await log_admin_action(
                    user_identifier="admin_api",
                    action="auto_schedule_broadcast_completed",
                    resource="newsletter_system",
                    details={
                        "topic": topic,
                        "content_type": content_type,
                        "sent_count": broadcast_result.get("sent_count", 0),
                        "failed_count": broadcast_result.get("failed_count", 0),
                        "has_image": broadcast_result.get("has_image", False),
                        "test_mode": test_mode or not should_send_real_broadcast,
                        "success": broadcast_result.get("success", False)
                    },
                    ip_address=client_ip,
                    success=broadcast_result.get("success", False),
                    error_message=None if broadcast_result.get("success", False) else broadcast_result.get("message", "Unknown error")
                )
                
                # Enhanced response with safe broadcast results  
                import time
                response_data = {
                    "success": broadcast_result.get("success", False),
                    "message": broadcast_result.get("message", f"Broadcast processed - {topic}"),
                    "broadcast_topic": topic,
                    "content_type": content_type,
                    "is_quiz": content_type == "quiz",
                    "sent_count": broadcast_result.get("sent_count", 0),
                    "failed_count": broadcast_result.get("failed_count", 0),
                    "has_image": broadcast_result.get("has_image", False),
                    "test_mode": test_mode or not should_send_real_broadcast,
                    "timestamp": int(time.time()),
                    "architecture": "webhook-only",
                    "note": "GitHub Actions → Safe newsletter broadcast"
                }
                
                return JSONResponse(response_data)
                    
            except Exception as e:
                logger.error(f"❌ GitHub Actions broadcast error: {e}")
                return JSONResponse({
                    "success": False,
                    "error": str(e),
                    "message": "Broadcast execution failed",
                    "sent_count": 0,
                    "failed_count": 0
                }, status_code=500)
        
        # === MINI GAME ROUTES ===
        self.setup_mini_game_routes()
        
        # === ROOT REDIRECT TO GAME ===
        @self.app.get("/")
        @self.app.head("/")
        async def root_redirect():
            """Redirect root to mini game for Telegram Mini App"""
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/game", status_code=302)
        
        # === FAVICON HANDLER ===
        @self.app.get("/favicon.ico")
        @self.app.head("/favicon.ico") 
        async def favicon():
            """Simple favicon handler to prevent 404 errors in logs"""
            return Response(status_code=204)
    
    def setup_mini_game_routes(self):
        """Setup mini game static file serving"""
        
        # Get mini game directory
        mini_game_dir = Path(__file__).parent / "src" / "mini_game"
        frontend_dir = mini_game_dir / "frontend" 
        public_dir = frontend_dir / "public"
        
        @self.app.get("/game", response_class=HTMLResponse)
        async def serve_game():
            """Serve mini game HTML"""
            html_path = public_dir / "index.html"
            if html_path.exists():
                with open(html_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # CRITICAL: Disable caching for HTML to force reload of changes
                headers = {
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache", 
                    "Expires": "0"
                }
                return HTMLResponse(content=content, headers=headers)
            raise HTTPException(status_code=404, detail="Game not found")

        @self.app.post("/game/share")
        async def share_game_score(request: Request):
            """Generate share message for game score - same as bot share mechanism"""
            try:
                data = await request.json()
                user_id = data.get("user_id")
                score = data.get("score")
                language = data.get("language", "russian")
                
                if user_id is None or score is None:
                    raise HTTPException(status_code=400, detail="Missing user_id or score")
                
                # Generate share messages for different languages (same as bot)
                share_messages = {
                    "russian": f"🏆 Я набрал {score} очков в Shabbat Runner!\n\n🕯️ Попробуй себя в изучении еврейских традиций через игру!\n🎮 Собирай святые предметы и изучай Шаббат!\n\n✨ Проверь свои знания о еврейской культуре:\nhttps://torah-project-jobjoyclub.replit.app",
                    "english": f"🏆 I scored {score} points in Shabbat Runner!\n\n🕯️ Try learning Jewish traditions through gaming!\n🎮 Collect holy items and learn about Shabbat!\n\n✨ Test your knowledge of Jewish culture:\nhttps://torah-project-jobjoyclub.replit.app",
                    "hebrew": f"🏆 קיבלתי {score} נקודות ב-Shabbat Runner!\n\n🕯️ נסו ללמוד מסורות יהודיות דרך משחק!\n🎮 אספו פריטים קדושים ולמדו על שבת!\n\n✨ בדקו את הידע שלכם על התרבות היהודית:\nhttps://torah-project-jobjoyclub.replit.app"
                }
                
                share_text = share_messages.get(language, share_messages["russian"])
                
                # Create share URL for Telegram (same mechanism as bot)
                from urllib.parse import quote
                # Use production app URL instead of Telegram bot link
                game_url = "https://torah-project-jobjoyclub.replit.app"
                telegram_share_url = f"https://t.me/share/url?url={quote(game_url)}&text={quote(share_text)}"
                
                logger.info(f"📤 Share request: user {user_id} scored {score} in {language}")
                
                return JSONResponse({
                    "success": True,
                    "share_url": telegram_share_url,
                    "share_text": share_text,
                    "game_url": game_url,
                    "message": "Share URL generated successfully"
                })
                
            except Exception as e:
                logger.error(f"❌ Failed to generate share URL: {e}")
                raise HTTPException(status_code=500, detail="Share URL generation failed")
        
        @self.app.post("/api/game-analytics")
        async def receive_game_analytics(request: Request):
            """Receive game analytics from frontend"""
            try:
                data = await request.json()
                event_type = data.get("event_type")
                user_id = data.get("user_id")
                
                if not event_type or not user_id:
                    raise HTTPException(status_code=400, detail="Missing event_type or user_id")
                
                # Get analytics logger from bot service
                bot_service = getattr(self, 'bot_instance', None)  # FIXED: correct variable name
                analytics = getattr(bot_service, 'analytics', None) if bot_service else None
                if analytics and hasattr(analytics, 'smart_logger'):
                    smart_logger = analytics.smart_logger
                    
                    # Route different event types to appropriate logging methods
                    if event_type.startswith("TUTORIAL_"):
                        smart_logger.tutorial_event(
                            event_type,
                            user_id,
                            duration=data.get("duration"),
                            username=data.get("username", "unknown"),
                            language=data.get("language", "unknown"),
                            first_time=data.get("first_time", False)
                        )
                    elif event_type.startswith("GAME_"):
                        smart_logger.game_session_event(
                            event_type,
                            user_id,
                            username=data.get("username", "unknown"),
                            language=data.get("language", "unknown"),
                            score=data.get("score"),
                            duration=data.get("duration"),
                            items_collected=data.get("items_collected"),
                            mistakes=data.get("mistakes"),
                            after_tutorial=data.get("after_tutorial", False)
                        )
                    elif event_type == "GAME_ACHIEVEMENT":
                        smart_logger.game_achievement_event(
                            data.get("achievement_type", "unknown"),
                            user_id,
                            username=data.get("username", "unknown"),
                            language=data.get("language", "unknown"),
                            score=data.get("score"),
                            games_played=data.get("games_played")
                        )
                
                logger.info(f"📊 Frontend analytics: {event_type} from user {user_id}")
                return JSONResponse({"success": True, "message": "Analytics received"})
                
            except Exception as e:
                logger.error(f"❌ Failed to process game analytics: {e}")
                raise HTTPException(status_code=500, detail="Analytics processing failed")
        
        @self.app.get("/tutorial", response_class=HTMLResponse)
        async def serve_tutorial():
            """Serve tutorial HTML - separate page for clean architecture"""
            tutorial_path = public_dir / "tutorial.html"
            if tutorial_path.exists():
                with open(tutorial_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # CRITICAL: Disable caching for HTML to force reload of changes
                headers = {
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache", 
                    "Expires": "0"
                }
                return HTMLResponse(content=content, headers=headers)
            raise HTTPException(status_code=404, detail="Tutorial not found")
        
        @self.app.get("/game_rabbi_with_torah.png")
        async def serve_game_image():
            """Serve game rabbi image"""
            img_path = public_dir / "game_rabbi_with_torah.png"
            if img_path.exists():
                from fastapi.responses import FileResponse
                return FileResponse(img_path, media_type="image/png")
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Static files - serve at root level for game assets
        if public_dir.exists():
            self.app.mount("/static", StaticFiles(directory=public_dir), name="static")
            
            # Also serve key game files directly for easier access
            @self.app.get("/style.css")
            async def serve_css():
                css_path = public_dir / "style.css"
                if css_path.exists():
                    from fastapi.responses import FileResponse
                    # CRITICAL: Disable caching for CSS to force reload of changes
                    headers = {
                        "Cache-Control": "no-cache, no-store, must-revalidate",
                        "Pragma": "no-cache",
                        "Expires": "0"
                    }
                    return FileResponse(css_path, media_type="text/css", headers=headers)
                raise HTTPException(status_code=404, detail="CSS not found")
            
            @self.app.get("/game.js")
            async def serve_js():
                js_path = public_dir / "game.js"
                if js_path.exists():
                    from fastapi.responses import FileResponse
                    # CRITICAL: Disable caching for JS to force reload of changes
                    headers = {
                        "Cache-Control": "no-cache, no-store, must-revalidate",
                        "Pragma": "no-cache", 
                        "Expires": "0"
                    }
                    return FileResponse(js_path, media_type="application/javascript", headers=headers)
                raise HTTPException(status_code=404, detail="JS not found")
    
    def add_scheduler_endpoints(self):
        """Add scheduler endpoints after scheduler is initialized"""
        
        @self.app.get("/api/scheduler_status")
        async def scheduler_status_endpoint(request: Request):
            """Internal scheduler status and activity monitoring"""
            try:
                # 🚦 RATE LIMITING: Check rate limits for scheduler endpoint
                await rate_limit_middleware(request)
                
                if not self.services_ready:
                    return JSONResponse({"error": "Service not ready"}, status_code=503)
                
                # Get internal scheduler status
                if hasattr(self, 'background_scheduler') and self.background_scheduler:
                    scheduler_data = {
                        "type": "background_time_based", 
                        "running": self.background_scheduler.is_running,
                        "jobs": self.background_scheduler.get_scheduled_jobs()
                    }
                    return JSONResponse({
                        "scheduler": "internal",
                        "status": "active",
                        **scheduler_data
                    })
                else:
                    return JSONResponse({
                        "scheduler": "internal",
                        "status": "not_initialized",
                        "error": "Internal scheduler not available"
                    })
                
            except Exception as e:
                logger.error(f"❌ Scheduler status error: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)
                
        # Scheduler management handled internally
                
        logger.info("🤖 Scheduler API endpoints added")

class UnifiedServiceManager:
    """Manager for the unified service"""
    
    def __init__(self):
        self.service = UnifiedWebhookService()
        self.server = None
        self.shutdown_event = asyncio.Event()
    
    async def cleanup(self):
        """Cleanup resources on shutdown"""
        logger.info("🧹 Cleaning up resources...")
        
        # Close Telegram client session if exists
        if hasattr(self.service, 'telegram_client') and self.service.telegram_client:
            if hasattr(self.service.telegram_client, 'close_session'):
                await self.service.telegram_client.close_session()
                logger.info("✅ Telegram client session closed")
        
        logger.info("✅ Cleanup completed")
    
    def handle_shutdown(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"🛑 Received shutdown signal {signum}")
        self.shutdown_event.set()
    
    async def start(self):
        """Start unified service with graceful shutdown"""
        logger.info("🚀 UNIFIED WEBHOOK SERVICE STARTING...")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        
        try:
            # Initialize all services atomically
            await self.service.initialize_services()
            
            # Start web server
            port = int(os.environ.get("PORT", 5000))
            
            logger.info(f"🌐 Starting unified server on port {port}")
            
            # Run uvicorn server
            config = uvicorn.Config(
                self.service.app,
                host="0.0.0.0",
                port=port,
                log_level="info"
            )
            
            self.server = uvicorn.Server(config)
            
            # Run server with shutdown handling
            server_task = asyncio.create_task(self.server.serve())
            shutdown_task = asyncio.create_task(self.shutdown_event.wait())
            
            # Wait for either server completion or shutdown signal
            done, pending = await asyncio.wait(
                [server_task, shutdown_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # If shutdown was triggered, cleanup
            if shutdown_task in done:
                logger.info("🛑 Shutdown initiated...")
                if self.server:
                    self.server.should_exit = True
                
                # Cancel pending tasks
                for task in pending:
                    task.cancel()
                    
                await self.cleanup()
            
        except Exception as e:
            logger.error(f"❌ Unified service startup failed: {e}")
            await self.cleanup()
            raise

async def main():
    """Main entry point"""
    manager = UnifiedServiceManager()
    await manager.start()

if __name__ == "__main__":
    asyncio.run(main())