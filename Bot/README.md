# 🕎 Torah Bot - AI-Powered Jewish Educational Platform

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Production-ready Telegram bot providing AI-powered educational content focused on Torah and Talmud studies. Features interactive quizzes, daily wisdom broadcasts, multilingual support, and a Telegram Mini App game.

## ✨ Features

### 🤖 AI-Powered Content
- **Daily Wisdom**: GPT-4o generated Torah teachings with DALL-E 3 images
- **Interactive Quizzes**: Engaging multiple-choice questions on Jewish topics
- **Smart Variety**: 177+ topic combinations with 15 style variations
- **Multilingual**: 9 languages (English, Russian, Hebrew, Spanish, French, German, Italian, Portuguese, Arabic)

### 📧 Newsletter System
- **Automated Broadcasts**: Scheduled wisdom (9 AM MSK) and quizzes (9 PM MSK)
- **User Management**: 264+ active subscribers with language preferences
- **Deduplication**: 45-day wisdom, 21-day quiz uniqueness guarantees
- **Delivery Tracking**: Comprehensive analytics and blocked user detection

### 🎮 Telegram Mini App
- **Shabbat Runner**: Interactive game with tutorial
- **Analytics Integration**: Game metrics tracked to TorahLogs
- **Native Menu Button**: Seamless Telegram integration

### 🔒 Enterprise Security
- **Audit Logging**: Complete action tracking with database persistence
- **Rate Limiting**: DDoS protection with customizable limits
- **Webhook Authentication**: Secure Telegram API integration
- **Admin Permissions**: Granular access control system

### 📊 Admin Features
- Newsletter statistics and subscriber management
- Test broadcasts and quiz generation
- Database backup system
- Blocked users CSV export
- Comprehensive API testing suite

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 16+
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- OpenAI API Key

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/torah-bot.git
cd torah-bot

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Initialize database
python src/database/init_database.py

# Run development server
python unified_webhook_service.py
```

Server will start on `http://localhost:5000`

### Configuration

See [`.env.example`](.env.example) for all environment variables. Required:

```env
TELEGRAM_BOT_TOKEN=your_bot_token
OPENAI_API_KEY=your_openai_key
DATABASE_URL=postgresql://user:pass@host:5432/db
```

## 📁 Project Structure

```
torah-bot/
├── src/
│   ├── core/              # Core infrastructure
│   │   ├── service_container.py   # Dependency injection
│   │   ├── audit_logger.py        # Security logging
│   │   └── error_handling.py      # Error management
│   ├── torah_bot/         # Main bot logic
│   │   ├── simple_bot.py          # Bot core
│   │   ├── admin_commands.py      # Admin features
│   │   └── newsletter_manager.py  # Newsletter system
│   ├── newsletter_api/    # Internal API service
│   ├── mini_game/         # Telegram Mini App
│   └── database/          # Database utilities
├── tests/                 # Test suite
├── unified_webhook_service.py  # ENTRY POINT
├── DEVELOPMENT.md         # Development guide
└── .cursorrules           # Cursor AI rules
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Test specific module
pytest tests/test_bot.py

# With coverage
pytest --cov=src tests/
```

### Admin Test Commands
- `/send_test_now` - Test wisdom broadcast
- `/send_test_quiz` - Test quiz broadcast
- `/newsletter_stats` - View statistics
- `/run_api_tests` - Run API tests

## 📖 Documentation

- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Complete development setup guide
- **[.cursorrules](.cursorrules)** - Cursor AI configuration and coding standards
- **[replit.md](replit.md)** - Project history and architecture decisions

## 🏗️ Architecture

### Service Container Pattern
All services initialized via dependency injection:
```python
from src.core.service_container import ServiceContainer

container = ServiceContainer()
bot = container.get_service("torah_bot")
```

### Webhook Architecture
- **Production**: Autoscale deployment with webhook mode
- **Entry Point**: `unified_webhook_service.py`
- **Port**: 5000 (bound to 0.0.0.0)
- **Health Check**: `GET /health`

### Database
- **Connection Pooling**: asyncpg with context managers
- **Advisory Locks**: Broadcast deduplication
- **Audit Logs**: Security event tracking
- **Migrations**: Schema managed via `npm run db:push`

## 🔐 Security

- ✅ Secrets in environment variables
- ✅ CORS restricted to Telegram domains
- ✅ Rate limiting middleware
- ✅ Webhook authentication
- ✅ Admin permission system
- ✅ Comprehensive audit logging

## 📊 Production Stats

- **Active Subscribers**: 264+
- **Daily Broadcasts**: 2 (wisdom + quiz)
- **Content Variety**: 177 topic combinations
- **Supported Languages**: 9
- **Uptime**: 99.9% (autoscale)

## 🛠️ Tech Stack

- **Backend**: Python 3.11, FastAPI, Uvicorn
- **Database**: PostgreSQL 16 (asyncpg)
- **AI**: OpenAI GPT-4o, DALL-E 3
- **Telegram**: Bot API (webhook mode)
- **Frontend**: Vanilla JS (Mini Game)
- **Deployment**: Replit Autoscale

## 🤝 Contributing

1. Read [DEVELOPMENT.md](DEVELOPMENT.md)
2. Follow [.cursorrules](.cursorrules) coding standards
3. Write tests for new features
4. Submit pull request

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🆘 Support

- **Documentation**: Check [DEVELOPMENT.md](DEVELOPMENT.md)
- **Issues**: Open a GitHub issue
- **Logs**: Production logs in TorahLogs Telegram chat

## 🙏 Acknowledgments

- OpenAI for GPT-4o and DALL-E 3
- Telegram for Bot API
- Replit for hosting platform
- Jewish educational content contributors

---

**Built with ❤️ for Jewish education**

Last updated: October 16, 2025
