# Torah Bot - Development Setup Guide

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- PostgreSQL 16+
- Node.js 20+ (for npm scripts if needed)
- Telegram Bot Token (from @BotFather)
- OpenAI API Key

### 1. Clone and Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
# or use uv (faster)
uv pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Create PostgreSQL database
createdb torah_bot

# Set DATABASE_URL environment variable
export DATABASE_URL="postgresql://user:password@localhost:5432/torah_bot"

# Initialize database (tables created automatically on first run)
python src/database/init_database.py
```

### 3. Environment Variables

Create `.env` file (see `.env.example` for all variables):

```env
# Required
TELEGRAM_BOT_TOKEN=your_bot_token_here
OPENAI_API_KEY=your_openai_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/torah_bot

# Optional
TORAH_LOGS_CHAT_ID=-1003025527880
SESSION_SECRET=your_random_secret_here
ADMIN_SECRET=your_admin_secret_here
```

### 4. Run Development Server

```bash
# Start unified webhook service
python unified_webhook_service.py

# Service will run on http://localhost:5000
```

### 5. Set Telegram Webhook (Production)

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -d "url=https://your-domain.replit.app/webhook"
```

For local development, use polling mode or ngrok.

---

## 📁 Project Structure

```
torah-bot/
├── src/
│   ├── core/              # Core infrastructure
│   │   ├── service_container.py   # Dependency injection
│   │   ├── audit_logger.py        # Security logging
│   │   ├── rate_limiter.py        # Rate limiting
│   │   ├── error_handling.py      # Error registry
│   │   └── user_context.py        # User data management
│   │
│   ├── torah_bot/         # Main bot logic
│   │   ├── simple_bot.py           # Bot core (TorahBotFinal)
│   │   ├── admin_commands.py       # Admin functionality
│   │   ├── newsletter_manager.py   # Newsletter database
│   │   ├── wisdom_topics.py        # Wisdom generation
│   │   ├── quiz_topics.py          # Quiz generation
│   │   ├── prompt_loader.py        # AI prompt management
│   │   └── prompts/                # AI prompt templates
│   │
│   ├── newsletter_api/    # Internal newsletter service
│   │   ├── service.py              # Newsletter API
│   │   └── client.py               # API client
│   │
│   ├── mini_game/         # Telegram Mini App
│   │   ├── frontend/               # Game UI (HTML/CSS/JS)
│   │   └── backend/                # Game logic
│   │
│   └── database/          # Database utilities
│       ├── init_database.py        # Schema initialization
│       └── backup_manager.py       # Backup system
│
├── tests/                 # Test suite
│   ├── test_bot.py
│   └── test_newsletter.py
│
├── unified_webhook_service.py  # MAIN ENTRY POINT
├── replit.md              # Project documentation
├── .cursorrules           # Cursor AI configuration
└── .env.example           # Environment template
```

---

## 🧪 Testing

### Run Tests
```bash
# All tests
pytest tests/

# Specific test
pytest tests/test_bot.py

# With coverage
pytest --cov=src tests/
```

### Test Admin Commands
Send these commands to your bot:
- `/send_test_now` - Test wisdom broadcast
- `/send_test_quiz` - Test quiz broadcast
- `/run_api_tests` - Run API integration tests
- `/newsletter_stats` - Check newsletter stats

### Health Check
```bash
curl http://localhost:5000/health
# Expected: {"status":"healthy","service":"torah-bot-unified"}
```

---

## 🗄️ Database Management

### Manual Queries
```bash
# Connect to database
psql $DATABASE_URL

# Common queries
SELECT COUNT(*) FROM users WHERE is_active = true;
SELECT * FROM broadcasts ORDER BY created_at DESC LIMIT 10;
SELECT * FROM delivery_log WHERE status = 'failed' LIMIT 20;
```

### Backup
```bash
# Via admin command
/backup_database

# Manual backup
pg_dump $DATABASE_URL > backup.sql
```

### Schema Changes
**NEVER** manually write migrations. If you need to modify the schema:
1. Update your schema file
2. Run `npm run db:push` (or `--force` if needed)
3. Check deployment logs for errors

---

## 🔧 Common Development Tasks

### Add New Admin Command

1. **Add handler** in `src/torah_bot/admin_commands.py`:
```python
async def handle_my_command(self, chat_id: int, user_id: int):
    await self.telegram_client.send_message(
        chat_id, 
        "My command response"
    )
```

2. **Register** in `handle_admin_command()`:
```python
elif command == "/my_command":
    await self.handle_my_command(chat_id, user_id)
```

3. **Add to help** in `_show_admin_help()`:
```python
help_text += "• /my_command - Description\n"
```

4. **Route** in `src/torah_bot/simple_bot.py`:
```python
elif text == "/my_command" and self.admin_commands:
    await self.admin_commands.handle_admin_command(chat_id, user_id, "/my_command")
```

### Add New Broadcast Type

1. Create generator in `src/torah_bot/new_broadcast.py`
2. Add to `newsletter_api/service.py`
3. Update deduplication logic
4. Test with `/send_test_now`

### Modify AI Prompts

Prompts are in `src/torah_bot/prompts/`:
- `wisdom_prompt.txt` - Daily wisdom
- `quiz_prompt.txt` - Interactive quizzes
- `image_prompt.txt` - Image generation
- `wisdom_variety_elements.txt` - Style variations

Changes reload automatically (hot reload enabled).

---

## 🐛 Debugging

### Enable Debug Logging
```python
import logging
logging.getLogger("src.torah_bot").setLevel(logging.DEBUG)
```

### Check Logs
```bash
# Workflow logs
tail -f logs/UnifiedWebhookService_*.log

# Audit logs (database)
psql $DATABASE_URL -c "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 10;"
```

### Common Issues

**Bot not responding?**
- Check webhook is set: `/getWebhookInfo`
- Verify DATABASE_URL is correct
- Check logs for exceptions

**Database connection errors?**
- Verify PostgreSQL is running
- Check connection string format
- Ensure database exists

**Import errors?**
- Check Python path: `sys.path`
- Verify all dependencies installed
- Try absolute imports

---

## 🚢 Deployment

### Replit Autoscale (Current)
- Entry point: `unified_webhook_service.py`
- Port: 5000
- Mode: Webhook
- Domain: https://torah-project-jobjoyclub.replit.app

### Deploy to Other Platforms

**Docker**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "unified_webhook_service.py"]
```

**Systemd Service**:
```ini
[Unit]
Description=Torah Bot
After=network.target

[Service]
Type=simple
User=torah
WorkingDirectory=/opt/torah-bot
ExecStart=/usr/bin/python3 unified_webhook_service.py
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 📊 Monitoring

### Key Metrics
- Active subscribers: `/newsletter_stats`
- Broadcast success rate: Check delivery_log
- Error rate: Check audit_log
- Scheduler status: `/schedule_status`

### Endpoints
- `GET /health` - Health check
- `GET /api/scheduler_status` - Scheduler info
- `POST /webhook` - Telegram webhook (authenticated)
- `GET /game` - Mini game

---

## 🔐 Security

### Best Practices
- Never commit secrets (use .env)
- Rotate API keys regularly
- Use admin permissions for sensitive commands
- Enable audit logging
- Rate limit API endpoints

### Admin Permissions
Configure in database:
```sql
UPDATE admin_permissions 
SET can_manage_users = true 
WHERE user_id = YOUR_ADMIN_ID;
```

---

## 📚 Additional Resources

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [OpenAI API Docs](https://platform.openai.com/docs)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [asyncpg Docs](https://magicstack.github.io/asyncpg/)

---

## 🆘 Need Help?

1. Check `replit.md` for project history
2. Review `.cursorrules` for coding standards
3. Check logs: `/tmp/logs/`
4. Ask in TorahLogs chat (if configured)

---

Last updated: October 16, 2025
