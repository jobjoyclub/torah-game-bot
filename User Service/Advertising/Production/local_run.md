# Local Run Guide (No GitHub)

## Quick run
- Open Cursor in Project Torah
- Run the shell script:

```bash
bash "scripts/run_enricher.sh"
```

This will:
- Read `contacts_database_v1.0.csv`
- Enrich Additional Email + update Last Verified
- Write updates and create `contacts_database_v1.1.csv`

## Notes
- Script uses only Python stdlib (no extra installs)
- Works on macOS without dev tools
- Make sure your file paths remain unchanged

## Optional
- Re-run any time after adding new contacts
- Keep CSV open in Excel/Numbers only in read-only mode to avoid locks

