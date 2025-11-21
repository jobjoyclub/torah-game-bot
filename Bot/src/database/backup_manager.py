#!/usr/bin/env python3
"""
Database Backup Manager for Torah Bot
Handles regular PostgreSQL database backups and restoration
"""
import os
import asyncio
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import gzip
import asyncpg

logger = logging.getLogger(__name__)

class DatabaseBackupManager:
    """Manages database backups and restoration"""
    
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        self.backup_dir = Path(__file__).parent / 'backups'
        self.max_backups = 30  # Keep 30 days of backups
        
        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(exist_ok=True)
    
    async def create_backup(self) -> Optional[str]:
        """Create a full database backup"""
        if not self.db_url:
            logger.error("DATABASE_URL not found for backup")
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"torah_bot_backup_{timestamp}.sql.gz"
        backup_path = self.backup_dir / backup_filename
        
        try:
            logger.info(f"🔄 Starting database backup: {backup_filename}")
            
            # Connect to database
            conn = await asyncpg.connect(self.db_url)
            
            # Get all table names
            tables = await conn.fetch("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY tablename
            """)
            
            backup_content = []
            
            # Add header
            backup_content.append(f"-- Torah Bot Database Backup")
            backup_content.append(f"-- Created: {datetime.now().isoformat()}")
            backup_content.append(f"-- Tables: {len(tables)}")
            backup_content.append("")
            
            # Backup each table
            for table_row in tables:
                table_name = table_row['tablename']
                logger.info(f"  📋 Backing up table: {table_name}")
                
                # Get table schema
                schema_query = f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}' 
                    ORDER BY ordinal_position
                """
                
                columns = await conn.fetch(schema_query)
                
                # Add table creation info (simplified)
                backup_content.append(f"-- Table: {table_name}")
                backup_content.append(f"-- Columns: {len(columns)}")
                
                # Get table data
                rows = await conn.fetch(f"SELECT * FROM {table_name}")
                
                if rows:
                    backup_content.append(f"-- Data for {table_name} ({len(rows)} rows)")
                    
                    # Convert rows to JSON for easy restoration
                    table_data = []
                    for row in rows:
                        row_dict = {}
                        for key, value in row.items():
                            # Handle special data types
                            if isinstance(value, datetime):
                                row_dict[key] = value.isoformat()
                            elif value is None:
                                row_dict[key] = None
                            else:
                                row_dict[key] = str(value)
                        table_data.append(row_dict)
                    
                    # Store as JSON comment for easy parsing
                    backup_content.append(f"-- JSON_DATA_{table_name}: {json.dumps(table_data)}")
                
                backup_content.append("")
            
            await conn.close()
            
            # Write compressed backup
            backup_text = "\\n".join(backup_content)
            
            with gzip.open(backup_path, 'wt', encoding='utf-8') as f:
                f.write(backup_text)
            
            # Get file size
            file_size = backup_path.stat().st_size / 1024  # KB
            
            logger.info(f"✅ Database backup completed: {backup_filename} ({file_size:.1f} KB)")
            
            # Clean up old backups
            await self._cleanup_old_backups()
            
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"❌ Database backup failed: {e}")
            if backup_path.exists():
                backup_path.unlink()  # Remove partial backup
            return None
    
    async def _cleanup_old_backups(self):
        """Remove old backup files"""
        try:
            backup_files = list(self.backup_dir.glob("torah_bot_backup_*.sql.gz"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Keep only the most recent backups
            if len(backup_files) > self.max_backups:
                files_to_remove = backup_files[self.max_backups:]
                for file_path in files_to_remove:
                    file_path.unlink()
                    logger.info(f"🗑️ Removed old backup: {file_path.name}")
                    
        except Exception as e:
            logger.error(f"⚠️ Backup cleanup warning: {e}")
    
    async def list_backups(self) -> List[Dict[str, str]]:
        """List available backups"""
        try:
            backup_files = list(self.backup_dir.glob("torah_bot_backup_*.sql.gz"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            backups = []
            for backup_file in backup_files:
                stat = backup_file.stat()
                backups.append({
                    'filename': backup_file.name,
                    'path': str(backup_file),
                    'size_kb': round(stat.st_size / 1024, 1),
                    'created': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'age_days': (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days
                })
            
            return backups
            
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return []
    
    async def get_backup_stats(self) -> Dict[str, any]:
        """Get backup system statistics"""
        try:
            backups = await self.list_backups()
            
            total_size = sum(backup['size_kb'] for backup in backups)
            latest_backup = backups[0] if backups else None
            
            return {
                'total_backups': len(backups),
                'total_size_mb': round(total_size / 1024, 2),
                'latest_backup': latest_backup['created'] if latest_backup else None,
                'backup_directory': str(self.backup_dir),
                'max_backups_kept': self.max_backups
            }
            
        except Exception as e:
            logger.error(f"Failed to get backup stats: {e}")
            return {}
    
    async def schedule_daily_backup(self):
        """Schedule daily backup (to be called by scheduler)"""
        logger.info("📅 Running scheduled daily backup")
        
        backup_path = await self.create_backup()
        
        if backup_path:
            # Log success
            stats = await self.get_backup_stats()
            logger.info(f"📊 Backup stats: {stats['total_backups']} backups, {stats['total_size_mb']} MB total")
            return True
        else:
            logger.error("❌ Scheduled backup failed")
            return False

class BackupScheduler:
    """Handles backup scheduling"""
    
    def __init__(self):
        self.backup_manager = DatabaseBackupManager()
        self.is_running = False
    
    async def start_daily_backups(self):
        """Start daily backup scheduler"""
        if self.is_running:
            logger.warning("⚠️ Backup scheduler already running")
            return
        
        self.is_running = True
        logger.info("🕒 Starting daily backup scheduler")
        
        while self.is_running:
            try:
                # Calculate time until next 3 AM
                now = datetime.now()
                next_backup = now.replace(hour=3, minute=0, second=0, microsecond=0)
                
                # If it's already past 3 AM today, schedule for tomorrow
                if now.hour >= 3:
                    next_backup += timedelta(days=1)
                
                wait_seconds = (next_backup - now).total_seconds()
                logger.info(f"⏰ Next backup scheduled for: {next_backup.strftime('%Y-%m-%d %H:%M')}")
                
                # Wait until backup time
                await asyncio.sleep(wait_seconds)
                
                if self.is_running:  # Check if still running after sleep
                    await self.backup_manager.schedule_daily_backup()
                
            except Exception as e:
                logger.error(f"❌ Backup scheduler error: {e}")
                # Wait 1 hour before retrying
                await asyncio.sleep(3600)
    
    def stop(self):
        """Stop the backup scheduler"""
        self.is_running = False
        logger.info("🛑 Backup scheduler stopped")

# Global instances
backup_manager = DatabaseBackupManager()
backup_scheduler = BackupScheduler()