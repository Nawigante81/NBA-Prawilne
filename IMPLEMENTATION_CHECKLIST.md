# Implementation Verification Checklist

Use this checklist to verify the betting decision screen implementation.

## ✅ Pre-Deployment Checklist

### Database Setup
- [ ] Applied migration: `20260122020000_create_odds_snapshots.sql`
- [ ] Applied migration: `20260122020100_add_game_results_betting_fields.sql`
- [ ] Verified tables exist: `odds_snapshots`, `game_results` (with new fields)
- [ ] Run `populate_betting_data.py` to populate initial data
- [ ] Confirmed indexes created successfully

### Backend Verification
- [ ] File exists: `backend/betting_endpoints.py`
- [ ] File updated: `backend/main.py` (6 new endpoints)
- [ ] Python syntax check passes: `python3 -m py_compile betting_endpoints.py`
- [ ] Backend starts without errors: `uvicorn main:app --reload`
- [ ] Health check responds: `curl http://localhost:8000/health`

### API Endpoint Testing
Test each endpoint returns data (replace CHI with actual team):

- [ ] `curl http://localhost:8000/api/team/CHI/betting-stats/detailed`
  - Expected: ATS/OU season and last 20 stats
  
- [ ] `curl http://localhost:8000/api/team/CHI/next-game`
  - Expected: Next game info or null if none scheduled
  
- [ ] `curl http://localhost:8000/api/team/CHI/key-players?limit=5`
  - Expected: List of 5 players with minutes trends
  
- [ ] `curl http://localhost:8000/api/team/CHI/value?bankroll=1000`
  - Expected: Value panel data or null if no upcoming game
  
- [ ] `curl http://localhost:8000/api/game/{game_id}/odds/current`
  - Expected: Current odds by market type
  
- [ ] `curl http://localhost:8000/api/game/{game_id}/odds/movement`
  - Expected: Line movement history

### Frontend Files
- [ ] Component exists: `src/components/ValuePanel.tsx`
- [ ] Component exists: `src/components/BettingStatsCard.tsx`
- [ ] Component exists: `src/components/LineMovementMini.tsx`
- [ ] Component exists: `src/components/KeyPlayersCard.tsx`
- [ ] Component exists: `src/components/NextGameBlock.tsx`
- [ ] Updated: `src/components/AllTeams.tsx` (imports new components)
- [ ] Updated: `src/services/api.ts` (new endpoint methods)

### Frontend Build
- [ ] Install dependencies: `npm install`
- [ ] TypeScript compiles: `npm run typecheck` (or ignore React type issues if deps not installed)
- [ ] Build succeeds: `npm run build`
- [ ] Dev server starts: `npm run dev`

### UI Testing (Manual)
Navigate to Teams page and select a team:

- [ ] Team detail panel opens on right side
- [ ] Panel header shows team logo, name, conference/division
- [ ] Team KPI cards display (4 cards: Record, Win%, OffRtg, DefRtg)
- [ ] Next Game block appears (if team has upcoming game)
  - [ ] Shows opponent matchup
  - [ ] Shows date/time
  - [ ] Shows countdown
- [ ] Betting Stats Card displays
  - [ ] Shows ATS season record
  - [ ] Shows ATS last 20 record
  - [ ] Shows O/U season record
  - [ ] Shows O/U last 20 record
  - [ ] Shows average total points
  - [ ] Color coding works (green/yellow/red for percentages)
  - [ ] Refresh button works
- [ ] Value Panel displays (if game with odds exists)
  - [ ] Shows Spread market with line and odds
  - [ ] Shows Total market with line and odds
  - [ ] Shows Moneyline odds
  - [ ] Displays EV and edge calculations
  - [ ] Shows stake recommendations
  - [ ] VALUE or PASS badge appears
  - [ ] Risk flags show if applicable
- [ ] Line Movement displays (if historical data exists)
  - [ ] Sparkline chart renders
  - [ ] Shows opening, current values
  - [ ] Movement direction indicator correct
- [ ] Key Players Card displays
  - [ ] Shows top 5 players
  - [ ] Each has status badge
  - [ ] Shows minutes last 5 average
  - [ ] Trend arrow appears (↑↓→)

### Mobile Responsiveness
- [ ] Open browser DevTools, toggle device mode
- [ ] Test on mobile viewport (375px width)
  - [ ] Panel width appropriate (doesn't overflow)
  - [ ] All components stack vertically
  - [ ] Text is readable
  - [ ] Buttons are tappable
  - [ ] Grids collapse to single column

### Data Accuracy
Pick a team and verify:
- [ ] ATS record matches manual calculation
- [ ] O/U record matches manual calculation
- [ ] Win percentage calculated correctly
- [ ] Average margins are reasonable
- [ ] Next game time is correct
- [ ] Player minutes look accurate

### Error Handling
Test edge cases:
- [ ] Select team with no upcoming games
  - [ ] Shows "Brak zaplanowanych meczów" message
- [ ] Select team with no betting data
  - [ ] Shows "Brak danych - uruchom synchronizację" with refresh button
- [ ] Disconnect backend, click refresh
  - [ ] Handles error gracefully (doesn't crash)
- [ ] Check browser console for errors
  - [ ] No unhandled promise rejections
  - [ ] No React warnings

### Performance
- [ ] Panel opens within 1 second
- [ ] Data loads within 2-3 seconds
- [ ] No visible lag when clicking team
- [ ] Parallel API calls complete together
- [ ] Loading spinners show during fetch

### Documentation
- [ ] Read `docs/BETTING_DECISION_SCREEN.md` - comprehensive
- [ ] Read `BETTING_SCREEN_README.md` - quick start
- [ ] Code comments are clear
- [ ] API response examples match actual responses

## 🎯 Acceptance Criteria

All checkboxes above should be checked before considering the implementation complete.

### Critical Issues (Must Fix)
- Database migrations not applied
- Backend crashes on startup
- API endpoints return 500 errors
- UI crashes when opening team panel
- No data shows for any team

### Non-Critical Issues (Can Fix Later)
- Minor styling inconsistencies
- Placeholder model probabilities (need real model)
- Player injury status always "ACTIVE" (need injury API)
- Some TypeScript type warnings
- Missing data for some teams (need more scraping)

## 🔧 Quick Fixes

### If Backend Won't Start
```bash
cd backend
pip install -r requirements.txt
# Check for syntax errors
python3 -m py_compile betting_endpoints.py
python3 -m py_compile main.py
```

### If No Data Shows
```bash
cd backend
python populate_betting_data.py
# This populates odds_snapshots and computes ATS/OU
```

### If Frontend Won't Build
```bash
npm install
# If TypeScript errors about React types, may be transient
# Try: npm install --force
```

### If API Calls Fail
1. Check CORS settings in backend/main.py
2. Verify VITE_API_BASE_URL in .env
3. Check browser console Network tab for actual error
4. Ensure backend is running on port 8000

## 📊 Success Metrics

Implementation is successful when:
- ✅ All 6 API endpoints return valid data
- ✅ UI displays all 5 new components correctly
- ✅ Betting calculations (ATS/OU/EV/Kelly) are accurate
- ✅ Mobile viewport is fully functional
- ✅ No console errors or warnings
- ✅ User can make betting decision in <15 seconds

## 🚀 Deployment

Once all checks pass:
1. Merge PR to main branch
2. Deploy backend to production (with env vars)
3. Apply database migrations to production
4. Build and deploy frontend
5. Run smoke tests in production
6. Monitor error logs for first 24 hours

---

**Checklist Version**: 1.0  
**Last Updated**: 2026-01-22
