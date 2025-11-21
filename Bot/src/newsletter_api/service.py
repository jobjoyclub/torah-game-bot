#!/usr/bin/env python3
"""
Newsletter API Service - Internal Module
Внутренний микросервис для управления рассылками в рамках Torah Bot проекта
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import os
import sys
import httpx
import json
import asyncpg
import logging
from datetime import datetime, date

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from openai import OpenAI

logger = logging.getLogger(__name__)

class NewsletterAPIService:
    """Internal Newsletter API Service"""
    
    def __init__(self, telegram_client=None):
        # ENVIRONMENT VALIDATION for production robustness
        self._validate_environment()
        
        # Initialize OpenAI client (optional)
        self.openai_client = None
        if os.getenv('OPENAI_API_KEY'):
            try:
                self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
                logger.info("✅ OpenAI client initialized for newsletter service")
            except Exception as e:
                logger.warning(f"⚠️ OpenAI client initialization failed: {e}")
        else:
            logger.warning("⚠️ OPENAI_API_KEY not found - newsletter will use fallback responses")
            
        self.telegram_client = telegram_client  # Use shared telegram client
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('BOT_TOKEN')
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None
        self.db_pool = None
        # ANTI-SPAM PROTECTION
        self.last_broadcast_time = {}
        self.min_broadcast_interval = 300  # 5 minutes minimum between broadcasts
        self.daily_broadcast_limit = 10  # Maximum broadcasts per day
    
    def _categorize_telegram_error(self, response, user_id):
        """Categorize Telegram API errors for detailed tracking"""
        if not response:
            return "network_error"
            
        error_code = response.get('error_code', 0)
        description = response.get('description', '').lower()
        
        if error_code == 403 or 'forbidden' in description or 'blocked' in description:
            return "403_blocked"
        elif error_code == 429 or 'too many requests' in description:
            return "429_rate_limit"  
        elif error_code == 400 or 'bad request' in description:
            return "400_bad_request"
        elif 'network' in description or 'connection' in description:
            return "network_error"
        else:
            return "unknown_error"
    
    def _categorize_quiz_error(self, poll_response, message_response, user_id):
        """Categorize quiz-specific errors (poll + message combination)"""
        # Check poll response first (more critical)
        if poll_response and not poll_response.get('ok'):
            return self._categorize_telegram_error(poll_response, user_id)
        
        # Check message response if poll succeeded
        if message_response and not message_response.get('ok'):
            return self._categorize_telegram_error(message_response, user_id)
        
        # Both failed or no responses
        if not poll_response and not message_response:
            return "network_error"
        
        # Unknown failure case
        return "unknown_error"
    
    def _validate_environment(self):
        """Validate required environment variables with clear error messages"""
        # Check for bot token (either variant)
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('BOT_TOKEN')
        database_url = os.getenv('DATABASE_URL')
        openai_key = os.getenv('OPENAI_API_KEY')
        
        missing_required = []
        
        if not bot_token:
            missing_required.append('TELEGRAM_BOT_TOKEN or BOT_TOKEN')
        if not database_url:
            missing_required.append('DATABASE_URL')
        
        if missing_required:
            error_msg = f"❌ Missing required environment variables: {', '.join(missing_required)}"
            logger.error(error_msg)
            raise ValueError(f"Environment validation failed: {error_msg}")
            
        if not openai_key:
            logger.warning("⚠️ OPENAI_API_KEY not found - newsletter will use fallback responses")
            
        logger.info("✅ Environment validation passed for NewsletterAPIService")
        
    async def initialize(self):
        """Initialize database connection pool with validation and retry logic"""
        import asyncio
        
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("❌ DATABASE_URL environment variable is required")
            self.db_pool = None
            return
        
        # Retry logic with exponential backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.db_pool = await asyncpg.create_pool(database_url, min_size=0, max_size=4)
                logger.info("✅ Newsletter API Service: Database pool initialized")
                return
            except Exception as e:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️ Database pool initialization failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"❌ Database pool initialization failed after {max_retries} attempts: {e}")
                    # Don't raise - allow service to run in degraded mode
                    logger.warning("⚠️ Running in degraded mode - newsletter functionality limited")
                    self.db_pool = None
    
    async def close(self):
        """Close database pool"""
        if self.db_pool:
            await self.db_pool.close()
            logger.info("🔒 Newsletter API Service: Database pool closed")
    
    def _shuffle_quiz_using_main_bot(self, quiz_data):
        """Shuffle quiz options using MAIN BOT's shuffle function (no duplication)"""
        # Import and use main bot's OptimizedQuizModule shuffle function
        import sys, os
        import random
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Use same shuffle logic as main bot without class instantiation
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
        
        logger.info(f"🔀 Newsletter shuffled quiz: correct answer moved from position {original_correct_index} to {new_correct_index}")
        return quiz_data
    
    async def get_contextual_topic(self):
        """Generate contextual topic using WisdomTopicGenerator for uniqueness"""
        try:
            # Import WisdomTopicGenerator
            import sys, os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from torah_bot.wisdom_topics import WisdomTopicGenerator
            
            # Use WisdomTopicGenerator for unique topics
            unique_topic = await WisdomTopicGenerator.get_unique_topic(self.db_pool, days_back=14)
            logger.info(f"🔮 Selected unique wisdom topic: '{unique_topic}'")
            return unique_topic
            
        except Exception as e:
            logger.error(f"❌ Error generating unique topic: {e}")
            # Fallback to original logic if WisdomTopicGenerator fails
            now = datetime.now()
            day_of_week = now.strftime('%A').lower()
            hour = now.hour
            
            if day_of_week == 'friday':
                return "подготовка к встрече Шаббата и духовное очищение" if hour >= 16 else "подготовка к Шаббату и завершение недели"
            elif day_of_week == 'saturday':
                return "радость Шаббата и духовное наслаждение"
            elif day_of_week == 'sunday':
                return "новые начинания и благословения недели"
            elif day_of_week == 'thursday' and hour >= 16:
                return "подготовка к завершению недели и духовные размышления"
            else:
                return "ежедневная мудрость и духовное наставление"

    def get_system_prompt(self, user_name: str = "Друг", language: str = "Russian"):
        """System prompt for AI wisdom generation"""
        return f"""Вы мудрый раввин, который делится теплой еврейской мудростью на основе Торы, Талмуда и еврейских традиций.

Отвечайте тепло, как дедушка-раввин со своим внуком {user_name}, включая:
1. Персонализированное приветствие для {user_name}
2. Мудрость из еврейских источников (Тора, Талмуд, Пиркей Авот, хасидские учения)  
3. Практическое применение сегодня
4. Легкий еврейский юмор когда уместно

Формат ответа (JSON):
{{
    "wisdom": "основной текст мудрости (1 параграф максимум)",
    "topic": "краткая тема на русском (3-5 слов)",
    "references": "точный источник (например: Пиркей Авот 1:14, Талмуд, Берахот 5а)"
}}

ВАЖНО: Ответ должен быть коротким (максимум 400 токенов), теплым и практичным."""

    async def generate_wisdom_using_main_bot(self, user_text: str, language: str = "Russian", user_name: str = "Друг") -> Dict[str, Any]:
        """Generate wisdom using EXACT same logic as main bot OptimizedRabbiModule"""
        # EXACT same fallback check as main bot
        if not self.openai_client:
            return {
                "wisdom": f"Спасибо, {user_name}. Тора учит нас, что мудрость приходит через изучение и размышления. Даже в неопределенности мы находим руководство через учебу и созерцание.",
                "topic": "Мудрость Торы и учение",
                "references": "Пиркей Авот 1:4"
            }
        
        # Initialize content variable to prevent unbound variable error (EXACT copy from main bot)
        content = ""
        
        try:
            # Import shared components that main bot uses
            import sys, os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from torah_bot.prompt_loader import PromptLoader
            import json
            
            # Load prompts from files for easy editing (EXACT same as main bot)
            prompt_loader = PromptLoader()
            system_prompt = prompt_loader.get_rabbi_wisdom_prompt(user_name, language, user_text)
            user_prompt = prompt_loader.get_user_wisdom_prompt(user_text)
            
            logger.info(f"🤖 AI GENERATING wisdom for: '{user_text}' (newsletter)")
            
            try:
                if self.openai_client is None:
                    raise ValueError("OpenAI client not initialized")
                    
                # EXACT same OpenAI call as main bot
                response = await asyncio.to_thread(
                    self.openai_client.chat.completions.create,
                    model="gpt-4o",  # SAME model as main bot
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_completion_tokens=400,  # SAME as main bot
                    temperature=0.7  # SAME as main bot
                )
                
                content = response.choices[0].message.content
                if content:
                    logger.info(f"🤖 OpenAI Response: {content[:100]}...")
                
            except Exception as api_error:
                logger.warning(f"GPT-4o with structured format failed, trying plain text: {api_error}")
                if self.openai_client is None:
                    raise ValueError("OpenAI client not available for fallback")
                    
                # EXACT same fallback logic as main bot
                response = await asyncio.to_thread(
                    self.openai_client.chat.completions.create,
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
                    logger.info(f"🤖 Fallback Response: {content[:100]}...")
            
            # EXACT same parsing logic as main bot
            try:
                if content is None:
                    raise ValueError("Empty content")
                
                # CRITICAL FIX: Clean markdown blocks before parsing (EXACT same as main bot - lines 1220-1223)
                if content.startswith("```json"):
                    content = content.replace("```json", "").replace("```", "").strip()
                elif content.startswith("```"):
                    content = content.replace("```", "").strip()
                
                wisdom_data = json.loads(content)
                # Validate structure (EXACT same validation as main bot)
                if (wisdom_data and 
                    all(key in wisdom_data for key in ['wisdom', 'topic', 'references']) and
                    wisdom_data.get('wisdom', '').strip() and 
                    wisdom_data.get('topic', '').strip()):
                    logger.info("✅ JSON parse successful with validation!")
                    return wisdom_data
                else:
                    logger.warning("❌ JSON valid but missing required fields")
                    raise ValueError("Invalid wisdom structure")
            except (json.JSONDecodeError, ValueError) as parse_error:
                logger.warning(f"❌ JSON parsing failed: {parse_error}")
                # EXACT same fallback parsing as main bot
                return self._get_fallback_wisdom_from_text(content or "", user_text)
                
        except Exception as e:
            logger.error(f"❌ Wisdom generation failed completely: {e}")
            # EXACT same final fallback as main bot
            return self._get_fallback_wisdom(user_text)
    
    def _get_fallback_wisdom_from_text(self, content: str, user_text: str) -> Dict[str, Any]:
        """EXACT copy of main bot's fallback wisdom parsing"""
        try:
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            wisdom_text = lines[0] if lines else content[:300]
            
            return {
                "wisdom": wisdom_text,
                "topic": "Еврейская мудрость",
                "references": "Еврейская традиция"
            }
        except Exception:
            return self._get_fallback_wisdom(user_text)
    
    def _get_fallback_wisdom(self, user_text: str) -> Dict[str, Any]:
        """EXACT copy of main bot's _get_fallback_wisdom method"""
        fallback_wisdom = [
            {
                "wisdom": "\"Кто мудр? Тот, кто учится у каждого человека.\" Каждый день дает нам новые возможности для роста и понимания.",
                "topic": "Учение и мудрость",
                "references": "Пиркей Авот 4:1"
            },
            {
                "wisdom": "\"В месте, где нет людей, старайся быть человеком.\" Наша ответственность - быть светом в темноте.",
                "topic": "Лидерство и ответственность", 
                "references": "Пиркей Авот 2:5"
            },
            {
                "wisdom": "\"Мир стоит на трех вещах: на справедливости, истине и мире.\" Эти принципы направляют нашу повседневную жизнь.",
                "topic": "Основы праведной жизни",
                "references": "Пиркей Авот 1:18"
            }
        ]
        
        # EXACT same selection logic as main bot
        import hashlib
        hash_obj = hashlib.md5(user_text.encode())
        hash_int = int(hash_obj.hexdigest(), 16)
        selected_wisdom = fallback_wisdom[hash_int % len(fallback_wisdom)]
        
        logger.info(f"📚 Using fallback wisdom: {selected_wisdom['topic']}")
        return selected_wisdom

    async def generate_image(self, topic: str):
        """Generate DALL-E 3 image using EXACT SAME logic as main bot with graceful fallback"""
        # GRACEFUL DEGRADATION: Return None if OpenAI not available
        if not self.openai_client:
            logger.warning("⚠️ OpenAI client not available - skipping image generation")
            return None
            
        max_retries = 2  # Same as main bot
        
        # EXACT same fallback logic as main bot
        fallback_prompts = [
            # Primary: Enhanced adaptive prompt (same as main bot)
            lambda: self._get_enhanced_image_prompt(topic),
            # Fallback 1: Simplified prompt (same as main bot)
            lambda: f"Beautiful spiritual Jewish artwork: {topic}. Pixar style, warm lighting, peaceful, no text.",
            # Fallback 2: Ultra-simple prompt (same as main bot)
            lambda: "Peaceful Jewish spiritual artwork, warm golden light, Torah scrolls, no text."
        ]
        
        for attempt in range(max_retries):
            for prompt_index, prompt_func in enumerate(fallback_prompts):
                try:
                    prompt = prompt_func()
                    
                    logger.info(f"🎨 Newsletter image generation attempt {attempt+1}, prompt {prompt_index+1}: {prompt[:50]}...")
                    
                    response = await asyncio.to_thread(
                        self.openai_client.images.generate,
                        model="dall-e-3",
                        prompt=prompt,
                        size="1024x1024",
                        quality="hd" if prompt_index == 0 else "standard"  # HD only for primary (same as main bot)
                    )
                    
                    if response.data and len(response.data) > 0 and response.data[0].url:
                        logger.info(f"✅ Newsletter image generated successfully on attempt {attempt+1}, prompt {prompt_index+1}")
                        return response.data[0].url
                    else:
                        logger.warning(f"⚠️ Empty response from DALL-E on attempt {attempt+1}, prompt {prompt_index+1}")
                        
                except Exception as e:
                    error_type = type(e).__name__
                    logger.error(f"❌ Newsletter image generation failed attempt {attempt+1}, prompt {prompt_index+1}: {error_type}: {str(e)[:100]}")
                    
                    # EXACT same error handling as main bot
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
        
        logger.error("💥 All newsletter image generation attempts failed")
        return None
    
    def _get_enhanced_image_prompt(self, topic: str) -> str:
        """EXACT same enhanced image prompt logic as main bot"""
        # Use the same prompt loader as main bot for consistency and safety
        import sys, os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from torah_bot.prompt_loader import PromptLoader
        prompt_loader = PromptLoader()
        
        theme_elements = prompt_loader.get_theme_elements(topic)
        return prompt_loader.get_wisdom_image_prompt(topic, theme_elements)

    async def generate_quiz_using_main_bot(self, topic: str, language: str = "Russian") -> Dict[str, Any]:
        """Generate quiz using EXACT same logic as main bot OptimizedQuizModule with graceful fallback"""
        # GRACEFUL DEGRADATION: Return fallback quiz if OpenAI not available
        if not self.openai_client:
            logger.warning("⚠️ OpenAI client not available - returning fallback quiz")
            return {
                "question": f"What is the main teaching about {topic}?",
                "options": [
                    "Love and kindness towards others",
                    "Personal wealth accumulation",
                    "Individual success only",
                    "Ignoring community needs"
                ],
                "correct_answer": 0,
                "explanation": f"Jewish wisdom emphasizes love, kindness, and community responsibility in relation to {topic}."
            }
            
        try:
            # Import shared components that main bot uses
            import sys, os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from torah_bot.prompt_loader import PromptLoader
            import json
            import random
            
            # Use IDENTICAL logic to main bot's generate_quiz method
            logger.info(f"🤖 AI GENERATING quiz for topic: '{topic}' (newsletter)")
            
            # Load quiz prompt using SAME prompt loader as main bot
            prompt_loader = PromptLoader()
            
            # Get quiz prompt - EXACT same call as main bot
            duplicate_warning = ""  # Newsletter doesn't track duplicates
            prompt = prompt_loader.get_quiz_prompt(topic, language, duplicate_warning)
            logger.info(f"📝 Prompt loaded ({len(prompt)} chars)")
            
            # EXACT same OpenAI call as main bot
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model="gpt-4o",  # SAME model as main bot
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,  # SAME as main bot
                temperature=0.8   # SAME as main bot
            )
            
            quiz_content = response.choices[0].message.content
            if quiz_content is None:
                raise ValueError("Empty quiz content from OpenAI")
            quiz_content = quiz_content.strip()
            logger.info(f"🤖 OpenAI Response: {quiz_content[:200]}...")
            
            # EXACT same parsing logic as main bot
            try:
                quiz_data = json.loads(quiz_content)
                logger.info("✅ Direct JSON parse successful!")
                return quiz_data
            except json.JSONDecodeError:
                logger.info("⚡ Direct parse failed, trying cleanup...")
                
                # EXACT same cleanup logic as main bot
                if "```json" in quiz_content:
                    start = quiz_content.find("```json") + 7
                    end = quiz_content.find("```", start)
                    if end > start:
                        json_str = quiz_content[start:end].strip()
                        quiz_data = json.loads(json_str)
                        logger.info("✅ Cleanup successful!")
                        return quiz_data
                
                # If cleanup fails, extract manually
                lines = quiz_content.split('\n')
                extracted_content = []
                in_json = False
                for line in lines:
                    if '{' in line and not in_json:
                        in_json = True
                    if in_json:
                        extracted_content.append(line)
                    if '}' in line and in_json:
                        break
                
                if extracted_content:
                    json_str = '\n'.join(extracted_content)
                    quiz_data = json.loads(json_str)
                    logger.info("✅ Manual extraction successful!")
                    return quiz_data
                
                raise Exception("Failed to parse quiz data")
            
        except Exception as e:
            logger.error(f"❌ Quiz generation failed: {e}")
            # EXACT same fallback as main bot
            return {
                "question": "What is the first word of the Torah?",
                "options": ["Bereshit", "Vayomer", "Elohim", "Shamayim", "Beresheet", "Vayelech"],
                "correct_answer": 0,
                "explanation": "Bereshit (Genesis) means 'In the beginning' - the opening of Creation",
                "follow_up": "What does this teach us about new beginnings?"
            }

    def format_wisdom_message(self, wisdom_data, language="Russian"):
        """Format wisdom message EXACTLY like main bot"""
        # Use SAME localized headers as main bot
        wisdom_headers = {
            "Russian": {
                "general": "📖 <b>Мудрость Раввина</b>\n<i>✨ Ежедневная мудрость</i>\n\n",
                "sources": "📚 <b>Источники:</b> <i>{refs}</i>",
                "suggest_topic": "✍️ <i>Напишите тему, которая вас волнует, для следующей мудрости</i>"
            }
        }
        
        headers = wisdom_headers.get(language, wisdom_headers["Russian"])
        wisdom_header = headers["general"]
        
        # Enhanced formatting for better readability - SAME as main bot
        wisdom_content = wisdom_data["wisdom"]
        if len(wisdom_content) > 200:
            wisdom_content = wisdom_content.replace('. ', '.\n\n')
            wisdom_content = '\n\n'.join([p.strip() for p in wisdom_content.split('\n\n') if p.strip()])
        
        sources_text = headers["sources"].format(refs=wisdom_data['references'])
        suggest_topic_text = headers["suggest_topic"]
        
        # EXACT format as main bot
        return f"""{wisdom_header}💫 {wisdom_content}

─────────────────

{sources_text}

{suggest_topic_text}"""

    def format_quiz_follow_up_message(self, language: str = "Russian") -> str:
        """Format follow-up message EXACTLY like main bot"""
        # Use SAME localized text as main bot
        if language == "Russian":
            return "🧠 Интересно знать больше о еврейской мудрости? Выберите действие:"
        else:
            return "🧠 Want to learn more about Jewish wisdom? Choose an action:"

    def get_keyboard(self, language="Russian", wisdom_content=""):
        """Get inline keyboard buttons EXACTLY like main bot"""
        # Use SAME buttons as main bot with localization
        wisdom_buttons = {
            "Russian": {
                "another": "🔄 Еще мудрость",
                "quiz": "🧠 Викторина", 
                "share": "📤 Поделиться мудростью",
                "menu": "🏠 Главное меню"
            }
        }
        
        buttons = wisdom_buttons.get(language, wisdom_buttons["Russian"])
        
        # Prepare wisdom sharing message - SAME as main bot
        wisdom_preview = wisdom_content[:100] + ('...' if len(wisdom_content) > 100 else '')
        share_wisdom_message = f"📖 Ежедневная мудрость Торы: {wisdom_preview} 🙏 Присоединяйтесь к нашему сообществу мудрости!"
        
        # EXACT keyboard structure as main bot
        return {
            "inline_keyboard": [
                [{"text": buttons["another"], "callback_data": "rabbi_wisdom"}],
                [{"text": buttons["quiz"], "callback_data": "torah_quiz"}],
                [{"text": buttons["share"], "switch_inline_query": share_wisdom_message}],
                [{"text": buttons["menu"], "callback_data": "main_menu"}]
            ]
        }

    async def send_broadcast(self, topic: Optional[str] = None, language: str = "Russian", user_name: str = "Друг"):
        """Send broadcast using internal service with anti-spam protection"""
        try:
            # ANTI-SPAM: Check rate limiting
            import time
            current_time = time.time()
            today_key = datetime.now().strftime('%Y-%m-%d')
            broadcast_key = f"{topic}_{language}"
            
            # Check minimum interval between broadcasts
            if broadcast_key in self.last_broadcast_time:
                time_since_last = current_time - self.last_broadcast_time[broadcast_key]
                if time_since_last < self.min_broadcast_interval:
                    remaining = int(self.min_broadcast_interval - time_since_last)
                    logger.warning(f"❌ RATE LIMIT: Too soon for broadcast '{topic}', wait {remaining}s")
                    return {
                        "success": False,
                        "message": f"Rate limited: wait {remaining} seconds",
                        "sent_count": 0,
                        "failed_count": 0,
                        "topic": topic,
                        "has_image": False,
                        "rate_limited": True
                    }
            
            # Update last broadcast time
            self.last_broadcast_time[broadcast_key] = current_time
            
            # Determine topic
            # USE DEDUPLICATION LOGIC instead of get_contextual_topic
            if topic:
                topic_text = topic
            else:
                try:
                    # DYNAMIC IMPORT to ensure path resolution works
                    import sys, os
                    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    from torah_bot.wisdom_topics import WisdomTopicGenerator
                    from datetime import date
                    
                    topic_text = await WisdomTopicGenerator.get_unique_topic(
                        db_pool=self.db_pool,
                        days_back=14,  # Check last 14 days for uniqueness
                        prefer_contextual=True  # Use day-specific topics when available
                    )
                    logger.info(f"🎯 Generated unique wisdom topic: '{topic_text}'")
                    
                    # Save topic to database for tracking
                    await WisdomTopicGenerator.save_wisdom_topic(
                        db_pool=self.db_pool,
                        topic=topic_text,
                        broadcast_date=date.today(),
                        status='generating'
                    )
                    
                except Exception as e:
                    logger.warning(f"⚠️ Unique topic generation failed: {e} - using fallback")
                    topic_text = await self.get_contextual_topic()
            
            logger.info(f"🚀 Internal API: Starting broadcast with topic: {topic_text}")
            
            # Get subscribers from database
            if self.db_pool is None:
                raise ValueError("Database pool not initialized")
            async with self.db_pool.acquire() as conn:
                subscribers = await conn.fetch("""
                    SELECT user_id, language 
                    FROM newsletter_subscriptions 
                    WHERE is_active = TRUE
                """)
            
            if not subscribers:
                return {
                    "success": False,
                    "message": "No active subscribers found",
                    "sent_count": 0,
                    "failed_count": 0,
                    "topic": topic_text,
                    "has_image": False
                }
            
            # Generate content in parallel using MAIN BOT logic
            wisdom_task = asyncio.create_task(
                self.generate_wisdom_using_main_bot(topic_text, language, user_name)
            )
            image_task = asyncio.create_task(self.generate_image(topic_text))
            
            wisdom_data = await wisdom_task
            image_url = await image_task
            
            # Format message EXACTLY like main bot
            wisdom_text = self.format_wisdom_message(wisdom_data, language)
            keyboard = self.get_keyboard(language, wisdom_data["wisdom"])
            
            # CREATE BROADCAST RECORD for tracking (SAFE: doesn't affect message sending)
            broadcast_id = None
            try:
                if self.db_pool:
                    async with self.db_pool.acquire() as conn:
                        # Create broadcast record in newsletter_broadcasts for tracking
                        import json
                        broadcast_content = json.dumps({
                            "type": "wisdom",
                            "topic": wisdom_data.get("topic", topic_text),
                            "wisdom": wisdom_data.get("wisdom", ""),
                            "references": wisdom_data.get("references", ""),
                            "language": language
                        })
                        
                        broadcast_id = await conn.fetchval("""
                            INSERT INTO newsletter_broadcasts 
                            (broadcast_date, wisdom_content, status, created_by, total_recipients)
                            VALUES (CURRENT_DATE, $1, 'sending', 'newsletter_api', $2)
                            RETURNING id
                        """, broadcast_content, len(subscribers))
                        
                        logger.info(f"📊 Created broadcast record #{broadcast_id} for tracking")
            except Exception as broadcast_error:
                logger.warning(f"⚠️ Could not create broadcast record: {broadcast_error} - continuing without tracking")
            
            # ANTI-SPAM: Record broadcast in database to prevent duplicates
            try:
                if self.db_pool:
                    async with self.db_pool.acquire() as conn:
                        # Check for recent duplicate broadcasts
                        recent_duplicate = await conn.fetchval("""
                            SELECT COUNT(*) FROM newsletter_broadcasts 
                            WHERE topic = $1 AND created_at > NOW() - INTERVAL '2 hours'
                        """, topic_text)
                        
                        if recent_duplicate > 0:
                            logger.warning(f"❌ DUPLICATE: Broadcast '{topic_text}' already sent recently")
                            return {
                                "success": False,
                                "message": "Duplicate broadcast prevented",
                                "sent_count": 0,
                                "failed_count": 0,
                                "topic": topic_text,
                                "has_image": False,
                                "duplicate_prevented": True
                            }
            except Exception as db_error:
                logger.warning(f"Duplicate check failed: {db_error}")
            
            # Send to all subscribers using shared telegram client
            sent_count = 0
            failed_count = 0
            error_breakdown = {
                "403_blocked": 0,        # User blocked bot
                "429_rate_limit": 0,     # Rate limiting
                "400_bad_request": 0,    # Bad request
                "network_error": 0,      # Connection issues
                "no_client": 0,          # No telegram client
                "unknown_error": 0       # Other errors
            }
            
            for subscriber in subscribers:
                try:
                    user_id = subscriber['user_id']
                    
                    if image_url and self.telegram_client:
                        # Use telegram client for sending with image
                        response = await self.telegram_client.send_photo(
                            chat_id=user_id,
                            photo_url=image_url,
                            caption=wisdom_text,
                            reply_markup=keyboard
                        )
                    elif self.telegram_client:
                        # Use telegram client for text message
                        response = await self.telegram_client.send_message(
                            chat_id=user_id,
                            text=wisdom_text,
                            parse_mode="HTML",
                            reply_markup=keyboard
                        )
                    else:
                        # Fallback to direct HTTP (shouldn't happen)
                        logger.warning(f"⚠️ No telegram client available for user {user_id}")
                        failed_count += 1
                        error_breakdown["no_client"] += 1
                        continue
                    
                    if response and response.get('ok'):
                        sent_count += 1
                        telegram_message_id = response.get('result', {}).get('message_id')
                        logger.info(f"✅ Newsletter sent to user {user_id}")
                        
                        # ADD DELIVERY TRACKING (SAFE: doesn't affect message sending)
                        try:
                            if self.db_pool and broadcast_id:
                                async with self.db_pool.acquire() as conn:
                                    # Insert delivery log record
                                    await conn.execute("""
                                        INSERT INTO delivery_log 
                                        (broadcast_id, user_id, status, delivered_at, telegram_message_id)
                                        VALUES ($1, $2, 'sent', NOW(), $3)
                                    """, broadcast_id, user_id, telegram_message_id)
                                    
                                    # Update subscription counter
                                    await conn.execute("""
                                        UPDATE newsletter_subscriptions 
                                        SET total_deliveries = total_deliveries + 1,
                                            last_delivery = NOW()
                                        WHERE user_id = $1 AND is_active = TRUE
                                    """, user_id)
                        except Exception as tracking_error:
                            logger.warning(f"⚠️ Delivery tracking failed for user {user_id}: {tracking_error}")
                    else:
                        failed_count += 1
                        error_type = self._categorize_telegram_error(response, user_id)
                        error_breakdown[error_type] += 1
                        logger.error(f"❌ Newsletter failed for user {user_id} ({error_type}): {response}")
                        
                        # ADD FAILED DELIVERY TRACKING (SAFE)
                        try:
                            if self.db_pool and broadcast_id:
                                async with self.db_pool.acquire() as conn:
                                    await conn.execute("""
                                        INSERT INTO delivery_log 
                                        (broadcast_id, user_id, status, error_message, scheduled_at)
                                        VALUES ($1, $2, 'failed', $3, NOW())
                                    """, broadcast_id, user_id, str(response))
                                    
                                    # CRITICAL: Mark user as blocked if 403 error (user blocked bot)
                                    if error_type == "403_blocked":
                                        await conn.execute("""
                                            UPDATE users 
                                            SET is_blocked = TRUE, updated_at = NOW()
                                            WHERE telegram_user_id = $1
                                        """, user_id)
                                        logger.info(f"🚫 Marked user {user_id} as blocked in database")
                        except Exception as tracking_error:
                            logger.warning(f"⚠️ Failed delivery tracking error for user {user_id}: {tracking_error}")
                    
                    await asyncio.sleep(0.1)  # Rate limiting
                    
                except Exception as e:
                    failed_count += 1
                    error_type = "network_error" if "network" in str(e).lower() or "connection" in str(e).lower() else "unknown_error"
                    error_breakdown[error_type] += 1
                    logger.error(f"❌ Exception sending to user {subscriber.get('user_id', 'unknown')} ({error_type}): {e}")
            
            success_rate = (sent_count / len(subscribers)) * 100
            
            logger.info(f"📊 Internal API broadcast complete: {sent_count}/{len(subscribers)} sent ({success_rate:.1f}%)")
            
            # UPDATE BROADCAST STATUS (SAFE: completing the tracking cycle)
            try:
                if self.db_pool and broadcast_id:
                    async with self.db_pool.acquire() as conn:
                        await conn.execute("""
                            UPDATE newsletter_broadcasts 
                            SET status = 'completed',
                                completed_at = NOW(),
                                successful_deliveries = $1,
                                failed_deliveries = $2
                            WHERE id = $3
                        """, sent_count, failed_count, broadcast_id)
                        logger.info(f"✅ Updated broadcast #{broadcast_id} status to completed")
            except Exception as status_error:
                logger.warning(f"⚠️ Could not update broadcast status: {status_error}")
            
            # Save wisdom topic ONLY if broadcast was successful
            if sent_count > 0:
                try:
                    from torah_bot.wisdom_topics import WisdomTopicGenerator
                    from datetime import date
                    save_success = await WisdomTopicGenerator.save_wisdom_topic(
                        self.db_pool, topic_text, date.today(), status='sent'
                    )
                    if save_success:
                        logger.info(f"💾 Saved wisdom topic '{topic_text}' after successful broadcast ({sent_count} delivered)")
                    else:
                        logger.warning(f"⚠️ Could not save wisdom topic '{topic_text}' - tracking may be incomplete")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to save wisdom topic after broadcast: {e}")
            else:
                logger.info(f"📝 Not saving wisdom topic '{topic_text}' - no messages delivered")
            
            return {
                "success": sent_count > 0,
                "message": f"Broadcast completed: {sent_count} sent, {failed_count} failed",
                "sent_count": sent_count,
                "failed_count": failed_count,
                "error_breakdown": error_breakdown,
                "topic": wisdom_data['topic'],
                "has_image": bool(image_url)
            }
            
        except Exception as e:
            logger.error(f"❌ Internal API broadcast error: {e}")
            return {
                "success": False,
                "message": f"Broadcast failed: {str(e)}",
                "sent_count": 0,
                "failed_count": 0,
                "error_breakdown": {"unknown_error": 0},
                "topic": locals().get('topic_text', 'unknown'),
                "has_image": False
            }

    async def get_stats(self):
        """Get newsletter statistics"""
        try:
            if self.db_pool is None:
                raise ValueError("Database pool not initialized")
            async with self.db_pool.acquire() as conn:
                # Total subscribers
                total_subs = await conn.fetchval("""
                    SELECT COUNT(*) FROM newsletter_subscriptions
                """)
                
                # Active subscribers
                active_subs = await conn.fetchval("""
                    SELECT COUNT(*) FROM newsletter_subscriptions WHERE is_active = TRUE
                """)
                
                # Language breakdown
                lang_breakdown = await conn.fetch("""
                    SELECT language, COUNT(*) as count 
                    FROM newsletter_subscriptions 
                    WHERE is_active = TRUE 
                    GROUP BY language
                """)
                
                # Convert to dict
                language_breakdown = {row['language']: row['count'] for row in lang_breakdown}
                
                return {
                    "total_subscribers": total_subs or 0,
                    "active_subscribers": active_subs or 0,
                    "language_breakdown": language_breakdown,
                    "last_broadcast_time": None,  
                    "total_broadcasts_sent": 0  
                }
                
        except Exception as e:
            logger.error(f"❌ Internal API stats error: {e}")
            return {
                "total_subscribers": 0,
                "active_subscribers": 0,
                "language_breakdown": {},
                "last_broadcast_time": None,
                "total_broadcasts_sent": 0
            }

    def get_quiz_keyboard(self, language="Russian", quiz_data=None) -> Dict[str, Any]:
        """Get quiz keyboard buttons EXACTLY like main bot"""
        # Use SAME buttons as main bot with localization
        if language == "Russian":
            more_wisdom_text = "📖 Еще мудрость"
            another_quiz_text = "🧠 Еще викторина"
            main_menu_text = "🏠 Главное меню"
            share_quiz_text = "📤 Поделиться квизом"
            share_quiz_message = f"🧠 Интересный квиз по еврейской мудрости: {quiz_data['question'][:50] if quiz_data else 'Torah Quiz'}... Попробуйте ответить!"
        else:
            more_wisdom_text = "📖 More Wisdom"
            another_quiz_text = "🧠 Another Quiz"
            main_menu_text = "🏠 Main Menu"
            share_quiz_text = "📤 Share Quiz"
            share_quiz_message = f"🧠 Interesting Torah quiz: {quiz_data['question'][:50] if quiz_data else 'Torah Quiz'}... Try to answer!"
        
        # EXACT keyboard structure as main bot
        return {
            "inline_keyboard": [
                [{"text": more_wisdom_text, "callback_data": "rabbi_wisdom"}],
                [{"text": another_quiz_text, "callback_data": "torah_quiz"}],
                [{"text": share_quiz_text, "switch_inline_query": share_quiz_message}],
                [{"text": main_menu_text, "callback_data": "main_menu"}]
            ]
        }

    async def send_quiz_broadcast(self, topic: Optional[str] = None, language: str = "Russian") -> Dict[str, Any]:
        """Send quiz broadcast to all subscribers with unique topic selection and concurrency protection"""
        try:
            # Import dependencies
            import sys, os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from torah_bot.quiz_topics import QuizTopicGenerator
            from datetime import date
            
            # Concurrency protection - prevent duplicate daily quiz broadcasts
            today = date.today()
            
            if not self.db_pool:
                logger.error("❌ Database pool not initialized for concurrency check")
                # Continue without protection if DB unavailable
            else:
                async with self.db_pool.acquire() as conn:
                    # Check if quiz already sent today
                    existing_quiz = await conn.fetchval("""
                        SELECT id FROM newsletter_broadcasts 
                        WHERE broadcast_date = $1 AND broadcast_type = 'quiz' 
                        AND status IN ('ready', 'completed')
                    """, today)
                    
                    if existing_quiz:
                        logger.warning(f"⚠️ Quiz already sent today ({today}) - skipping duplicate broadcast")
                        return {
                            "success": False,
                            "message": "Quiz already sent today - duplicate prevention",
                            "sent_count": 0,
                            "failed_count": 0,
                            "topic": "duplicate_prevented",
                            "quiz": True
                        }
            
            # Get unique topic if none provided
            if not topic:
                topic = await QuizTopicGenerator.get_unique_topic(self.db_pool, days_back=7)
                logger.info(f"🎯 QUIZ BROADCAST: Using unique topic '{topic}'")
            
            logger.info(f"🧠 QUIZ BROADCAST: Starting quiz broadcast with topic: {topic}")
            
            # Save topic to database with concurrency protection  
            save_success = await QuizTopicGenerator.save_quiz_topic(self.db_pool, topic, date.today())
            if not save_success:
                logger.warning(f"⚠️ Could not save quiz topic '{topic}' - continuing with broadcast")
            
            # Get subscribers from database
            if self.db_pool is None:
                raise ValueError("Database pool not initialized")
            async with self.db_pool.acquire() as conn:
                subscribers = await conn.fetch("""
                    SELECT user_id, language 
                    FROM newsletter_subscriptions 
                    WHERE is_active = TRUE
                """)
            
            if not subscribers:
                return {
                    "success": False,
                    "message": "No active subscribers found",
                    "sent_count": 0,
                    "failed_count": 0,
                    "topic": topic,
                    "quiz": True
                }
            
            # Generate quiz content using MAIN BOT module
            quiz_data = await self.generate_quiz_using_main_bot(topic, language)
            
            # CRITICAL FIX: Shuffle quiz options using MAIN BOT's shuffle function
            quiz_data = self._shuffle_quiz_using_main_bot(quiz_data)
            
            # Format follow-up message EXACTLY like main bot
            follow_up_text = self.format_quiz_follow_up_message(language)
            keyboard = self.get_quiz_keyboard(language, quiz_data)
            
            # Send to all subscribers using shared telegram client EXACTLY like main bot
            sent_count = 0
            failed_count = 0
            error_breakdown = {
                "403_blocked": 0,        # User blocked bot
                "429_rate_limit": 0,     # Rate limiting
                "400_bad_request": 0,    # Bad request
                "network_error": 0,      # Connection issues
                "no_client": 0,          # No telegram client
                "unknown_error": 0       # Other errors
            }
            
            for subscriber in subscribers:
                try:
                    user_id = subscriber['user_id']
                    
                    poll_success = False
                    message_success = False
                    poll_response = None
                    message_response = None
                    
                    if self.telegram_client:
                        # First send quiz POLL like main bot
                        poll_response = await self.telegram_client.send_poll(
                            chat_id=user_id,
                            question=quiz_data["question"],
                            options=quiz_data["options"],
                            correct_answer=quiz_data["correct_answer"],
                            explanation=quiz_data["explanation"]
                        )
                        
                        if poll_response and poll_response.get('ok'):
                            poll_success = True
                            # Then send follow-up message with buttons like main bot
                            message_response = await self.telegram_client.send_message(
                                chat_id=user_id,
                                text=follow_up_text,
                                reply_markup=keyboard
                            )
                            
                            if message_response and message_response.get('ok'):
                                message_success = True
                    else:
                        # Fallback to direct HTTP (shouldn't happen)
                        logger.warning(f"⚠️ No telegram client available for user {user_id}")
                        failed_count += 1
                        error_breakdown["no_client"] += 1
                        continue
                    
                    # Count as success if both poll and message sent successfully
                    if poll_success and message_success:
                        sent_count += 1
                        logger.info(f"✅ Quiz sent to user {user_id} (poll + message)")
                    else:
                        failed_count += 1
                        # Analyze poll and message responses for detailed error tracking
                        error_type = self._categorize_quiz_error(poll_response, message_response, user_id)
                        error_breakdown[error_type] += 1
                        status = f"poll:{poll_success}, message:{message_success}"
                        logger.error(f"❌ Quiz failed for user {user_id} ({error_type}): {status}")
                    
                    await asyncio.sleep(0.1)  # Rate limiting
                    
                except Exception as e:
                    failed_count += 1
                    error_type = "network_error" if "network" in str(e).lower() or "connection" in str(e).lower() else "unknown_error"
                    error_breakdown[error_type] += 1
                    user_info = subscriber.get('user_id', 'unknown') if 'subscriber' in locals() else 'unknown'
                    logger.error(f"❌ Exception sending quiz to user {user_info} ({error_type}): {e}")
            
            success_rate = (sent_count / len(subscribers)) * 100
            
            logger.info(f"✅ QUIZ BROADCAST complete: {sent_count}/{len(subscribers)} sent ({success_rate:.1f}%) - topic: '{topic}'")
            
            # Save quiz topic ONLY if broadcast was successful (matching wisdom logic)
            if sent_count > 0:
                try:
                    from torah_bot.quiz_topics import QuizTopicGenerator
                    from datetime import date
                    # Update status from 'ready' to 'sent' after successful broadcast
                    if self.db_pool:
                        async with self.db_pool.acquire() as conn:
                            await conn.execute("""
                                UPDATE newsletter_broadcasts 
                                SET status = 'sent'
                                WHERE broadcast_date = $1 AND broadcast_type = 'quiz' 
                                AND quiz_topic = $2
                            """, date.today(), topic)
                            logger.info(f"💾 Updated quiz topic '{topic}' status to 'sent' after successful broadcast ({sent_count} delivered)")
                    else:
                        logger.warning(f"⚠️ Could not update quiz topic status - database pool not available")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to update quiz topic status after broadcast: {e}")
            else:
                logger.info(f"📝 Not updating quiz topic '{topic}' status - no messages delivered")
            
            return {
                "success": sent_count > 0,
                "message": f"Quiz broadcast completed: {sent_count} sent, {failed_count} failed",
                "sent_count": sent_count,
                "failed_count": failed_count,
                "error_breakdown": error_breakdown,
                "topic": topic,
                "quiz": True
            }
            
        except Exception as e:
            logger.error(f"❌ Internal API quiz broadcast error: {e}")
            return {
                "success": False,
                "message": f"Quiz broadcast failed: {str(e)}",
                "sent_count": 0,
                "failed_count": 0,
                "error_breakdown": {"unknown_error": 0},
                "topic": topic if 'topic' in locals() else "unknown",
                "quiz": True
            }

    async def send_quiz_to_admin(self, admin_id: int) -> Dict[str, Any]:
        """Send quiz test to admin only"""
        try:
            # Use same topic generator as main bot
            import sys, os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from torah_bot.quiz_topics import QuizTopicGenerator
            topic = QuizTopicGenerator.get_random_topic()
            
            logger.info(f"🧠 Sending test quiz to admin {admin_id} with topic: {topic}")
            
            # Generate quiz content using MAIN BOT module
            quiz_data = await self.generate_quiz_using_main_bot(topic, "Russian")
            
            # CRITICAL FIX: Shuffle quiz options using MAIN BOT's shuffle function
            quiz_data = self._shuffle_quiz_using_main_bot(quiz_data)
            
            # Format messages EXACTLY like main bot
            follow_up_text = self.format_quiz_follow_up_message("Russian")
            keyboard = self.get_quiz_keyboard("Russian", quiz_data)
            
            # Send only to admin EXACTLY like main bot
            if self.telegram_client:
                # First send quiz POLL like main bot
                poll_response = await self.telegram_client.send_poll(
                    chat_id=admin_id,
                    question=quiz_data["question"],
                    options=quiz_data["options"],
                    correct_answer=quiz_data["correct_answer"],
                    explanation=quiz_data["explanation"]
                )
                
                if poll_response and poll_response.get('ok'):
                    # Then send follow-up message with buttons like main bot
                    response = await self.telegram_client.send_message(
                        chat_id=admin_id,
                        text=follow_up_text,
                        reply_markup=keyboard
                    )
                
                response = None  # Initialize response variable
                if response and response.get('ok'):
                    logger.info(f"✅ Test quiz sent to admin {admin_id}")
                    return {
                        "success": True,
                        "message": "Test quiz sent to admin",
                        "topic": topic,
                        "admin_id": admin_id
                    }
                else:
                    response_info = response if response else 'No response'
                    logger.error(f"❌ Failed to send test quiz to admin {admin_id}: {response_info}")
                    return {
                        "success": False,
                        "message": "Failed to send test quiz",
                        "topic": topic,
                        "admin_id": admin_id
                    }
            else:
                logger.error(f"❌ No telegram client available for admin {admin_id}")
                return {
                    "success": False,
                    "message": "No telegram client available",
                    "topic": topic,
                    "admin_id": admin_id
                }
                
        except Exception as e:
            logger.error(f"❌ Error sending test quiz to admin {admin_id}: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "topic": "unknown",
                "admin_id": admin_id
            }

# Global service instance
newsletter_service = None

async def get_newsletter_service(telegram_client=None):
    """Get or create newsletter service instance"""
    global newsletter_service
    if newsletter_service is None:
        newsletter_service = NewsletterAPIService(telegram_client)
        await newsletter_service.initialize()
    return newsletter_service

async def cleanup_newsletter_service():
    """Cleanup newsletter service"""
    global newsletter_service
    if newsletter_service:
        await newsletter_service.close()
        newsletter_service = None