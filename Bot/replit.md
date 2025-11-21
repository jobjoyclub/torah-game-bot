# Overview
This project is a production-ready Python Telegram bot providing AI-powered educational content focused on Torah and Talmud. It offers interactive features like AI-generated wisdom, relevant image generation, multilingual support, engaging quizzes, and a comprehensive newsletter broadcast system with daily wisdom delivery. The bot is designed for modularity, performance, and deployment on Replit Autoscale, aiming to provide an interactive educational service for Jewish topics with ambitions in the educational technology sector.

**ENHANCED ANALYTICS SYSTEM - October 05, 2025**
✅ **TorahLogs Enhanced**: Comprehensive mini-app game usage data and tutorial completion metrics
✅ **Smart Analytics Pipeline**: Frontend → /api/game-analytics → SmartLogger → TorahLogs chat
✅ **Detailed Game Metrics**: Score, duration, items_collected, mistakes, achievements tracking
✅ **Tutorial Analytics**: TUTORIAL_STARTED/COMPLETED events with timing and user data
✅ **Daily Reports Extended**: Game statistics, tutorial completion rates, user engagement data
✅ **Production Tested**: All endpoints functional, architect-reviewed, stable in autoscale mode
✅ **UserContext Integration**: Unified user data handling with proper username extraction from webhooks
✅ **Unified Log Formatting**: Consistent structured logs with UnifiedLogFormatter for all game events
✅ **Fixed Username Loss**: Username now properly captured at webhook boundary and preserved throughout pipeline

**CONTENT DEDUPLICATION FIX - October 10, 2025**
✅ **Fixed Wisdom/Quiz Conflicts**: Quiz and Wisdom broadcasts now properly separated by broadcast_type
✅ **Enhanced Deduplication**: All statuses (sent, generating, ready) now checked to prevent race conditions
✅ **Database Cleanup**: Removed 18 corrupted records where quiz system overwrote wisdom topics
✅ **Unique Content Guaranteed**: 14-day lookback ensures no duplicate wisdom topics in broadcasts

**CONTENT VARIETY EXPANSION - October 12, 2025**
✅ **Wisdom Topics Expanded**: Increased from 20 to 100 base topics + 77 day-specific (177 total combinations)
✅ **Quiz Topics Expanded**: Increased from 35 to 75 diverse topics across all Jewish categories
✅ **Variety Instructions Added**: wisdom_variety_elements.txt with 15 style variations for diverse content
✅ **Extended Uniqueness Period**: Wisdom 14→45 days, Quiz 7→21 days for better content rotation
✅ **Enhanced Prompts**: Wisdom generation now uses variety instructions like quiz system
✅ **Content Categories**: Organized into Biblical figures, Holidays, Ethics, Kabbalah, Daily practices

**BLOCKED USERS TRACKING & EXPORT - October 16, 2025**
✅ **Fixed delivery_log Tracking**: wisdom_topics.py no longer overwrites broadcast tracking data - preserves broadcast_id and stats
✅ **Automatic Blocking Detection**: Users who block bot (403 error) automatically flagged with users.is_blocked = TRUE
✅ **CSV Export Command**: New /export_blocked_users admin command for subscriber management
✅ **Comprehensive Export**: CSV includes user_id, username, first_name, last_name, blocked_date, last_interaction, error_details
✅ **Excel Compatible**: UTF-8 BOM encoding for correct Cyrillic display in Excel/Google Sheets
✅ **Admin Gated**: Requires can_manage_users permission, documented in /newsletter_help
✅ **Architecture**: LEFT JOIN LATERAL query for efficient blocked user retrieval with latest error details

# User Preferences
Preferred communication style: Simple, everyday language.

Deployment Management: User prefers automatic deployments when changes are made. Agent should proactively handle deployments and resolve deployment conflicts/errors without asking permission.

## Agent Cost Optimization Guidelines - September 11, 2025
**PRODUCTION-SAFE COST REDUCTION STRATEGIES:**

### ✅ Immediate Cost Reduction Rules:
1. **Batch Operations**: Use `multi_edit()` instead of multiple `edit()` calls
2. **Minimize Screenshots**: Screenshot tool is expensive - use only for final verification
3. **Efficient Workflow Restarts**: Group changes → restart ONCE → verify ONCE
4. **Strategic Tool Usage**: 
   - Use `search_codebase()` before targeted `read()` operations
   - Avoid redundant `refresh_all_logs()` calls
   - Minimize `architect` tool usage for simple changes

### 🎯 Operational Patterns:
**OLD Pattern (Expensive):**
```
edit() → restart → screenshot → edit() → restart → screenshot
```
**NEW Pattern (Cost-Optimized):**
```
multi_edit() → restart ONCE → screenshot ONCE (if needed)
```

### 📊 Cost-Effective Workflow:
1. **Plan First** (Free planning mode)
2. **Batch All Changes** in single session
3. **Test in Browser** instead of frequent screenshots  
4. **Final Verification** with minimal tool usage
5. **Production Safety** maintained through careful change grouping

### 🔒 Production Safety Rules:
- All cost optimizations must maintain production stability
- No experimental changes to production code
- Group UI/CSS changes for batch deployment
- Verify functionality before marking tasks complete

Current Mode: PRODUCTION AUTOSCALE - Bot and Game running as unified autoscale deployment on torah-project-jobjoyclub.replit.app. Webhook mode for efficient request-based scaling.

**SECURITY-HARDENED VERSION - September 05, 2025 - 23:47 MSK**
✅ PRODUCTION READY - All systems optimized and deployment-ready
✅ DEPLOYMENT PROTECTION - Блокировки против переключения в development без согласования
✅ HTTP SESSION LEAKS FIXED - Proper resource cleanup and context managers implemented
✅ GRACEFUL SHUTDOWN - Signal handlers and automatic resource cleanup on termination
✅ Telegram Mini App "Shabbat Runner: Kedusha Path" - FULLY FUNCTIONAL
✅ Production Autoscale Deployment - Unified bot + game deployment
✅ Game URL: https://torah-project-jobjoyclub.replit.app/game (production autoscale)
✅ Health Check Endpoint: /health returns {"status":"healthy","service":"torah-bot-unified"}
✅ Rabbi Photo Integration - Startup screen image fixed and cached for faster loading
✅ Callback Query Fix - Inline buttons now work correctly (chat_id extraction fixed)
✅ Webhook Mode Fixed - Production webhook properly configured on torah-project domain
✅ Newsletter System - 9 AM Moscow time daily broadcasts operational via GitHub Actions
✅ All Endpoints Working - /health, /webhook, /game, startup images cached
✅ TRUE UNIFIED SERVICE - Single entry point (unified_webhook_service.py) for all functions
✅ Production URL Resolution - Forced correct domain for autoscale deployment
✅ SECURITY ENFORCEMENTS - Active protection against unauthorized development mode switches

# System Architecture
The bot utilizes a production-ready modular architecture with separated functional modules for Rabbi, Quiz, Donation, Language, and Analytics. Key technical implementations include retry logic for Telegram API calls via `httpx`, optimized OpenAI prompts for efficiency, lightweight analytics tracking, automatic session cleanup, and comprehensive error recovery. The system uses pure async long polling for Reserved VM deployment compatibility, eliminating the need for Flask or other HTTP servers.

**Production Features:**
- Smart deployment mode detection via `main.py` entry point
- Production orchestrator (`production_main.py`) with graceful shutdown
- Comprehensive safety checks (`deployment_config.py`) 
- 24/7 microservices architecture (Newsletter API, Backup Service, Scheduled Broadcasts)
- Automatic fallback mechanisms and error recovery
- Autoscale deployment optimizations with health monitoring
- Telegram Mini App fully integrated and tested

AI-powered content generation leverages GPT-5/GPT-4o (with fallback) for dynamic wisdom and quiz questions, and DALL-E 3 for image creation. A robust multi-level image generation fallback system ensures high success rates even with API limitations. All AI prompts are externalized to the `prompts/` directory for easy editing and hot reloading.

The bot supports multilingual interactions (English, Russian, Hebrew, Spanish, French, German, Italian, Portuguese, Arabic) with automatic language detection and consistent language application across all UI elements and messages. Context management is crucial, maintaining `current_topic` for coherent AI responses.

UI/UX prioritizes user experience with animated placeholders, automatic cleanup of loading messages, and utilization of native Telegram features for quizzes. Wisdom responses are concise (max 1 paragraph, 400 tokens) and designed with a warm, grandfather-rabbi personality. Performance is optimized with parallel processing for wisdom and image generation, significantly reducing response times.

A complete newsletter system is integrated, featuring a PostgreSQL database for user management and broadcast tracking. It supports AI-powered content generation in 7 languages, DALL-E 3 image integration, scheduled mass delivery with rate limiting, and analytics.

The project maintains a comprehensive test suite for critical functionality, AI integration, and production deployment readiness, ensuring a 100% production-ready status with clean code, proper type safety, and optimized dependencies.

# External Dependencies
- **httpx**: For asynchronous HTTP requests, primarily for Telegram API calls.
- **openai**: Provides AI capabilities for text generation (GPT-5, GPT-4o fallback) and image creation (DALL-E 3).
- **python-dotenv**: For managing environment variables securely.
- **fastapi + uvicorn**: Web server for Telegram Mini App game serving.
- **asyncpg**: PostgreSQL async database connection for newsletter system.

# Development Workflow
**UNIFIED DEPLOYMENT ARCHITECTURE - September 01, 2025**
- **universal_main.py**: Single universal entry point for all deployment modes
- Auto-detects environment (Development/Autoscale/Production)
- Intelligent mode selection (Webhook for Autoscale, Polling for Reserved VM)
- Unified health checks and service naming
- **Deprecated**: main.py, production_main.py, autoscale_main.py, webhook_autoscale_main.py

**Development Mode**: Direct development workspace access via port 5000
**Autoscale Mode**: Request-based webhook architecture with scale-to-zero
**Production Override**: Polling mode can be forced with DEPLOYMENT_MODE=production

# Production Deployment Strategy
**STABLE AUTOSCALE DEPLOYMENT - September 01, 2025**:

**Sleep/Wake Behavior:**
- Autoscale засыпает через 15 минут без активности
- Просыпается мгновенно при первом запросе от Telegram
- Работает 24/7 по требованию - НЕ НУЖНО БЕСПОКОИТЬСЯ
- Webhook от Telegram автоматически "будит" бота
- Newsletter рассылка теперь работает через GitHub Actions для autoscale режима

**ELEGANT WAKE-UP ARCHITECTURE - September 16, 2025:**
- ✅ **External Wake-up**: Cron-job.org pings `/wake` endpoint to activate autoscale
- ✅ **Internal Scheduler**: Service manages broadcasts internally when awake
- ✅ **Atomic Deduplication**: Race condition fixed with INSERT ON CONFLICT logic
- ✅ **Time Windows**: Morning (06:00-12:00 MSK) and Evening (18:00-22:00 MSK)
- ✅ **Simple Cron Setup**: Single ping URL instead of complex broadcast triggers
- ✅ **Optimal Endpoints**: `/wake` (wake-up) and `/api/scheduler_status` (monitoring)

**TRUE UNIFIED SERVICE ARCHITECTURE - September 03, 2025**:
- **Run Command**: `python3 unified_webhook_service.py` (single entry point)
- **Critical Fixes Applied**:
  - ✅ Callback query chat_id extraction corrected (callback_query["message"]["chat"]["id"])
  - ✅ Production domain forced for autoscale (torah-project-jobjoyclub.replit.app)
  - ✅ Startup image path fixed and cached (rabbi_welcome.png in root)
  - ✅ Webhook configuration hardcoded for production reliability
- **Features**:
  - ✅ Atomic service initialization (3-second cold start)
  - ✅ Unified health endpoints with deployment detection
  - ✅ Single FastAPI app serving bot + game + API
  - ✅ Automatic webhook URL resolution for autoscale
  - ✅ Production-ready error handling and fallbacks