import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, UserCheck, TrendingUp, X } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { getAlert, updateAlert } from '../services/alertService';
import { getAuditTrail, assignAlert, escalateAlert, closeCase } from '../services/investigationService';
import RiskBadge from '../components/common/RiskBadge';
import StatusBadge from '../components/common/StatusBadge';
import { LoadingSpinner } from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import { formatDate, formatCurrency, getRiskBarColor, scoreToLevel } from '../utils/formatters';

export default function AlertDetails() {
  const { id } = useParams<{ id: string }>();
  const { data: alert, loading, error, refetch } = useApi(() => getAlert(id!), [id]);
  const { data: audit, refetch: refetchAudit } = useApi(() => getAuditTrail(id!).catch(() => null as any), [id]);
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [actioning, setActioning] = useState(false);

  async function handleAction(type: 'assign' | 'escalate' | 'close') {
    if (!alert) return;
    setActioning(true);
    try {
      if (type === 'assign') {
        await assignAlert(alert.alert_id, 'Investigator A', 'Assigned for review');
        setActionMsg('Alert assigned to Investigator A');
      } else if (type === 'escalate') {
        await escalateAlert(alert.alert_id, 'Senior Investigator', 'High risk pattern confirmed');
        setActionMsg('Alert escalated to Senior Investigator');
      } else {
        await closeCase(alert.alert_id, 'FALSE_POSITIVE', 'No criminal intent found', 'Investigator A');
        setActionMsg('Case closed — logged in audit trail');
      }
      refetch(); refetchAudit();
    } catch (e: any) {
      setActionMsg('Action failed: ' + (e?.response?.data?.detail ?? e.message));
    } finally { setActioning(false); }
  }

  if (loading) return <LoadingSpinner />;
  if (error || !alert) return <ErrorState message="Alert not found" onRetry={refetch} />;

  const scoreLevel = scoreToLevel(alert.risk_score ?? 0);

  return (
    <div className="space-y-5 max-w-5xl">
      <Link to="/alerts" className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-blue-600 font-['Inter'] transition">
        <ArrowLeft className="w-4 h-4" /> Back to Alerts
      </Link>

      {actionMsg && (
        <div className="flex items-center justify-between bg-blue-50 border border-blue-200 rounded-xl px-4 py-3 text-sm text-blue-700 font-['Inter']">
          <span>{actionMsg}</span>
          <button onClick={() => setActionMsg(null)}><X className="w-4 h-4" /></button>
        </div>
      )}

      {/* Header */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="font-mono text-lg font-bold text-gray-900">{alert.alert_id}</h2>
              <RiskBadge level={alert.risk_level} />
              <StatusBadge status={alert.status} />
            </div>
            <p className="text-xs text-gray-400 font-['Inter'] mt-1">{alert.alert_type} · Created {formatDate(alert.created_at)}</p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-gray-900 font-mono">{alert.risk_score?.toFixed(0) ?? '—'}</div>
            <div className="text-xs text-gray-400">Risk Score / 100</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Transaction Info */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-4">
          <div className="text-sm font-semibold text-gray-900 font-['Poppins']">Transaction Information</div>
          <div className="space-y-2 text-xs font-['Inter']">
            {[
              { label: 'Transaction ID', val: alert.transaction_id && <Link to={`/transactions/${alert.transaction_id}`} className="text-blue-600 hover:underline font-mono">{alert.transaction_id}</Link> },
              { label: 'Subject Account', val: alert.account_id && <Link to={`/accounts/${alert.account_id}`} className="text-blue-600 hover:underline font-mono">{alert.account_id}</Link> },
              { label: 'Detected Pattern', val: alert.detected_patterns },
              { label: 'Alert Type', val: alert.alert_type },
              { label: 'Assigned To', val: alert.assigned_to ?? 'Unassigned' },
            ].map(({ label, val }) => (
              <div key={label} className="flex items-start justify-between gap-3">
                <span className="text-gray-400 shrink-0">{label}</span>
                <span className="text-gray-800 font-medium text-right">{val ?? '—'}</span>
              </div>
            ))}
          </div>
        </div>

        {/* AI Explanation */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-3">
          <div className="text-sm font-semibold text-gray-900 font-['Poppins']">Why was this flagged?</div>
          {alert.explanation ? (
            <div className="text-xs text-gray-600 font-['Inter'] leading-relaxed bg-blue-50 border border-blue-100 rounded-lg p-3">{alert.explanation}</div>
          ) : (
            <div className="text-xs text-gray-400 font-['Inter']">No explanation available.</div>
          )}
          {alert.top_features && Object.keys(alert.top_features).length > 0 && (
            <div className="space-y-2 mt-2">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Top Risk Drivers</div>
              {Object.entries(alert.top_features).slice(0, 5).map(([feat, val]) => (
                <div key={feat} className="space-y-0.5">
                  <div className="flex justify-between text-xs text-gray-600">
                    <span className="font-mono">{feat}</span>
                    <span className="font-semibold">{(val * 100).toFixed(1)}%</span>
                  </div>
                  <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full bg-orange-400 rounded-full" style={{ width: `${Math.min(100, val * 100)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Investigation Actions */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <div className="text-sm font-semibold text-gray-900 font-['Poppins'] mb-4">Investigation Actions</div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => handleAction('assign')}
            disabled={actioning}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 transition disabled:opacity-60 font-['Inter']"
          >
            <UserCheck className="w-4 h-4" /> Assign
          </button>
          <button
            onClick={() => handleAction('escalate')}
            disabled={actioning}
            className="flex items-center gap-2 px-4 py-2 bg-orange-500 text-white text-sm font-semibold rounded-lg hover:bg-orange-600 transition disabled:opacity-60 font-['Inter']"
          >
            <TrendingUp className="w-4 h-4" /> Escalate
          </button>
          <button
            onClick={() => handleAction('close')}
            disabled={actioning}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 text-sm font-semibold rounded-lg hover:bg-gray-50 transition disabled:opacity-60 font-['Inter']"
          >
            <X className="w-4 h-4" /> Close Case
          </button>
          {alert.transaction_id && (
            <Link
              to={`/transactions/${alert.transaction_id}`}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 text-sm font-semibold rounded-lg hover:bg-gray-50 transition font-['Inter']"
            >
              View Transaction →
            </Link>
          )}
        </div>
        {alert.investigation_notes && (
          <div className="mt-4 p-3 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-600 font-['Inter']">
            <span className="font-semibold text-gray-800 block mb-1">Investigation Notes</span>
            {alert.investigation_notes}
          </div>
        )}
      </div>

      {/* Audit Trail */}
      {audit && audit.events?.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <div className="text-sm font-semibold text-gray-900 font-['Poppins'] mb-4">Audit Trail ({audit.total_events} events)</div>
          <div className="relative pl-4">
            <div className="absolute left-0 top-0 bottom-0 w-px bg-gray-200" />
            <div className="space-y-4">
              {audit.events.map((ev, i) => (
                <div key={i} className="relative">
                  <div className="absolute -left-4 top-1 w-2 h-2 rounded-full bg-blue-500 border-2 border-white" />
                  <div className="text-xs font-['Inter']">
                    <span className="font-semibold text-gray-800">{ev.action}</span>
                    {ev.actor && <span className="text-gray-400 ml-2">by {ev.actor}</span>}
                    <span className="text-gray-400 ml-2">{formatDate(ev.timestamp)}</span>
                    {ev.notes && <div className="text-gray-500 mt-0.5">{ev.notes}</div>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
