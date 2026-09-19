import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { getAccount, getAccountTransactions } from '../services/accountService';
import RiskBadge from '../components/common/RiskBadge';
import { LoadingSpinner, LoadingTable } from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import { formatCurrency, formatDate, getRiskBarColor, scoreToLevel } from '../utils/formatters';

export default function AccountDetails() {
  const { id } = useParams<{ id: string }>();
  const { data: acc, loading, error, refetch } = useApi(() => getAccount(id!), [id]);
  const { data: txData, loading: txLoading } = useApi(() => getAccountTransactions(id!, 1, 10), [id]);

  if (loading) return <LoadingSpinner />;
  if (error || !acc) return <ErrorState message="Account not found" onRetry={refetch} />;

  const inOut = acc.total_inflow + acc.total_outflow;
  const inflowPct = inOut > 0 ? (acc.total_inflow / inOut) * 100 : 50;

  return (
    <div className="space-y-5 max-w-5xl">
      <Link to="/accounts" className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-blue-600 font-['Inter'] transition">
        <ArrowLeft className="w-4 h-4" /> Back to Accounts
      </Link>

      {/* Profile Header */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-mono text-lg font-bold text-gray-900">{acc.account_id}</h2>
              <RiskBadge level={acc.risk_level} />
              {acc.is_flagged && <span className="text-xs bg-orange-50 text-orange-600 border border-orange-200 px-2 py-0.5 rounded font-semibold">Flagged</span>}
            </div>
            <p className="text-xs text-gray-400 font-['Inter'] mt-1">{acc.account_type} · {acc.country}{acc.city ? `, ${acc.city}` : ''}</p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-gray-900 font-mono">{acc.risk_score?.toFixed(1) ?? '—'}</div>
            <div className="text-xs text-gray-400 font-['Inter']">Risk Score / 100</div>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 mt-5 pt-5 border-t border-gray-100">
          {[
            { label: 'Total Txns', val: acc.total_transactions.toLocaleString('en-IN') },
            { label: 'Total Inflow', val: formatCurrency(acc.total_inflow) },
            { label: 'Total Outflow', val: formatCurrency(acc.total_outflow) },
            { label: 'Unique Senders', val: acc.unique_senders },
            { label: 'Unique Receivers', val: acc.unique_receivers },
            { label: 'Network Cycles', val: acc.cycle_count },
          ].map(({ label, val }) => (
            <div key={label}>
              <div className="text-[10px] text-gray-400 uppercase tracking-wide font-['Inter']">{label}</div>
              <div className="text-sm font-semibold text-gray-900 font-mono mt-0.5">{val}</div>
            </div>
          ))}
        </div>

        {/* Inflow/Outflow bar */}
        <div className="mt-4">
          <div className="flex justify-between text-xs text-gray-500 font-['Inter'] mb-1">
            <span>Inflow {inflowPct.toFixed(0)}%</span>
            <span>Outflow {(100 - inflowPct).toFixed(0)}%</span>
          </div>
          <div className="h-2 bg-gray-100 rounded-full overflow-hidden flex">
            <div className="bg-blue-500 h-full" style={{ width: `${inflowPct}%` }} />
            <div className="bg-orange-400 h-full flex-1" />
          </div>
        </div>
      </div>

      {/* Recent Transactions */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <div className="text-sm font-semibold text-gray-900 font-['Poppins']">Recent Transactions</div>
        </div>
        {txLoading ? <LoadingTable rows={6} cols={5} /> : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm font-['Inter']">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  {['Txn ID', 'Direction', 'Counterparty', 'Amount', 'Timestamp', 'Status'].map((h) => (
                    <th key={h} className="text-left px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {(txData?.items ?? []).map((tx) => {
                  const isOut = tx.sender_account_id === acc.account_id;
                  return (
                    <tr key={tx.transaction_id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <Link to={`/transactions/${tx.transaction_id}`} className="font-mono text-xs text-blue-700 font-semibold hover:underline">{tx.transaction_id}</Link>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`text-xs font-semibold ${isOut ? 'text-orange-600' : 'text-blue-600'}`}>{isOut ? '↑ Out' : '↓ In'}</span>
                      </td>
                      <td className="px-4 py-3 text-xs font-mono text-gray-600">{isOut ? tx.receiver_account_id : tx.sender_account_id}</td>
                      <td className="px-4 py-3 text-xs font-mono font-semibold text-gray-900">{formatCurrency(tx.amount)}</td>
                      <td className="px-4 py-3 text-xs text-gray-400">{formatDate(tx.timestamp)}</td>
                      <td className="px-4 py-3">
                        {tx.is_suspicious
                          ? <span className="text-xs bg-orange-50 text-orange-600 border border-orange-200 px-2 py-0.5 rounded font-semibold">Suspicious</span>
                          : <span className="text-xs bg-gray-50 text-gray-500 border border-gray-100 px-2 py-0.5 rounded">Normal</span>}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
