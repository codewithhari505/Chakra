import React, { useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Search, Filter, ChevronLeft, ChevronRight } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { fetchTransactions } from '../services/transactionService';
import { useDebounce } from '../hooks/useDebounce';
import RiskBadge from '../components/common/RiskBadge';
import { LoadingTable } from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import EmptyState from '../components/common/EmptyState';
import { formatCurrency, formatDate } from '../utils/formatters';

import JellyRadio from '../components/common/JellyRadio';

const RISK_LEVELS = ['ALL', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];

export default function Transactions() {
  const [page, setPage] = useState(1);
  const [riskFilter, setRiskFilter] = useState('ALL');
  const [suspFilter, setSuspFilter] = useState<boolean | undefined>(undefined);
  const [search, setSearch] = useState('');
  const debSearch = useDebounce(search, 350);

  const { data, loading, error, refetch } = useApi(
    () => fetchTransactions(page, 30, {
      risk_level: riskFilter !== 'ALL' ? riskFilter : undefined,
      is_suspicious: suspFilter,
      sender_account: debSearch.startsWith('ACC') ? debSearch : undefined,
    }),
    [page, riskFilter, suspFilter, debSearch]
  );

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / 30);

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="bg-white border border-gray-200 rounded-xl p-4 flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-[200px] max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search by account ID..."
            className="w-full pl-9 pr-3 py-1.5 text-sm bg-gray-50 border border-gray-200 rounded-lg font-['Inter'] focus:outline-none focus:border-blue-400"
          />
        </div>

        <div className="flex items-center">
          <JellyRadio
            items={RISK_LEVELS}
            value={riskFilter}
            onChange={(val: string) => { setRiskFilter(val); setPage(1); }}
            chipColor="#F3F4F6"
            activeColor="#2563EB"
            textColor="#374151"
            activeTextColor="#FFFFFF"
            size="sm"
            radius={8}
          />
        </div>

        <button
          onClick={() => { setSuspFilter(suspFilter === true ? undefined : true); setPage(1); }}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition font-['Inter'] ${
            suspFilter === true ? 'bg-orange-100 text-orange-700 border-orange-300' : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'
          }`}
        >
          Suspicious Only
        </button>

        <span className="text-xs text-gray-400 font-['Inter'] ml-auto">{total.toLocaleString('en-IN')} results</span>
      </div>

      {/* Table */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        {loading ? (
          <LoadingTable rows={10} cols={8} />
        ) : error ? (
          <ErrorState message="Failed to load transactions" onRetry={refetch} />
        ) : items.length === 0 ? (
          <EmptyState title="No transactions found" message="Try adjusting your filters." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm font-['Inter']">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  {['Transaction ID', 'Sender', 'Receiver', 'Amount', 'Type', 'Channel', 'Timestamp', 'Risk', 'Status'].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {items.map((tx) => (
                  <tr
                    key={tx.transaction_id}
                    className="hover:bg-blue-50/30 transition-colors cursor-pointer"
                    onClick={() => window.location.href = `/transactions/${tx.transaction_id}`}
                  >
                    <td className="px-4 py-3 font-mono text-xs font-semibold text-blue-700">
                      <Link to={`/transactions/${tx.transaction_id}`} onClick={(e) => e.stopPropagation()} className="hover:underline">
                        {tx.transaction_id}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-700 font-mono">{tx.sender_account_id}</td>
                    <td className="px-4 py-3 text-xs text-gray-700 font-mono">{tx.receiver_account_id}</td>
                    <td className="px-4 py-3 text-xs font-semibold text-gray-900 font-mono whitespace-nowrap">
                      {formatCurrency(tx.amount)}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-600">{tx.transaction_type}</td>
                    <td className="px-4 py-3 text-xs text-gray-500">{tx.channel ?? '—'}</td>
                    <td className="px-4 py-3 text-xs text-gray-400 whitespace-nowrap">{formatDate(tx.timestamp)}</td>
                    <td className="px-4 py-3">
                      <RiskBadge level={tx.risk_level} size="sm" />
                    </td>
                    <td className="px-4 py-3">
                      {tx.is_suspicious ? (
                        <span className="text-xs bg-orange-50 text-orange-600 border border-orange-200 px-2 py-0.5 rounded font-semibold">Suspicious</span>
                      ) : (
                        <span className="text-xs bg-gray-50 text-gray-500 border border-gray-200 px-2 py-0.5 rounded">Normal</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-5 py-3 border-t border-gray-100 bg-gray-50">
            <span className="text-xs text-gray-500 font-['Inter']">Page {page} of {totalPages}</span>
            <div className="flex items-center gap-1">
              <button
                disabled={page === 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="p-1.5 rounded-lg border border-gray-200 text-gray-600 hover:bg-white disabled:opacity-40 transition"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const pg = Math.max(1, Math.min(totalPages - 4, page - 2)) + i;
                return (
                  <button
                    key={pg}
                    onClick={() => setPage(pg)}
                    className={`w-8 h-8 rounded-lg text-xs font-semibold border transition ${pg === page ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-600 border-gray-200 hover:border-blue-300'}`}
                  >
                    {pg}
                  </button>
                );
              })}
              <button
                disabled={page === totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                className="p-1.5 rounded-lg border border-gray-200 text-gray-600 hover:bg-white disabled:opacity-40 transition"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
