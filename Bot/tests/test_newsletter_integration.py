#!/usr/bin/env python3
"""
Basic Newsletter System Integration Test
"""
import asyncio
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

async def test_newsletter_system():
    """Test newsletter system integration"""
    print("🧪 NEWSLETTER SYSTEM INTEGRATION TEST")
    print("=" * 50)
    
    try:
        # Test database connection
        from database.init_database import test_database_connection
        print("1. Testing database connection...")
        db_result = await test_database_connection()
        if db_result:
            print("✅ Database connection successful")
        else:
            print("❌ Database connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Database test error: {e}")
        return False
    
    try:
        # Test newsletter manager import
        print("2. Testing newsletter manager import...")
        from torah_bot.newsletter_manager import newsletter_manager
        print("✅ Newsletter manager imported successfully")
        
        # Test admin commands import
        print("3. Testing admin commands import...")
        from torah_bot.admin_commands import AdminCommands
        print("✅ Admin commands imported successfully")
        
    except Exception as e:
        print(f"❌ Import test error: {e}")
        return False
    
    try:
        # Test database initialization
        print("4. Testing database initialization...")
        await newsletter_manager.initialize()
        print("✅ Newsletter manager initialized")
        
        # Test admin check
        print("5. Testing admin permissions...")
        is_admin = await newsletter_manager.is_admin(6630727156)  # torah_support
        if is_admin:
            print("✅ Admin user @torah_support found")
        else:
            print("⚠️ Admin user not found (expected for fresh database)")
            
        await newsletter_manager.close()
        
    except Exception as e:
        print(f"❌ Manager test error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 NEWSLETTER SYSTEM INTEGRATION TEST COMPLETE")
    print("📧 System ready for testing with @torah_support")
    print("🔧 Admin commands available:")
    print("   • /newsletter_stats")
    print("   • /newsletter_subscribers") 
    print("   • /test_broadcast [topic]")
    print("   • /send_test_now")
    print("   • /newsletter_help")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_newsletter_system())
    exit(0 if success else 1)