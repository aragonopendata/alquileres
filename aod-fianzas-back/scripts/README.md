# Scripts Directory

Utility scripts for testing and maintenance.

## Testing Scripts

### test_streets_endpoint_manual.py

Manual testing script for the streets endpoint migration.

**Features:**
- Test single municipality
- Compare multiple municipalities
- Performance benchmarking
- Cache hit/miss analysis
- Health check integration

**Requirements:**
```bash
pip install httpx rich
```

**Usage:**
```bash
# Test single municipality
python scripts/test_streets_endpoint_manual.py --municipality ZARAGOZA

# Compare multiple municipalities
python scripts/test_streets_endpoint_manual.py --compare

# Test against custom API URL
python scripts/test_streets_endpoint_manual.py --url http://localhost:8000

# Show help
python scripts/test_streets_endpoint_manual.py --help
```

**Example Output:**
```
🚀 Streets Endpoint Tester
   API: http://localhost:8000

✅ API is healthy
   Database: healthy
   Cache: healthy

============================================================
Testing: ZARAGOZA
============================================================

📍 Request 1: http://localhost:8000/municipality/ZARAGOZA/street
  Status: 200
  Duration: 45.23ms
  Source: Database
  Cache: N/A
  Streets: 1234

📍 Request 2: http://localhost:8000/municipality/ZARAGOZA/street
  Status: 200
  Duration: 42.15ms
  Cache: N/A

📋 Sample streets (first 10):
  • CALLE MAYOR
  • AVENIDA CENTRAL
  • PLAZA DEL PILAR
  ...
```

## Future Scripts

Additional scripts can be added here for:
- Database migrations
- Cache warming
- Data validation
- Performance monitoring
