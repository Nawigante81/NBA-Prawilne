# 🚀 Deployment Guide - NBA Analysis & Betting Intelligence Platform

## Migration from Old System to New Architecture

This document explains how to migrate from the old `main.py` to the new production-grade `main_new.py`.

### What's New

The new system implements:

1. **Provider-Based Architecture** - Clean separation of data sources
2. **Quality Gates** - Ensures data quality before recommendations
3. **Budget Management** - Strict API call tracking and enforcement
4. **CLV Tracking** - Closing line value analysis
5. **Enhanced Reports** - Quality-gated betting proposals
6. **Complete Testing** - 25 betting math tests (100% pass)

### Prerequisites

1. **Database Migration**
   ```bash
   # Apply new migration in Supabase SQL Editor
   supabase/migrations/20260122014000_011_add_betting_platform_tables.sql
   ```

2. **Environment Configuration**
   ```bash
   # Update .env with new variables (see backend/.env.example)
   cp backend/.env.example backend/.env
   # Edit backend/.env with your keys
   ```

3. **Python Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

### Step-by-Step Migration

#### 1. Test the New System

```bash
cd backend

# Test imports
python -c "import main_new; print('✓ Imports successful')"

# Run unit tests
pytest test_betting_math.py -v

# Test API startup (Ctrl+C to stop)
uvicorn main_new:app --reload --port 8001
```

Open http://localhost:8001/docs to see the new API documentation.

#### 2. Verify Database Tables

Check that all new tables exist in Supabase:

```sql
-- Run this in Supabase SQL Editor
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
```

Expected new tables:
- `api_budget`
- `api_cache`
- `odds_snapshots`
- `picks`
- `pick_results`
- `reports`
- `team_game_stats`
- `uploads_stub`

#### 3. Configure Quality Gates

Edit `backend/.env` to tune quality gates:

```bash
# Minimum expected value for picks
MIN_EV=0.02

# Minimum edge over implied probability
MIN_EDGE_PROB=0.03

# Minimum model confidence
MIN_CONFIDENCE=0.55

# Maximum American odds for favorites (too much juice)
ODDS_MAX_AMERICAN_FAVORITE=-160

# Stats must be this recent
STATS_MAX_AGE_HOURS=24
ODDS_MAX_SNAPSHOT_AGE_HOURS=12
```

#### 4. Test with API Calls

```bash
# Start server
uvicorn main_new:app --port 8000

# In another terminal, test endpoints:

# Health check
curl http://localhost:8000/health

# System status
curl http://localhost:8000/api/status

# Today's budget
curl http://localhost:8000/api/budget

# Teams
curl http://localhost:8000/api/teams

# Today's games
curl http://localhost:8000/api/games/today
```

#### 5. Replace main.py (Optional)

Once you've verified everything works:

```bash
cd backend

# Backup old main.py
mv main.py main_old.py

# Use new main.py
mv main_new.py main.py

# Update Dockerfile CMD if needed (should work as-is)
```

Or keep both and update your deployment scripts to use `main_new:app`.

### Docker Deployment

#### Using Docker Compose

```bash
# Update docker-compose.yml backend service
services:
  backend:
    build: ./backend
    command: uvicorn main_new:app --host 0.0.0.0 --port 8000
    # ... rest of config
```

Then:

```bash
docker-compose down
docker-compose build backend
docker-compose up -d
```

#### Standalone Docker

```bash
cd backend

# Build image
docker build -t nba-backend:v2 .

# Run container
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name nba-backend \
  nba-backend:v2
```

### Production Checklist

Before deploying to production:

- [ ] Run database migration
- [ ] Update all environment variables in `.env`
- [ ] Set secure `ADMIN_API_KEY`
- [ ] Test all API endpoints locally
- [ ] Run `pytest test_betting_math.py -v` (must pass 25/25)
- [ ] Verify quality gates work (try fetching value board)
- [ ] Check scheduler starts correctly (view logs)
- [ ] Verify reports generate at correct times (7:50, 8:00, 11:00 CT)
- [ ] Monitor API budget tracking (check `/api/budget` endpoint)
- [ ] Set up log aggregation (logs to `backend/logs/main.log`)
- [ ] Configure alerts for API budget exceeded
- [ ] Test provider health checks
- [ ] Verify CORS settings for your frontend domain

### Monitoring

#### Key Metrics to Monitor

1. **API Budget Usage**
   ```bash
   curl http://your-domain/api/budget
   ```
   Watch for:
   - Odds API calls approaching daily limit (10/day)
   - NBA API cache hit rate
   - Basketball-Reference request intervals

2. **Quality Gate Performance**
   ```bash
   curl http://your-domain/api/value-board/today
   ```
   Check for frequent "NO_BET" responses with reasons.

3. **CLV Performance**
   ```bash
   curl http://your-domain/api/performance
   ```
   Monitor:
   - Average CLV
   - Positive CLV rate (should be > 50%)
   - ROI and yield

4. **Scheduler Status**
   ```bash
   curl http://your-domain/api/status
   ```
   Verify:
   - Scheduler is running
   - All 4 jobs scheduled (startup, 12h sync, 3 reports)
   - Next run times are correct

#### Logs

```bash
# View real-time logs
tail -f backend/logs/main.log

# Search for errors
grep ERROR backend/logs/main.log

# Check quality gate failures
grep "Quality gate failed" backend/logs/main.log

# Check API budget warnings
grep "budget exceeded" backend/logs/main.log
```

### Troubleshooting

#### Problem: Imports fail

**Solution:**
```bash
cd backend
export PYTHONPATH=$PYTHONPATH:$(pwd)
python -c "import main_new"
```

#### Problem: Database connection fails

**Solution:**
- Check `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in `.env`
- Verify you're using SERVICE_ROLE_KEY not ANON_KEY
- Test connection:
  ```python
  python -c "from db import get_db; db = get_db(); print('✓ Connected')"
  ```

#### Problem: Scheduler doesn't start

**Solution:**
- Check timezone setting: `TIMEZONE=America/Chicago`
- Verify pytz is installed: `pip install pytz`
- Look for errors in logs during startup

#### Problem: Quality gates block all picks

**Solution:**
- Lower thresholds in `.env`:
  ```bash
  MIN_EV=0.01  # instead of 0.02
  MIN_CONFIDENCE=0.50  # instead of 0.55
  ```
- Check if you have sufficient data (run sync_service first)
- Verify odds are recent (< 12h old)

#### Problem: Odds API budget exceeded

**Solution:**
- Check current usage: `curl http://localhost:8000/api/budget`
- Increase interval: `ODDS_FETCH_INTERVAL_HOURS=24`
- Reduce max calls: `ODDS_MAX_CALLS_PER_DAY=5`
- Wait until next day for budget reset

### Rollback Procedure

If you need to rollback to the old system:

```bash
cd backend

# Stop new service
pkill -f "uvicorn main_new"

# Restore old main.py
mv main_old.py main.py

# Start old service
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Note:** Old system won't have access to new tables (picks, api_budget, etc.) but will continue to work with existing tables.

### Support

For issues or questions:

1. Check backend/README.md for detailed documentation
2. Review API docs at http://localhost:8000/docs
3. Check logs in backend/logs/main.log
4. Run unit tests: `pytest test_betting_math.py -v`

### Next Steps

After successful deployment:

1. Monitor API budget usage daily
2. Review CLV performance weekly
3. Tune quality gate thresholds based on results
4. Add custom analytics as needed
5. Expand to more teams beyond focus teams
6. Implement email notifications for reports (optional)

---

**Questions?** See backend/README.md for comprehensive documentation.
