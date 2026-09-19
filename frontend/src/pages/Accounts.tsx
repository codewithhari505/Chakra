import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { fetchAccounts } from '../services/accountService';
import RiskBadge from '../components/common/RiskBadge';
import { LoadingTable } from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import EmptyState from '../components/common/EmptyState';
import { formatCurrency, formatDate } from '../utils/formatters';

const RISK_LEVELS = ['ALL', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];

export default function Accounts() {
  const [page, setPage] = useState(1);
  const [riskFilter, setRiskFilter] = useState('ALL');
  const [flaggedOnly, setFlaggedOnly] = useState(false);

  const { data, loading, error, refetch } = useApi(
    () => fetchAccounts(page, 30, {
      risk_level: riskFilter !== 'ALL' ? riskFilter : undefined,
      is_flagged: flaggedOnly ? true : undefined,
    }),
    [page, riskFilter, flaggedOnly]
  );

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / 30);

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="bg-white border border-gray-200 rounded-xl p-4 flex flex-wrap gap-3 items-center">
        <div className="flex items-center gap-1">
          {RISK_LEVELS.map((lvl) => (
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
        </div>
        <button
          onClick={() => { setFlaggedOnly(!flaggedOnly); setPage(1); }}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition font-['Inter'] ${
            flaggedOnly ? 'bg-orange-100 text-orange-700 border-orange-300' : 'bg-white text-gray-600 border-gray-200'
          }`}
        >
          Flagged Only
        </button>
        <span className="text-xs text-gray-400 font-['Inter'] ml-auto">{total.toLocaleString('en-IN')} accounts</span>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        {loading ? <LoadingTable rows={10} cols={8} /> :
         error ? <ErrorState message="Failed to load accounts" onRetry={refetch} /> :
         items.length === 0 ? <EmptyState title="No accounts found" /> : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm font-['Inter']">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  {['Account ID', 'Type', 'Country', 'Transactions', 'Total Inflow', 'Total Outflow', 'Risk Score', 'Risk Level', 'Flagged'].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {items.map((acc) => (
                  <tr
                    key={acc.account_id}
                    className="hover:bg-blue-50/30 transition-colors cursor-pointer"
                    onClick={() => window.location.href = `/accounts/${acc.account_id}`}
                  >
                    <td className="px-4 py-3">
                      <Link to={`/accounts/${acc.account_id}`} onClick={(e) => e.stopPropagation()} className="font-mono text-xs text-blue-700 font-semibold hover:underline">
                        {acc.account_id}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-600">{acc.account_type}</td>
                    <td className="px-4 py-3 text-xs text-gray-600">{acc.country}</td>
                    <td className="px-4 py-3 text-xs font-mono text-gray-800">{acc.total_transactions.toLocaleString('en-IN')}</td>
                    <td className="px-4 py-3 text-xs font-mono text-gray-800">{formatCurrency(acc.total_inflow)}</td>
                    <td className="px-4 py-3 text-xs font-mono text-gray-800">{formatCurrency(acc.total_outflow)}</td>
                    <td className="px-4 py-3 text-xs font-mono font-semibold text-gray-900">{acc.risk_score?.toFixed(1) ?? '—'}</td>
                    <td className="px-4 py-3"><RiskBadge level={acc.risk_level} size="sm" /></td>
                    <td className="px-4 py-3">
                      {acc.is_flagged && <span className="text-xs bg-orange-50 text-orange-600 border border-orange-200 px-2 py-0.5 rounded font-semibold">Flagged</span>}
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
