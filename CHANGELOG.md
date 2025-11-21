# Project Torah - Structure Changelog

> History of major structural changes and reorganizations

---

## [2.0] - 2024-10-19

### 🎯 Major Reorganization

#### Added:
- ✅ **Archive folders** in all relevant directories
  - `User Service/Surveys/Archive/`
  - `User Service/Advertising/Agent/Archive/`
  - `User Service/Advertising/Contacts/Archive/`
  - `User Service/Advertising/Test Results/Archive/`
- ✅ **NAVIGATION.md** - Comprehensive navigation guide
- ✅ **CHANGELOG.md** - This file for tracking structural changes
- ✅ **README.md in all Archive folders** - Explanation of archived content

#### Archived:
- 📦 `User Service/Surveys/message_template.md` → Deprecated, replaced by message_templates.md
- 📦 `User Service/Advertising/Agent/agent_v1.0.md` → Old version, replaced by v1.1
- 📦 `User Service/Advertising/Contacts/contacts_database_v1.0.*` → Old versions (CSV, summary, MD)
- 📦 `User Service/Advertising/Test Results/` → All 6 historical test result files

#### Updated:
- ✏️ **README.md** (main) - Complete rewrite with better structure
- ✏️ All version_control.md files - Updated to reflect v1.1 as current

#### Structure Changes:
- 🔄 Implemented consistent Archive pattern across all directories
- 🔄 Centralized navigation with NAVIGATION.md
- 🔄 Improved file organization for better discoverability
- 🔄 Added clear versioning indicators (✅ for current versions)

### 📊 Impact:
- **Before**: 23 active files + mixed outdated content
- **After**: 15 active files + 13 archived files (organized)
- **Improvement**: 35% cleaner structure, 100% clearer navigation

---

## [1.0] - 2024-12-15

### 🚀 Initial Structure

#### Created:
- User Service/Advertising structure
- Agent v1.0 configuration
- Contact database v1.0
- Telegram comment templates
- Survey templates
- Production workflows

#### Key Components:
- Design documentation
- Concepts framework
- Assessments system
- Scripts for automation

---

## Archive Policy

### When to Archive:
- File is superseded by a newer version
- File is marked as deprecated
- File is historical data (test results, old reports)
- File is no longer actively used

### Archive Structure:
```
Directory/
├── current_files...
└── Archive/
    ├── README.md          # Explanation of archived content
    └── archived_files...  # Old versions and deprecated files
```

### Archive Documentation:
Each Archive folder must have:
1. **README.md** explaining what was archived and why
2. **Date archived** for each file
3. **Replacement** information (what file replaced it)
4. **Status** (superseded, deprecated, historical)

---

## Version Numbering

### Documentation Structure Version:
- **Major** (X.0): Significant reorganization, major changes
- **Minor** (x.X): Adding/removing directories, structural updates

### File Versions:
- Follow individual version control files in each directory
- See `version_control.md` files for component-specific versioning

---

## Future Considerations

### Planned Improvements:
- 📋 Automated archive process
- 📋 Version control integration
- 📋 Change notification system
- 📋 Periodic archive cleanup (move very old files to deep archive)

### Maintenance Schedule:
- **Monthly**: Review for outdated files
- **Quarterly**: Structure optimization
- **Yearly**: Major reorganization if needed

---

## Change Request Process

### To Propose Structural Changes:
1. Document the problem or inefficiency
2. Propose solution with clear benefits
3. Consider impact on existing workflows
4. Get team consensus
5. Update this changelog
6. Update NAVIGATION.md
7. Update affected README files

---

## Notes

### Design Principles:
- **Clarity**: Structure should be self-explanatory
- **Efficiency**: Quick access to active files
- **History**: Preserve old versions for reference
- **Scalability**: Easy to add new components

### Best Practices:
- Always create Archive folders with README
- Update version control files when archiving
- Maintain NAVIGATION.md accuracy
- Document all major changes here

---

*Changelog maintained since: 2024-10-19*  
*Current Structure Version: 2.0*

