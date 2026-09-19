import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { fetchAlerts } from '../services/alertService';
import RiskBadge from '../components/common/RiskBadge';
import StatusBadge from '../components/common/StatusBadge';
import { LoadingTable } from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import EmptyState from '../components/common/EmptyState';
import { timeAgo } from '../utils/formatters';

const STATUS_TABS = ['ALL', 'NEW', 'UNDER_REVIEW', 'ESCALATED', 'CLOSED'];

export default function Alerts() {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [riskFilter, setRiskFilter] = useState('ALL');

  const { data, loading, error, refetch } = useApi(
    () => fetchAlerts(page, 30, {
      status: statusFilter !== 'ALL' ? statusFilter : undefined,
      risk_level: riskFilter !== 'ALL' ? riskFilter : undefined,
    }),
    [page, statusFilter, riskFilter]
  );

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / 30);

  return (
    <div className="space-y-4">
      {/* Status Tabs */}
      <div className="flex items-center gap-1 bg-gray-100 rounded-xl p-1 w-fit">
        {STATUS_TABS.map((s) => (
          <button
            key={s}
            onClick={() => { setStatusFilter(s); setPage(1); }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition font-['Inter'] ${
              statusFilter === s ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {s === 'ALL' ? 'All Alerts' : s === 'UNDER_REVIEW' ? 'Under Review' : s.charAt(0) + s.slice(1).toLowerCase()}
          </button>
        ))}
      </div>

      {/* Risk filter */}
      <div className="flex items-center gap-2 flex-wrap">
        {['ALL', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map((lvl) => (
          <button
            key={lvl}
            onClick={() => { setRiskFilter(lvl); setPage(1); }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition font-['Inter'] ${
              riskFilter === lvl ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'
            }`}
          >
            {lvl}
          </button>
        ))}
        <span className="text-xs text-gray-400 font-['Inter'] ml-auto">{total.toLocaleString('en-IN')} alerts</span>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        {loading ? <LoadingTable rows={10} cols={7} /> :
         error ? <ErrorState message="Failed to load alerts" onRetry={refetch} /> :
         items.length === 0 ? <EmptyState title="No alerts found" message="Try changing your status or risk filter." /> : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm font-['Inter']">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  {['Alert ID', 'Account', 'Transaction', 'Pattern', 'Risk Score', 'Risk Level', 'Created', 'Status', ''].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {items.map((alert) => (
                  <tr key={alert.alert_id} className="hover:bg-blue-50/30 transition-colors cursor-pointer" onClick={() => window.location.href = `/alerts/${alert.alert_id}`}>
                    <td className="px-4 py-3 font-mono text-xs font-semibold text-blue-700">
                      <Link to={`/alerts/${alert.alert_id}`} onClick={(e) => e.stopPropagation()} className="hover:underline">{alert.alert_id}</Link>
                    </td>
                    <td className="px-4 py-3 text-xs font-mono text-gray-600">{alert.account_id ?? '—'}</td>
                    <td className="px-4 py-3 text-xs font-mono text-gray-600">{alert.transaction_id ?? '—'}</td>
                    <td className="px-4 py-3 text-xs text-gray-600 max-w-[160px] truncate">{alert.alert_type ?? '—'}</td>
                    <td className="px-4 py-3 text-xs font-mono font-semibold text-gray-900">{alert.risk_score?.toFixed(0) ?? '—'}</td>
                    <td className="px-4 py-3"><RiskBadge level={alert.risk_level} size="sm" /></td>
                    <td className="px-4 py-3 text-xs text-gray-400 whitespace-nowrap">{timeAgo(alert.created_at)}</td>
                    <td className="px-4 py-3"><StatusBadge status={alert.status} /></td>
                    <td className="px-4 py-3">
                      <Link to={`/alerts/${alert.alert_id}`} onClick={(e) => e.stopPropagation()} className="text-xs text-blue-600 hover:underline font-medium">View</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-5 py-3 border-t border-gray-100 bg-gray-50">
            <span className="text-xs text-gray-500 font-['Inter']">Page {page} of {totalPages}</span>
            <div className="flex items-center gap-1">
              <button disabled={page === 1} onClick={() => setPage((p) => p - 1)} className="p-1.5 rounded-lg border border-gray-200 text-gray-600 hover:bg-white disabled:opacity-40"><ChevronLeft className="w-4 h-4" /></button>
              <button disabled={page === totalPages} onClick={() => setPage((p) => p + 1)} className="p-1.5 rounded-lg border border-gray-200 text-gray-600 hover:bg-white disabled:opacity-40"><ChevronRight className="w-4 h-4" /></button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
