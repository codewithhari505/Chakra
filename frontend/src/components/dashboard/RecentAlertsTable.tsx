import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { useApi } from '../../hooks/useApi';
import { fetchAlerts } from '../../services/alertService';
import RiskBadge from '../common/RiskBadge';
import StatusBadge from '../common/StatusBadge';
import { timeAgo, formatCurrency } from '../../utils/formatters';
import { LoadingTable } from '../common/LoadingState';

export default function RecentAlertsTable() {
  const { data, loading, error } = useApi(() => fetchAlerts(1, 6), []);
  const alerts = data?.items ?? [];

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
      <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
        <div>
          <div className="text-sm font-semibold text-gray-900 font-['Poppins']">Recent Alerts</div>
          <div className="text-xs text-gray-400 mt-0.5 font-['Inter']">Latest AML detection events</div>
        </div>
        <Link to="/alerts" className="text-xs text-blue-600 hover:text-blue-700 flex items-center gap-1 font-['Inter'] font-medium">
          View all <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {loading ? (
        <LoadingTable rows={6} cols={5} />
      ) : error ? (
        <div className="p-8 text-center text-sm text-gray-400">Unable to load alerts</div>
      ) : alerts.length === 0 ? (
        <div className="p-8 text-center text-sm text-gray-400">No alerts found</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm font-['Inter']">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                {['Alert ID', 'Account', 'Pattern', 'Risk', 'Score', 'Time', 'Status', ''].map((h) => (
                  <th key={h} className="text-left px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {alerts.map((alert) => (
                <tr key={alert.alert_id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-mono text-xs text-gray-800 font-semibold">{alert.alert_id}</td>
                  <td className="px-4 py-3 text-xs text-gray-600">{alert.account_id ?? '—'}</td>
                  <td className="px-4 py-3 text-xs text-gray-600 max-w-[140px] truncate">{alert.alert_type ?? '—'}</td>
                  <td className="px-4 py-3"><RiskBadge level={alert.risk_level} size="sm" /></td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-800">{alert.risk_score?.toFixed(0) ?? '—'}</td>
                  <td className="px-4 py-3 text-xs text-gray-400 whitespace-nowrap">{timeAgo(alert.created_at)}</td>
                  <td className="px-4 py-3"><StatusBadge status={alert.status} /></td>
                  <td className="px-4 py-3">
                    <Link to={`/alerts/${alert.alert_id}`} className="text-xs text-blue-600 hover:underline font-medium">View</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
