# Autonomous Contact Enrichment Service

## What it does
- Reads current contacts CSV (`contacts_database_v1.0.csv`)
- Parses organization websites to discover additional emails
- Updates `Additional Email` and `Last Verified`
- Writes updates back and creates `contacts_database_v1.1.csv` snapshot
- Runs automatically weekly and commits results

## Where
- Script: `Project Torah/scripts/contact_enricher.py`
- Runner: `Project Torah/scripts/run_enricher.sh`
- Data: `User Service/Advertising/Contacts/`

## Schedule
- On demand: Run manually when you need to enrich contacts
- Command: `bash scripts/run_enricher.sh` from Project Torah folder

## Cost footprint
- Pure HTTP + HTML parsing; no paid APIs required
- Add API keys later (e.g., Google Maps) if needed

## Safety
- Non‑destructive snapshot v1.1 is created on each run
- Original v1.0 file is updated; v1.1 is a backup snapshot

## Extending
- Add DNS/MX validation (dnspython)
- Add domain‑scoped email preference rules
- Add country/city batching from YAML config

## Outputs
- Updated `contacts_database_v1.0.csv`
- New snapshot `contacts_database_v1.1.csv`
- Console message showing updated file paths
