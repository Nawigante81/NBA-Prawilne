# 🏀 NBA Analysis & Betting Intelligence Platform - Backend

**Production-grade NBA analytics and betting intelligence system with automated data ingestion, quality gates, and Kelly Criterion optimization.**

## 🎯 Overview

This backend implements a complete betting intelligence platform focused on the Chicago Bulls, using only free data sources:

- **Basketball-Reference** (polite scraping)
- **NBA Stats API** (`nba_api` library - free)
- **The Odds API** (500 credits/month free tier)

## 🏗️ Architecture

### Provider-Based Design

```
backend/
├── providers/           # Data source integrations
│   ├── base.py         # BaseProvider interface
│   ├── nba_stats.py    # NBA Stats API (nba_api)
│   ├── odds_api.py     # The Odds API
│   └── basketball_reference.py  # Web scraping
├── services/           # Business logic
│   ├── betting_math.py      # EV, Kelly, CLV calculations
│   ├── budget_service.py    # API call tracking
│   ├── clv_service.py      # Closing line value
│   ├── quality_gates.py    # Data quality enforcement
│   ├── analytics_service.py # Team/player analytics
│   ├── sync_service.py     # Provider orchestration
│   └── report_service.py   # Daily reports
├── api/                # REST endpoints
│   ├── routes_teams.py
│   ├── routes_games.py
│   ├── routes_odds.py
│   ├── routes_value_board.py
│   ├── routes_picks.py
│   ├── routes_performance.py
│   ├── routes_reports.py
│   └── routes_uploads_stub.py
├── main_new.py         # FastAPI app with scheduler
├── models.py           # Pydantic models
├── settings.py         # Configuration
└── db.py              # Supabase client
```

## 🔧 Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-key

# The Odds API
ODDS_API_KEY=your-key-here
ODDS_MAX_CALLS_PER_DAY=10

# Betting parameters
BANKROLL_USD=1000
MAX_STAKE_PCT=0.03

# Quality gates
MIN_EV=0.02
MIN_EDGE_PROB=0.03
MIN_CONFIDENCE=0.55
```

### 3. Run Database Migrations

Apply migrations in Supabase SQL Editor:

```sql
-- Run all files in supabase/migrations/ in order
```

### 4. Start Server

```bash
# Development
uvicorn main_new:app --reload --port 8000

# Production
gunicorn main_new:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 📊 Core Features

### Rate Limiting & Budget Management

**Odds API (500 calls/month)**
- Max 10 calls per day
- Fetch games today + tomorrow only
- 3 bookmakers max (DraftKings, BetMGM, FanDuel)
- 12h baseline interval, 6h on game days
- Deduplication by content hash

**NBA Stats API**
- Concurrent limit: 2 requests
- Caching with TTL:
  - Scoreboard: 1 hour
  - Player lists: 7 days
  - Game logs: 6 hours

**Basketball-Reference**
- 3 second interval between requests
- Concurrency = 1
- Graceful fallback on 429

### Quality Gates System

All betting recommendations pass through quality gates:

**1. Data Availability**
- Odds within last 12h OR closing line available
- Spreads/totals must have line + price
- Team stats: minimum 5 recent games
- Player stats: minimum 3 games with minutes

**2. Sample Size & Recency**
- Team trends require N≥7 days or N≥5 games
- Stats must be < 24h old
- Odds must be < 12h old for today's games

**3. Market Quality**
- Reject extreme juice (> -160 American odds)
- Reject missing prices or points

**4. Confidence & EV**
- EV ≥ +2% (configurable)
- Edge ≥ +3 percentage points
- Confidence ≥ 0.55

**5. Parlay Quality**
- Max 5 legs
- Combined implied prob ≥ 0.20 for "low-risk"
- Each leg passes single-pick gates

**6. Injury/Uncertainty**
- Flag minutes volatility (stddev > 8)
- Block picks on high uncertainty

### Betting Mathematics

**Implemented Functions:**
- Odds conversion (American ↔ Decimal)
- Implied probability calculation
- Expected Value (EV)
- Kelly Criterion (full & fractional)
- CLV for spreads, totals, moneyline
- Vig removal
- Parlay odds calculation

All functions tested with 25+ unit tests (100% pass rate).

### Three Daily Reports

**7:50 AM - Previous Day Analysis**
- Results vs closing line (ATS, O/U)
- Top 3 trendy teams
- Bulls player breakdown
- Risks for next day

**8:00 AM - Morning Summary**
- Focus team one-liners
- 7-day trends
- Bulls form
- Betting leans
- Upload reminder

**11:00 AM - Game-Day Scouting**
- Today's slate (Chicago time)
- Matchup analysis
- Bulls game sheet
- **Quality-gated betting proposals:**
  - General parlay (3-5 legs)
  - Bulls parlay (2-5 legs)
  - Conservative alternatives
- Game day risks

Focus teams: Celtics, Wolves, Thunder, Magic, Cavs, Kings, Rockets, Knicks, **Bulls**

### Scheduler

APScheduler manages:
- **Startup sync**: Teams → Players → Games → Odds → Bulls roster
- **12h sync**: Refresh all data (budget-aware)
- **7:50 AM**: Previous day report
- **8:00 AM**: Morning summary
- **11:00 AM**: Game-day scouting

All times in America/Chicago timezone.

## 🛣️ API Endpoints

### Core
- `GET /health` - Health check
- `GET /api/status` - System status with provider health
- `GET /api/budget` - Today's API usage

### Data
- `GET /api/teams` - All NBA teams
- `GET /api/games/today` - Today's games

### Odds & Lines
- `GET /api/odds/{game_id}` - Current odds
- `GET /api/line-movement/{game_id}` - Line movement timeline

### Betting
- `GET /api/value-board/today` - Value bets (quality-gated)
- `GET /api/picks/today` - Recommended picks
- `POST /api/picks/settle` - Settle picks (admin)

### Performance
- `GET /api/performance` - ROI, CLV, Win Rate

### Reports
- `GET /api/reports/750am` - Previous day analysis
- `GET /api/reports/800am` - Morning summary
- `GET /api/reports/1100am` - Game-day scouting

### Uploads
- `POST /api/uploads` - Screenshot metadata (no OCR)

## 🔒 Authentication

**Basic Auth** for protected endpoints:
```
Authorization: Bearer <ADMIN_API_KEY>
```

**Exempt paths:**
- `/health`
- `/docs`
- `/openapi.json`
- `/redoc`

## 🧪 Testing

```bash
# Run betting math tests
pytest test_betting_math.py -v

# Run all tests
pytest -v

# With coverage
pytest --cov=services --cov-report=html
```

## 🐋 Docker

```bash
# Build
docker build -t nba-backend .

# Run
docker run -p 8000:8000 --env-file .env nba-backend
```

## 📈 Monitoring

**Logs:**
- Console output (structured JSON)
- File: `logs/main.log`

**Metrics tracked:**
- API call budgets (per provider per day)
- Pick performance (ROI, CLV, Win Rate)
- Quality gate pass/fail rates
- Provider health status

## 🔧 Configuration

All settings in `settings.py` can be overridden via environment variables:

```python
# Budget enforcement
ODDS_MAX_CALLS_PER_DAY = 10
ODDS_FETCH_INTERVAL_HOURS = 12

# Quality gates
MIN_EV = 0.02
MIN_EDGE_PROB = 0.03
MIN_CONFIDENCE = 0.55

# Rate limits
BASKETBALL_REF_REQUEST_INTERVAL_SECONDS = 3
NBA_API_MAX_CONCURRENT = 2
```

## 🚨 Error Handling

**API Budget Exceeded:**
- Logs warning
- Skips fetch
- Returns cached data if available

**Provider Errors:**
- Exponential backoff (3 retries)
- Graceful fallback
- Continues with other providers

**Quality Gate Failures:**
- Returns "NO BET" with reason codes
- Includes analysis without recommendations

## 📖 Documentation

- API docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI spec: `http://localhost:8000/openapi.json`

## 🎯 Production Checklist

- [ ] Configure `.env` with real API keys
- [ ] Run database migrations
- [ ] Set `ADMIN_API_KEY` to secure value
- [ ] Configure proper CORS origins
- [ ] Enable HTTPS
- [ ] Set up log aggregation
- [ ] Configure backup strategy
- [ ] Monitor API budgets
- [ ] Test all quality gates
- [ ] Verify scheduler runs correctly

## 📝 License

Educational purposes only. Not financial advice.

## 🙏 Attribution

- NBA Stats: `nba_api` library
- Odds: The Odds API (free tier)
- Historical data: Basketball-Reference (with respect)
