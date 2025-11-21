# Project Torah — Documentation Hub

> Educational Telegram bot and mini-app for Torah learning through interactive gameplay

---

## 🎯 Quick Start

**New to the project?** Start here:
1. 📖 Read this README for project overview
2. 🧭 Check [NAVIGATION.md](./NAVIGATION.md) for detailed structure guide
3. 📊 Review latest [Assessment](./Assessments/) for current status
4. 🎮 See [GAMEPLAY.md](./Design/GAMEPLAY.md) for game mechanics

---

## 📂 Project Structure

```
Project Torah/
├── 📖 README.md                    # You are here - Project overview
├── 🧭 NAVIGATION.md               # Detailed navigation guide
│
├── 🎯 Design/                     # Game design & user experience
│   ├── GAMEPLAY.md                # Main game design document
│   └── README.md                  # Design philosophy
│
├── 💡 Concepts/                   # Ideas and proposals
│   ├── Game Design Ideas/         # New feature concepts
│   │   ├── idea-template.md       # Template for proposals
│   │   └── README.md              # How to submit ideas
│   └── README.md                  # Concepts overview
│
├── 📊 Assessments/                # Performance evaluations
│   ├── Torah_Bot_Application_Assessment_September_2025.md
│   └── README.md                  # Assessment overview
│
├── 👥 User Service/               # Marketing & user engagement
│   ├── Advertising/               # Marketing campaigns
│   │   ├── Agent/                 # AI outreach agent
│   │   │   ├── agent_v1.1.md     # ✅ Current version
│   │   │   ├── version_control.md
│   │   │   └── Archive/           # Old versions
│   │   ├── Contacts/              # Contact database
│   │   │   ├── contacts_database_v1.1.csv  # ✅ Current version
│   │   │   ├── contacts_version_control.md
│   │   │   └── Archive/           # Old versions
│   │   ├── Emails/                # Email templates
│   │   ├── Production/            # Automation workflows
│   │   ├── Test Results/
│   │   │   └── Archive/           # Historical test data
│   │   ├── telegram_comment_templates.md      # Comment templates
│   │   ├── telegram_comment_templates_table.md  # Table format
│   │   ├── contextual_ads_phrases.md
│   │   ├── agent_testing_plan.md
│   │   ├── test_launch_instructions.md
│   │   └── test_results_template.md
│   │
│   └── Surveys/                   # User feedback
│       ├── message_templates.md   # ✅ Current templates
│       ├── summary.md             # Survey tracker
│       ├── responses/             # User feedback
│       └── Archive/               # Old templates
│
└── ⚙️ scripts/                    # Automation tools
    ├── contact_enricher.py        # Contact data enrichment
    ├── run_enricher.sh            # Shell wrapper
    └── README.md                  # Scripts documentation
```

---

## 🎯 Project Overview

### What is Project Torah?

**Project Torah** is an educational Telegram bot (@torah_robot) that combines Torah learning with interactive gameplay. The project uses gamification to make Torah study engaging, accessible, and fun for all ages.

### Key Features:
- 🎮 **Interactive Shabbat Mini-Game** - Learn through play
- 📚 **Educational Content** - Torah wisdom and values
- 🆓 **Free & Ad-Free** - Pure educational experience
- 👨‍👩‍👧‍👦 **Family Friendly** - Suitable for all ages
- 📱 **Telegram Platform** - Easy access, no installation

---

## 🗂️ Documentation Sections

### 🎯 Design
**Purpose**: Game mechanics, UX design, and player experience

**Key Files**:
- `GAMEPLAY.md` - Complete game design document
- `README.md` - Design principles and philosophy

**Use for**: Game mechanics updates, UX improvements, feature design

---

### 💡 Concepts
**Purpose**: New ideas, proposals, and creative concepts

**Key Files**:
- `Game Design Ideas/` - Feature proposals and concepts
- `idea-template.md` - Template for new proposals

**Use for**: Brainstorming, feature proposals, creative exploration

---

### 📊 Assessments
**Purpose**: Project evaluation and performance analysis

**Key Files**:
- Latest assessment reports
- Performance metrics
- Strategic recommendations

**Use for**: Performance reviews, strategic planning, progress tracking

---

### 👥 User Service
**Purpose**: Marketing, user acquisition, and community management

#### 📢 Advertising
**Current Focus**: Telegram outreach, contact management, automated campaigns

**Active Versions**:
- **Agent**: v1.1 ✅
- **Contacts**: v1.1 ✅
- **Templates**: v1.0 ✅

**Key Resources**:
- Comment templates for Telegram
- Agent configuration and testing
- Contact database and enrichment
- Email templates and campaigns

#### 📋 Surveys
**Current Focus**: User feedback collection and analysis

**Key Resources**:
- Message templates for outreach
- Survey tracker and insights
- User response database

---

### ⚙️ Scripts
**Purpose**: Automation and utility tools

**Available Scripts**:
- `contact_enricher.py` - Automated contact data enhancement
- `run_enricher.sh` - Shell wrapper for automation

**Use for**: Contact management automation, data processing

---

## 🔄 Version Control & Archives

### Current Active Versions:

| Component | Version | File Location |
|-----------|---------|---------------|
| Agent | v1.1 | `User Service/Advertising/Agent/agent_v1.1.md` |
| Contacts | v1.1 | `User Service/Advertising/Contacts/contacts_database_v1.1.csv` |
| Message Templates | Latest | `User Service/Surveys/message_templates.md` |
| Comment Templates | v1.0 | `User Service/Advertising/telegram_comment_templates.md` |

### Archive Policy:

**All outdated files are moved to `Archive/` subfolders**:
- ✅ Each Archive has a README explaining contents
- ✅ Old versions kept for reference only
- ✅ Never use archived files for active work
- ✅ Version control files track all changes

---

## 🎯 Common Tasks

### For Marketing Activities:
1. **Create Telegram comments**: Use `User Service/Advertising/telegram_comment_templates.md`
2. **Contact outreach**: Check `User Service/Advertising/Contacts/contacts_database_v1.1.csv`
3. **Configure agent**: See `User Service/Advertising/Agent/agent_v1.1.md`
4. **Email campaigns**: Use `User Service/Advertising/Emails/v1/`

### For User Research:
1. **Send surveys**: Use `User Service/Surveys/message_templates.md`
2. **Track responses**: Update `User Service/Surveys/summary.md`
3. **Store feedback**: Add to `User Service/Surveys/responses/`

### For Development:
1. **Update game mechanics**: Edit `Design/GAMEPLAY.md`
2. **Propose features**: Add to `Concepts/Game Design Ideas/`
3. **Run automation**: Execute scripts from `scripts/`

### For Planning:
1. **Review performance**: Check latest `Assessments/`
2. **Set goals**: Update `User Service/README.md`
3. **Plan campaigns**: See `User Service/Advertising/README.md`

---

## 📝 Documentation Guidelines

### Creating New Files:
1. Check if similar content exists (avoid duplicates)
2. Use appropriate templates when available
3. Follow naming conventions (YYYY-MM-DD for dates)
4. Update relevant README files
5. Add clear purpose and metadata

### Updating Existing Files:
1. Update "Last Updated" date
2. Document significant changes
3. Update version if applicable
4. Notify team of major updates

### Archiving Files:
1. Move to `Archive/` subfolder in same directory
2. Create/update Archive README
3. Update version control documentation
4. Update parent directory README

---

## 🚀 Current Status

### ✅ Completed:
- Core bot functionality
- Basic gameplay mechanics
- Contact database v1.1 (68+ contacts)
- Agent v1.1 with global reach
- Telegram comment templates
- Email templates (EN/RU)
- Automation scripts

### 🔄 In Progress:
- User feedback collection
- Marketing campaigns
- Contact database expansion
- Agent testing and optimization

### ⏳ Planned:
- Telegram Mini App development
- AI integration for personalization
- Advanced game mechanics
- Community features
- Analytics dashboard

---

## 📊 Key Metrics

### User Acquisition:
- **Target**: 10,000 users by end of year
- **Current**: Growing steadily
- **Strategy**: Community-driven, organic growth

### User Engagement:
- **Target**: 60%+ weekly active users
- **Strategy**: Daily value delivery through gameplay

### Contact Database:
- **Current**: 68+ qualified contacts (v1.1)
- **Target**: 500+ contacts
- **Coverage**: 18+ countries, 8+ organization types

---

## 🔗 Related Resources

### Internal:
- [NAVIGATION.md](./NAVIGATION.md) - Detailed navigation guide
- [Design/GAMEPLAY.md](./Design/GAMEPLAY.md) - Game design document
- [User Service/README.md](./User Service/README.md) - User service overview

### External:
- Telegram Bot: [@torah_robot](https://t.me/torah_robot)
- Development tools: See `scripts/README.md`

---

## 💡 Need Help?

### Finding Information:
1. Check [NAVIGATION.md](./NAVIGATION.md) for structure
2. Use README files in each directory
3. Search for relevant keywords

### Making Changes:
1. Review documentation guidelines above
2. Use templates when available
3. Update version control as needed
4. Keep archives organized

### Questions or Issues:
- Check relevant README files
- Review version control documentation
- Consult team members

---

## 📅 Update Log

**2024-10-19**:
- ✅ Reorganized structure with Archive folders
- ✅ Created NAVIGATION.md for easy reference
- ✅ Updated version control system
- ✅ Added README files to all Archive folders
- ✅ Consolidated outdated files
- ✅ Improved documentation clarity

**Previous Updates**: See specific version_control.md files in subdirectories

---

*Last Updated: 2024-10-19*  
*Project: @torah_robot - Educational Telegram Bot*  
*Documentation Version: 2.0*
