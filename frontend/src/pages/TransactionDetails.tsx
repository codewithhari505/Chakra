import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Zap } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { getTransaction, analyzeTransaction } from '../services/transactionService';
import RiskBadge from '../components/common/RiskBadge';
import { LoadingSpinner } from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import { formatCurrency, formatDate, scoreToLevel, getRiskBarColor } from '../utils/formatters';
import type { RiskAnalysis } from '../types';

function ScoreBar({ label, value, weight }: { label: string; value: number; weight: string }) {
  const lvl = scoreToLevel(value);
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="text-gray-600 font-['Inter']">{label} <span className="text-gray-400">({weight})</span></span>
        <span className="font-mono font-semibold text-gray-800">{value}/100</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${getRiskBarColor(lvl)}`} style={{ width: `${Math.min(100, value)}%` }} />
      </div>
    </div>
  );
}

export default function TransactionDetails() {
  const { id } = useParams<{ id: string }>();
  const { data: tx, loading, error, refetch } = useApi(() => getTransaction(id!), [id]);
  const [analysis, setAnalysis] = useState<RiskAnalysis | null>(null);
  const [analyzing, setAnalyzing] = useState(false);

  async function runAnalysis() {
    if (!tx) return;
    setAnalyzing(true);
    try {
      const res = await analyzeTransaction(tx as any);
      setAnalysis(res.analysis);
    } catch (e) { console.error(e); }
    finally { setAnalyzing(false); }
  }

  if (loading) return <LoadingSpinner />;
  if (error || !tx) return <ErrorState message="Transaction not found" onRetry={refetch} />;

  const scores = analysis?.component_scores;

  return (
    <div className="space-y-5 max-w-5xl">
      {/* Back */}
      <Link to="/transactions" className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-blue-600 font-['Inter'] transition">
        <ArrowLeft className="w-4 h-4" /> Back to Transactions
      </Link>

      {/* Header */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-mono text-lg font-bold text-gray-900">{tx.transaction_id}</h2>
              <RiskBadge level={tx.risk_level} />
            </div>
            <p className="text-xs text-gray-400 font-['Inter'] mt-1">{formatDate(tx.timestamp)} · {tx.channel} · {tx.location}</p>
          </div>
          <button
            onClick={runAnalysis}
            disabled={analyzing}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 transition disabled:opacity-60 font-['Inter']"
          >
            <Zap className="w-4 h-4" />
            {analyzing ? 'Analyzing...' : 'Run AI Analysis'}
          </button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-5 pt-5 border-t border-gray-100">
          <div>
            <div className="text-xs text-gray-400 font-['Inter'] uppercase tracking-wide">Amount</div>
            <div className="text-xl font-bold text-gray-900 font-mono mt-0.5">{formatCurrency(tx.amount)}</div>
          </div>
          <div>
            <div className="text-xs text-gray-400 font-['Inter'] uppercase tracking-wide">Remitter</div>
            <div className="text-sm font-semibold text-blue-700 font-mono mt-0.5">{tx.sender_account_id}</div>
          </div>
          <div>
            <div className="text-xs text-gray-400 font-['Inter'] uppercase tracking-wide">Beneficiary</div>
            <div className="text-sm font-semibold text-gray-700 font-mono mt-0.5">{tx.receiver_account_id}</div>
          </div>
          <div>
            <div className="text-xs text-gray-400 font-['Inter'] uppercase tracking-wide">Type</div>
            <div className="text-sm font-semibold text-gray-700 font-mono mt-0.5">{tx.transaction_type}</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* 4-Pillar Risk */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-4">
          <div className="text-sm font-semibold text-gray-900 font-['Poppins']">Risk Assessment</div>
          {scores ? (
            <div className="space-y-3">
              <div className="flex items-center gap-3 mb-2">
                <div className="text-3xl font-bold text-gray-900 font-mono">{analysis!.final_risk_score}</div>
                <div><RiskBadge level={analysis!.risk_level} /><div className="text-xs text-gray-400 mt-0.5 font-['Inter']">Composite Score / 100</div></div>
              </div>
              <ScoreBar label="P1: Supervised ML" value={scores.ml_score} weight="40%" />
              <ScoreBar label="P2: Isolation Forest" value={scores.anomaly_score} weight="20%" />
              <ScoreBar label="P3: Regulatory Rules" value={scores.rule_score} weight="20%" />
              <ScoreBar label="P4: Network Graph" value={scores.network_score} weight="20%" />
            </div>
          ) : (
            <div className="text-sm text-gray-400 font-['Inter'] py-6 text-center">
              Click "Run AI Analysis" to see the 4-pillar risk breakdown.
            </div>
          )}
        </div>

        {/* AI Explanation */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-3">
          <div className="text-sm font-semibold text-gray-900 font-['Poppins']">Why was this flagged?</div>
          {analysis ? (
            <div className="space-y-3">
              {analysis.explanation_summary && (
                <div className="text-xs text-gray-600 font-['Inter'] leading-relaxed bg-blue-50 border border-blue-100 rounded-lg p-3">
                  {analysis.explanation_summary}
                </div>
              )}
              {analysis.triggered_rules.length > 0 && (
                <div className="space-y-1.5">
                  <div className="text-xs font-semibold text-orange-700 uppercase tracking-wide">Triggered Rules</div>
                  {analysis.triggered_rules.map((rule, i) => (
                    <div key={i} className="flex gap-2 text-xs font-['Inter'] bg-orange-50 border border-orange-100 rounded-lg px-3 py-2 text-orange-800">
                      <span>•</span>
                      <span>{typeof rule === 'string' ? rule : (rule as any).rule_name ?? JSON.stringify(rule)}</span>
                    </div>
                  ))}
                </div>
              )}
              {Object.keys(analysis.feature_attributions).length > 0 && (
                <div className="space-y-1.5">
                  <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Key Risk Drivers (SHAP)</div>
                  {Object.entries(analysis.feature_attributions).slice(0, 5).map(([feat, val]) => (
                    <div key={feat} className="flex justify-between text-xs font-mono text-gray-600">
                      <span>{feat}</span>
                      <span className={Number(val) >= 0 ? 'text-orange-600 font-semibold' : 'text-blue-600'}>{Number(val) >= 0 ? '+' : ''}{Number(val).toFixed(3)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="text-xs text-gray-400 font-['Inter'] py-6 text-center">Run AI Analysis to view explainability report.</div>
          )}
        </div>
      </div>

      {/* Status flags */}
      {tx.is_suspicious && (
        <div className="bg-orange-50 border border-orange-200 rounded-xl px-5 py-3 flex items-center gap-3">
          <span className="text-orange-500 font-bold text-lg">⚠</span>
          <div>
            <div className="text-sm font-semibold text-orange-800 font-['Poppins']">Suspicious Pattern Detected</div>
            <div className="text-xs text-orange-600 font-['Inter']">{tx.detected_patterns ?? 'Pattern anomaly identified by AML rules engine'}</div>
          </div>
        </div>
      )}
    </div>
  );
}
