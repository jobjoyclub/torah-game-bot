# 📦 Torah Bot → Cursor Transfer Checklist

Quick reference guide for moving Torah Bot to Cursor IDE.

---

## 🎯 Before You Start

### Files Created for Migration:
- ✅ `.cursorrules` - Cursor AI configuration
- ✅ `DEVELOPMENT.md` - Complete setup guide
- ✅ `MIGRATION_GUIDE.md` - Detailed migration steps
- ✅ `.env.example` - Environment variables template
- ✅ `requirements.txt` - Python dependencies
- ✅ `README.md` - Project documentation
- ✅ `.gitignore` - Git exclusions (Cursor-ready)

---

## 📋 Quick Transfer Steps

### 1. Export from Replit (5 min)

```bash
# In Replit Shell:

# Export environment variables
cat > .env.export << EOF
TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
OPENAI_API_KEY=$OPENAI_API_KEY
DATABASE_URL=$DATABASE_URL
ADMIN_SECRET=$ADMIN_SECRET
SESSION_SECRET=$SESSION_SECRET
TORAH_LOGS_CHAT_ID=$TORAH_LOGS_CHAT_ID
EOF

# Backup database (optional if keeping Replit DB)
pg_dump $DATABASE_URL > torah_bot_backup.sql

# Download both files
```

### 2. Setup in Cursor (10 min)

```bash
# Clone/open project in Cursor
cd torah-bot

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with values from .env.export

# Test database
python src/database/init_database.py
```

### 3. Update Telegram (2 min)

```bash
# For local development (with ngrok):
ngrok http 5000
# Copy the HTTPS URL

# Set webhook:
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -d "url=https://your-url.ngrok.io/webhook"
```

### 4. Run & Test (3 min)

```bash
# Start server
python unified_webhook_service.py

# Test health
curl http://localhost:5000/health

# Test bot - send to Telegram:
/start
/newsletter_stats
```

---

## ⚙️ Environment Variables (Copy These)

```env
# .env (minimum required)
TELEGRAM_BOT_TOKEN=<from_replit>
OPENAI_API_KEY=<from_replit>
DATABASE_URL=<from_replit_or_new>
ADMIN_SECRET=<from_replit>
SESSION_SECRET=<from_replit>
TORAH_LOGS_CHAT_ID=-1003025527880
```

---

## 🗄️ Database Options

### Option A: Keep Replit Database (Easiest)
- Copy DATABASE_URL from Replit
- No migration needed
- Works immediately

### Option B: Migrate to New Database
- Create new PostgreSQL
- Import: `psql $NEW_URL < backup.sql`
- Update DATABASE_URL in .env

**Recommended**: Option A for quick start

---

## 🧪 Verification Tests

Run these to verify everything works:

```bash
# 1. Health check
curl http://localhost:5000/health
# Expected: {"status":"healthy","service":"torah-bot-unified"}

# 2. Database connection
python -c "from src.database.init_database import test_database_connection; import asyncio; asyncio.run(test_database_connection())"

# 3. Bot commands (in Telegram)
/start
/newsletter_stats
/send_test_now  # If admin
```

---

## 🚨 Common Issues & Fixes

### Bot not responding
```bash
# Check webhook
curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo

# Verify server running
curl http://localhost:5000/health
```

### Database error
```bash
# Test connection
psql $DATABASE_URL -c "SELECT version();"

# Check format
echo $DATABASE_URL
# Should be: postgresql://user:pass@host:5432/db
```

### Port 5000 in use
```bash
# Kill process
lsof -i :5000
kill -9 <PID>

# Or use different port
PORT=8000 python unified_webhook_service.py
```

### Import errors
```bash
# Verify Python version
python --version  # Must be 3.11+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview & features |
| `DEVELOPMENT.md` | Complete setup guide |
| `MIGRATION_GUIDE.md` | Detailed migration steps |
| `.cursorrules` | Cursor AI configuration |
| `.env.example` | Environment variables |
| `replit.md` | Project history |

---

## ✅ Success Checklist

- [ ] Code downloaded/cloned
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file configured
- [ ] Database connected
- [ ] Server starts without errors
- [ ] Health check passes
- [ ] Telegram webhook updated
- [ ] Bot responds to `/start`
- [ ] Newsletter stats display correctly

---

## 🎉 You're Done!

Your Torah Bot is now running in Cursor with:
- ✅ Full development environment
- ✅ Cursor AI assistance configured
- ✅ Complete documentation
- ✅ All features operational

---

## 📞 Next Steps

1. **Read** `DEVELOPMENT.md` for development guide
2. **Configure** Cursor AI extensions (Python, GitLens)
3. **Test** all admin commands
4. **Deploy** to production (see `MIGRATION_GUIDE.md`)

---

## 🆘 Need Help?

- Check `DEVELOPMENT.md` for detailed instructions
- Review `MIGRATION_GUIDE.md` for troubleshooting
- Verify `.cursorrules` for coding standards
- Test with: `curl localhost:5000/health`

---

**Total Migration Time**: ~20 minutes

**Difficulty**: Easy (if keeping Replit database)

---

Last updated: October 16, 2025
