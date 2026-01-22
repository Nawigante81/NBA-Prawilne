/**
 * Betting Calculations Utilities
 * Core algorithms for EV, odds conversion, Kelly, etc.
 */

// ============================================================================
// Odds Conversion
// ============================================================================

/**
 * Convert decimal odds to implied probability
 * @param decimalOdds - Decimal odds (e.g., 2.50)
 * @returns Implied probability (0-1)
 */
export function decimalToImpliedProbability(decimalOdds: number): number {
  if (decimalOdds <= 1) return 0;
  return 1 / decimalOdds;
}

/**
 * Convert American odds to decimal odds
 * @param americanOdds - American odds (e.g., -110 or +150)
 * @returns Decimal odds
 */
export function americanToDecimal(americanOdds: number): number {
  if (americanOdds > 0) {
    return (americanOdds / 100) + 1;
  } else {
    return (100 / Math.abs(americanOdds)) + 1;
  }
}

/**
 * Convert decimal odds to American odds
 * @param decimalOdds - Decimal odds (e.g., 2.50)
 * @returns American odds
 */
export function decimalToAmerican(decimalOdds: number): number {
  if (decimalOdds >= 2) {
    return Math.round((decimalOdds - 1) * 100);
  } else {
    return Math.round(-100 / (decimalOdds - 1));
  }
}

/**
 * Convert American odds to implied probability
 * @param americanOdds - American odds
 * @returns Implied probability (0-1)
 */
export function americanToImpliedProbability(americanOdds: number): number {
  if (americanOdds > 0) {
    return 100 / (americanOdds + 100);
  } else {
    return Math.abs(americanOdds) / (Math.abs(americanOdds) + 100);
  }
}

// ============================================================================
// Expected Value Calculations
// ============================================================================

/**
 * Calculate Expected Value
 * @param odds - Decimal odds
 * @param winProbability - Model's win probability (0-1)
 * @param stake - Bet amount (default 100)
 * @returns Expected value in currency
 */
export function calculateEV(
  odds: number,
  winProbability: number,
  stake: number = 100
): number {
  const winAmount = (odds - 1) * stake;
  const loseAmount = stake;
  
  const ev = (winProbability * winAmount) - ((1 - winProbability) * loseAmount);
  
  return ev;
}

/**
 * Calculate EV as percentage of stake
 * @param odds - Decimal odds
 * @param winProbability - Model's win probability (0-1)
 * @returns EV percentage
 */
export function calculateEVPercentage(
  odds: number,
  winProbability: number
): number {
  const ev = calculateEV(odds, winProbability, 100);
  return ev; // Already as percentage since stake is 100
}

// ============================================================================
// Edge Calculations
// ============================================================================

/**
 * Calculate betting edge
 * @param modelProb - Model's probability (0-1)
 * @param impliedProb - Bookmaker's implied probability (0-1)
 * @returns Edge as decimal (0.057 = 5.7% edge)
 */
export function calculateEdge(modelProb: number, impliedProb: number): number {
  return modelProb - impliedProb;
}

/**
 * Determine recommendation based on edge and confidence
 * @param edge - Edge percentage (0-1)
 * @param confidence - Confidence level (0-1)
 * @returns Recommendation level
 */
export function getRecommendation(
  edge: number,
  confidence: number
): 'STRONG_PLAY' | 'PLAY' | 'LEAN' | 'NO_PLAY' {
  if (edge <= 0) return 'NO_PLAY';
  
  if (edge >= 0.07 && confidence >= 0.80) return 'STRONG_PLAY';
  if (edge >= 0.05 && confidence >= 0.70) return 'PLAY';
  if (edge >= 0.03 && confidence >= 0.60) return 'LEAN';
  
  return 'NO_PLAY';
}

// ============================================================================
// Kelly Criterion
// ============================================================================

/**
 * Calculate Kelly Criterion stake
 * @param odds - Decimal odds
 * @param winProbability - Model's win probability (0-1)
 * @param kellyFraction - Fractional Kelly (0.25 = Quarter Kelly)
 * @returns Recommended stake as % of bankroll (0-1)
 */
export function calculateKelly(
  odds: number,
  winProbability: number,
  kellyFraction: number = 0.25
): number {
  const b = odds - 1;
  const p = winProbability;
  const q = 1 - p;
  
  const kellyPct = (b * p - q) / b;
  
  // Only bet if positive expectation
  if (kellyPct <= 0) return 0;
  
  // Apply fractional Kelly for risk management
  return kellyPct * kellyFraction;
}

/**
 * Calculate stake recommendations
 * @param odds - Decimal odds
 * @param winProbability - Model's win probability
 * @param bankroll - Current bankroll
 * @param edge - Betting edge
 * @param confidence - Model confidence
 * @returns Stake recommendations
 */
export function calculateStakeRecommendations(
  odds: number,
  winProbability: number,
  bankroll: number,
  edge: number,
  confidence: number
): {
  kelly_stake: number;
  quarter_kelly: number;
  half_kelly: number;
  flat_stake: number;
  recommended: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  warnings: string[];
} {
  const fullKelly = calculateKelly(odds, winProbability, 1.0);
  const quarterKelly = calculateKelly(odds, winProbability, 0.25);
  const halfKelly = calculateKelly(odds, winProbability, 0.5);
  const flatStake = 0.02; // 2% flat
  
  const kellyStake = fullKelly * bankroll;
  const quarterKellyStake = quarterKelly * bankroll;
  const halfKellyStake = halfKelly * bankroll;
  const flatStakeAmount = flatStake * bankroll;
  
  // Determine recommended stake based on edge and confidence
  let recommended = quarterKellyStake; // Default to quarter Kelly
  let riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' = 'MEDIUM';
  const warnings: string[] = [];
  
  // High confidence, high edge -> can do half Kelly
  if (edge >= 0.07 && confidence >= 0.80) {
    recommended = halfKellyStake;
    riskLevel = 'MEDIUM';
  }
  // Medium confidence -> quarter Kelly
  else if (edge >= 0.05 && confidence >= 0.65) {
    recommended = quarterKellyStake;
    riskLevel = 'MEDIUM';
  }
  // Lower confidence -> flat stake
  else if (edge >= 0.03) {
    recommended = flatStakeAmount;
    riskLevel = 'LOW';
  } else {
    recommended = 0;
    riskLevel = 'HIGH';
    warnings.push('Edge too low - consider skipping this bet');
  }
  
  // Safety checks
  if (recommended > bankroll * 0.1) {
    warnings.push('Recommended stake >10% of bankroll - consider reducing');
    riskLevel = 'HIGH';
  }
  
  if (confidence < 0.60) {
    warnings.push('Low confidence - proceed with caution');
    riskLevel = 'HIGH';
  }
  
  return {
    kelly_stake: kellyStake,
    quarter_kelly: quarterKellyStake,
    half_kelly: halfKellyStake,
    flat_stake: flatStakeAmount,
    recommended,
    risk_level: riskLevel,
    warnings
  };
}

// ============================================================================
// Performance Metrics
// ============================================================================

/**
 * Calculate ROI (Return on Investment)
 * @param totalProfit - Total profit (net)
 * @param totalWagered - Total amount wagered
 * @returns ROI as percentage
 */
export function calculateROI(totalProfit: number, totalWagered: number): number {
  if (totalWagered === 0) return 0;
  return (totalProfit / totalWagered) * 100;
}

/**
 * Calculate Yield
 * @param netProfit - Net profit
 * @param totalRisked - Total amount risked
 * @returns Yield as percentage
 */
export function calculateYield(netProfit: number, totalRisked: number): number {
  if (totalRisked === 0) return 0;
  return (netProfit / totalRisked) * 100;
}

/**
 * Calculate Closing Line Value (CLV)
 * @param betOdds - Odds when bet was placed
 * @param closingOdds - Closing odds
 * @returns CLV as percentage
 */
export function calculateCLV(betOdds: number, closingOdds: number): number {
  const betImplied = decimalToImpliedProbability(betOdds);
  const closeImplied = decimalToImpliedProbability(closingOdds);
  
  // CLV = how much better were your odds vs closing
  // Positive = you got better value
  const clv = ((closeImplied - betImplied) / betImplied) * 100;
  
  return clv;
}

/**
 * Calculate win rate
 * @param wins - Number of wins
 * @param losses - Number of losses
 * @returns Win rate as percentage
 */
export function calculateWinRate(wins: number, losses: number): number {
  const total = wins + losses;
  if (total === 0) return 0;
  return (wins / total) * 100;
}

// ============================================================================
// Formatting Utilities
// ============================================================================

/**
 * Format odds as American (with + or -)
 * @param decimalOdds - Decimal odds
 * @returns Formatted American odds string
 */
export function formatAmericanOdds(decimalOdds: number): string {
  const american = decimalToAmerican(decimalOdds);
  return american > 0 ? `+${american}` : `${american}`;
}

/**
 * Format percentage
 * @param value - Value (0-1 or 0-100)
 * @param asDecimal - If true, treats input as 0-1, else 0-100
 * @param decimals - Number of decimal places
 * @returns Formatted percentage string
 */
export function formatPercentage(
  value: number,
  asDecimal: boolean = true,
  decimals: number = 1
): string {
  const pct = asDecimal ? value * 100 : value;
  return `${pct.toFixed(decimals)}%`;
}

/**
 * Format currency
 * @param value - Currency value
 * @param showSign - Show + for positive values
 * @returns Formatted currency string
 */
export function formatCurrency(value: number, showSign: boolean = false): string {
  const sign = showSign && value > 0 ? '+' : '';
  return `${sign}$${Math.abs(value).toFixed(2)}`;
}

/**
 * Format edge with color indicator
 * @param edge - Edge value (0-1)
 * @returns Object with formatted text and color class
 */
export function formatEdge(edge: number): {
  text: string;
  colorClass: string;
} {
  const pct = edge * 100;
  let colorClass = 'text-gray-400';
  
  if (pct >= 7) colorClass = 'text-green-400';
  else if (pct >= 5) colorClass = 'text-green-300';
  else if (pct >= 3) colorClass = 'text-yellow-400';
  else if (pct > 0) colorClass = 'text-yellow-300';
  else colorClass = 'text-red-400';
  
  return {
    text: `${pct >= 0 ? '+' : ''}${pct.toFixed(1)}%`,
    colorClass
  };
}

// ============================================================================
// Risk Assessment
// ============================================================================

/**
 * Assess risk level of a bet
 * @param stake - Bet stake
 * @param bankroll - Total bankroll
 * @param confidence - Model confidence (0-1)
 * @param edge - Betting edge (0-1)
 * @returns Risk level
 */
export function assessRiskLevel(
  stake: number,
  bankroll: number,
  confidence: number,
  edge: number
): 'LOW' | 'MEDIUM' | 'HIGH' {
  const pctOfBankroll = (stake / bankroll) * 100;
  
  // High stake, low confidence = HIGH risk
  if (pctOfBankroll > 5 && confidence < 0.70) return 'HIGH';
  
  // High stake, medium confidence = MEDIUM-HIGH risk
  if (pctOfBankroll > 5) return 'MEDIUM';
  
  // Medium stake, low edge = MEDIUM risk
  if (pctOfBankroll > 3 && edge < 0.05) return 'MEDIUM';
  
  // Otherwise LOW
  return 'LOW';
}

/**
 * Check if bet should be skipped based on criteria
 * @param edge - Betting edge
 * @param confidence - Model confidence
 * @param stake - Proposed stake
 * @param bankroll - Total bankroll
 * @param activeExposure - Current exposure amount
 * @param dailyLimit - Daily exposure limit
 * @returns Whether to skip and reason
 */
export function shouldSkipBet(
  edge: number,
  confidence: number,
  stake: number,
  bankroll: number,
  activeExposure: number,
  dailyLimit: number
): { skip: boolean; reason?: string } {
  // No edge or negative edge
  if (edge <= 0) {
    return { skip: true, reason: 'No edge or negative expectation' };
  }
  
  // Edge too small
  if (edge < 0.025) {
    return { skip: true, reason: 'Edge too small (<2.5%)' };
  }
  
  // Confidence too low
  if (confidence < 0.55) {
    return { skip: true, reason: 'Confidence too low (<55%)' };
  }
  
  // Would exceed daily limit
  if (activeExposure + stake > dailyLimit) {
    return { skip: true, reason: 'Would exceed daily exposure limit' };
  }
  
  // Stake too large
  if (stake > bankroll * 0.15) {
    return { skip: true, reason: 'Stake >15% of bankroll - too risky' };
  }
  
  return { skip: false };
}
