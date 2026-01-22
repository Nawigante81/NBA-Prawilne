# Backend Testing Guide

## Quick Start Test

After setting up the backend, you can test the endpoints manually:

### 1. Start the server

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Test health endpoint

```bash
curl http://localhost:8000/health
# Expected: {"status":"ok","timestamp":"2026-01-22T..."}
```

### 3. Test system status

```bash
curl http://localhost:8000/api/status
# Returns database status, API budget, sync times, etc.
```

### 4. Test API documentation

Open browser to: http://localhost:8000/docs

You'll see the interactive Swagger UI with all endpoints.

## API Endpoint Tests

### Team Endpoints

```bash
# Team betting stats (ATS/O-U)
curl "http://localhost:8000/api/team/LAL/betting-stats?window=20"

# Next game for team
curl "http://localhost:8000/api/team/LAL/next-game"

# Key players
curl "http://localhost:8000/api/team/LAL/key-players"
```

### Game Endpoints

```bash
# Today's games
curl "http://localhost:8000/api/games/today"
```

### Odds Endpoints

```bash
# Current odds for a game (replace {game_id})
curl "http://localhost:8000/api/game/{game_id}/odds/current"

# Odds movement
curl "http://localhost:8000/api/game/{game_id}/odds/movement?market_type=spread"

# Closing line value
curl "http://localhost:8000/api/game/{game_id}/clv"

# Consensus line
curl "http://localhost:8000/api/game/{game_id}/consensus?cutoff=now"
```

### Value Board

```bash
# Today's value bets with quality gates applied
curl "http://localhost:8000/api/value-board/today"
```

### Picks & Performance

```bash
# Today's picks
curl "http://localhost:8000/api/picks/today"

# Performance metrics
curl "http://localhost:8000/api/performance"

# Settle a pick (POST request)
curl -X POST "http://localhost:8000/api/picks/settle" \
  -H "Content-Type: application/json" \
  -d '{
    "pick_id": "uuid-here",
    "result": "win",
    "pnl_units": 0.91
  }'
```

## Integration Testing

### Prerequisites

1. Database migrations must be run in Supabase
2. Environment variables must be set in `.env`
3. Odds API key must be valid

### Test Sequence

1. **Database Connection**
   ```bash
   # Check status endpoint returns database: true
   curl http://localhost:8000/api/status | jq '.database'
   ```

2. **Sync Jobs** (run manually first time)
   ```python
   # In Python console:
   import asyncio
   from services.stats_service import sync_nba_teams, sync_nba_games
   
   asyncio.run(sync_nba_teams())
   asyncio.run(sync_nba_games())
   ```

3. **Odds Fetching** (check budget)
   ```bash
   curl http://localhost:8000/api/status | jq '.odds_api_budget'
   # Ensure calls_used < ODDS_MAX_CALLS_PER_DAY
   ```

4. **Value Board** (after data is synced)
   ```bash
   curl http://localhost:8000/api/value-board/today | jq '.total_count'
   # Should return number of opportunities found
   ```

## Common Issues

### "Database pool initialization failed"
- Check SUPABASE_URL and SUPABASE_SERVICE_KEY in .env
- Verify Supabase project is accessible
- Ensure migrations have been run

### "No games returned"
- Data sync may not have run yet
- Check logs for sync job status
- Manually trigger sync jobs if needed

### "No odds available"
- API budget may be exhausted
- Check ODDS_API_KEY is valid
- Verify bookmakers in ODDS_BOOKMAKERS_ALLOWLIST exist for NBA

### "Import errors"
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version is 3.11+
- Verify PYTHONPATH includes backend directory

## Manual Testing Script

Save this as `test_backend.sh`:

```bash
#!/bin/bash

BASE_URL="http://localhost:8000"

echo "Testing NBA Betting Analytics Backend..."
echo "=========================================="

echo -e "\n1. Health Check"
curl -s $BASE_URL/health | jq '.'

echo -e "\n2. System Status"
curl -s $BASE_URL/api/status | jq '.status, .database'

echo -e "\n3. Today's Games"
curl -s $BASE_URL/api/games/today | jq 'length'

echo -e "\n4. Team Stats (Lakers)"
curl -s "$BASE_URL/api/team/LAL/betting-stats?window=10" | jq '.team_abbrev, .ats_record'

echo -e "\n5. Value Board"
curl -s $BASE_URL/api/value-board/today | jq '.total_count'

echo -e "\n6. Performance Metrics"
curl -s $BASE_URL/api/performance | jq '.total_picks, .roi'

echo -e "\n=========================================="
echo "Backend test complete!"
```

Run with: `chmod +x test_backend.sh && ./test_backend.sh`

## Automated Tests

For CI/CD, create pytest tests in `backend/tests/`:

```python
# test_api.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_status():
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "database" in data
    assert "odds_api_budget" in data
```

Run tests: `pytest backend/tests/`
