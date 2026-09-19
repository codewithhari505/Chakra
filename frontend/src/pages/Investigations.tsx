import React from 'react';
import { Link } from 'react-router-dom';
import { useApi } from '../hooks/useApi';
import { getInvestigationSummary } from '../services/investigationService';
import { fetchAlerts } from '../services/alertService';
import RiskBadge from '../components/common/RiskBadge';
import StatusBadge from '../components/common/StatusBadge';
import { LoadingCards, LoadingTable } from '../components/common/LoadingState';
import { timeAgo } from '../utils/formatters';

export default function Investigations() {
  const { data: summary, loading: sumLoading } = useApi(() => getInvestigationSummary().catch(() => null as any), []);
  const { data: alerts, loading: alertLoading } = useApi(() => fetchAlerts(1, 20, { status: 'NEW' }), []);

  const caseCards = [
    { label: 'Active Cases', val: summary?.active_cases ?? '—', color: 'border-blue-200 bg-blue-50 text-blue-700' },
    { label: 'Pending Triage', val: summary?.pending_triage ?? '—', color: 'border-orange-200 bg-orange-50 text-orange-700' },
    { label: 'Escalated', val: summary?.escalated_cases ?? '—', color: 'border-red-200 bg-red-50 text-red-700' },
    { label: 'Closed Cases', val: summary?.closed_cases ?? '—', color: 'border-gray-200 bg-gray-50 text-gray-700' },
  ];

  return (
    <div className="space-y-6">
      {sumLoading ? <LoadingCards count={4} /> : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {caseCards.map(({ label, val, color }) => (
            <div key={label} className={`border rounded-xl p-5 ${color}`}>
              <div className="text-xs font-medium uppercase tracking-wide opacity-70 font-['Inter']">{label}</div>
              <div className="text-3xl font-bold font-mono mt-1">{val}</div>
            </div>
          ))}
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
          <div>
            <div className="text-sm font-semibold text-gray-900 font-['Poppins']">Open Investigations — New Alerts</div>
            <div className="text-xs text-gray-400 font-['Inter'] mt-0.5">Alerts requiring triage and assignment</div>
          </div>
          <Link to="/alerts" className="text-xs text-blue-600 font-medium font-['Inter'] hover:underline">View all alerts →</Link>
        </div>

        {alertLoading ? <LoadingTable rows={8} cols={6} /> : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm font-['Inter']">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  {['Alert ID', 'Account', 'Pattern', 'Risk Level', 'Score', 'Created', 'Status', 'Actions'].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {(alerts?.items ?? []).map((alert) => (
                  <tr key={alert.alert_id} className="hover:bg-blue-50/30 transition-colors">
                    <td className="px-4 py-3 font-mono text-xs font-semibold text-blue-700">
                      <Link to={`/alerts/${alert.alert_id}`} className="hover:underline">{alert.alert_id}</Link>
                    </td>
                    <td className="px-4 py-3 text-xs font-mono text-gray-600">{alert.account_id ?? '—'}</td>
                    <td className="px-4 py-3 text-xs text-gray-600 max-w-[160px] truncate">{alert.alert_type ?? '—'}</td>
                    <td className="px-4 py-3"><RiskBadge level={alert.risk_level} size="sm" /></td>
                    <td className="px-4 py-3 text-xs font-mono font-semibold text-gray-900">{alert.risk_score?.toFixed(0) ?? '—'}</td>
                    <td className="px-4 py-3 text-xs text-gray-400 whitespace-nowrap">{timeAgo(alert.created_at)}</td>
                    <td className="px-4 py-3"><StatusBadge status={alert.status} /></td>
                    <td className="px-4 py-3">
                      <Link to={`/alerts/${alert.alert_id}`} className="text-xs text-blue-600 font-semibold hover:underline">Investigate →</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
