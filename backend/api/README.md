# API Routes Documentation

This document describes the API routes created in `/backend/api/`.

## Overview

The API is organized into 8 route modules, each handling a specific domain:

1. **Teams** - NBA team data
2. **Games** - Game schedules and matchups  
3. **Odds** - Betting odds and line movements
4. **Value Board** - Betting opportunities with quality gates
5. **Picks** - Betting recommendations and settlements
6. **Performance** - ROI and CLV tracking
7. **Reports** - Scheduled daily reports
8. **Uploads** - Bookmaker screenshot metadata

## Routes

### 1. Teams (`routes_teams.py`)

#### `GET /api/teams`
Get all NBA teams.

**Response:**
```json
[
  {
    "id": "uuid",
    "abbreviation": "CHI",
    "full_name": "Chicago Bulls",
    "name": "Bulls",
    "city": "Chicago"
  }
]
```

---

### 2. Games (`routes_games.py`)

#### `GET /api/games/today`
Get games scheduled for today (next 24 hours).

**Response:**
```json
[
  {
    "id": "game-uuid",
    "sport_key": "basketball_nba",
    "commence_time": "2024-01-22T19:00:00Z",
    "home_team": "CHI",
    "away_team": "LAL"
  }
]
```

---

### 3. Odds (`routes_odds.py`)

#### `GET /api/odds/{game_id}`
Get current odds for a specific game.

**Query Parameters:**
- `market_type` (optional): Filter by market type (`h2h`, `spreads`, `totals`)

**Response:**
```json
{
  "game_id": "game-uuid",
  "ts": "2024-01-22T18:00:00Z",
  "odds": [
    {
      "bookmaker_key": "draftkings",
      "market_type": "h2h",
      "team": "CHI",
      "price": -110,
      "point": null
    }
  ]
}
```

#### `GET /api/odds/line-movement/{game_id}`
Get line movement timeline for a game.

**Query Parameters:**
- `market_type` (required): Market type (`h2h`, `spreads`, `totals`)
- `bookmaker_key` (optional): Filter by bookmaker
- `hours_back` (optional): Hours of history (1-168, default: 24)

**Response:**
```json
{
  "game_id": "game-uuid",
  "market_type": "spreads",
  "timeline_by_bookmaker": {
    "draftkings": [
      {
        "ts": "2024-01-22T12:00:00Z",
        "point": -7.5,
        "price": -110
      }
    ]
  }
}
```

---

### 4. Value Board (`routes_value_board.py`)

#### `GET /api/value-board/today`
Get value bets for today that pass quality gates.

**Query Parameters:**
- `min_ev` (optional): Minimum expected value (default: 0.03)
- `min_edge` (optional): Minimum edge (default: 0.02)
- `market_types` (optional): Comma-separated market types

**Response:**
```json
{
  "value_bets": [
    {
      "game_id": "game-uuid",
      "game": {
        "home_team": "CHI",
        "away_team": "LAL",
        "commence_time": "2024-01-22T19:00:00Z"
      },
      "market_type": "spreads",
      "bookmaker": "draftkings",
      "team": "CHI",
      "point": -7.5,
      "odds": -110,
      "implied_prob": 0.5238,
      "estimated_prob": 0.5738,
      "edge": 0.05,
      "ev": 0.0262,
      "quality_gate_passed": true
    }
  ],
  "count": 1
}
```

---

### 5. Picks (`routes_picks.py`)

#### `GET /api/picks/today`
Get betting picks for today's games.

**Response:**
```json
[
  {
    "id": "pick-uuid",
    "game_id": "game-uuid",
    "market_type": "spreads",
    "selection": "CHI",
    "bookmaker": "draftkings",
    "odds": -110,
    "point": -7.5,
    "stake_units": 1.5,
    "stake_usd": 15.00,
    "edge": 0.05,
    "ev": 0.0262,
    "confidence": 0.65,
    "status": "pending"
  }
]
```

#### `POST /api/picks/settle`
Settle picks after games complete (admin only).

**Request:**
```json
{
  "pick_ids": ["pick-uuid-1", "pick-uuid-2"],
  "admin_key": "your-admin-key"
}
```

**Response:**
```json
{
  "settled_count": 2,
  "picks": [
    {
      "pick_id": "pick-uuid-1",
      "status": "won",
      "clv": 0.015,
      "closing_odds": -115,
      "closing_point": -8.0
    }
  ]
}
```

---

### 6. Performance (`routes_performance.py`)

#### `GET /api/performance`
Get ROI and CLV performance summary.

**Query Parameters:**
- `days_back` (optional): Days of history (1-365, default: 30)
- `market_type` (optional): Filter by market type

**Response:**
```json
{
  "period": {
    "start_date": "2023-12-23T00:00:00Z",
    "end_date": "2024-01-22T00:00:00Z",
    "days": 30
  },
  "summary": {
    "total_picks": 45,
    "total_stake_usd": 450.00,
    "total_profit_usd": 23.50,
    "roi_percent": 5.22,
    "win_rate_percent": 54.5,
    "average_clv": 0.012,
    "average_edge": 0.035,
    "average_ev": 0.028
  },
  "status_breakdown": {
    "won": 24,
    "lost": 20,
    "push": 1,
    "pending": 0
  },
  "market_breakdown": {
    "h2h": {"picks": 15, "profit": 8.50, "roi": 5.67},
    "spreads": {"picks": 20, "profit": 12.00, "roi": 6.00},
    "totals": {"picks": 10, "profit": 3.00, "roi": 3.00}
  }
}
```

---

### 7. Reports (`routes_reports.py`)

#### `GET /api/reports/750am`
Get or generate the 7:50 AM report.

**Query Parameters:**
- `report_date` (optional): Date in YYYY-MM-DD format (default: today)

**Response:**
```json
{
  "report": {
    "overnight_movements": [...],
    "injury_updates": [...],
    "value_opportunities": [...]
  },
  "generated_at": "2024-01-22T07:50:00Z",
  "cached": false
}
```

#### `GET /api/reports/800am`
Get or generate the 8:00 AM report (full day analysis).

#### `GET /api/reports/1100am`
Get or generate the 11:00 AM report (final pre-game update).

---

### 8. Uploads (`routes_uploads_stub.py`)

#### `POST /api/uploads`
Upload bookmaker screenshot metadata.

**Form Data:**
- `file` (required): Image file (PNG, JPEG, WebP, max 10MB)
- `bookmaker` (optional): Bookmaker name
- `notes` (optional): Notes about the upload

**Response:**
```json
{
  "success": true,
  "upload_id": "upload-uuid",
  "filename": "bet_slip_20240122.png",
  "bookmaker": "draftkings",
  "uploaded_at": "2024-01-22T10:30:00Z"
}
```

---

## Integration

To use these routes in your FastAPI app, import and include them:

```python
from fastapi import FastAPI
from api import (
    teams_router,
    games_router,
    odds_router,
    value_board_router,
    picks_router,
    performance_router,
    reports_router,
    uploads_router
)

app = FastAPI()

# Include all routers
app.include_router(teams_router)
app.include_router(games_router)
app.include_router(odds_router)
app.include_router(value_board_router)
app.include_router(picks_router)
app.include_router(performance_router)
app.include_router(reports_router)
app.include_router(uploads_router)
```

## Quality Gates

The following routes apply quality gate checks:
- `/api/value-board/today` - Validates odds availability, EV, and edge thresholds
- `/api/picks/today` - Re-validates picks against current quality gates

Quality gate configuration is in `backend/settings.py`:
- `min_ev`: Minimum expected value (default: 0.02)
- `min_edge_prob`: Minimum edge probability (default: 0.03)
- `min_confidence`: Minimum model confidence (default: 0.55)
- `odds_max_snapshot_age_hours`: Maximum age of odds data (default: 12)

## Error Handling

All routes include proper error handling:
- `400`: Bad request (invalid parameters)
- `403`: Forbidden (invalid admin key)
- `404`: Not found (resource doesn't exist)
- `500`: Internal server error (logged with details)

## Security Notes

1. **Admin Endpoints**: The `/api/picks/settle` endpoint requires an admin key. Set `ADMIN_API_KEY` in your `.env` file.

2. **File Uploads**: The uploads endpoint validates file types and sizes. In production, implement proper cloud storage integration.

3. **Rate Limiting**: Consider adding rate limiting middleware for production deployments.

4. **CORS**: Configure CORS properly in `main.py` for frontend access.

## Testing

To test the routes:

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Run the FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Access the interactive API docs
# Open http://localhost:8000/docs
```

## Dependencies

These routes require the following services:
- `db.py`: Database connection (Supabase)
- `services/quality_gates.py`: Quality gate validation
- `services/betting_math.py`: Betting calculations
- `services/clv_service.py`: CLV tracking
- `services/analytics_service.py`: Analytics (future)
- `reports.py`: Report generation
- `models.py`: Pydantic models
- `settings.py`: Configuration

## Future Enhancements

Potential improvements:
- Add pagination to list endpoints
- Implement WebSocket support for real-time odds updates
- Add filtering and sorting to performance metrics
- Implement caching layer (Redis) for frequently accessed data
- Add authentication/authorization middleware
- Expand upload endpoint to handle actual file storage (S3, Supabase Storage)
