#!/usr/bin/env python3
"""
Инициализация базы данных для Torah Bot Newsletter System
"""
import os
import asyncio
import asyncpg
from pathlib import Path

# Получаем DATABASE_URL из environment
DATABASE_URL = os.getenv('DATABASE_URL')

async def init_database():
    """Инициализирует базу данных со схемой рассылки"""
    if not DATABASE_URL:
        import logging
        logging.error("❌ ERROR: DATABASE_URL not found in environment variables")
        return False
    
    try:
        import logging
        logging.info("🔗 Connecting to database...")
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Читаем SQL схему
        schema_path = Path(__file__).parent / 'newsletter_schema.sql'
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        logging.info("📊 Creating database schema...")
        
        # Выполняем SQL по частям (для лучшей обработки ошибок)
        sql_commands = schema_sql.split('-- ===================================================================')
        
        for i, command_section in enumerate(sql_commands):
            if command_section.strip():
                try:
                    await conn.execute(command_section)
                    logging.info(f"✅ Section {i+1} executed successfully")
                except Exception as e:
                    logging.warning(f"⚠️ Warning in section {i+1}: {e}")
                    # Продолжаем выполнение, некоторые команды могут быть дублирующимися
        
        # Проверяем что таблицы созданы
        tables = await conn.fetch("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename IN ('users', 'newsletter_subscriptions', 'newsletter_broadcasts', 'delivery_log', 'admin_users')
            ORDER BY tablename
        """)
        
        logging.info("📋 Created tables:")
        for table in tables:
            logging.info(f"  ✅ {table['tablename']}")
        
        # Проверяем админского пользователя
        admin_check = await conn.fetchrow("""
            SELECT username, role FROM admin_users WHERE username = 'torah_support'
        """)
        
        if admin_check:
            logging.info(f"👤 Admin user found: @{admin_check['username']} (role: {admin_check['role']})")
        else:
            logging.warning("❌ Admin user not created")
        
        # Проверяем views
        views = await conn.fetch("""
            SELECT viewname FROM pg_views 
            WHERE schemaname = 'public'
            AND viewname IN ('active_subscribers_by_language', 'broadcast_statistics')
        """)
        
        logging.info("📊 Created views:")
        for view in views:
            logging.info(f"  ✅ {view['viewname']}")
        
        await conn.close()
        
        logging.info("🎉 Database initialization completed successfully!")
        logging.info("🔧 Newsletter system is ready for testing")
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_database_connection():
    """Тестирует подключение к базе данных"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Простой тест
        result = await conn.fetchrow("SELECT 'Database connection successful!' as message")
        logging.info(f"✅ {result['message']}")
        
        # Тест админского пользователя
        admin = await conn.fetchrow("""
            SELECT * FROM admin_users WHERE username = 'torah_support'
        """)
        
        if admin:
            logging.info(f"👤 Admin user: @{admin['username']} (ID: {admin['telegram_user_id']})")
            logging.info(f"📋 Permissions: {admin['permissions']}")
        
        await conn.close()
        return True
        
    except Exception as e:
        logging.error(f"❌ Database connection test failed: {e}")
        return False

if __name__ == "__main__":
    logging.info("🗄️ TORAH BOT NEWSLETTER - DATABASE INITIALIZATION")
    logging.info("=" * 60)
    
    # Инициализируем базу данных
    success = asyncio.run(init_database())
    
    if success:
        logging.info("🧪 Testing database connection...")
        test_success = asyncio.run(test_database_connection())
        
        if test_success:
            logging.info("✅ All database operations completed successfully!")
            logging.info("📱 Ready to start newsletter development")
        else:
            logging.warning("⚠️ Database created but connection test failed")
    else:
        logging.error("❌ Database initialization failed")
        exit(1)