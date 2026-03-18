# Storage Directory Structure

This folder contains runtime data for the RASA-ID backend application.

## Directory Layout

```
storage/
├── uploads/           # User uploads (organized by date: YYYY/MM/DD/)
├── models/            # Active YOLO model (best.pt + active_model.json)
├── feedback/          # Feedback correction dataset
│   ├── images/
│   └── labels/
├── class_requests/    # New class request images
│   └── images/
├── exports/           # Production exports from admin endpoints
│   ├── feedback/
│   └── class_requests/
└── temp/              # Temporary/debug files ONLY
    ├── test_data/
    ├── manual_exports/
    └── quarantine/
```

## Rules

1. **`temp/` is NOT for permanent storage** - clean periodically
2. **`exports/` is for endpoint-generated ZIPs only** - not manual tests
3. **DO NOT commit runtime data to git** - only structure files like .gitkeep
4. **Use `app/core/paths.py`** for path constants in code
