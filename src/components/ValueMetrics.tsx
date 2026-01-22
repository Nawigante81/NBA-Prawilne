import React from 'react';
import { TrendingUp, TrendingDown, Target, AlertCircle } from 'lucide-react';
import {
  calculateEV,
  calculateEVPercentage,
  decimalToImpliedProbability,
  getRecommendation,
  formatAmericanOdds,
  formatPercentage,
  formatCurrency,
} from '../utils/bettingCalculations';

interface ValueMetricsProps {
  odds: number;              // Decimal odds
  modelProb: number;         // Model probability (0-1)
  edge: number;              // Edge (0-1)
  stake?: number;            // Optional stake for EV calculation
  compact?: boolean;         // Compact mode for mobile
}

/**
 * ValueMetrics Component
 * Displays Expected Value, Edge, Implied vs Fair Probability, and Recommendation
 */
export const ValueMetrics: React.FC<ValueMetricsProps> = ({
  odds,
  modelProb,
  edge,
  stake = 100,
  compact = false
}) => {
  const impliedProb = decimalToImpliedProbability(odds);
  const ev = calculateEV(odds, modelProb, stake);
  const evPercentage = calculateEVPercentage(odds, modelProb);
  
  // Confidence approximation (simplified - in real app would come from model)
  const confidence = Math.min(0.95, Math.max(0.50, modelProb + edge * 2));
  const recommendation = getRecommendation(edge, confidence);
  
  // Color schemes
  const getRecommendationColor = () => {
    switch (recommendation) {
      case 'STRONG_PLAY':
        return {
          bg: 'bg-green-500/20',
          border: 'border-green-500/50',
          text: 'text-green-400',
          badge: 'bg-green-500',
          label: 'STRONG PLAY'
        };
      case 'PLAY':
        return {
          bg: 'bg-green-500/10',
          border: 'border-green-500/30',
          text: 'text-green-300',
          badge: 'bg-green-600',
          label: 'PLAY'
        };
      case 'LEAN':
        return {
          bg: 'bg-yellow-500/10',
          border: 'border-yellow-500/30',
          text: 'text-yellow-400',
          badge: 'bg-yellow-600',
          label: 'LEAN'
        };
      default:
        return {
          bg: 'bg-gray-500/10',
          border: 'border-gray-500/30',
          text: 'text-gray-400',
          badge: 'bg-gray-600',
          label: 'NO PLAY'
        };
    }
  };
  
  const colors = getRecommendationColor();
  
  if (compact) {
    return (
      <div className={`${colors.bg} ${colors.border} border rounded-lg p-3`}>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className={`px-2 py-0.5 ${colors.badge} text-white text-xs font-semibold rounded`}>
              {colors.label}
            </span>
            {edge > 0 ? (
              <TrendingUp className={`w-4 h-4 ${colors.text}`} />
            ) : (
              <TrendingDown className="w-4 h-4 text-red-400" />
            )}
          </div>
          <div className={`text-lg font-bold ${colors.text}`}>
            {formatPercentage(edge, true, 1)}
          </div>
        </div>
        
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div>
            <div className="text-gray-500">EV</div>
            <div className={`font-semibold ${ev > 0 ? 'text-green-400' : 'text-red-400'}`}>
              {formatCurrency(ev, true)}
            </div>
          </div>
          <div>
            <div className="text-gray-500">Fair</div>
            <div className="text-white font-semibold">
              {formatPercentage(modelProb, true, 1)}
            </div>
          </div>
          <div>
            <div className="text-gray-500">Conf</div>
            <div className="text-white font-semibold">
              {formatPercentage(confidence, true, 0)}
            </div>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className={`${colors.bg} ${colors.border} border rounded-lg p-4`}>
      {/* Header: Recommendation Badge */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className={`px-3 py-1 ${colors.badge} text-white text-sm font-bold rounded-full`}>
            {colors.label}
          </span>
          {recommendation !== 'NO_PLAY' && (
            <div className="flex items-center gap-1">
              <Target className="w-4 h-4 text-yellow-400" />
              <span className="text-xs text-gray-400">
                {(confidence * 100).toFixed(0)}% confidence
              </span>
            </div>
          )}
        </div>
        <div className={`text-2xl font-bold ${colors.text}`}>
          {formatPercentage(edge, true, 1)}
        </div>
      </div>
      
      {/* Key Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {/* Expected Value */}
        <div className="bg-gray-800/50 rounded-lg p-3">
          <div className="text-xs text-gray-400 mb-1">Expected Value</div>
          <div className={`text-lg font-bold ${ev > 0 ? 'text-green-400' : 'text-red-400'}`}>
            {formatCurrency(ev, true)}
          </div>
          <div className="text-xs text-gray-500">
            {formatPercentage(evPercentage / 100, true, 1)} ROI
          </div>
        </div>
        
        {/* Implied Probability */}
        <div className="bg-gray-800/50 rounded-lg p-3">
          <div className="text-xs text-gray-400 mb-1">Implied Prob</div>
          <div className="text-lg font-bold text-white">
            {formatPercentage(impliedProb, true, 1)}
          </div>
          <div className="text-xs text-gray-500">
            {formatAmericanOdds(odds)}
          </div>
        </div>
        
        {/* Fair Probability (Model) */}
        <div className="bg-gray-800/50 rounded-lg p-3">
          <div className="text-xs text-gray-400 mb-1">Fair Prob</div>
          <div className="text-lg font-bold text-blue-400">
            {formatPercentage(modelProb, true, 1)}
          </div>
          <div className="text-xs text-gray-500">Model</div>
        </div>
        
        {/* Edge */}
        <div className="bg-gray-800/50 rounded-lg p-3">
          <div className="text-xs text-gray-400 mb-1">Edge</div>
          <div className={`text-lg font-bold ${colors.text}`}>
            {formatPercentage(edge, true, 1)}
          </div>
          <div className="text-xs text-gray-500">
            {edge > 0 ? 'Value' : 'No Value'}
          </div>
        </div>
      </div>
      
      {/* Warning for low confidence */}
      {confidence < 0.65 && edge > 0 && (
        <div className="mt-3 flex items-start gap-2 text-xs text-yellow-400 bg-yellow-500/10 border border-yellow-500/20 rounded p-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>Lower confidence - consider reducing stake or skipping</span>
        </div>
      )}
    </div>
  );
};

interface ConfidenceMeterProps {
  confidence: number;  // 0-1
  compact?: boolean;
}

/**
 * ConfidenceMeter Component
 * Visual representation of model confidence
 */
export const ConfidenceMeter: React.FC<ConfidenceMeterProps> = ({
  confidence,
  compact = false
}) => {
  const percentage = confidence * 100;
  const stars = Math.round(confidence * 5); // 0-5 stars
  
  const getColor = () => {
    if (confidence >= 0.80) return 'bg-green-400';
    if (confidence >= 0.70) return 'bg-yellow-400';
    if (confidence >= 0.60) return 'bg-orange-400';
    return 'bg-red-400';
  };
  
  if (compact) {
    return (
      <div className="flex items-center gap-1">
        {[...Array(5)].map((_, i) => (
          <div
            key={i}
            className={`w-2 h-2 rounded-full ${
              i < stars ? getColor() : 'bg-gray-600'
            }`}
          />
        ))}
      </div>
    );
  }
  
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-400">Confidence</span>
        <span className="text-sm font-semibold text-white">
          {percentage.toFixed(0)}%
        </span>
      </div>
      <div className="relative w-full h-2 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`absolute top-0 left-0 h-full ${getColor()} transition-all duration-300`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="flex items-center gap-1 mt-2">
        {[...Array(5)].map((_, i) => (
          <div
            key={i}
            className={`flex-1 h-1 rounded-full ${
              i < stars ? getColor() : 'bg-gray-600'
            }`}
          />
        ))}
      </div>
    </div>
  );
};

interface QuickStatsProps {
  ev: number;
  edge: number;
  odds: number;
  confidence: number;
}

/**
 * QuickStats Component
 * Condensed metrics for quick scanning
 */
export const QuickStats: React.FC<QuickStatsProps> = ({
  ev,
  edge,
  odds,
  confidence
}) => {
  return (
    <div className="flex items-center gap-4 text-sm">
      <div className="flex items-center gap-1">
        <span className="text-gray-400">EV:</span>
        <span className={`font-semibold ${ev > 0 ? 'text-green-400' : 'text-red-400'}`}>
          {formatCurrency(ev, true)}
        </span>
      </div>
      
      <div className="flex items-center gap-1">
        <span className="text-gray-400">Edge:</span>
        <span className={`font-semibold ${edge > 0 ? 'text-green-400' : 'text-gray-400'}`}>
          {formatPercentage(edge, true, 1)}
        </span>
      </div>
      
      <div className="flex items-center gap-1">
        <span className="text-gray-400">Odds:</span>
        <span className="font-semibold text-white">
          {formatAmericanOdds(odds)}
        </span>
      </div>
      
      <div className="flex items-center gap-1">
        <span className="text-gray-400">Conf:</span>
        <ConfidenceMeter confidence={confidence} compact />
      </div>
    </div>
  );
};

export default ValueMetrics;
