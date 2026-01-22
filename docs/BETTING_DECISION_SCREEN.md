# Betting Decision Screen Implementation

## Overview

This implementation transforms the Team/Division view into a comprehensive betting decision support screen. It provides actionable insights for sports betting including:

- **Fixed ATS/O-U Statistics**: Real-time Against The Spread and Over/Under records
- **Value Panel**: Market lines with Expected Value (EV) and Kelly Criterion stake recommendations
- **Line Movement Visualization**: Historical odds movement tracking with sparklines
- **Enhanced Player Information**: Injury status and minutes trend analysis
- **Mobile-First Design**: Optimized for quick scanning and decision-making in under 15 seconds

## Architecture

### Frontend Components

#### 1. `ValuePanel.tsx`
Displays actionable betting opportunities with:
- Market odds (Spread, Total, Moneyline)
- Implied vs Model probabilities
- Edge calculations
- Expected Value (EV)
- Kelly Criterion stake recommendations
- Risk flags (LINE_STALE, NO_CLOSING_LINE, VOLATILITY_RISK)

**Props:**
```typescript
interface ValuePanelProps {
  data: ValuePanelData | null;
  loading?: boolean;
  onRefresh?: () => void;
}
```

#### 2. `BettingStatsCard.tsx`
Comprehensive ATS/O-U statistics display featuring:
- Season and Last 20 games records
- Win percentages with color coding
- Average margin vs spread/total
- Average total points
- Home/Away splits (optional)

**Props:**
```typescript
interface BettingStatsCardProps {
  data: BettingStatsData | null;
  loading?: boolean;
  onRefresh?: () => void;
  teamName?: string;
}
```

#### 3. `LineMovementMini.tsx`
Lightweight line movement visualization with:
- SVG sparkline charts
- Opening, Current, and Closing values
- Movement direction indicators
- Compact mobile-friendly design

**Props:**
```typescript
interface LineMovementMiniProps {
  data: LineMovementData[];
  loading?: boolean;
}
```

#### 4. `KeyPlayersCard.tsx`
Enhanced player information cards showing:
- Player name and position
- Injury status (OUT/Q/Probable/Active)
- Minutes last 5 games average
- Minutes trend (↑↓→)
- Injury notes

**Props:**
```typescript
interface KeyPlayersCardProps {
  players: PlayerStatus[];
  loading?: boolean;
}
```

#### 5. `NextGameBlock.tsx`
Next game information widget displaying:
- Matchup with team logos
- Date and time
- Home/Away designation
- Venue
- Time until game

**Props:**
```typescript
interface NextGameBlockProps {
  data: NextGameData | null;
  teamAbbrev: string;
  loading?: boolean;
}
```

### Backend Implementation

#### API Endpoints

##### 1. GET `/api/team/{team_abbrev}/betting-stats/detailed`
Returns comprehensive ATS and O/U statistics.

**Query Parameters:**
- `window` (optional): Number of recent games to analyze

**Response:**
```json
{
  "team": "CHI",
  "ats_season": {
    "wins": 28,
    "losses": 25,
    "pushes": 2,
    "percentage": 0.528,
    "avg_margin": 1.2
  },
  "ats_last_20": { ... },
  "ou_season": { ... },
  "ou_last_20": { ... },
  "avg_total_points": {
    "season": 223.5,
    "last_20": 225.8
  }
}
```

##### 2. GET `/api/team/{team_abbrev}/next-game`
Returns information about the team's next scheduled game.

**Response:**
```json
{
  "team": "CHI",
  "next_game": {
    "game_id": "abc123",
    "opponent": "LAL",
    "opponent_abbrev": "LAL",
    "commence_time": "2026-01-22T19:00:00Z",
    "is_home": true,
    "venue": "United Center",
    "status": "scheduled"
  }
}
```

##### 3. GET `/api/game/{game_id}/odds/current`
Returns current odds for all markets.

**Response:**
```json
{
  "game_id": "abc123",
  "odds": {
    "spread": [...],
    "totals": [...],
    "h2h": [...]
  }
}
```

##### 4. GET `/api/game/{game_id}/odds/movement`
Returns line movement history with sparkline data.

**Response:**
```json
{
  "game_id": "abc123",
  "movements": [
    {
      "market_type": "spread",
      "opening": { "timestamp": "...", "value": -2.5, "bookmaker": "DraftKings" },
      "current": { "timestamp": "...", "value": -3.5, "bookmaker": "DraftKings" },
      "movement": { "value_change": -1.0, "direction": "DOWN" },
      "history": [...]
    }
  ]
}
```

##### 5. GET `/api/team/{team_abbrev}/key-players`
Returns key players with status and trends.

**Query Parameters:**
- `limit` (default: 5): Number of players to return

**Response:**
```json
{
  "team": "CHI",
  "players": [
    {
      "player_name": "Zach LaVine",
      "team": "CHI",
      "status": "ACTIVE",
      "minutes_last_5_avg": 34.2,
      "minutes_trend": { "change": 2.1, "direction": "UP" }
    }
  ]
}
```

##### 6. GET `/api/team/{team_abbrev}/value`
Returns value betting recommendations with EV and Kelly calculations.

**Query Parameters:**
- `bankroll` (default: 1000): User's bankroll for stake calculations

**Response:**
```json
{
  "game_id": "abc123",
  "home_team": "CHI",
  "away_team": "LAL",
  "commence_time": "2026-01-22T19:00:00Z",
  "markets": {
    "spread": {
      "market_type": "spread",
      "line_value": -3.5,
      "odds": 1.91,
      "bookmaker": "DraftKings",
      "implied_prob": 0.524,
      "model_prob": 0.575,
      "edge": 5.1,
      "ev": 0.048,
      "ev_percentage": 4.8,
      "recommendation": "VALUE",
      "stake_recommendations": {
        "kelly_full": 50.00,
        "kelly_half": 25.00,
        "recommended": 25.00,
        "risk_level": "LOW"
      }
    }
  }
}
```

#### Helper Functions

Located in `backend/betting_endpoints.py`:

1. **`_compute_ats_ou_stats()`**: Calculates ATS and O/U records from game results
2. **`_get_next_game_info()`**: Fetches upcoming game details
3. **`_get_current_odds()`**: Gets latest odds by market type
4. **`_get_odds_movement()`**: Tracks historical line movement
5. **`_get_key_players_with_status()`**: Returns players with minutes trends
6. **`_calculate_ev_and_kelly()`**: Computes EV and Kelly Criterion

### Database Schema

#### New Tables

##### `odds_snapshots`
Stores historical odds for line movement tracking.

```sql
CREATE TABLE odds_snapshots (
  id uuid PRIMARY KEY,
  game_id text NOT NULL,
  bookmaker_key text NOT NULL,
  market_type text NOT NULL,
  team text,
  point numeric,
  price numeric NOT NULL,
  ts timestamptz DEFAULT now()
);
```

##### Extended `game_results`
Added fields for ATS/O-U tracking:

```sql
ALTER TABLE game_results ADD COLUMN
  closing_spread_home numeric,
  closing_spread_away numeric,
  closing_total numeric,
  ats_result_home text,
  ats_result_away text,
  ou_result text;
```

### Calculations

#### ATS (Against The Spread)
```
actual_margin = home_score - away_score
spread_diff = actual_margin - closing_spread

if |spread_diff| < 0.5: PUSH
elif spread_diff > 0: HOME COVERED
else: AWAY COVERED
```

#### O/U (Over/Under)
```
actual_total = home_score + away_score
total_diff = actual_total - closing_total

if |total_diff| < 0.5: PUSH
elif total_diff > 0: OVER
else: UNDER
```

#### Expected Value (EV)
```
EV = (model_prob × payout) - (1 - model_prob)
where payout = (odds - 1) × stake
```

#### Kelly Criterion
```
f = (bp - q) / b
where:
  b = odds - 1
  p = win probability
  q = 1 - p

Recommended: 0.5 × Kelly (Half Kelly)
Max stake: min(half_kelly, 3% of bankroll)
```

## UI Layout

The team detail panel follows this mobile-first layout:

1. **Header**: Team logo, name, conference/division
2. **Team KPI Cards**: Record, Win %, Off Rtg, Def Rtg (2×2 grid)
3. **Next Game Block**: Opponent, date/time, venue, countdown
4. **Betting Stats Card**: ATS and O/U records (season + last 20)
5. **Value Panel**: Market lines with EV and stake recommendations (if game exists)
6. **Line Movement**: Sparkline charts showing odds movement (if data available)
7. **Key Players**: Enhanced player cards with status and minutes trends

## Setup & Usage

### Prerequisites
- Python 3.9+
- Node.js 18+
- Supabase database with required tables

### Backend Setup

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Set environment variables:
```bash
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_key
```

3. Run database migrations:
```bash
# Apply migrations in supabase/migrations/
# 20260122020000_create_odds_snapshots.sql
# 20260122020100_add_game_results_betting_fields.sql
```

4. Populate initial data (optional):
```bash
python populate_betting_data.py
```

5. Start the backend:
```bash
uvicorn main:app --reload --port 8000
```

### Frontend Setup

1. Install dependencies:
```bash
npm install
```

2. Set environment variables:
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_anon_key
```

3. Start development server:
```bash
npm run dev
```

4. Build for production:
```bash
npm run build
```

## Testing

### Manual Testing

1. Navigate to the Teams view
2. Select a team to open the detail panel
3. Verify all components load:
   - Team KPI cards display correctly
   - Next game information (if scheduled)
   - Betting stats show ATS/O-U records
   - Value panel displays (if game exists with odds)
   - Line movement charts render
   - Key players list with status

### API Testing

Test endpoints using curl:

```bash
# Test betting stats
curl http://localhost:8000/api/team/CHI/betting-stats/detailed

# Test next game
curl http://localhost:8000/api/team/CHI/next-game

# Test key players
curl http://localhost:8000/api/team/CHI/key-players?limit=5

# Test value betting
curl http://localhost:8000/api/team/CHI/value?bankroll=1000
```

## Troubleshooting

### Common Issues

**"Brak danych" (No data) in Betting Stats**
- Ensure `game_results` table has completed games
- Run `populate_betting_data.py` to compute ATS/OU results
- Check that closing lines are populated

**No Value Panel Showing**
- Verify team has an upcoming game scheduled
- Check that `odds` table has current odds for the game
- Ensure odds data includes spread, totals, and h2h markets

**Line Movement Not Displaying**
- Confirm `odds_snapshots` table has historical data
- Run migration to create the table if missing
- Populate from existing odds using the utility script

**Player Status Shows "UNKNOWN"**
- Player injury data integration is pending
- Currently defaults to "ACTIVE" or "UNKNOWN"
- Future enhancement: integrate with injury API

## Future Enhancements

1. **Real-time Updates**: WebSocket integration for live odds updates
2. **Injury Data Integration**: Connect with official NBA injury reports API
3. **Model Probabilities**: Integrate actual predictive model instead of placeholder values
4. **Bet Tracking**: Save user bets and track performance
5. **Alerts**: Push notifications for value opportunities or line movements
6. **Historical Analysis**: Deeper dive into team trends and patterns
7. **Props Integration**: Add player prop bets to value panel
8. **Bankroll Management**: User-specific bankroll tracking and recommendations

## Performance Considerations

- All API calls are made in parallel where possible
- Components use loading states to prevent UI blocking
- Database queries use proper indexes for fast lookups
- Odds snapshots table may grow large; consider archival strategy
- Consider caching frequently accessed data (Redis)

## Security Notes

- All sensitive calculations happen server-side
- Never expose betting algorithms or models to frontend
- Validate all user inputs on backend
- Use Row Level Security (RLS) for user-specific data
- Rate limit API endpoints to prevent abuse

## Support

For issues or questions:
- Check the logs: `backend/logs/` and browser console
- Review API responses in Network tab
- Verify database table schemas match migrations
- Ensure environment variables are set correctly

---

**Version**: 1.0.0  
**Last Updated**: 2026-01-22  
**Author**: NBA Prawilne Development Team
