# 🚀 Torah Bot - Migration to Cursor Guide

Complete guide for migrating Torah Bot from Replit to Cursor IDE with local or cloud development.

---

## 📋 Pre-Migration Checklist

### ✅ What to Export from Replit

1. **Environment Variables** (CRITICAL):
   ```bash
   # In Replit Shell, export secrets
   echo "TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN" > .env.export
   echo "OPENAI_API_KEY=$OPENAI_API_KEY" >> .env.export
   echo "DATABASE_URL=$DATABASE_URL" >> .env.export
   echo "ADMIN_SECRET=$ADMIN_SECRET" >> .env.export
   echo "SESSION_SECRET=$SESSION_SECRET" >> .env.export
   echo "TORAH_LOGS_CHAT_ID=$TORAH_LOGS_CHAT_ID" >> .env.export
   
   # Download .env.export file
   ```

2. **Database Backup** (if migrating database):
   ```bash
   # Export database
   pg_dump $DATABASE_URL > torah_bot_backup.sql
   
   # Or use admin command
   /backup_database
   ```

3. **Code Repository**:
   - All files already ready in project structure
   - `.cursorrules` configured
   - `DEVELOPMENT.md` prepared
   - `.env.example` documented

---

## 🔧 Migration Steps

### Step 1: Setup Cursor Environment

```bash
# 1. Open Cursor IDE
# 2. Clone or create new project
git clone <your-repo-url> torah-bot
cd torah-bot

# 3. Open in Cursor
cursor .
```

### Step 2: Install Python Dependencies

```bash
# Create virtual environment (recommended)
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or use uv (faster)
pip install uv
uv pip install -r requirements.txt
```

### Step 3: Setup PostgreSQL

**Option A: Local PostgreSQL**
```bash
# Install PostgreSQL 16
# macOS: brew install postgresql@16
# Ubuntu: sudo apt install postgresql-16
# Windows: Download from postgresql.org

# Create database
createdb torah_bot

# Restore backup (if migrating data)
psql torah_bot < torah_bot_backup.sql
```

**Option B: Cloud PostgreSQL (Recommended)**
- Use Replit database (keep existing DATABASE_URL)
- Or migrate to: Neon, Supabase, Railway, etc.

### Step 4: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use Cursor to edit

# Required variables:
# - TELEGRAM_BOT_TOKEN
# - OPENAI_API_KEY
# - DATABASE_URL
# - ADMIN_SECRET
# - SESSION_SECRET
```

### Step 5: Initialize Database

```bash
# Test database connection
python src/database/init_database.py

# Tables will be created automatically on first run
```

### Step 6: Update Telegram Webhook

```bash
# Get your new webhook URL (ngrok for local, or deployment URL)

# For local development with ngrok:
ngrok http 5000
# Copy the HTTPS URL

# Set webhook
curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook" \
  -d "url=https://your-ngrok-url.ngrok.io/webhook"

# Verify
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo"
```

### Step 7: Run Development Server

```bash
# Activate virtual environment
source venv/bin/activate

# Start server
python unified_webhook_service.py

# Server runs on http://localhost:5000
# Check health: curl http://localhost:5000/health
```

---

## 🔄 Database Migration Options

### Option 1: Keep Replit Database (Easiest)

**Pros**: No data migration, instant setup
**Cons**: Depends on Replit service

```env
# .env
DATABASE_URL=<your_replit_postgres_url>
# Keep existing Replit database connection
```

### Option 2: Migrate to New Database

**Pros**: Full ownership, no external dependencies
**Cons**: Requires data migration

```bash
# 1. Export from Replit
pg_dump $DATABASE_URL > backup.sql

# 2. Create new database (Neon/Supabase/Local)
# 3. Import data
psql $NEW_DATABASE_URL < backup.sql

# 4. Update .env
DATABASE_URL=<new_database_url>
```

### Option 3: Hybrid (Development + Production)

**Development**: Local PostgreSQL
**Production**: Replit or cloud database

```bash
# .env.local (development)
DATABASE_URL=postgresql://localhost:5432/torah_bot_dev

# .env.production (production)
DATABASE_URL=<production_database_url>
```

---

## 🧪 Testing After Migration

### 1. Health Check
```bash
curl http://localhost:5000/health
# Expected: {"status":"healthy","service":"torah-bot-unified"}
```

### 2. Database Connection
```bash
python -c "from src.database.init_database import test_database_connection; import asyncio; asyncio.run(test_database_connection())"
```

### 3. Bot Commands
Send to bot:
- `/start` - Should respond with welcome message
- `/newsletter_stats` - Should show subscriber count
- `/send_test_now` - Test wisdom broadcast (admin only)

### 4. Webhook Verification
```bash
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
# Check: url, pending_update_count, last_error_date
```

---

## 🚀 Deployment Options from Cursor

### Option 1: Keep Replit Deployment

```bash
# Push changes to Replit
git remote add replit https://replit.com/@your-username/torah-bot.git
git push replit main

# Replit will auto-deploy
```

### Option 2: Deploy to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and init
railway login
railway init

# Deploy
railway up
```

### Option 3: Deploy to Render

```yaml
# render.yaml
services:
  - type: web
    name: torah-bot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python unified_webhook_service.py
    envVars:
      - key: TELEGRAM_BOT_TOKEN
        sync: false
      - key: OPENAI_API_KEY
        sync: false
```

### Option 4: Docker Deployment

```bash
# Build image
docker build -t torah-bot .

# Run container
docker run -p 5000:5000 --env-file .env torah-bot
```

---

## 📝 Cursor-Specific Configuration

### 1. Enable Cursor AI Features

Cursor AI will automatically use `.cursorrules` for:
- Code suggestions
- Best practices
- Project conventions
- Security guidelines

### 2. Recommended Extensions

Install in Cursor:
- Python
- Pylance
- Better Comments
- GitLens
- PostgreSQL (if local DB)

### 3. Cursor Settings

```json
// .cursor/settings.json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    ".pythonlibs": true
  }
}
```

---

## 🔐 Security Considerations

### 1. Environment Variables

```bash
# NEVER commit .env to git
# Verify .gitignore includes:
echo ".env" >> .gitignore

# Use secrets manager for production
# - GitHub Secrets
# - Railway Variables
# - Render Environment Groups
```

### 2. API Keys Rotation

After migration, consider rotating:
- ✅ ADMIN_SECRET
- ✅ SESSION_SECRET
- ⚠️ TELEGRAM_BOT_TOKEN (optional)
- ⚠️ OPENAI_API_KEY (optional)

### 3. Database Credentials

```bash
# If migrating database, update:
# 1. PostgreSQL password
# 2. DATABASE_URL in .env
# 3. Webhook URL in Telegram
```

---

## 🐛 Troubleshooting

### Issue: Bot not responding

**Check:**
1. Webhook URL is correct
2. Server is running on correct port
3. No firewall blocking port 5000
4. Telegram webhook is set

```bash
# Debug webhook
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

### Issue: Database connection failed

**Check:**
1. DATABASE_URL format is correct
2. PostgreSQL is running
3. Database exists
4. Credentials are valid

```bash
# Test connection
psql $DATABASE_URL -c "SELECT version();"
```

### Issue: Import errors

**Check:**
1. Virtual environment activated
2. All dependencies installed
3. Python version is 3.11+

```bash
# Verify Python version
python --version

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Issue: Port 5000 already in use

```bash
# Find and kill process
lsof -i :5000
kill -9 <PID>

# Or use different port
PORT=8000 python unified_webhook_service.py
```

---

## ✅ Post-Migration Checklist

- [ ] All environment variables configured
- [ ] Database connected and tables created
- [ ] Telegram webhook updated
- [ ] Health check passes
- [ ] Test commands work
- [ ] Newsletter broadcasts functional
- [ ] Admin commands accessible
- [ ] Mini game loads correctly
- [ ] Logs visible and working
- [ ] Backup system operational

---

## 📞 Support

If you encounter issues:

1. **Check logs**: `tail -f logs/*.log`
2. **Review documentation**: `DEVELOPMENT.md`
3. **Verify environment**: `.env.example`
4. **Test health**: `curl localhost:5000/health`

---

## 🎉 Success Indicators

Your migration is successful when:

✅ Server starts without errors
✅ Health check returns healthy status
✅ Bot responds to `/start` command
✅ Newsletter stats show correct subscriber count
✅ Test broadcasts work
✅ Database queries execute successfully
✅ Webhook receives updates from Telegram

---

**Migration Time Estimate**: 30-60 minutes

**Difficulty**: Intermediate (requires basic DevOps knowledge)

---

Last updated: October 16, 2025
