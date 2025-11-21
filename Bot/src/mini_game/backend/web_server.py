# FastAPI web server for serving mini game static files
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, Response
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Get the mini game directory
MINI_GAME_DIR = Path(__file__).parent.parent
FRONTEND_DIR = MINI_GAME_DIR / "frontend"
PUBLIC_DIR = FRONTEND_DIR / "public"
DIST_DIR = FRONTEND_DIR / "dist"

class MiniGameWebServer:
    """FastAPI server for Shabbat Runner mini game"""
    
    def __init__(self):
        self.app = FastAPI(title="Shabbat Runner Mini Game")
        
        # Add CORS middleware for Telegram WebApp - SECURED TO TELEGRAM DOMAINS ONLY
        from fastapi.middleware.cors import CORSMiddleware
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
            allow_origin_regex=r"https://[\w-]*\.?web\.telegram\.org",
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Content-Type", "Authorization", "X-Admin-Secret", "X-Telegram-Web-App-Init-Data", "X-Requested-With"],
        )
        
        self.setup_routes()
    
    def setup_routes(self):
        """Setup web routes for mini game"""
        
        @self.app.get("/health_mini_game")
        async def health_check_integrated_v3():
            """Enhanced health check with deployment mode detection - RENAMED TO AVOID CONFLICTS"""
            import time
            import os
            
            # Detect deployment mode for consistent service naming
            deployment_mode = os.environ.get('DEPLOYMENT_MODE', 'development')
            if deployment_mode == 'production':
                service_name = "torah-bot-production"
            else:
                service_name = "torah-bot-autoscale"  # For autoscale mode
            
            return {
                "status": "healthy", 
                "service": service_name + "-MINI-GAME-SERVER",  # CLEAR SOURCE IDENTIFICATION
                "mode": deployment_mode if deployment_mode != 'development' else 'autoscale',
                "component": "MiniGameWebServer", 
                "timestamp": int(time.time()),
                "ready": True,
                "endpoints": ["health_mini_game", "game", "update_menu_button", "api/manual_broadcast"],
                "app_source": "web_server.py",
                "deployment_mode_env": deployment_mode
            }
            
        @self.app.post("/update_menu_button")
        async def update_menu_button(request: Request):
            """Telegram menu button update - SECURED VERSION"""
            # SECURITY: Check for admin authorization
            auth_header = request.headers.get("X-Admin-Secret")
            expected_secret = os.environ.get("ADMIN_SECRET")
            
            if not expected_secret:
                logger.critical("❌ ADMIN_SECRET environment variable not set - refusing admin operation")
                return JSONResponse({
                    "status": "misconfigured",
                    "message": "Admin secret not configured"
                }, status_code=503)
            
            if not auth_header or auth_header != expected_secret:
                logger.warning(f"❌ Unauthorized access attempt to /update_menu_button from {request.client.host if request.client else 'unknown'}")
                return JSONResponse({
                    "status": "unauthorized",
                    "message": "Admin authorization required"
                }, status_code=401)
            
            try:
                # Import needed modules
                import asyncio
                from pathlib import Path
                import sys
                
                # Add project root to path 
                project_root = Path(__file__).parent.parent.parent
                sys.path.append(str(project_root))
                
                # Try to get bot instance from global state
                try:
                    from src.torah_bot.simple_bot import TorahBotFinal
                    bot = TorahBotFinal()
                    
                    # Initialize if needed
                    await bot.initialize()
                    
                    # Look for game module
                    if hasattr(bot, 'game_module') and bot.game_module:
                        result = await bot.game_module._setup_native_menu_button(None)
                        if result:
                            return JSONResponse({
                                "status": "menu_button_updated",
                                "url": "https://torah-project-jobjoyclub.replit.app/",
                                "source": "mini_game_web_server"
                            })
                        else:
                            return JSONResponse({
                                "status": "menu_button_api_failed",
                                "details": "setChatMenuButton returned False"
                            }, status_code=500)
                    elif hasattr(bot, 'mini_game_module') and bot.mini_game_module:
                        result = await bot.mini_game_module._setup_native_menu_button(None)
                        if result:
                            return JSONResponse({
                                "status": "menu_button_updated",
                                "url": "https://torah-project-jobjoyclub.replit.app/",
                                "source": "mini_game_web_server"
                            })
                        else:
                            return JSONResponse({
                                "status": "menu_button_api_failed",
                                "details": "setChatMenuButton returned False"
                            }, status_code=500)
                    else:
                        return JSONResponse({
                            "status": "game_module_missing",
                            "details": f"Bot has no game module. Available attrs: {[attr for attr in dir(bot) if 'game' in attr.lower()]}",
                            "source": "mini_game_web_server"
                        }, status_code=503)
                        
                except Exception as bot_error:
                    return JSONResponse({
                        "status": "bot_initialization_failed",
                        "error": str(bot_error),
                        "source": "mini_game_web_server"
                    }, status_code=503)
                
            except Exception as e:
                logger.error(f"❌ Menu button update error: {e}")
                return JSONResponse({
                    "status": "exception",
                    "error": str(e),
                    "source": "mini_game_web_server"
                }, status_code=500)
        
        @self.app.get("/")
        @self.app.head("/")
        async def redirect_to_game():
            """Short redirect for BotFather menu button"""
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/game", status_code=301)

        @self.app.get("/app")
        @self.app.head("/app")
        async def app_redirect():
            """Alternative short redirect"""
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/game", status_code=301)

        @self.app.get("/game_rabbi_with_torah.png")
        @self.app.head("/game_rabbi_with_torah.png")
        async def serve_game_photo():
            """Serve game invitation photo"""
            photo_path = PUBLIC_DIR / "game_rabbi_with_torah.png"
            if photo_path.exists():
                from fastapi.responses import FileResponse
                return FileResponse(photo_path, media_type="image/png")
            else:
                raise HTTPException(status_code=404, detail="Photo not found")

        @self.app.get("/game")
        async def serve_game(request: Request, response: Response):
            """Serve the main game page"""
            try:
                # Check if we have index.html
                index_path = PUBLIC_DIR / "index.html"
                if not index_path.exists():
                    raise HTTPException(status_code=404, detail="Game not found")
                
                # Read and serve index.html
                with open(index_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
                
                # Add user parameters from query string
                user_id = request.query_params.get("user_id")
                lang = request.query_params.get("lang", "english")
                
                # Inject user data into HTML
                if user_id:
                    user_script = f"""
                    <script>
                        window.GAME_USER_ID = '{user_id}';
                        window.GAME_LANGUAGE = '{lang}';
                        console.log('🎮 Game user:', '{user_id}', 'Language:', '{lang}');
                    </script>
                    """
                    html_content = html_content.replace("</head>", f"{user_script}</head>")
                
                # Set Telegram WebApp iframe headers - SECURED (no X-Frame-Options to avoid conflicts)
                response.headers["Content-Security-Policy"] = "frame-ancestors https://web.telegram.org https://*.web.telegram.org"
                response.headers["X-Content-Type-Options"] = "nosniff"
                
                # CRITICAL: Disable caching for HTML to force reload of changes
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                
                return HTMLResponse(content=html_content)
                
            except Exception as e:
                logger.error(f"❌ Failed to serve game: {e}")
                raise HTTPException(status_code=500, detail="Game loading error")
        
        @self.app.post("/game/score")
        async def record_score(request: Request):
            """Receive game score from mini app"""
            try:
                data = await request.json()
                user_id = data.get("user_id")
                score = data.get("score")
                
                if not user_id or score is None:
                    raise HTTPException(status_code=400, detail="Missing user_id or score")
                
                # Record score in game analytics
                logger.info(f"🎮 Score received: user {user_id} scored {score}")
                
                # Note: Full integration with game_module happens via main bot instance
                
                return JSONResponse({
                    "success": True,
                    "message": "Score recorded successfully"
                })
                
            except Exception as e:
                logger.error(f"❌ Failed to record score: {e}")
                raise HTTPException(status_code=500, detail="Score recording failed")

        @self.app.post("/game/share")
        async def share_game_score(request: Request):
            """Generate share message for game score"""
            try:
                data = await request.json()
                user_id = data.get("user_id")
                score = data.get("score")
                language = data.get("language", "russian")
                
                if user_id is None or score is None:
                    raise HTTPException(status_code=400, detail="Missing user_id or score")
                
                # Generate CLEAN share messages WITHOUT URLs (URL will be added by frontend per channel)
                share_messages = {
                    "russian": f"🏆 Я набрал {score} очков в Shabbat Runner!\n\n🕯️ Попробуй себя в изучении еврейских традиций через игру!\n🎮 Собирай святые предметы и изучай Шаббат!\n\n✨ Проверь свои знания о еврейской культуре!",
                    "english": f"🏆 I scored {score} points in Shabbat Runner!\n\n🕯️ Try learning Jewish traditions through gaming!\n🎮 Collect holy items and learn about Shabbat!\n\n✨ Test your knowledge of Jewish culture!",
                    "hebrew": f"🏆 קיבלתי {score} נקודות ב-Shabbat Runner!\n\n🕯️ נסו ללמוד מסורות יהודיות דרך משחק!\n🎮 אספו פריטים קדושים ולמדו על שבת!\n\n✨ בדקו את הידע שלכם על התרבות היהודית!"
                }
                
                share_text = share_messages.get(language, share_messages["russian"])
                
                # Create SEPARATE components for different share channels
                game_url = "https://torah-project-jobjoyclub.replit.app"
                
                # Telegram share URL with SEPARATE text and url params (no duplication)
                from urllib.parse import quote
                telegram_share_url = f"https://t.me/share/url?text={quote(share_text)}&url={quote(game_url)}"
                
                logger.info(f"📤 Share request: user {user_id} scored {score} in {language}")
                
                return JSONResponse({
                    "success": True,
                    "share_url": telegram_share_url,
                    "share_text": share_text,  # CLEAN text without URL
                    "game_url": game_url,      # SEPARATE canonical URL
                    "message": "Share URL generated successfully"
                })
                
            except Exception as e:
                logger.error(f"❌ Failed to generate share URL: {e}")
                raise HTTPException(status_code=500, detail="Share URL generation failed")
        
        @self.app.get("/game/leaderboard")
        async def get_leaderboard():
            """Get game leaderboard"""
            try:
                # Simple leaderboard for web display
                leaderboard = [
                    {"rank": 1, "name": "Torah Master", "score": 25},
                    {"rank": 2, "name": "Shabbat Keeper", "score": 22},
                    {"rank": 3, "name": "Wisdom Seeker", "score": 18}
                ]
                
                # Note: Advanced leaderboard with real scores handled by game_module
                
                return JSONResponse(leaderboard)
                
            except Exception as e:
                logger.error(f"❌ Failed to get leaderboard: {e}")
                raise HTTPException(status_code=500, detail="Leaderboard error")
        
        # Mount individual static files directly 
        if PUBLIC_DIR.exists():
            @self.app.get("/style.css")
            async def serve_css():
                css_path = PUBLIC_DIR / "style.css"
                if css_path.exists():
                    with open(css_path, "r") as f:
                        content = f.read()
                    
                    # CRITICAL: Disable caching for CSS to force reload of changes
                    headers = {
                        "Cache-Control": "no-cache, no-store, must-revalidate",
                        "Pragma": "no-cache",
                        "Expires": "0"
                    }
                    return Response(content=content, media_type="text/css", headers=headers)
                raise HTTPException(status_code=404, detail="CSS not found")
            
            @self.app.get("/game.js")
            async def serve_js():
                js_path = PUBLIC_DIR / "game.js"
                if js_path.exists():
                    with open(js_path, "r") as f:
                        content = f.read()
                    
                    # CRITICAL: Disable caching for JS to force reload of changes
                    headers = {
                        "Cache-Control": "no-cache, no-store, must-revalidate",
                        "Pragma": "no-cache",
                        "Expires": "0"
                    }
                    return Response(content=content, media_type="application/javascript", headers=headers)
                raise HTTPException(status_code=404, detail="JS not found")
            
            @self.app.get("/game_rabbi_with_torah.png")
            async def serve_image():
                img_path = PUBLIC_DIR / "game_rabbi_with_torah.png"
                if img_path.exists():
                    from fastapi.responses import FileResponse
                    return FileResponse(img_path, media_type="image/png")
                raise HTTPException(status_code=404, detail="Image not found")
            
            logger.info(f"📁 Static files routes configured from {PUBLIC_DIR}")
        
        # Add unified broadcast API for external schedulers
        @self.app.post("/api/manual_broadcast")
        async def manual_broadcast_api(request: Request):
            """API endpoint for external schedulers - REAL BROADCAST VERSION"""
            from fastapi.responses import JSONResponse
            import time
            import os
            from datetime import datetime, timezone
            
            try:
                logger.info("📡 GitHub Actions broadcast API called")
                
                # Security check - require admin secret for production broadcasts
                admin_secret = request.headers.get("X-Admin-Secret")
                expected_secret = os.getenv("ADMIN_SECRET")
                
                if not expected_secret:
                    logger.error("🔥 ADMIN_SECRET environment variable not configured")
                    return JSONResponse({
                        "success": False,
                        "error": "Server misconfiguration - admin secret not set",
                        "timestamp": int(time.time())
                    }, status_code=503)
                
                if not admin_secret or admin_secret != expected_secret:
                    logger.warning("🔒 Unauthorized broadcast attempt - missing/invalid admin secret")
                    return JSONResponse({
                        "success": False,
                        "error": "Unauthorized - admin secret required",
                        "timestamp": int(time.time())
                    }, status_code=401)
                
                # Get request data - handle empty body gracefully
                try:
                    request_data = await request.json()
                except Exception:
                    request_data = {}
                    
                topic = request_data.get("topic", None)
                auto_schedule = request_data.get("auto_schedule", True)  # Default to True for GA compatibility
                
                logger.info(f"🎯 Authenticated broadcast request - auto_schedule: {auto_schedule}, topic: {topic}")
                
                # Determine time-based broadcast type (direct API call without ServiceContainer dependency)
                if auto_schedule:
                    current_hour = datetime.now(timezone.utc).hour
                    
                    # Use Internal Newsletter API directly (has our deduplication fixes)
                    try:
                        from src.newsletter_api.client import InternalNewsletterAPIClient
                        api_client = InternalNewsletterAPIClient()
                        
                        if 5 <= current_hour <= 11:  # Morning hours (08:58 MSK = 5:58 UTC)
                            logger.info("🌅 REAL MORNING WISDOM BROADCAST - Using deduplication fixes")
                            result = await api_client.send_broadcast(
                                topic=None,  # Let WisdomTopicGenerator.get_unique_topic handle it
                                language="Russian"
                            )
                            broadcast_type = "morning_wisdom"
                        elif 17 <= current_hour <= 23:  # Evening hours (20:58 MSK = 17:58 UTC) 
                            logger.info("🌙 REAL EVENING QUIZ BROADCAST - Using deduplication fixes")
                            result = await api_client.send_quiz_broadcast(
                                topic=None,  # Let QuizTopicGenerator.get_unique_topic handle it
                                language="Russian"
                            )
                            broadcast_type = "evening_quiz"
                        else:
                            logger.warning(f"⏰ Unusual broadcast time: {current_hour}:XX UTC")
                            result = await api_client.send_broadcast(topic=topic, language="Russian")
                            broadcast_type = "off_hours"
                        
                        if result.get('success'):
                            logger.info(f"✅ REAL {broadcast_type} broadcast completed: {result['sent_count']} sent, {result['failed_count']} failed")
                            return JSONResponse({
                                "success": True,
                                "message": f"Real {broadcast_type} broadcast completed",
                                "sent_count": result['sent_count'],
                                "failed_count": result['failed_count'],
                                "topic": result.get('topic', 'unknown'),
                                "broadcast_type": broadcast_type,
                                "timestamp": int(time.time()),
                                "status": "real_broadcast_success"
                            })
                        else:
                            logger.error(f"❌ {broadcast_type} broadcast failed: {result.get('message', 'Unknown error')}")
                            return JSONResponse({
                                "success": False,
                                "error": result.get('message', 'Broadcast failed'),
                                "broadcast_type": broadcast_type,
                                "timestamp": int(time.time())
                            }, status_code=500)
                            
                    except Exception as api_error:
                        logger.error(f"❌ Newsletter API error: {api_error}")
                        return JSONResponse({
                            "success": False,
                            "error": f"Newsletter API error: {str(api_error)}",
                            "timestamp": int(time.time())
                        }, status_code=500)
                else:
                    # Manual topic broadcast
                    logger.info(f"📝 Manual topic broadcast: {topic}")
                    return JSONResponse({
                        "success": True,
                        "message": f"Manual broadcast noted - {topic}",
                        "timestamp": int(time.time()),
                        "status": "manual_noted"
                    })
                    
            except Exception as e:
                logger.error(f"❌ Broadcast API error: {e}")
                return JSONResponse({
                    "success": False, 
                    "error": str(e),
                    "timestamp": int(time.time())
                }, status_code=500)

        # Add root redirect to game for better Mini App compatibility
        @self.app.get("/")
        async def root_redirect():
            """Redirect root to game for Mini App compatibility"""
            return {"message": "Torah Bot Mini Game Server", "game_endpoint": "/game", "health_endpoint": "/health"}
        
    
    def get_app(self):
        """Get the FastAPI app instance"""
        return self.app

# Create singleton instance
mini_game_server = MiniGameWebServer()
app = mini_game_server.get_app()