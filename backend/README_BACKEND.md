# NBA Betting Analytics Backend

Professional-grade backend API for NBA betting analytics with consensus odds, ATS/O-U tracking, value identification, and betting math calculations.

## Overview

This FastAPI-based backend provides:

- **Consensus Line Builder**: Median-based consensus with MAD outlier removal across multiple bookmakers
- **ATS/O-U Tracking**: Against The Spread and Over/Under statistics using closing lines
- **Value Identification**: EV and Kelly criterion calculations with quality gates
- **Closing Line Value**: Track CLV for pick analysis
- **API Budget Management**: Strict rate limiting for The Odds API free tier (10 calls/day)
- **NBA Stats Integration**: Real-time data from nba_api
- **Scheduled Sync Jobs**: Automated data updates with APScheduler

## Architecture

```
backend/
├── main.py                    # FastAPI app with lifespan management
├── settings.py                # Environment configuration
├── db.py                      # Database layer (asyncpg)
├── models.py                  # Pydantic models
├── api/                       # API route handlers
│   ├── routes_health.py
│   ├── routes_status.py
│   ├── routes_team.py
│   ├── routes_game.py
│   ├── routes_odds.py
│   ├── routes_value.py
│   ├── routes_picks.py
│   └── routes_performance.py
└── services/                  # Business logic
    ├── betting_math.py        # EV, Kelly, implied prob
    ├── odds_service.py        # Odds API + consensus builder
    ├── stats_service.py       # NBA API integration
    ├── betting_stats_service.py  # ATS/O-U calculations
    ├── clv_service.py         # Closing line value
    ├── value_service.py       # Value board generation
    ├── gating_service.py      # Quality gates
    └── sync_service.py        # Scheduled jobs
```

## Database Schema

See `supabase/migrations/20260122000000_betting_analytics_complete.sql` for complete schema.

### Key Tables

- **games**: Game schedule with nba_game_id
- **odds_snapshots**: Historical odds with deduplication
- **closing_lines**: Consensus closing lines per game/market/team
- **team_game_results**: Final scores
- **team_game_stats**: Advanced stats (pace, ratings, shooting)
- **player_game_stats**: Player performance
- **picks**: Bet recommendations with EV/Kelly
- **pick_results**: Settled bets with P&L
- **api_budget**: Daily API call tracking
- **api_cache**: Response caching

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL (via Supabase)
- The Odds API key (free tier: https://the-odds-api.com/)

### Installation

1. **Clone and navigate to backend**:
   ```bash
   cd backend
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. **Run migrations**:
   - Go to Supabase Dashboard → SQL Editor
   - Run `supabase/migrations/20260122000000_betting_analytics_complete.sql`

6. **Start server**:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Docker Setup

1. **Build image**:
   ```bash
   docker build -t nba-backend .
   ```

2. **Run container**:
   ```bash
   docker run -d \
     --name nba-backend \
     -p 8000:8000 \
     --env-file .env \
     nba-backend
   ```

3. **Docker Compose** (recommended):
   ```yaml
   version: '3.8'
   services:
     backend:
       build: ./backend
       ports:
         - "8000:8000"
       env_file:
         - ./backend/.env
       restart: unless-stopped
   ```

   Run with: `docker-compose up -d`

## API Endpoints

### Health & Status

- `GET /health` - Health check
- `GET /api/status` - System status with API budget

### Team Endpoints

- `GET /api/team/{abbrev}/betting-stats?window=20` - ATS/O-U statistics
- `GET /api/team/{abbrev}/next-game` - Next scheduled game
- `GET /api/team/{abbrev}/key-players` - Top players by minutes

### Game & Odds

- `GET /api/games/today` - Today's games
- `GET /api/game/{game_id}/odds/current` - Current odds
- `GET /api/game/{game_id}/odds/movement` - Historical odds movement
- `GET /api/game/{game_id}/clv` - Closing line value
- `GET /api/game/{game_id}/consensus?cutoff=now|closing` - Consensus lines

### Value & Picks

- `GET /api/value-board/today` - Value bets with quality gates applied
- `GET /api/picks/today` - Today's picks
- `POST /api/picks/settle` - Settle a pick with result
- `GET /api/performance` - Overall betting performance metrics

## Configuration

All settings in `settings.py` can be overridden via environment variables:

### Critical Settings

```bash
# API Budget (MUST configure for free tier)
ODDS_MAX_CALLS_PER_DAY=10
ODDS_BOOKMAKERS_ALLOWLIST=draftkings,fanduel,betmgm

# Quality Gates
MIN_EV=0.02                    # 2% minimum EV
MIN_EDGE_PROB=0.03             # 3% minimum edge
ODDS_STALE_HOURS=12            # Odds freshness
MIN_LIQUIDITY_SAMPLES=2        # Minimum bookmakers

# Sync Schedule
SYNC_NBA_STATS_INTERVAL_HOURS=2
SYNC_ODDS_INTERVAL_MINUTES=30
```

## Consensus Line Algorithm

The consensus builder uses **Median Absolute Deviation (MAD)** for robust outlier detection:

1. Collect latest snapshot per bookmaker before cutoff
2. Calculate median `m` of all points
3. Calculate MAD: `median(|x - m|)`
4. Remove outliers: `|x - m| > max(0.5, 3*MAD)`
5. Return median of remaining points
6. Select price from bookmaker closest to consensus point

This approach is robust to single-bookmaker errors while respecting true line movements.

## Betting Math

### Implied Probability
```python
implied_prob = 1.0 / decimal_odds
```

### Expected Value
```python
ev = (win_prob * (odds - 1)) - ((1 - win_prob) * 1)
```

### Kelly Criterion (Half Kelly)
```python
kelly = 0.5 * ((odds - 1) * win_prob - (1 - win_prob)) / (odds - 1)
```

## Quality Gates

All value bets must pass:

- ✅ **Odds Recency**: < 12 hours old
- ✅ **Stats Availability**: >= 5 recent games
- ✅ **Minimum EV**: >= 2%
- ✅ **Minimum Edge**: >= 3%
- ✅ **Game Data**: Valid commence_time

Warnings (don't block):
- ⚠️ **Low Liquidity**: < 2 bookmakers

## ATS/O-U Calculations

### Against The Spread (ATS)
```
ATS Win: team_points + spread > opponent_points
ATS Loss: team_points + spread < opponent_points
ATS Push: team_points + spread = opponent_points
```

### Over/Under (O/U)
```
Over: total_points > closing_total
Under: total_points < closing_total
Push: total_points = closing_total
```

Both use **consensus closing lines** (not single bookmaker).

## Monitoring

### Check API Budget
```bash
curl http://localhost:8000/api/status
```

### View Logs
```bash
# Local
tail -f logs/backend.log

# Docker
docker logs -f nba-backend
```

### Database Queries
```sql
-- API budget usage
SELECT * FROM api_budget WHERE day = CURRENT_DATE;

-- Recent odds snapshots
SELECT game_id, bookmaker_key, COUNT(*) 
FROM odds_snapshots 
WHERE ts > NOW() - INTERVAL '24 hours'
GROUP BY game_id, bookmaker_key;

-- Closing lines computed
SELECT COUNT(*) FROM closing_lines;
```

## Troubleshooting

### "Missing SUPABASE_SERVICE_KEY"
- Check `.env` has `SUPABASE_SERVICE_KEY` set
- Get from Supabase Dashboard → Settings → API → service_role key

### "ODDS_API_KEY not set"
- Sign up at https://the-odds-api.com/ (free tier)
- Add key to `.env`

### "Database pool initialization failed"
- Verify Supabase URL format
- Check service key permissions
- Ensure migrations have run

### "No odds data returned"
- Check API budget: `SELECT * FROM api_budget WHERE day = CURRENT_DATE`
- Verify bookmakers in allowlist exist for NBA
- Check logs for API errors

## Development

### Run Tests
```bash
pytest backend/tests/
```

### Lint Code
```bash
flake8 backend/
black backend/
```

### Type Check
```bash
mypy backend/
```

## Production Deployment

### Recommended Setup

1. **Use Docker** for consistent environment
2. **Set LOG_LEVEL=INFO** (not DEBUG)
3. **Configure CORS_ORIGINS** to your frontend domain
4. **Use reverse proxy** (nginx) for SSL/rate limiting
5. **Monitor API budget** daily
6. **Set up alerts** for sync job failures

### Environment Variables (Production)
```bash
LOG_LEVEL=INFO
CORS_ORIGINS=https://yourdomain.com
ODDS_MAX_CALLS_PER_DAY=10
SYNC_NBA_STATS_INTERVAL_HOURS=2
SYNC_ODDS_INTERVAL_MINUTES=30
TZ=America/Chicago
```

## License

See main repository LICENSE file.

## Support

For issues or questions, open a GitHub issue in the main repository.
