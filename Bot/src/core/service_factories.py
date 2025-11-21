#!/usr/bin/env python3
"""
Service Factory Functions for ServiceContainer
Centralized creation logic for all shared services
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

async def create_torah_bot():
    """Factory function to create TorahBotFinal instance"""
    from ..torah_bot.simple_bot import TorahBotFinal
    
    logger.info("🤖 Creating TorahBotFinal instance...")
    bot = TorahBotFinal()
    
    # Initialize for webhook mode
    if hasattr(bot, 'initialize_webhook_mode'):
        await bot.initialize_webhook_mode()
    else:
        await bot.initialize()
    
    logger.info("✅ TorahBotFinal instance created and initialized")
    return bot

async def create_telegram_client(bot_instance):
    """Factory function to extract telegram_client from bot"""
    if not hasattr(bot_instance, 'telegram_client'):
        raise ValueError("Bot instance missing telegram_client")
    
    telegram_client = bot_instance.telegram_client
    logger.info("📡 TelegramClient extracted from bot instance")
    return telegram_client

async def create_newsletter_manager(bot_instance):
    """Factory function to extract newsletter_manager from bot"""
    # Check different possible attribute names
    if hasattr(bot_instance, 'newsletter_manager'):
        newsletter_manager = bot_instance.newsletter_manager
    elif hasattr(bot_instance, 'newsletter_system'):
        newsletter_manager = bot_instance.newsletter_system
    elif hasattr(bot_instance, '_newsletter_manager'):
        newsletter_manager = bot_instance._newsletter_manager
    else:
        # Fallback: Create new newsletter manager instance
        from ..torah_bot.newsletter_manager import NewsletterManager
        logger.warning("⚠️ Bot missing newsletter_manager, creating new instance")
        newsletter_manager = NewsletterManager()
        await newsletter_manager.initialize()
    
    logger.info("📧 NewsletterManager retrieved/created for ServiceContainer")
    return newsletter_manager

async def create_admin_commands(telegram_client, newsletter_manager):
    """Factory function to create AdminCommands instance"""
    from ..torah_bot.admin_commands import AdminCommands
    
    logger.info("👑 Creating AdminCommands instance...")
    admin_commands = AdminCommands(telegram_client, newsletter_manager)
    logger.info("✅ AdminCommands instance created")
    return admin_commands

# Service creation order - important for dependencies
SERVICE_DEPENDENCIES = {
    'torah_bot': [],
    'telegram_client': ['torah_bot'],
    'newsletter_manager': ['torah_bot'],
    'admin_commands': ['telegram_client', 'newsletter_manager']
}

async def initialize_all_services(container):
    """Initialize all services in correct dependency order"""
    logger.info("🚀 Starting ServiceContainer initialization sequence...")
    
    # 1. Create Torah Bot (base dependency)
    bot = await container.get_service('torah_bot', create_torah_bot)
    
    # 2. Extract Telegram Client
    telegram_client = await container.get_service(
        'telegram_client', 
        create_telegram_client, 
        bot
    )
    
    # 3. Extract Newsletter Manager  
    newsletter_manager = await container.get_service(
        'newsletter_manager',
        create_newsletter_manager,
        bot
    )
    
    # 4. Create Admin Commands with both dependencies
    admin_commands = await container.get_service(
        'admin_commands',
        create_admin_commands,
        telegram_client,
        newsletter_manager
    )
    
    logger.info("✅ All services initialized in ServiceContainer")
    return {
        'torah_bot': bot,
        'telegram_client': telegram_client,
        'newsletter_manager': newsletter_manager,
        'admin_commands': admin_commands
    }