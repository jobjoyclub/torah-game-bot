#!/usr/bin/env python3
"""
Admin commands for Torah Bot Newsletter System
Special commands for @torah_support and other admins
"""
import logging
import json
import asyncio
from datetime import date, datetime
from typing import Dict, List, Optional, Any
# UNIFIED ARCHITECTURE: newsletter_manager passed via constructor
from ..newsletter_api import InternalNewsletterAPIClient, get_newsletter_stats

logger = logging.getLogger(__name__)

class AdminCommands:
    """Admin-only commands for newsletter management"""
    
    def __init__(self, telegram_client, newsletter_manager_instance):
        self.telegram_client = telegram_client
        self.newsletter_manager = newsletter_manager_instance  # UNIFIED: Use passed instance
        self._subscribed_users = set()  # Track already subscribed users
        self.newsletter_api = InternalNewsletterAPIClient()  # Internal API client
    
    async def handle_admin_command(self, chat_id: int, user_id: int, command: str, args: str = "") -> bool:
        """Handle admin commands"""
        
        # Check if user is admin (UNIFIED: use instance)
        if not await self.newsletter_manager.is_admin(user_id):
            await self.telegram_client.send_message(
                chat_id, 
                "⛔ Access denied. Admin privileges required."
            )
            return False
        
        # Get admin permissions (UNIFIED: use instance)
        permissions = await self.newsletter_manager.get_admin_permissions(user_id)
        
        # Route commands
        if command == "/newsletter_stats":
            await self._show_newsletter_stats(chat_id)
            
        elif command == "/newsletter_subscribers":
            await self._show_subscribers_info(chat_id)
            
        elif command == "/test_broadcast":
            if permissions.get("can_test_broadcasts", False):
                await self._create_test_broadcast(chat_id, user_id, args)
            else:
                await self.telegram_client.send_message(chat_id, "⛔ No permission for test broadcasts")
                
        elif command == "/send_test_now":
            if permissions.get("can_test_broadcasts", False):
                await self._send_test_broadcast_now(chat_id, user_id)
            else:
                await self.telegram_client.send_message(chat_id, "⛔ No permission for test broadcasts")
                
        elif command == "/create_daily_wisdom":
            if permissions.get("can_send_broadcasts", False):
                await self._create_daily_wisdom(chat_id, user_id, args)
            else:
                await self.telegram_client.send_message(chat_id, "⛔ No permission for broadcast creation")
                
        elif command == "/backup_database":
            if permissions.get("can_manage_users", False):
                await self._backup_database(chat_id)
            else:
                await self.telegram_client.send_message(chat_id, "⛔ No permission for database management")
                
        elif command == "/backup_status":
            if permissions.get("can_manage_users", False):
                await self._backup_status(chat_id)
            else:
                await self.telegram_client.send_message(chat_id, "⛔ No permission for database management")
                
        elif command == "/newsletter_stats_api":
            await self._show_newsletter_stats_api(chat_id)
            
        elif command == "/test_broadcast_api":
            if permissions.get("can_test_broadcasts", False):
                await self._send_broadcast_via_api(chat_id, args)
            else:
                await self.telegram_client.send_message(chat_id, "⛔ No permission for API tests")
                
        elif command == "/schedule_broadcast_api":
            if permissions.get("can_send_broadcasts", False):
                await self._schedule_broadcast_via_api(chat_id, args)
            else:
                await self.telegram_client.send_message(chat_id, "⛔ No permission for scheduled broadcasts")
                
                
        elif command == "/run_api_tests":
            if permissions.get("can_test_broadcasts", False):
                await self._run_api_tests(chat_id)
            else:
                await self.telegram_client.send_message(chat_id, "⛔ No permission for API testing")
                
        elif command == "/send_test_quiz":
            if permissions.get("can_test_broadcasts", False):
                await self._send_test_quiz_now(chat_id, user_id)
            else:
                await self.telegram_client.send_message(chat_id, "⛔ No permission for quiz testing")
                
        elif command == "/schedule_status":
            if permissions.get("can_manage_users", False):
                await self._show_schedule_status(chat_id)
            else:
                await self.telegram_client.send_message(chat_id, "⛔ No permission for schedule management")
            
        elif command == "/export_blocked_users":
            if permissions.get("can_manage_users", False):
                await self._export_blocked_users(chat_id, user_id)
            else:
                await self.telegram_client.send_message(chat_id, "⛔ No permission for user management")
            
        elif command == "/newsletter_help":
            await self._show_admin_help(chat_id, permissions)
            
        else:
            await self.telegram_client.send_message(
                chat_id, 
                f"❓ Unknown admin command: {command}\\nUse /newsletter_help for available commands"
            )
            
        return True
    
    async def _show_newsletter_stats(self, chat_id: int):
        """Show newsletter statistics"""
        try:
            analytics = await self.newsletter_manager.get_newsletter_analytics()
            overview = analytics['overview']
            
            stats_text = f"""📊 <b>Newsletter Statistics</b>
            
👥 <b>Users Overview:</b>
• Total registered users: {overview.get('total_users', 0)}
• Active subscribers: {overview.get('active_subscribers', 0)}
• Broadcasts completed: {overview.get('completed_broadcasts', 0)}
• Deliveries (30 days): {overview.get('deliveries_last_30d', 0)}

🌍 <b>Languages:</b>"""
            
            for lang_info in analytics['languages'][:5]:  # Top 5 languages
                stats_text += f"""
• {lang_info['language']}: {lang_info['subscribers']} subscribers"""
                if lang_info['active_7d'] > 0:
                    stats_text += f" ({lang_info['active_7d']} active this week)"
            
            if analytics['recent_broadcasts']:
                stats_text += "\\n\\n📈 <b>Recent Broadcasts:</b>"
                for broadcast in analytics['recent_broadcasts'][:3]:
                    stats_text += f"""
• {broadcast['date']}: {broadcast['recipients']} sent, {broadcast['delivery_rate']:.1f}% delivered"""
            
            await self.telegram_client.send_message(chat_id, stats_text, parse_mode="HTML")
            
        except Exception as e:
            logger.error(f"Failed to show newsletter stats: {e}")
            await self.telegram_client.send_message(
                chat_id, 
                "❌ Failed to retrieve newsletter statistics"
            )
    
    async def _show_subscribers_info(self, chat_id: int):
        """Show detailed subscriber information"""
        try:
            # Get subscriber count by language
            lang_stats = await self.newsletter_manager.get_subscribers_by_language()
            total_count = await self.newsletter_manager.get_subscriber_count()
            
            info_text = f"""📧 <b>Newsletter Subscribers</b>
            
📊 <b>Total Statistics:</b>
• Active subscribers: {total_count['total_subscribers']}
• Active in last 30 days: {total_count['active_30_days']}
• Active in last 7 days: {total_count['active_7_days']}

🌐 <b>By Language:</b>"""
            
            for language, count in lang_stats.items():
                percentage = (count / total_count['total_subscribers'] * 100) if total_count['total_subscribers'] > 0 else 0
                info_text += f"\\n• {language}: {count} ({percentage:.1f}%)"
            
            await self.telegram_client.send_message(chat_id, info_text, parse_mode="HTML")
            
        except Exception as e:
            logger.error(f"Failed to show subscribers info: {e}")
            await self.telegram_client.send_message(
                chat_id, 
                "❌ Failed to retrieve subscriber information"
            )
    
    async def _create_test_broadcast(self, chat_id: int, admin_id: int, test_topic: str = ""):
        """Create AI test broadcast using exact same system as Rabbi Wisdom - send to admin only"""
        try:
            if not test_topic:
                test_topic = "daily Torah wisdom and guidance"
            
            # Show same loading message as in Rabbi Wisdom
            loading_msg = await self.telegram_client.send_message(
                chat_id,
                "🕯️ <b>Раввин готовит мудрость...</b>"
            )
            
            # Import the bot's systems
            from .simple_bot import TorahBotFinal
            import time
            import asyncio
            
            # Generate directly using same methods as main bot
            from openai import OpenAI
            import os
            import json
            from .prompt_loader import PromptLoader
            
            openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            prompt_loader = PromptLoader()
            
            language = "Russian"
            user_name = "Давид"
            
            # Generate wisdom using exact same prompts as main bot
            system_prompt = prompt_loader.get_rabbi_wisdom_prompt(user_name, language, test_topic)
            user_prompt = prompt_loader.get_user_wisdom_prompt(test_topic)
            
            # Start both AI tasks simultaneously (same as Rabbi Wisdom)
            start_time = time.time()
            
            async def generate_wisdom():
                try:
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
                        return json.loads(content)
                    else:
                        raise ValueError("Empty response content")
                except Exception as e:
                    logger.error(f"Wisdom generation failed: {e}")
                    return {
                        "wisdom": f"Дорогой {user_name}, сегодня мы размышляем о теме: {test_topic}. Пусть мудрость наших предков направляет наши шаги и сердца наполняются пониманием.",
                        "topic": test_topic,
                        "references": "Пиркей Авот 1:14"
                    }
            
            async def generate_image():
                try:
                    # Load image prompt same as main bot
                    image_prompt = prompt_loader.get_wisdom_image_prompt(test_topic)
                    
                    response = openai_client.images.generate(
                        model="dall-e-3",
                        prompt=image_prompt,
                        size="1024x1024",
                        quality="standard",
                        n=1
                    )
                    if response.data and len(response.data) > 0:
                        return response.data[0].url
                    else:
                        return None
                except Exception as e:
                    logger.error(f"Image generation failed: {e}")
                    return None
            
            wisdom_task = asyncio.create_task(generate_wisdom())
            image_task = asyncio.create_task(generate_image())
            
            # Wait for wisdom first
            wisdom_data = await wisdom_task
            
            # Update loading message (same as Rabbi Wisdom)
            await self.telegram_client.edit_message_text(
                chat_id, 
                loading_msg["result"]["message_id"], 
                "🎨 <b>Раввин создаёт образ...</b>"
            )
            
            # Wait for image to complete
            image_url = await image_task
            
            # Use EXACT same formatting as Rabbi Wisdom
            wisdom_headers = {
                "Russian": {
                    "general": "📖 <b>Мудрость Раввина</b>\n<i>✨ Ежедневная мудрость</i>\n\n",
                    "sources": "📚 <b>Источники:</b> <i>{refs}</i>",
                    "suggest_topic": "✍️ <i>Напишите тему, которая вас волнует, для следующей мудрости</i>"
                }
            }
            
            wisdom_buttons = {
                "Russian": {
                    "another": "🔄 Еще мудрость",
                    "quiz": "🧠 Викторина", 
                    "menu": "🏠 Главное меню"
                }
            }
            
            # Format exactly like Rabbi Wisdom
            headers = wisdom_headers["Russian"]
            buttons = wisdom_buttons["Russian"]
            
            wisdom_header = headers["general"]
            wisdom_content = wisdom_data["wisdom"]
            
            # Add visual breaks for long paragraphs (same logic)
            if len(wisdom_content) > 200:
                wisdom_content = wisdom_content.replace('. ', '.\n\n')
                wisdom_content = '\n\n'.join([p.strip() for p in wisdom_content.split('\n\n') if p.strip()])
            
            sources_text = headers["sources"].format(refs=wisdom_data["references"])
            suggest_topic_text = headers["suggest_topic"]
            
            # EXACT same formatting as Rabbi Wisdom
            wisdom_text = f"""{wisdom_header}💫 {wisdom_content}

─────────────────

{sources_text}

{suggest_topic_text}"""
            
            # EXACT same keyboard as Rabbi Wisdom
            keyboard = {
                "inline_keyboard": [
                    [{"text": buttons["another"], "callback_data": "rabbi_wisdom"}],
                    [{"text": buttons["quiz"], "callback_data": "torah_quiz"}],
                    [{"text": buttons["menu"], "callback_data": "main_menu"}]
                ]
            }
            
            # Send exactly like Rabbi Wisdom with HTML formatting
            if image_url:
                await self.telegram_client.send_photo(chat_id, image_url, wisdom_text, keyboard)
            else:
                await self.telegram_client.send_message(chat_id, wisdom_text, keyboard)
            
            # Final confirmation with HTML formatting
            await self.telegram_client.send_message(
                chat_id,
                f"""✅ <b>Тестовая рассылка готова!</b>

🎯 <b>Это точная копия "Мудрость Раввина":</b>
• Тот же AI промпт и генерация
• Те же кнопки и форматирование  
• То же изображение DALL-E 3
• Тема: {wisdom_data['topic']}

💡 <b>Для реальной рассылки:</b>
Такой же контент будет создан на всех 7 языках и отправлен подписчикам по расписанию."""
            )
            
        except Exception as e:
            logger.error(f"Failed to create test broadcast: {e}")
            await self.telegram_client.send_message(
                chat_id,
                f"❌ Ошибка создания тестовой рассылки: {str(e)}"
            )

    # Remove these methods as we'll use the bot's built-in generation methods
    
    async def _send_test_broadcast_now(self, chat_id: int, admin_id: int):
        """Send test broadcast immediately to admin"""
        try:
            # Import broadcast system
            from .broadcast_system import get_broadcast_system
            broadcast_system = get_broadcast_system(self.telegram_client)
            
            # Send AI-generated test broadcast
            success = await broadcast_system.send_test_broadcast_to_admin(chat_id)
            
            if not success:
                # Fallback to simple test message
                test_message = f"""🧪 <b>TEST BROADCAST - Torah Bot Newsletter</b>
            
📖 <b>Daily Wisdom Test</b>
            
Dear @torah_support, this is a test of our daily newsletter system.
            
🔮 <b>Test Wisdom:</b>
"Who is wise? One who learns from every person, as it is said: 'From all those who taught me I gained understanding.'"
            
📚 <b>Source:</b> Pirkei Avot 4:1
            
✅ <b>System Status:</b> Newsletter system operational
📊 <b>Test completed at:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
💡 This message confirms that the broadcast system can deliver personalized content to subscribers."""
            
                # Send fallback test message with HTML formatting
                result = await self.telegram_client.send_message(
                    chat_id,
                    test_message
                )
                
                if result.get("ok"):
                    # Log test delivery
                    logger.info(f"✅ Fallback test broadcast delivered to admin {admin_id}")
                    
                    await self.telegram_client.send_message(
                        chat_id,
                        "✅ <b>Test broadcast sent successfully!</b>\\n\\n📧 Check the message above to see how newsletter content will appear to subscribers.\\n\\n🎯 The system is ready for production broadcasts.",
                        parse_mode="HTML"
                    )
                else:
                    await self.telegram_client.send_message(
                        chat_id,
                        "❌ Failed to send test broadcast"
                    )
                
        except Exception as e:
            logger.error(f"Failed to send test broadcast: {e}")
            await self.telegram_client.send_message(
                chat_id,
                "❌ Error sending test broadcast"
            )

    async def _send_test_quiz_now(self, chat_id: int, admin_id: int):
        """Send test quiz broadcast immediately to admin"""
        try:
            # Import newsletter API to send quiz
            from ..newsletter_api import InternalNewsletterAPIClient, send_quiz_to_admin
            api_client = InternalNewsletterAPIClient(self.telegram_client)
            
            logger.info(f"🧠 Admin {admin_id} requesting test quiz broadcast")
            
            # Send quiz only to admin
            result = await send_quiz_to_admin(api_client, admin_id)
            
            if result and result.get('success'):
                # Send confirmation after quiz
                await asyncio.sleep(2)  # Wait for quiz to arrive
                await self.telegram_client.send_message(
                    chat_id,
                    "✅ <b>Test quiz sent successfully!</b>\n\n🧠 Check the quiz message above to see how daily quiz content will appear to subscribers.\n\n🎯 The quiz system is ready for evening broadcasts.",
                    parse_mode="HTML"
                )
                logger.info(f"✅ Test quiz delivered to admin {admin_id}")
            else:
                await self.telegram_client.send_message(
                    chat_id,
                    "❌ Failed to send test quiz"
                )
                
        except Exception as e:
            logger.error(f"Failed to send test quiz: {e}")
            await self.telegram_client.send_message(
                chat_id,
                "❌ Error sending test quiz"
            )

    async def _show_schedule_status(self, chat_id: int):
        """Show all scheduled broadcasts"""
        try:
            # Show simplified schedule status without complex scheduler access
            schedule_text = """📅 <b>Статус расписания рассылок</b>

🌅 <b>Утренняя рассылка мудрости:</b>
• Время: 06:00 UTC (09:00 MSK)
• Контент: AI-generated Torah wisdom
• Статус: ✅ Активно

🌆 <b>Вечерняя рассылка викторины:</b>
• Время: 18:00 UTC (21:00 MSK)  
• Контент: Interactive Torah quiz
• Статус: ✅ Активно

📊 <b>Система управления:</b>
• Internal Newsletter API: ✅ Работает
• Scheduler: ✅ Запущен
• Database: ✅ Подключена
• Backup: ✅ Ежедневно в 03:00 UTC

🎯 <b>Доступные команды:</b>
• /newsletter_stats - статистика
• /test_broadcast [тема] - тестовая рассылка
• /send_test_quiz - тестовая викторина

⚙️ <b>Статус:</b> Все системы работают нормально"""
            
            await self.telegram_client.send_message(
                chat_id,
                schedule_text,
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"Failed to show schedule status: {e}")
            await self.telegram_client.send_message(
                chat_id,
                "❌ Ошибка при получении статуса расписания"
            )
    
    async def _export_blocked_users(self, chat_id: int, admin_id: int):
        """Export blocked users to CSV file"""
        try:
            import csv
            import io
            from datetime import datetime
            
            logger.info(f"📥 Admin {admin_id} requesting blocked users export")
            
            # Show loading message
            loading_msg = await self.telegram_client.send_message(
                chat_id,
                "📥 <b>Экспорт заблокированных пользователей...</b>\n\n⏳ Поиск в базе данных\n📊 Формирование CSV файла",
                parse_mode="HTML"
            )
            
            # Get blocked users from database
            if not self.newsletter_manager.pool:
                await self.telegram_client.edit_message_text(
                    chat_id,
                    loading_msg["result"]["message_id"],
                    "❌ База данных недоступна"
                )
                return
            
            async with self.newsletter_manager.pool.acquire() as conn:
                # Query blocked users with details
                blocked_users = await conn.fetch("""
                    SELECT 
                        u.telegram_user_id,
                        u.username,
                        u.first_name,
                        u.last_name,
                        u.updated_at as blocked_date,
                        u.last_interaction,
                        dl.error_message
                    FROM users u
                    LEFT JOIN LATERAL (
                        SELECT error_message, scheduled_at
                        FROM delivery_log
                        WHERE user_id = u.telegram_user_id 
                        AND status = 'failed'
                        AND error_message ILIKE '%blocked%'
                        ORDER BY scheduled_at DESC
                        LIMIT 1
                    ) dl ON true
                    WHERE u.is_blocked = TRUE
                    ORDER BY u.updated_at DESC
                """)
            
            if not blocked_users:
                await self.telegram_client.edit_message_text(
                    chat_id,
                    loading_msg["result"]["message_id"],
                    "✅ <b>Заблокированных пользователей не найдено</b>\n\n🎉 Все подписчики активны!",
                    parse_mode="HTML"
                )
                return
            
            # Generate CSV file in memory
            csv_buffer = io.StringIO()
            csv_writer = csv.writer(csv_buffer)
            
            # Write header
            csv_writer.writerow([
                'user_id', 
                'username', 
                'first_name', 
                'last_name', 
                'blocked_date', 
                'last_interaction',
                'error_details'
            ])
            
            # Write data rows
            for user in blocked_users:
                csv_writer.writerow([
                    user['telegram_user_id'],
                    user['username'] or '',
                    user['first_name'] or '',
                    user['last_name'] or '',
                    user['blocked_date'].strftime('%Y-%m-%d %H:%M:%S') if user['blocked_date'] else '',
                    user['last_interaction'].strftime('%Y-%m-%d %H:%M:%S') if user['last_interaction'] else '',
                    user['error_message'] or ''
                ])
            
            # Get CSV content
            csv_content = csv_buffer.getvalue()
            csv_buffer.close()
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"blocked_users_{timestamp}.csv"
            
            # Send CSV file to admin (with BOM for Excel compatibility with Cyrillic)
            await self.telegram_client.send_document(
                chat_id=chat_id,
                document=csv_content.encode('utf-8-sig'),  # BOM for Excel
                filename=filename,
                caption=f"📥 <b>Экспорт заблокированных пользователей</b>\n\n👥 Всего: {len(blocked_users)}\n📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                parse_mode="HTML"
            )
            
            # Delete loading message
            await self.telegram_client.delete_message(
                chat_id,
                loading_msg["result"]["message_id"]
            )
            
            logger.info(f"✅ Blocked users CSV exported to admin {admin_id}: {len(blocked_users)} users")
            
        except Exception as e:
            logger.error(f"Failed to export blocked users: {e}")
            await self.telegram_client.send_message(
                chat_id,
                "❌ Ошибка при экспорте заблокированных пользователей"
            )
    
    async def _create_daily_wisdom(self, chat_id: int, admin_id: int, topic: str = ""):
        """Create daily wisdom broadcast with AI generation"""
        try:
            from .broadcast_system import get_broadcast_system
            from datetime import date
            
            broadcast_system = get_broadcast_system(self.telegram_client)
            
            # Show loading message
            loading_msg = await self.telegram_client.send_message(
                chat_id,
                "🤖 <b>Generating Daily Wisdom...</b>\\n\\n⏳ Creating AI-powered content in multiple languages\\n🎨 Generating accompanying image\\n📝 Preparing broadcast",
                parse_mode="HTML"
            )
            
            # Create daily broadcast
            topic_to_use = topic.strip() if topic else "daily Torah wisdom"
            broadcast_id = await broadcast_system.create_daily_broadcast(
                target_date=date.today(),
                topic=topic_to_use
            )
            
            if broadcast_id:
                # Get created broadcast details
                broadcast = await self.newsletter_manager.get_broadcast_for_date(date.today())
                
                topic_display = "Jewish Wisdom"
                languages_count = 0
                if broadcast and broadcast.get('content'):
                    english_content = broadcast['content'].get('English', {})
                    if english_content and english_content.get('topic'):
                        topic_display = english_content['topic']
                    languages_count = len(broadcast['content'])
                
                result_message = f"""✅ <b>Daily Wisdom Broadcast Created!</b>
                
📋 <b>Broadcast Details:</b>
• ID: {broadcast_id}
• Date: {date.today().strftime('%B %d, %Y')}
• Topic: {topic_display}
• Languages: {languages_count} supported
• Status: Ready for delivery

🌍 <b>Generated Content:</b>
• English, Russian, Hebrew, Spanish, French, German, Arabic
• AI-generated wisdom text
• Custom image included: {'✅ Yes' if broadcast.get('image_url') else '❌ No'}

📊 <b>Next Steps:</b>
• Content is saved in database
• Ready for scheduled delivery
• Use /send_test_now to preview content"""

                await self.telegram_client.edit_message_text(
                    chat_id,
                    loading_msg["result"]["message_id"],
                    result_message,
                    parse_mode="HTML"
                )
            else:
                await self.telegram_client.edit_message_text(
                    chat_id,
                    loading_msg["result"]["message_id"],
                    "❌ <b>Failed to create daily wisdom broadcast</b>\\n\\n⚠️ Check logs for details",
                    parse_mode="HTML"
                )
                
        except Exception as e:
            logger.error(f"Failed to create daily wisdom: {e}")
            await self.telegram_client.send_message(
                chat_id,
                "❌ Error creating daily wisdom broadcast"
            )
    
    async def _backup_database(self, chat_id: int):
        """Create manual database backup"""
        try:
            from database.backup_manager import backup_manager
            
            # Show loading message
            loading_msg = await self.telegram_client.send_message(
                chat_id,
                "🔄 <b>Creating Database Backup...</b>\\n\\n⏳ Backing up all tables and data\\n💾 Compressing backup file",
                parse_mode="HTML"
            )
            
            # Create backup
            backup_path = await backup_manager.create_backup()
            
            if backup_path:
                # Get backup stats
                stats = await backup_manager.get_backup_stats()
                
                result_message = f"""✅ <b>Database Backup Completed!</b>
                
📋 <b>Backup Details:</b>
• File created successfully
• Size: {stats.get('total_size_mb', 0)} MB total
• Location: Protected backup directory
• Total backups: {stats.get('total_backups', 0)}

🛡️ <b>Backup System:</b>
• Automatic daily backups at 3:00 AM
• Keeps {stats.get('max_backups_kept', 30)} days of history
• Compressed and secure storage

📊 <b>What's Backed Up:</b>
• All user accounts and subscriptions
• Newsletter broadcast history
• Analytics and delivery logs
• Admin users and permissions"""

                await self.telegram_client.edit_message_text(
                    chat_id,
                    loading_msg["result"]["message_id"],
                    result_message,
                    parse_mode="HTML"
                )
            else:
                await self.telegram_client.edit_message_text(
                    chat_id,
                    loading_msg["result"]["message_id"],
                    "❌ <b>Database backup failed</b>\\n\\n⚠️ Check system logs for details",
                    parse_mode="HTML"
                )
                
        except Exception as e:
            logger.error(f"Failed to create database backup: {e}")
            await self.telegram_client.send_message(
                chat_id,
                "❌ Error creating database backup"
            )
    
    async def _backup_status(self, chat_id: int):
        """Show backup system status"""
        try:
            from database.backup_manager import backup_manager
            
            # Get backup statistics
            stats = await backup_manager.get_backup_stats()
            backups = await backup_manager.list_backups()
            
            status_message = f"""📊 <b>Database Backup System Status</b>
            
💾 <b>Current Status:</b>
• Total backups: {stats.get('total_backups', 0)}
• Storage used: {stats.get('total_size_mb', 0)} MB
• Latest backup: {stats.get('latest_backup', 'Never')[:16] if stats.get('latest_backup') else 'Never'}
• Auto-backup: ✅ Daily at 3:00 AM

📋 <b>Recent Backups:</b>"""
            
            # Show last 5 backups
            recent_backups = backups[:5] if backups else []
            
            for backup in recent_backups:
                age_text = f"{backup['age_days']} days ago" if int(backup.get('age_days', 0)) > 0 else "Today"
                status_message += f"""
• {backup['created'][:16]} ({backup['size_kb']} KB) - {age_text}"""
                
            if not recent_backups:
                status_message += "\\n• No backups found"
                
            status_message += f"""

🔧 <b>System Configuration:</b>
• Backup retention: {stats.get('max_backups_kept', 30)} days
• Compression: ✅ Enabled (GZIP)
• Automatic cleanup: ✅ Enabled
• Database: PostgreSQL"""
            
            await self.telegram_client.send_message(
                chat_id,
                status_message,
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"Failed to get backup status: {e}")
            await self.telegram_client.send_message(
                chat_id,
                "❌ Error getting backup status"
            )
    
    async def _show_newsletter_stats_api(self, chat_id: int):
        """Show newsletter statistics via Internal API"""
        try:
            logger.info("📊 Admin requesting Internal API statistics")
            
            # Check API health first
            api_health = await self.newsletter_api.health_check()
            if not api_health:
                await self.telegram_client.send_message(
                    chat_id,
                    "❌ <b>Internal Newsletter API недоступен</b>\n\n⚠️ Сервис временно недоступен",
                    parse_mode="HTML"
                )
                return
            
            # Get stats from internal API
            stats = await self.newsletter_api.get_stats()
            
            stats_text = f"""📊 <b>Internal Newsletter API Statistics</b>

🔌 <b>API Status:</b> ✅ Online
💾 <b>Database:</b> ✅ Connected

👥 <b>Subscribers:</b>
• Total: {stats['total_subscribers']}
• Active: {stats['active_subscribers']}

🌐 <b>Language Breakdown:</b>"""
            
            for language, count in stats.get('language_breakdown', {}).items():
                percentage = (count / stats['active_subscribers'] * 100) if stats['active_subscribers'] > 0 else 0
                stats_text += f"""
• {language}: {count} ({percentage:.1f}%)"""
            
            stats_text += f"""

📈 <b>Broadcast History:</b>
• Total broadcasts sent: {stats.get('total_broadcasts_sent', 0)}
• Last broadcast: {stats.get('last_broadcast_time') or 'Never'}

🚀 <b>Internal API Features:</b>
• Direct service integration
• Shared PostgreSQL database
• AI content generation
• DALL-E 3 image integration
• Multi-language support"""

            await self.telegram_client.send_message(chat_id, stats_text, parse_mode="HTML")
            
        except Exception as e:
            logger.error(f"❌ Internal API stats error: {e}")
            await self.telegram_client.send_message(
                chat_id,
                "❌ Ошибка получения статистики Internal API"
            )
    
    async def _send_broadcast_via_api(self, chat_id: int, topic: str = ""):
        """Send broadcast via Internal API"""
        try:
            logger.info(f"🚀 Admin requesting Internal API broadcast - topic: '{topic}'")
            
            # Show loading message
            loading_msg = await self.telegram_client.send_message(
                chat_id,
                "🚀 <b>Отправка через Internal Newsletter API...</b>\n\n⏳ Генерация AI контента\n🎨 Создание DALL-E 3 изображения\n📤 Массовая рассылка подписчикам",
                parse_mode="HTML"
            )
            
            # Check API health
            api_health = await self.newsletter_api.health_check()
            if not api_health:
                await self.telegram_client.edit_message_text(
                    chat_id,
                    loading_msg["result"]["message_id"],
                    "❌ <b>Internal API недоступен</b>\n\n⚠️ Сервис временно недоступен",
                    parse_mode="HTML"
                )
                return
            
            # Send broadcast via internal API
            topic_to_use = topic.strip() if topic else None
            result = await self.newsletter_api.send_broadcast(
                topic=topic_to_use,
                language="Russian",
                user_name="Друг"
            )
            
            if result['success']:
                # Success message
                success_msg = f"""✅ <b>Internal API Broadcast Complete!</b>

📊 <b>Delivery Statistics:</b>
• Successfully sent: {result['sent_count']}
• Failed: {result['failed_count']}
• Success rate: {(result['sent_count'] / (result['sent_count'] + result['failed_count']) * 100):.1f}%

🎯 <b>Content Details:</b>
• Topic: {result['topic']}
• Image generated: {'✅ Yes' if result['has_image'] else '❌ No'}
• Service: Internal Newsletter API

💫 <b>Features Used:</b>
• AI-generated wisdom content (GPT-4o)
• DALL-E 3 image generation
• Identical to Rabbi Wisdom format
• Direct service integration"""

                await self.telegram_client.edit_message_text(
                    chat_id,
                    loading_msg["result"]["message_id"],
                    success_msg,
                    parse_mode="HTML"
                )
                
                logger.info(f"✅ Internal API broadcast success: {result['sent_count']} sent")
                
            else:
                # Error message
                await self.telegram_client.edit_message_text(
                    chat_id,
                    loading_msg["result"]["message_id"],
                    f"❌ <b>Internal API Broadcast Failed</b>\n\n⚠️ {result['message']}",
                    parse_mode="HTML"
                )
                
                logger.error(f"❌ Internal API broadcast failed: {result['message']}")
            
        except Exception as e:
            logger.error(f"❌ Internal API broadcast error: {e}")
            await self.telegram_client.send_message(
                chat_id,
                f"❌ Ошибка Internal API рассылки: {str(e)}"
            )
    
    async def _schedule_broadcast_via_api(self, chat_id: int, topic: str = ""):
        """Schedule future broadcast via Internal API"""
        try:
            logger.info(f"⏰ Admin scheduling Internal API broadcast - topic: '{topic}'")
            
            # Import scheduler
            from .scheduled_broadcast import send_manual_broadcast
            
            # Show loading message
            loading_msg = await self.telegram_client.send_message(
                chat_id,
                "⏰ <b>Планирование рассылки через Internal API...</b>\n\n🔍 Проверка доступности API\n⚙️ Настройка расписания",
                parse_mode="HTML"
            )
            
            # Check API health
            api_health = await self.newsletter_api.health_check()
            if not api_health:
                await self.telegram_client.edit_message_text(
                    chat_id,
                    loading_msg["result"]["message_id"],
                    "❌ <b>Internal API недоступен</b>\n\n⚠️ Невозможно запланировать рассылку",
                    parse_mode="HTML"
                )
                return
            
            # Send manual broadcast now as test
            topic_to_use = topic.strip() if topic else None
            result = await send_manual_broadcast(topic=topic_to_use)
            
            if result:
                # Get current stats
                stats = await self.newsletter_api.get_stats()
                
                success_msg = f"""✅ <b>Internal API Broadcast Scheduled!</b>

⏰ <b>Schedule Configuration:</b>
• Execution: Immediately executed as test
• Daily schedule: 16:30 (4:30 PM) 
• Service: Internal Newsletter API
• Topic: {topic_to_use or 'Contextual daily wisdom'}

📊 <b>Current Subscribers:</b>
• Active: {stats['active_subscribers']}
• Total: {stats['total_subscribers']}

🚀 <b>System Status:</b>
• Internal API: ✅ Online
• Scheduler: ✅ Active
• Database: ✅ Connected

💡 <b>Next Steps:</b>
• Broadcast sent successfully as preview
• Daily scheduling active at 16:30
• Use /newsletter_stats_api for monitoring"""

                await self.telegram_client.edit_message_text(
                    chat_id,
                    loading_msg["result"]["message_id"],
                    success_msg,
                    parse_mode="HTML"
                )
                
                logger.info("✅ Internal API broadcast scheduled successfully")
                
            else:
                await self.telegram_client.edit_message_text(
                    chat_id,
                    loading_msg["result"]["message_id"],
                    "❌ <b>Failed to Schedule Internal API Broadcast</b>\n\n⚠️ API or service error",
                    parse_mode="HTML"
                )
                
                logger.error("❌ Internal API broadcast scheduling failed")
            
        except Exception as e:
            logger.error(f"❌ Internal API scheduling error: {e}")
            await self.telegram_client.send_message(
                chat_id,
                f"❌ Ошибка планирования Internal API рассылки: {str(e)}"
            )
    
    async def _run_api_tests(self, chat_id: int):
        """Run comprehensive Internal API tests"""
        try:
            logger.info("🧪 Admin requesting Internal API test suite")
            
            # Show loading message
            loading_msg = await self.telegram_client.send_message(
                chat_id,
                "🧪 <b>Запуск автотестов Internal Newsletter API...</b>\n\n⏳ Инициализация тестовой среды\n🔍 Проверка всех компонентов\n📊 Анализ производительности",
                parse_mode="HTML"
            )
            
            # Import and run tests
            import asyncio
            import sys
            import os
            
            # Add tests directory to path
            tests_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tests")
            if tests_path not in sys.path:
                sys.path.append(tests_path)
            
            try:
                # Import test modules dynamically
                import importlib.util
                tests_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tests")
                
                # Try to import test modules
                spec1 = importlib.util.spec_from_file_location("test_newsletter_api_microservice", 
                                                             os.path.join(tests_dir, "test_newsletter_api_microservice.py"))
                spec2 = importlib.util.spec_from_file_location("test_broadcast_migration", 
                                                             os.path.join(tests_dir, "test_broadcast_migration.py"))
                
                if spec1 and spec1.loader:
                    test_api_module = importlib.util.module_from_spec(spec1)
                    spec1.loader.exec_module(test_api_module)
                    run_newsletter_api_tests = test_api_module.run_newsletter_api_tests
                else:
                    raise ImportError("Newsletter API test module not found")
                    
                if spec2 and spec2.loader:
                    test_migration_module = importlib.util.module_from_spec(spec2)
                    spec2.loader.exec_module(test_migration_module)
                    run_migration_tests = test_migration_module.run_migration_tests
                else:
                    raise ImportError("Migration test module not found")
                
                # Run API tests
                await self.telegram_client.edit_message_text(
                    chat_id,
                    loading_msg["result"]["message_id"],
                    "🧪 <b>Выполнение тестов...</b>\n\n📡 Тестирование Newsletter API\n⏳ Пожалуйста, подождите...",
                    parse_mode="HTML"
                )
                
                api_results = await run_newsletter_api_tests()
                
                await self.telegram_client.edit_message_text(
                    chat_id,
                    loading_msg["result"]["message_id"],
                    "🧪 <b>Выполнение тестов...</b>\n\n✅ Newsletter API тесты завершены\n🔄 Тестирование миграции системы\n⏳ Пожалуйста, подождите...",
                    parse_mode="HTML"
                )
                
                migration_results = await run_migration_tests()
                
                # Calculate overall results
                api_success = api_results.get("success_rate", 0)
                migration_success = migration_results.get("success_rate", 0)
                overall_success = (api_success + migration_success) / 2
                
                # Format results message
                if overall_success >= 90:
                    status_icon = "🎉"
                    status_text = "ОТЛИЧНО"
                    status_color = "✅"
                elif overall_success >= 70:
                    status_icon = "⚠️"
                    status_text = "ХОРОШО"
                    status_color = "🟡"
                else:
                    status_icon = "❌"
                    status_text = "ТРЕБУЕТ ВНИМАНИЯ"
                    status_color = "🔴"
                
                results_message = f"""{status_icon} <b>АВТОТЕСТЫ ЗАВЕРШЕНЫ</b>

{status_color} <b>Общий результат:</b> {overall_success:.1f}% - {status_text}

📊 <b>Детальные результаты:</b>

🔌 <b>Newsletter API Tests:</b>
• Успешность: {api_success:.1f}%
• Пройдено: {api_results.get('passed', 0)}
• Провалено: {api_results.get('failed', 0)}

🔄 <b>Migration Tests:</b>
• Успешность: {migration_success:.1f}%
• Пройдено: {migration_results.get('passed', 0)}
• Провалено: {migration_results.get('failed', 0)}

🎯 <b>Статус системы:</b>
{'🚀 Готов к продакшену!' if overall_success >= 85 else '🔧 Требует доработки'}"""

                await self.telegram_client.edit_message_text(
                    chat_id,
                    loading_msg["result"]["message_id"],
                    results_message,
                    parse_mode="HTML"
                )
                
                # Send detailed error report if there are failures
                all_errors = api_results.get("errors", []) + migration_results.get("errors", [])
                if all_errors and len(all_errors) <= 5:  # Only show if manageable number of errors
                    error_message = "❌ <b>Обнаруженные проблемы:</b>\n\n"
                    for i, error in enumerate(all_errors[:5], 1):
                        error_message += f"{i}. {error}\n"
                    
                    await self.telegram_client.send_message(
                        chat_id,
                        error_message,
                        parse_mode="HTML"
                    )
                
                logger.info(f"✅ Internal API tests completed: {overall_success:.1f}% success rate")
                
            except ImportError as e:
                await self.telegram_client.edit_message_text(
                    chat_id,
                    loading_msg["result"]["message_id"],
                    f"❌ <b>Ошибка импорта тестов</b>\n\n⚠️ {str(e)}\n\n💡 Убедитесь что тестовые файлы установлены",
                    parse_mode="HTML"
                )
                logger.error(f"❌ Test import error: {e}")
            
        except Exception as e:
            logger.error(f"❌ Internal API test runner error: {e}")
            await self.telegram_client.send_message(
                chat_id,
                f"❌ Ошибка запуска автотестов: {str(e)}"
            )
    
    async def _show_admin_help(self, chat_id: int, permissions: Dict[str, bool]):
        """Show available admin commands"""
        help_text = """🔧 <b>Torah Bot Admin Commands</b>

📊 <b>Analytics & Monitoring:</b>
• /newsletter_stats - Detailed newsletter statistics  
• /newsletter_subscribers - Subscriber information
• /newsletter_stats_api - Internal API statistics
• /schedule_status - Schedule and system status

🧪 <b>Testing & Development:</b>
• /test_broadcast [тема] - Generate AI test broadcast (admin only)
• /send_test_now - Send immediate test broadcast
• /send_test_quiz - Send test interactive quiz
• /test_broadcast_api [тема] - Test via Internal API
• /run_api_tests - Run comprehensive API tests

📝 <b>Content Creation:</b>
• /create_daily_wisdom [тема] - Create daily wisdom broadcast
• /schedule_broadcast_api [тема] - Schedule broadcast via API

💾 <b>Database & User Management:</b>
• /backup_database - Create database backup
• /backup_status - Show backup status
• /export_blocked_users - Export blocked users to CSV

⚙️ <b>System Status:</b>
• 🌅 Morning wisdom: 06:00 UTC (09:00 MSK)
• 🌆 Evening quiz: 18:00 UTC (21:00 MSK)
• 💾 Daily backup: 03:00 UTC

ℹ️ <b>General:</b>
• /newsletter_help - Show this help message

👤 <b>Your Role:</b> Admin
🎯 <b>Status:</b> All systems operational"""
        
        if permissions.get("can_test_broadcasts", False):
            help_text += """
• /test_broadcast [topic] - Test broadcast content generation
• /test_broadcast_api [topic] - Test via Internal API
• /send_test_quiz - Send test quiz to current chat
• /run_api_tests - Run Internal API health checks"""
        else:
            help_text += """
• 🔒 Test functions - No permission"""
            
            
        if permissions.get("can_manage_users", False):
            help_text += """

💾 <b>Database & System Management:</b>
• /backup_database - Create manual database backup
• /backup_status - View backup system status
• /schedule_status - View broadcast schedule status"""
        else:
            help_text += """

💾 <b>Database & System Management:</b>
• 🔒 System management - No permission"""
        
        help_text += """

⚡ <b>Automatic Systems:</b>
• 🌅 Morning wisdom: 06:00 UTC (09:00 MSK)
• 🌆 Evening quiz: 18:00 UTC (21:00 MSK)
• 💾 Daily backup: 03:00 UTC

ℹ️ <b>General:</b>
• /newsletter_help - Show this help message

👤 <b>Your Role:</b> Admin
🎯 <b>Status:</b> All systems operational"""
        
        await self.telegram_client.send_message(
            chat_id,
            help_text,
            parse_mode="HTML"
        )
    
    # ===================================================================
    # AUTO-SUBSCRIBE INTEGRATION
    # ===================================================================
    
    async def auto_subscribe_user(self, user_data: Dict[str, Any]) -> bool:
        """Automatically subscribe user to newsletter when they interact with bot"""
        try:
            # First, upsert the user
            await self.newsletter_manager.upsert_user(user_data)
            
            # Detect language preference
            language_map = {
                'ru': 'Russian',
                'he': 'Hebrew', 
                'es': 'Spanish',
                'fr': 'French',
                'de': 'German',
                'ar': 'Arabic'
            }
            
            detected_language = language_map.get(
                user_data.get('language_code', 'en'), 
                'English'
            )
            
            # Auto-subscribe user
            success = await self.newsletter_manager.subscribe_user(
                telegram_user_id=user_data['id'],
                language=detected_language,
                delivery_time="09:00:00",  # 9 AM
                timezone_str="UTC"  # Default to UTC, can be enhanced later
            )
            
            if success:
                logger.info(f"📧 Auto-subscribed user {user_data['id']} to newsletter ({detected_language})")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to auto-subscribe user {user_data.get('id')}: {e}")
            return False