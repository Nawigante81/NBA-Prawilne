# 🎯 UX Audit - NBA Betting Analytics Platform
## Comprehensive Audit & Improvement Plan

**Data Audytu**: 2026-01-22  
**Wersja**: 1.0  
**Typ aplikacji**: NBA Betting Decision Support System  

---

## 📊 Executive Summary

Aplikacja dostarcza podstawowe dane analityczne NBA i kursy bukmacherskie, ale **nie jest jeszcze narzędziem do podejmowania decyzji o zakładach**. Jest to obecnie bardziej platforma informacyjna niż system wspierający decyzje bettingowe.

**Ogólna ocena**: 4.5/10 jako betting decision tool

### Kluczowe problemy:
1. ❌ Brak wyraźnego Expected Value (EV) i "edge" w punktach/procentach
2. ❌ Użytkownik nie może podjąć decyzji w <15 sekund
3. ❌ Brak historii typów i trackingu ROI/yield
4. ❌ Niewystarczające wskaźniki confidence z uzasadnieniem
5. ❌ Brak zarządzania banrollem i exposure
6. ⚠️  Limited injury impact indicators
7. ⚠️  No line movement tracking
8. ⚠️  No value bet filtering and ranking

---

## 🔍 Detailed Assessment by Area

### 1. Przewaga w obstawianiu (Edge) - **Ocena: 3/10**

#### ❌ Brakuje:
- **Expected Value (EV)** w każdym typie - obecnie pokazane tylko "edge" jako liczba 0-1
- **Implied probability** vs **fair odds** comparison
- **Spread/Total analysis** - brak porównania modelu vs linia
- **Value bet indicator** - brak jasnego "PLAY" / "NO PLAY"
- Edge w punktach dla spread bets

#### ✅ Obecne:
- Podstawowy "edge" pokazany jako decimal (np. 0.05 = 5%)
- Consensus probability
- Best price comparison across books

#### 🎯 Propozycje naprawy (P0 - Critical):
```typescript
// Component: ValueIndicator.tsx
interface ValueMetrics {
  ev: number;              // Expected Value in currency ($2.50)
  evPercentage: number;    // EV as percentage (5.2%)
  impliedProb: number;     // From bookmaker odds (52.4%)
  fairProb: number;        // From model (58.1%)
  edge: number;            // fairProb - impliedProb (5.7%)
  edgePoints?: number;     // For spreads (2.3 pts)
  recommendation: 'STRONG_PLAY' | 'PLAY' | 'LEAN' | 'NO_PLAY';
}
```

**SQL Schema Addition:**
```sql
CREATE TABLE IF NOT EXISTS bet_values (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  game_id TEXT NOT NULL,
  market_type TEXT NOT NULL, -- 'h2h', 'spread', 'total'
  selection TEXT NOT NULL,
  bookmaker_odds DECIMAL(10,3),
  implied_probability DECIMAL(5,4),
  model_probability DECIMAL(5,4),
  edge_percentage DECIMAL(5,4),
  expected_value DECIMAL(10,2),
  recommendation TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

### 2. Warstwa decyzyjna (Decision Support) - **Ocena: 4/10**

#### ❌ Brakuje:
- **Quick decision indicators** - użytkownik musi czytać całą kartę
- **Clear CTA buttons** ("Place Bet", "Track", "Skip")
- **Ranking typów** po confidence/EV
- **Explainability** - dlaczego model to rekomenduje?
- **Sortable columns** - nie można sortować po edge/EV
- **Sticky filters** - filtry nie są persystentne

#### ✅ Obecne:
- Category filters (All, Featured, Value, General)
- Basic layout with picks
- Bookmaker information

#### 🎯 Propozycje naprawy (P0 - Critical):

**1. Quick Decision Card Design:**
```tsx
<div className="value-bet-card border-l-4 border-green-500">
  {/* Header: Decision in <3 seconds */}
  <div className="flex justify-between items-start">
    <div>
      <h4 className="text-xl font-bold">CHI Bulls ML</h4>
      <p className="text-sm text-gray-400">vs LAL • 7:00 PM CT</p>
    </div>
    <div className="text-right">
      <div className="text-2xl font-bold text-green-400">+5.7%</div>
      <div className="text-xs">STRONG PLAY</div>
    </div>
  </div>

  {/* Key Metrics - Scannable */}
  <div className="grid grid-cols-4 gap-2 mt-3">
    <MetricBox label="EV" value="$2.85" highlight />
    <MetricBox label="Edge" value="5.7%" />
    <MetricBox label="Odds" value="+145" />
    <MetricBox label="Book" value="DraftKings" />
  </div>

  {/* Confidence & Reason */}
  <div className="mt-3 bg-gray-800/50 rounded p-2">
    <div className="flex items-center gap-2">
      <div className="text-yellow-400">⭐⭐⭐⭐</div>
      <span className="text-sm">85% Confidence</span>
    </div>
    <p className="text-xs text-gray-400 mt-1">
      Bulls 7-3 ATS at home. LAL on B2B with travel. Injury advantage.
    </p>
  </div>

  {/* CTA */}
  <div className="flex gap-2 mt-3">
    <button className="flex-1 bg-green-600 hover:bg-green-700 py-2 rounded font-semibold">
      Place Bet
    </button>
    <button className="px-4 bg-gray-700 hover:bg-gray-600 rounded">
      Track
    </button>
  </div>
</div>
```

**2. Add Sortable Table Component:**
```tsx
// components/SortableValueTable.tsx
const columns = [
  { key: 'game', label: 'Game', sortable: false },
  { key: 'edge', label: 'Edge %', sortable: true, default: 'desc' },
  { key: 'ev', label: 'EV', sortable: true },
  { key: 'confidence', label: 'Confidence', sortable: true },
  { key: 'odds', label: 'Odds', sortable: false },
];
```

---

### 3. Zarządzanie ryzykiem i stawkowanie - **Ocena: 5/10**

#### ✅ Obecne:
- Kelly calculator (Quarter Kelly)
- Bankroll input field
- Basic stake calculation

#### ❌ Brakuje:
- **Max exposure daily/per game**
- **Bankroll tracking over time**
- **Recommended stake per bet** (automated)
- **Risk indicators** (high variance bets)
- **Unit sizing based on confidence**

#### 🎯 Propozycje naprawy (P1 - Important):

**New Component: RiskManagementPanel.tsx**
```tsx
interface BankrollSettings {
  total_bankroll: number;
  current_balance: number;
  daily_exposure_limit: number;  // % of bankroll
  max_bet_size: number;          // % of bankroll
  current_exposure: number;       // $ currently at risk
  recommended_stake_per_bet: number;
}

// Risk Levels
const getRiskLevel = (stake: number, bankroll: number, confidence: number) => {
  const pctOfBankroll = (stake / bankroll) * 100;
  if (pctOfBankroll > 5 && confidence < 70) return 'HIGH';
  if (pctOfBankroll > 3) return 'MEDIUM';
  return 'LOW';
};
```

**SQL Schema:**
```sql
CREATE TABLE IF NOT EXISTS user_bankroll (
  user_id UUID PRIMARY KEY,
  total_bankroll DECIMAL(10,2) NOT NULL,
  current_balance DECIMAL(10,2) NOT NULL,
  daily_limit_pct DECIMAL(5,2) DEFAULT 10.00,
  max_bet_pct DECIMAL(5,2) DEFAULT 5.00,
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS active_exposure (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_bankroll(user_id),
  game_id TEXT NOT NULL,
  stake DECIMAL(10,2) NOT NULL,
  status TEXT DEFAULT 'pending', -- pending, won, lost
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

### 4. Wiarygodność i mierzenie skuteczności - **Ocena: 2/10** ❌

#### ❌ Krytyczne braki:
- **No bet history tracking**
- **No ROI/yield display**
- **No closing line value (CLV) tracking**
- **No performance by market** (spread/total/ML)
- **No historical picks archive**

#### 🎯 Propozycje naprawy (P0 - Critical):

**New Component: PerformanceTracker.tsx**
```tsx
interface PerformanceMetrics {
  total_bets: number;
  win_rate: number;          // % wins
  roi: number;               // Return on Investment %
  yield: number;             // Net profit / total risked
  total_wagered: number;
  total_profit: number;
  avg_odds: number;
  clv: number;               // Closing Line Value %
  
  // By market
  by_market: {
    moneyline: { bets: number; roi: number; win_rate: number };
    spread: { bets: number; roi: number; win_rate: number };
    total: { bets: number; roi: number; win_rate: number };
  };
  
  // Recent form
  last_10: { wins: number; losses: number; roi: number };
  last_30: { wins: number; losses: number; roi: number };
}
```

**SQL Schema:**
```sql
CREATE TABLE IF NOT EXISTS bet_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID,
  game_id TEXT NOT NULL,
  market_type TEXT NOT NULL,
  selection TEXT NOT NULL,
  odds DECIMAL(10,3) NOT NULL,
  stake DECIMAL(10,2) NOT NULL,
  placed_at TIMESTAMP DEFAULT NOW(),
  
  -- Result tracking
  result TEXT, -- 'won', 'lost', 'push', 'pending'
  profit DECIMAL(10,2),
  settled_at TIMESTAMP,
  
  -- CLV tracking
  closing_odds DECIMAL(10,3),
  clv_percentage DECIMAL(5,4),
  
  -- Model tracking
  model_edge DECIMAL(5,4),
  model_confidence DECIMAL(5,4),
  
  CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES user_bankroll(user_id)
);

CREATE INDEX idx_bet_history_user ON bet_history(user_id);
CREATE INDEX idx_bet_history_result ON bet_history(result);
CREATE INDEX idx_bet_history_market ON bet_history(market_type);
```

**API Endpoints:**
```python
# backend/main.py

@app.get("/api/performance/summary")
async def get_performance_summary(user_id: str):
    """Get overall betting performance"""
    # Calculate ROI, yield, CLV
    pass

@app.get("/api/performance/by-market")
async def get_performance_by_market(user_id: str):
    """Performance breakdown by market type"""
    pass

@app.get("/api/bet-history")
async def get_bet_history(user_id: str, limit: int = 50):
    """Recent bet history with results"""
    pass
```

---

### 5. Dane NBA wpływające na zakłady - **Ocena: 6/10**

#### ✅ Obecne:
- Player stats and prop bet analyzer
- Form tracker
- Matchup analyzer
- Injury impact analyzer (basic)

#### ❌ Brakuje:
- **Real-time injury updates** with impact indicators
- **B2B, 3-in-4, rest disadvantage** indicators
- **Travel distance** impact
- **Lineup/rotation changes** notifications
- **Projected minutes** for player props

#### 🎯 Propozycje naprawy (P1 - Important):

**Enhanced Game Context Component:**
```tsx
interface GameContext {
  home_team: string;
  away_team: string;
  
  // Rest & Fatigue
  home_rest_days: number;
  away_rest_days: number;
  home_b2b: boolean;
  away_b2b: boolean;
  home_3in4: boolean;
  away_3in4: boolean;
  
  // Travel
  away_travel_miles: number;
  away_timezone_change: number;
  
  // Injuries
  injuries: Array<{
    player: string;
    team: string;
    status: 'OUT' | 'DOUBTFUL' | 'QUESTIONABLE' | 'PROBABLE';
    impact_points: number;  // Estimated point swing
    projected_replacement: string;
  }>;
  
  // Rotation
  rotation_changes: Array<{
    player: string;
    change: string;
    impact: string;
  }>;
}
```

**New Component: GameContextCard.tsx**
```tsx
<div className="game-context-card">
  <h4>Game Context & Edges</h4>
  
  {/* Fatigue Indicators */}
  <div className="context-row">
    <span>Rest Advantage:</span>
    <span className="text-green-400">CHI +2 days</span>
  </div>
  
  {/* Injuries */}
  <div className="context-row">
    <span>Key Injury:</span>
    <div>
      <span className="text-red-400">LeBron James OUT</span>
      <span className="text-xs text-gray-400">(-5.2 pts impact)</span>
    </div>
  </div>
  
  {/* Travel */}
  <div className="context-row">
    <span>Travel:</span>
    <span>LAL 1,745 mi (2 timezone)</span>
  </div>
</div>
```

---

### 6. UX/UI Audit - **Ocena: 5/10**

#### ✅ Dobre aspekty:
- Dark mode by default
- Responsive layout
- Clean glassmorphism design
- Logical sidebar navigation

#### ❌ Problemy:
- **Mobile optimization** - tabele trudne do użycia na telefonie
- **No sticky headers** in tables
- **No advanced filters** (edge %, confidence, market type)
- **Information hierarchy** - nie ułożone w kolejności decyzyjnej
- **No pinning** favorite bets
- **Long scroll** - zbyt dużo scrollowania do kluczowych danych

#### 🎯 Propozycje naprawy (P1 - Important):

**1. Mobile-First Value Board:**
```tsx
// Mobile: Card view, Desktop: Table view
<div className="value-board">
  {/* Mobile Filters - Horizontal Scroll */}
  <div className="mobile-filters flex overflow-x-auto gap-2">
    <FilterChip label="Edge >5%" active />
    <FilterChip label="High Conf" />
    <FilterChip label="ML Only" />
    <FilterChip label="Live" />
  </div>
  
  {/* Responsive Grid */}
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    {valueBets.map(bet => (
      <ValueBetCard key={bet.id} {...bet} />
    ))}
  </div>
</div>
```

**2. Advanced Filter Panel:**
```tsx
interface FilterState {
  minEdge: number;           // 0-20%
  minConfidence: number;     // 0-100%
  markets: ('h2h' | 'spread' | 'total')[];
  bookmakers: string[];
  injuryFlag: boolean;       // Games with key injuries
  restAdvantage: boolean;    // Teams with rest edge
  liveOnly: boolean;
  valueBetsOnly: boolean;    // Edge > 0
}
```

**3. Sticky Header for Tables:**
```css
.value-table {
  position: relative;
}

.value-table thead {
  position: sticky;
  top: 0;
  z-index: 10;
  background: rgba(17, 24, 39, 0.95);
  backdrop-filter: blur(10px);
}
```

---

### 7. Moduły, które powinny istnieć - **Ocena: 3/10**

#### ❌ Brakujące moduły:

**A. Value Board (Dzisiejsze mecze)** - ❌ Brak
```tsx
// components/ValueBoard.tsx
// Shows today's games with clear value indicators
// Sorted by EV, filterable, quick actions
```

**B. Line Movement Tracker** - ❌ Brak
```tsx
// components/LineMovement.tsx
// Opening line vs current line vs model line
// Sharp money indicators
// Steam moves detection
```

**C. Alerts System** - ❌ Brak
```tsx
// components/AlertsPanel.tsx
// New injury → value change
// Line moves > X%
// Model confidence > Y%
```

**D. Props Board** - ⚠️ Partial (PropBetAnalyzer exists but not integrated)
```tsx
// components/PropsBoard.tsx
// Player props with projected minutes
// Over/Under recommendations
// Correlation indicators
```

**E. Arbitrage/Middles** - ❌ Brak
```tsx
// components/ArbitrageBoard.tsx
// Risk-free profit opportunities
// Middle opportunities on totals/spreads
```

#### 🎯 Propozycje naprawy (P0-P1):

**Priority 1: Value Board Component**
```tsx
// src/components/ValueBoard.tsx
export const ValueBoard: React.FC = () => {
  const [todaysGames, setTodaysGames] = useState<Game[]>([]);
  const [filters, setFilters] = useState<FilterState>({});
  
  // Fetch today's games with value calculations
  useEffect(() => {
    api.betting.getTodaysValue().then(setTodaysGames);
  }, []);
  
  return (
    <div className="value-board">
      <div className="header">
        <h2>Today's Value Opportunities</h2>
        <div className="quick-stats">
          <span>{todaysGames.length} games</span>
          <span className="text-green-400">
            {todaysGames.filter(g => g.hasValue).length} value bets
          </span>
        </div>
      </div>
      
      <FilterBar filters={filters} onChange={setFilters} />
      
      <div className="games-grid">
        {todaysGames.map(game => (
          <ValueGameCard key={game.id} game={game} />
        ))}
      </div>
    </div>
  );
};
```

**Priority 2: Line Movement Component**
```tsx
// src/components/LineMovement.tsx
export const LineMovement: React.FC<{ gameId: string }> = ({ gameId }) => {
  const [lineHistory, setLineHistory] = useState<LineSnapshot[]>([]);
  
  return (
    <div className="line-movement">
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={lineHistory}>
          <Line type="monotone" dataKey="spread" stroke="#10b981" name="Spread" />
          <Line type="monotone" dataKey="total" stroke="#3b82f6" name="Total" />
          <Tooltip />
        </LineChart>
      </ResponsiveContainer>
      
      <div className="line-stats">
        <StatCard label="Opening" value={lineHistory[0]?.spread} />
        <StatCard label="Current" value={lineHistory[lineHistory.length - 1]?.spread} />
        <StatCard label="Movement" value={calculateMovement(lineHistory)} />
      </div>
    </div>
  );
};
```

---

### 8. Rekomendacje implementacyjne - **Architecture**

#### A. Struktura widoków (Routes/Pages)

```typescript
// src/App.tsx - Enhanced sections
type Section = 
  | 'dashboard'      // Overview + today's value
  | 'value-board'    // Main betting dashboard 🆕
  | 'props'          // Player props 🆕
  | 'line-movement'  // Line tracking 🆕
  | 'performance'    // Bet history & ROI 🆕
  | 'alerts'         // Notifications 🆕
  | 'teams'
  | 'players'
  | 'analytics'
  | 'settings';      // Bankroll management 🆕
```

#### B. Komponenty UI (Cards/Tables/Filters)

**New Components Needed:**
1. `ValueBetCard.tsx` - Quick decision card
2. `ValueBoard.tsx` - Main value dashboard
3. `PerformanceTracker.tsx` - ROI/yield display
4. `LineMovementChart.tsx` - Line history
5. `AlertsPanel.tsx` - Notifications
6. `PropsBoard.tsx` - Player props dashboard
7. `FilterBar.tsx` - Advanced filtering
8. `BankrollManager.tsx` - Risk management
9. `GameContextCard.tsx` - Fatigue/injury context
10. `ConfidenceMeter.tsx` - Visual confidence indicator

#### C. Model danych (Supabase/Postgres)

**New Tables:**
```sql
-- Value tracking
CREATE TABLE value_bets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  game_id TEXT NOT NULL,
  market_type TEXT NOT NULL,
  selection TEXT NOT NULL,
  odds DECIMAL(10,3),
  implied_prob DECIMAL(5,4),
  model_prob DECIMAL(5,4),
  edge DECIMAL(5,4),
  ev DECIMAL(10,2),
  confidence DECIMAL(5,4),
  recommendation TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Bet history
CREATE TABLE bet_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID,
  game_id TEXT NOT NULL,
  market_type TEXT NOT NULL,
  selection TEXT NOT NULL,
  odds DECIMAL(10,3) NOT NULL,
  stake DECIMAL(10,2) NOT NULL,
  result TEXT, -- 'won', 'lost', 'push', 'pending'
  profit DECIMAL(10,2),
  placed_at TIMESTAMP DEFAULT NOW(),
  settled_at TIMESTAMP,
  closing_odds DECIMAL(10,3),
  clv_percentage DECIMAL(5,4)
);

-- Line movements
CREATE TABLE line_movements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  game_id TEXT NOT NULL,
  bookmaker TEXT NOT NULL,
  market_type TEXT NOT NULL,
  line_value DECIMAL(10,3),
  odds DECIMAL(10,3),
  timestamp TIMESTAMP DEFAULT NOW()
);

-- Bankroll management
CREATE TABLE user_bankroll (
  user_id UUID PRIMARY KEY,
  total_bankroll DECIMAL(10,2) NOT NULL,
  current_balance DECIMAL(10,2) NOT NULL,
  daily_limit_pct DECIMAL(5,2) DEFAULT 10.00,
  max_bet_pct DECIMAL(5,2) DEFAULT 5.00,
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Alerts
CREATE TABLE user_alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID,
  alert_type TEXT NOT NULL, -- 'injury', 'line_move', 'value'
  game_id TEXT,
  message TEXT NOT NULL,
  is_read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Game context
CREATE TABLE game_context (
  game_id TEXT PRIMARY KEY,
  home_team TEXT NOT NULL,
  away_team TEXT NOT NULL,
  home_rest_days INTEGER,
  away_rest_days INTEGER,
  home_b2b BOOLEAN DEFAULT FALSE,
  away_b2b BOOLEAN DEFAULT FALSE,
  away_travel_miles INTEGER,
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Injury impact
CREATE TABLE injury_impact (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  game_id TEXT NOT NULL,
  player_name TEXT NOT NULL,
  team TEXT NOT NULL,
  status TEXT NOT NULL,
  impact_points DECIMAL(5,2),
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### D. Kluczowe endpointy API

```python
# backend/main.py - New endpoints

@app.get("/api/value/today")
async def get_todays_value_bets(
    min_edge: float = 0.03,
    min_confidence: float = 0.65,
    markets: List[str] = Query(default=["h2h", "spread", "total"])
):
    """Get today's games with value bet opportunities"""
    # Calculate EV, edge, confidence for all today's games
    # Filter by criteria
    # Return sorted by EV descending
    pass

@app.get("/api/value/game/{game_id}")
async def get_game_value_analysis(game_id: str):
    """Detailed value analysis for a specific game"""
    # All markets
    # Line movements
    # Context (injuries, rest, etc.)
    pass

@app.get("/api/line-movement/{game_id}")
async def get_line_movement(
    game_id: str,
    hours_back: int = 24
):
    """Line movement history for a game"""
    # Historical odds from multiple books
    # Opening line, current line, movements
    pass

@app.post("/api/bet/place")
async def record_bet(bet: BetPlacement):
    """Record a placed bet for tracking"""
    # Save to bet_history
    # Update active exposure
    # Check against limits
    pass

@app.get("/api/performance/summary")
async def get_performance_summary(user_id: str):
    """Overall betting performance metrics"""
    # ROI, yield, win rate
    # By market breakdown
    # CLV tracking
    pass

@app.get("/api/alerts")
async def get_user_alerts(
    user_id: str,
    unread_only: bool = False
):
    """Get user alerts/notifications"""
    pass

@app.post("/api/alerts/create")
async def create_alert(alert: AlertRule):
    """Create a new alert rule"""
    # Injury updates
    # Line moves > X%
    # New value bets
    pass

@app.get("/api/context/game/{game_id}")
async def get_game_context(game_id: str):
    """Get full context for betting decision"""
    # Rest/fatigue
    # Injuries with impact
    # Travel
    # Matchup history
    pass

@app.get("/api/props/today")
async def get_todays_props():
    """Get player props with recommendations"""
    # Player props with OVER/UNDER recommendations
    # Projected minutes
    # Form analysis
    pass
```

#### E. Algorytmy obliczeń

**1. Expected Value (EV) Calculation:**
```python
def calculate_ev(odds: float, win_probability: float, stake: float = 100) -> float:
    """
    Calculate Expected Value
    
    Args:
        odds: Decimal odds (e.g., 2.50)
        win_probability: Model's probability of winning (0-1)
        stake: Bet amount
    
    Returns:
        Expected value in currency
    """
    decimal_odds = odds
    implied_prob = 1 / decimal_odds
    
    # EV = (Probability of Winning × Amount Won) - (Probability of Losing × Amount Lost)
    win_amount = (decimal_odds - 1) * stake
    lose_amount = stake
    
    ev = (win_probability * win_amount) - ((1 - win_probability) * lose_amount)
    
    return ev
```

**2. Implied Probability:**
```python
def decimal_to_implied_probability(odds: float) -> float:
    """Convert decimal odds to implied probability"""
    return 1 / odds

def american_to_implied_probability(american_odds: int) -> float:
    """Convert American odds to implied probability"""
    if american_odds > 0:
        return 100 / (american_odds + 100)
    else:
        return abs(american_odds) / (abs(american_odds) + 100)
```

**3. Edge Calculation:**
```python
def calculate_edge(model_prob: float, implied_prob: float) -> float:
    """
    Calculate betting edge
    
    Edge = Model Probability - Implied Probability
    
    Positive edge = value bet
    """
    return model_prob - implied_prob
```

**4. Kelly Criterion:**
```python
def calculate_kelly(
    odds: float,
    win_probability: float,
    kelly_fraction: float = 0.25
) -> float:
    """
    Calculate Kelly Criterion stake
    
    Kelly % = (bp - q) / b
    where:
        b = odds - 1 (decimal odds minus 1)
        p = probability of winning
        q = probability of losing (1 - p)
    
    Args:
        odds: Decimal odds
        win_probability: Model's win probability (0-1)
        kelly_fraction: Fractional Kelly (0.25 = Quarter Kelly for safety)
    
    Returns:
        Recommended stake as % of bankroll
    """
    b = odds - 1
    p = win_probability
    q = 1 - p
    
    kelly_pct = (b * p - q) / b
    
    # Only bet if positive expectation
    if kelly_pct <= 0:
        return 0
    
    # Apply fractional Kelly for risk management
    return kelly_pct * kelly_fraction
```

**5. ROI & Yield:**
```python
def calculate_roi(total_profit: float, total_wagered: float) -> float:
    """
    Calculate Return on Investment
    
    ROI = (Total Profit / Total Wagered) × 100%
    """
    if total_wagered == 0:
        return 0
    return (total_profit / total_wagered) * 100

def calculate_yield(net_profit: float, total_risked: float) -> float:
    """
    Calculate Yield (similar to ROI but focuses on net results)
    
    Yield = (Net Profit / Total Amount Risked) × 100%
    """
    if total_risked == 0:
        return 0
    return (net_profit / total_risked) * 100
```

**6. Closing Line Value (CLV):**
```python
def calculate_clv(
    bet_odds: float,
    closing_odds: float
) -> float:
    """
    Calculate Closing Line Value
    
    CLV measures how much better your odds were compared to closing line
    Positive CLV = you got better value than the market consensus
    
    CLV % = ((1 / Implied Prob at Bet) - (1 / Implied Prob at Close)) × 100
    """
    bet_implied = 1 / bet_odds
    close_implied = 1 / closing_odds
    
    clv = ((1 / bet_implied) - (1 / close_implied)) * 100
    
    return clv
```

---

## 🚨 Lista błędów według priorytetu

### P0 - Krytyczne (Must Fix w 1 dzień)

1. **Brak Expected Value (EV) display** - Niemożliwe określenie realnej wartości zakładu
2. **Brak clear recommendation** (PLAY/NO PLAY) - Użytkownik musi sam interpretować
3. **Brak bet history tracking** - Niemożliwe śledzenie skuteczności
4. **Brak ROI/yield metrics** - Nie wiadomo czy system działa
5. **Zbyt długi czas decyzji** - >30 sekund na analizę pojedynczego typu
6. **Mobile UX** - Tabele nieczytelne na telefonie
7. **Brak Value Board** - Główny widok dla dzisiejszych value betów

### P1 - Ważne (Fix w 1 tydzień)

1. **Brak line movement tracking** - Nie widać zmian kursów
2. **Brak injury impact indicators** - Kontuzje nie są uwzględnione w displayu
3. **Brak rest/fatigue context** - B2B, travel nie są pokazane
4. **Brak sortowania/filtrowania** - Trudno znaleźć najlepsze typy
5. **Brak confidence meter** - Nie widać jak pewny jest model
6. **Brak explainability** - Dlaczego typ jest rekomendowany?
7. **Brak bankroll exposure tracking** - Ryzyko niekontrolowane
8. **Brak alerts** - Użytkownik nie wie o nowych opportunities
9. **No sticky headers** - Scrolling w tabelach problematyczny
10. **No dark mode toggle** - (jest domyślnie dark, ale brak switcha)

### P2 - Mniej ważne (Fix w 1 miesiąc)

1. **Brak props board** - Player props nie są zintegrowane
2. **Brak arbitrage detection** - Missed risk-free opportunities
3. **Brak alternate lines** - Tylko główne linie
4. **Brak parlay builder** - Manual parlay construction
5. **Brak notifications system** - No push/email alerts
6. **No bet correlations** - Same game parlays not supported
7. **No advanced stats** - Sharpe ratio, drawdown analysis
8. **No export functionality** - Can't export bet history
9. **No social features** - Can't share or follow other bettors
10. **No mobile app** - Only web interface

---

## 📋 Rekomendacje: CO ZROBIĆ

### ✅ 1 DZIEŃ (Quick Wins - P0)

#### Task 1: Add EV and Value Indicators (4h)
```bash
# Create ValueMetrics component
touch src/components/ValueMetrics.tsx

# Update BettingRecommendations to show EV
# Add colored badges: GREEN (PLAY), YELLOW (LEAN), RED (NO PLAY)
```

**Changes:**
- Display EV in dollars and percentage
- Add implied vs fair probability
- Show edge in percentage
- Add clear PLAY/NO PLAY badge

#### Task 2: Create Quick Decision Cards (3h)
```bash
# Redesign bet cards for <15sec decisions
# Key info above the fold
# Clear CTA buttons
```

#### Task 3: Mobile Optimization (3h)
```bash
# Responsive card layout for mobile
# Horizontal scrollable filters
# Touch-friendly buttons
# Reduced data density on small screens
```

**Total Day 1: 10 hours** ✅

---

### ✅ 1 TYDZIEŃ (Essential Features - P0 + P1)

#### Day 1: EV & Quick Decisions (done above)

#### Day 2-3: Bet History & Performance Tracking (12h)
```bash
# Backend: Create bet_history table
# API: Endpoints for placing/retrieving bets
# Frontend: PerformanceTracker component
# Display ROI, yield, win rate, CLV
```

#### Day 4: Value Board & Filters (8h)
```bash
# Create ValueBoard.tsx - main betting dashboard
# Advanced FilterBar component
# Sortable tables with sticky headers
# Today's value opportunities highlighted
```

#### Day 5: Game Context & Indicators (8h)
```bash
# GameContextCard component
# Display B2B, rest, travel, injuries
# Impact indicators (-5.2 pts, +2 rest days)
# Color-coded severity
```

#### Day 6: Confidence & Explainability (6h)
```bash
# ConfidenceMeter component (visual)
# Add "Why this pick?" explanation
# Model reasoning display
# Factors contributing to recommendation
```

#### Day 7: Testing & Polish (6h)
```bash
# Test all new features
# Mobile testing
# Performance optimization
# Bug fixes
```

**Total Week 1: ~50 hours** ✅

---

### ✅ 1 MIESIĄC (Full Featured Platform - P0 + P1 + P2)

#### Week 1: Core Features (done above)

#### Week 2: Line Movement & Alerts
- Line movement tracking and visualization
- Historical line data storage
- Alerts system (injuries, line moves, value)
- Email/push notifications
- Steam move detection

#### Week 3: Props & Advanced Features
- Props board integration
- Player props recommendations
- Arbitrage detection
- Alternate lines analysis
- Parlay builder (basic)

#### Week 4: Risk Management & Advanced Analytics
- Bankroll management UI
- Exposure tracking
- Advanced metrics (Sharpe, drawdown)
- Performance by time period
- Export functionality
- Final testing & documentation

**Total Month 1: ~200 hours** ✅

---

## 🎯 TOP 5 Features o najwyższym ROI dla użytkownika

### 1. **Expected Value (EV) Display** - ROI: ⭐⭐⭐⭐⭐

**Dlaczego najważniejsze:**
- Bezpośrednio pokazuje ile można zarobić
- Pozwala porównać typy numerycznie
- Foundation dla wszystkich decyzji
- Edukuje użytkownika o value betting

**Implementacja:** 2-4 godziny  
**Impact:** Transformuje platformę z informacyjnej w decyzyjną

---

### 2. **Value Board (Today's Opportunities)** - ROI: ⭐⭐⭐⭐⭐

**Dlaczego ważne:**
- Jeden widok = wszystkie dzisiejsze value bety
- Sortowanie po EV
- Quick decision workflow
- Filtry (edge %, confidence, market)

**Implementacja:** 6-8 godzin  
**Impact:** Użytkownik wie co grać w <60 sekund

---

### 3. **Bet History & ROI Tracking** - ROI: ⭐⭐⭐⭐⭐

**Dlaczego krytyczne:**
- Proof of concept - czy system działa?
- Motywacja (seeing profits grow)
- Learning (what works, what doesn't)
- Trust (transparent results)
- CLV tracking = long-term edge validation

**Implementacja:** 10-12 godzin  
**Impact:** Builds trust, enables data-driven improvements

---

### 4. **Game Context (Injuries, Rest, Fatigue)** - ROI: ⭐⭐⭐⭐

**Dlaczego valuable:**
- Real NBA insights that move lines
- Injury impact = instant edge
- B2B/travel = quantifiable advantage
- Context = better decisions

**Implementacja:** 8-10 godzin  
**Impact:** Differentiates from basic odds comparison sites

---

### 5. **Confidence Meter + Explainability** - ROI: ⭐⭐⭐⭐

**Dlaczego ważne:**
- User trust ("Why should I bet this?")
- Education (learning what the model sees)
- Risk management (confidence = stake sizing)
- Transparency = credibility

**Implementacja:** 4-6 godzin  
**Impact:** Increases user confidence, reduces second-guessing

---

## 📊 Podsumowanie w 10 punktach

### Co poprawić, żeby strona była narzędziem do wygrywania:

1. **Dodaj Expected Value (EV)** - Pokazuj konkretne $ value każdego zakładu, nie tylko procent edge

2. **Stwórz Value Board** - Jeden ekran z dzisiejszymi value opportunities, sorted by EV, with quick actions

3. **Trackuj zakłady i ROI** - Historia typów, ROI, yield, CLV - proof that system works

4. **Ułóż UI w kolejności decyzyjnej** - User widzi: Edge → EV → Confidence → CTA w <10 sekund

5. **Dodaj game context indicators** - Injuries (-5.2 pts), B2B, travel, rest advantage - realny NBA insight

6. **Implementuj filtry i sortowanie** - Edge >5%, Confidence >75%, Market type, Live games

7. **Zoptymalizuj mobile** - Card view, horizontal filters, touch-friendly, quick scan

8. **Dodaj confidence + wyjaśnienia** - Dlaczego typ jest dobry? (⭐⭐⭐⭐ 85% - Bulls 7-3 ATS home, LAL B2B)

9. **Zarządzanie banrollem** - Max exposure, daily limits, recommended stakes, risk alerts

10. **Line movement tracking** - Opening vs current vs closing, sharp money, steam moves

---

## 🎬 Finalne myśli

Aplikacja ma **solidne podstawy techniczne** i **dobre dane**, ale:

### Obecnie (4.5/10):
- ✅ Pokazuje odds
- ✅ Ma podstawową analizę
- ❌ User musi sam obliczyć value
- ❌ User musi sam zdecydować
- ❌ Brak proof of effectiveness

### Po implementacji (9/10):
- ✅ Pokazuje exact EV w $
- ✅ Jasna rekomendacja PLAY/NO PLAY
- ✅ Decyzja w <15 sekund
- ✅ Tracking skuteczności (ROI/CLV)
- ✅ Full game context
- ✅ Mobile-first experience
- ✅ Filtering & sorting
- ✅ Bankroll management

### Transformacja: Informational → **Actionable Betting Tool** 🎯

**Następny krok:** Zaimplementować TOP 5 features w pierwszym tygodniu.

---

**Koniec audytu**  
*Data: 2026-01-22*  
*Prepared by: UX Analyst specializing in sports betting analytics*
