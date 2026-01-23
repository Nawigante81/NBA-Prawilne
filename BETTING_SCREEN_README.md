# Quick Start: Betting Decision Screen

## What Was Implemented

✅ **Fixed Missing ATS/O-U Data**

- Comprehensive betting statistics display
- Season and Last 20 games records
- Average margins and totals
- Home/Away splits

✅ **Value Panel**

- Market lines (Spread, Total, Moneyline)
- Expected Value (EV) calculations
- Kelly Criterion stake recommendations
- VALUE/PASS badges
- Risk flags

✅ **Line Movement Visualization**

- SVG sparkline charts
- Opening → Current → Closing lines
- Movement indicators (↑↓→)

✅ **Enhanced Player Cards**

- Injury status (OUT/Q/Probable/Active)
- Minutes last 5 games average
- Trend indicators

✅ **Next Game Widget**

- Matchup display
- Date/time with countdown
- Venue information

## File Structure

```text
src/components/
  ├── ValuePanel.tsx           # EV and Kelly stake recommendations
  ├── BettingStatsCard.tsx     # ATS/O-U statistics
  ├── LineMovementMini.tsx     # Line movement charts
  ├── KeyPlayersCard.tsx       # Player status and trends
  ├── NextGameBlock.tsx        # Upcoming game info
  └── AllTeams.tsx            # Integrated team detail panel

backend/
  ├── betting_endpoints.py     # Helper functions for calculations
  ├── main.py                 # API routes (6 new endpoints)
  └── populate_betting_data.py # Data population utility

supabase/migrations/
  ├── 20260122020000_create_odds_snapshots.sql
  └── 20260122020100_add_game_results_betting_fields.sql

docs/
  └── BETTING_DECISION_SCREEN.md  # Full documentation
```

## New API Endpoints

1. `GET /api/team/{abbrev}/betting-stats/detailed` - ATS/O-U stats
2. `GET /api/team/{abbrev}/next-game` - Next scheduled game
3. `GET /api/game/{game_id}/odds/current` - Current market odds
4. `GET /api/game/{game_id}/odds/movement` - Line movement history
5. `GET /api/team/{abbrev}/key-players` - Players with status/trends
6. `GET /api/team/{abbrev}/value` - Value betting recommendations

## How to Use

### 1. Apply Database Migrations

Run the SQL migrations in your Supabase dashboard or via CLI:

```bash
supabase migration up
```

### 2. Populate Initial Data (Optional)

If you have existing odds and game_results data:

```bash
cd backend
python populate_betting_data.py
```

This will:

- Copy odds to odds_snapshots for line movement tracking
- Calculate ATS/OU results for game_results

### 3. Start the Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 4. View in UI

1. Navigate to Teams page
2. Click on any team
3. The detail panel now shows:
   - Team KPIs
   - Next game info
   - Betting statistics
   - Value panel (if game with odds exists)
   - Line movement charts
   - Key players with status

## Key Features

### Betting Stats Card

- **Season Record**: Full season ATS and O/U
- **Last 20**: Recent form analysis

- **Color Coding**:
  - Green: >55% win rate
  - Yellow: 48-55%
  - Red: <48%

### Value Panel

- **EV Calculation**: `(model_prob × payout) - (1 - model_prob)`
- **Kelly Formula**: `f = (bp - q) / b`
- **Stake Recommendation**: Half Kelly, capped at 3% bankroll
- **Risk Levels**: LOW/MEDIUM/HIGH based on edge and stake size

### Line Movement

- **Sparkline Charts**: Visual representation of odds movement
- **Direction Indicators**: UP (↑), DOWN (↓), STABLE (→)
- **Snapshot Count**: Number of historical data points

### Player Cards

- **Status Badges**: Color-coded injury status
- **Minutes Trend**: Last 5 games average with change indicator
- **Position**: Player position if available

## Configuration

### Backend (backend/.env)

```env
SUPABASE_URL=your_url
SUPABASE_SERVICE_ROLE_KEY=your_key
BETTING_CACHE_TTL_HOURS=6
```

### Frontend (.env)

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=your_url
VITE_SUPABASE_ANON_KEY=your_key
```

## Calculations Reference

### ATS (Against The Spread)

```text
if |actual_margin - closing_spread| < 0.5: PUSH
elif actual_margin > closing_spread: COVERED
else: MISSED
```

### O/U (Over/Under)

```text
if |actual_total - closing_total| < 0.5: PUSH
elif actual_total > closing_total: OVER
else: UNDER
```

### Expected Value

```text
EV = win_prob × (odds - 1) - (1 - win_prob)
EV% = EV × 100
```

### Kelly Criterion

```text
Full Kelly = (bp - q) / b
Half Kelly = 0.5 × Full Kelly
Recommended = min(Half Kelly, 3% bankroll)
```

## Troubleshooting

**No data showing in Betting Stats?**

- Check if game_results table has data
- Run `populate_betting_data.py`
- Verify closing lines are populated

**Value Panel not appearing?**

- Team needs an upcoming scheduled game
- Game must have odds in the odds table
- Check API response in browser console

**Line movement empty?**

- odds_snapshots table needs data
- Run migration to create table
- Populate from existing odds

## Next Steps

1. **Test with Real Data**: Import actual game results and odds
2. **Integrate Model**: Replace placeholder probabilities with real predictions
3. **Add Injury API**: Connect to official NBA injury reports
4. **Bet Tracking**: Implement user bet history and performance tracking
5. **Alerts**: Add notifications for value opportunities

## Documentation

See `docs/BETTING_DECISION_SCREEN.md` for complete documentation including:

- Detailed API specifications
- All component props and interfaces
- Database schema details
- Advanced configuration
- Security considerations

---

**Implementation Date**: 2026-01-22  
**Stack**: Next.js 14, React, TypeScript, TailwindCSS, FastAPI, Supabase
