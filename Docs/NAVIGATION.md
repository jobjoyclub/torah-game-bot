# 🧭 Project Torah - Navigation Guide

> **Quick reference for navigating the Project Torah documentation structure**

---

## 📂 Main Structure

```
Project Torah/
├── 📖 README.md                    # Main project overview
├── 🧭 NAVIGATION.md               # This file - quick navigation guide
├── 🎯 Design/                     # Game design and UX
├── 💡 Concepts/                   # Ideas and proposals
├── 📊 Assessments/                # Project evaluations
├── 👥 User Service/               # Marketing & user engagement
└── ⚙️ scripts/                    # Automation tools
```

---

## 🎯 Design

**Purpose**: Game mechanics, gameplay, and user experience design

### Key Files:
- 📄 `GAMEPLAY.md` - Main game design document (GDD)
- 📄 `README.md` - Design philosophy and overview

**When to use**: Game mechanics changes, UX improvements, feature design

---

## 💡 Concepts

**Purpose**: Creative ideas and game design proposals

### Structure:
- 📁 `Game Design Ideas/` - New concept proposals
  - 📄 `idea-template.md` - Template for new ideas
  - 📄 `README.md` - How to submit ideas

**When to use**: Proposing new features, brainstorming game mechanics

---

## 📊 Assessments

**Purpose**: Project performance evaluations and analysis

### Key Files:
- 📄 `Torah_Bot_Application_Assessment_September_2025.md` - Latest assessment

**When to use**: Performance reviews, strategic planning, progress tracking

---

## 👥 User Service

**Purpose**: User engagement, marketing, and community management

### 📢 Advertising

**Path**: `User Service/Advertising/`

#### Active Files:
- 📄 `README.md` - Overview of advertising strategy
- 📄 `telegram_comment_templates.md` - Comment templates (regular format)
- 📄 `telegram_comment_templates_table.md` - Comment templates (table format)
- 📄 `contextual_ads_phrases.md` - Natural promotional phrases
- 📄 `agent_testing_plan.md` - Agent testing methodology
- 📄 `contact_research_prompt.md` - Research prompts
- 📄 `test_launch_instructions.md` - Test launch guide
- 📄 `test_results_template.md` - Template for test results

#### 🤖 Agent/
**Current Version**: v1.1

**Active Files**:
- 📄 `agent_v1.1.md` - ✅ Current agent configuration
- 📄 `version_control.md` - Version history

**Archive**:
- 📁 `Archive/agent_v1.0.md` - Old version (reference only)

#### 📇 Contacts/
**Current Version**: v1.1

**Active Files**:
- 📄 `contacts_database_v1.1.csv` - ✅ Current contact database
- 📄 `contacts_version_control.md` - Version history

**Archive**:
- 📁 `Archive/` - Old versions (v1.0.x) for reference

#### 📧 Emails/
- 📁 `v1/base_email_en_ru.md` - Email templates (English/Russian)

#### 🚀 Production/
- 📄 `automation_readme.md` - Automation setup guide
- 📄 `workflow_v1.0.md` - Production workflow
- 📄 `local_run.md` - Local testing guide
- 📄 `contact_automation_analysis.md` - Automation analysis

#### 🧪 Test Results/
**Archive**:
- 📁 `Archive/` - All historical test results (6 files)

### 📋 Surveys

**Path**: `User Service/Surveys/`

#### Active Files:
- 📄 `README.md` - Survey overview
- 📄 `message_templates.md` - ✅ Current message templates
- 📄 `summary.md` - Survey tracker and insights
- 📁 `responses/` - Individual user responses

**Archive**:
- 📁 `Archive/message_template.md` - Deprecated template

---

## ⚙️ Scripts

**Purpose**: Automation and utility scripts

### Available Scripts:
- 🐍 `contact_enricher.py` - Contact data enrichment automation
- 🔧 `run_enricher.sh` - Shell wrapper for enricher
- 📄 `README.md` - Scripts documentation and usage guide

**When to use**: Automating contact management, data enrichment

---

## 🎯 Quick Access - Most Used Files

### For Marketing Activities:
1. 📄 `User Service/Advertising/telegram_comment_templates.md` - Comment templates
2. 📄 `User Service/Advertising/Agent/agent_v1.1.md` - Current agent config
3. 📄 `User Service/Advertising/Contacts/contacts_database_v1.1.csv` - Contact list

### For User Research:
1. 📄 `User Service/Surveys/message_templates.md` - Outreach templates
2. 📄 `User Service/Surveys/summary.md` - Survey tracker
3. 📄 `User Service/Surveys/responses/` - User feedback

### For Development:
1. 📄 `Design/GAMEPLAY.md` - Game mechanics
2. 📄 `Concepts/Game Design Ideas/` - Feature ideas
3. 📄 `scripts/` - Automation tools

### For Planning:
1. 📄 `README.md` - Project overview
2. 📄 `Assessments/` - Performance reviews
3. 📄 `User Service/README.md` - User service goals

---

## 📁 Archive Policy

**All Archive folders contain**:
- Historical versions of files
- Deprecated documents
- Reference-only materials
- README.md explaining what was archived and why

**Never use archived files for active work** - always use latest versions from parent directories.

---

## 🔄 Version Control

### Current Active Versions:
- **Agent**: v1.1 (`User Service/Advertising/Agent/agent_v1.1.md`)
- **Contacts**: v1.1 (`User Service/Advertising/Contacts/contacts_database_v1.1.csv`)
- **Message Templates**: Latest (`User Service/Surveys/message_templates.md`)
- **Comment Templates**: v1.0 (`User Service/Advertising/telegram_comment_templates*.md`)

### Version History:
Check `version_control.md` files in respective directories for detailed changelog.

---

## 💡 Tips for Navigation

### Finding Specific Content:
- **Marketing materials** → `User Service/Advertising/`
- **User feedback** → `User Service/Surveys/`
- **Game design** → `Design/GAMEPLAY.md`
- **New ideas** → `Concepts/Game Design Ideas/`
- **Automation** → `scripts/`

### Before Creating New Files:
1. Check if similar content exists
2. Review templates in `Concepts/Game Design Ideas/`
3. Follow naming conventions (YYYY-MM-DD format for dates)
4. Update relevant README files

### When Archiving:
1. Move to `Archive/` subfolder in same directory
2. Add README.md in Archive explaining what and why
3. Update parent README if needed
4. Keep version control files updated

---

## 📞 Support

### Documentation Issues:
- Outdated information? Update the file and its last modified date
- Missing documentation? Create it using templates from similar sections
- Unclear structure? Add clarifying comments or improve README

### File Organization:
- Always maintain Archive folders with README files
- Keep version control documentation updated
- Follow established naming conventions
- Update this navigation guide when structure changes

---

*Last Updated: 2024-10-19*  
*Version: 1.0*  
*Purpose: Quick navigation and structure understanding*

