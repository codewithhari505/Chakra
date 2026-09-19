import React, { useState, useEffect } from "react";
import { fetchAnalyticsOverview, fetchRiskDistribution, fetchTransactions } from "../services/api";

export default function DashboardPage({ onSelectTransaction }) {
  const [overview, setOverview] = useState(null);
  const [riskDist, setRiskDist] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterSuspicious, setFilterSuspicious] = useState(false);

  useEffect(() => {
    loadData();
  }, [filterSuspicious]);

  async function loadData() {
    try {
      setLoading(true);
      const [ov, dist, txs] = await Promise.all([
        fetchAnalyticsOverview().catch(() => null),
        fetchRiskDistribution().catch(() => null),
        fetchTransactions(1, 20, filterSuspicious ? { is_suspicious: true } : {}).catch(() => ({ items: [] }))
      ]);
      setOverview(ov);
      setRiskDist(dist);
      setTransactions(txs.items || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  const kpis = [
    {
      title: "Total Transactions Monitored",
      value: overview?.total_transactions?.toLocaleString("en-IN") || "—",
      subtext: "10,000 Connected Accounts",
      bg: "bg-indigo-50",
      border: "border-indigo-200",
      text: "text-indigo-700",
      badge: "bg-indigo-100 text-indigo-600",
    },
    {
      title: "Flagged Suspicious Patterns",
      value: overview?.suspicious_transactions?.toLocaleString("en-IN") || "—",
      subtext: `${overview?.suspicion_rate || "0"}% anomaly baseline rate`,
      bg: "bg-rose-50",
      border: "border-rose-200",
      text: "text-rose-700",
      badge: "bg-rose-100 text-rose-600",
    },
    {
      title: "High / Critical Risk Entities",
      value: overview?.high_risk_accounts?.toLocaleString("en-IN") || "—",
      subtext: "Ego-network cycles & smurfing hubs",
      bg: "bg-amber-50",
      border: "border-amber-200",
      text: "text-amber-700",
      badge: "bg-amber-100 text-amber-600",
    },
    {
      title: "Active Investigation Caseload",
      value: overview?.open_investigations?.toLocaleString("en-IN") || "—",
      subtext: "PMLA / RBI Compliance Queue",
      bg: "bg-emerald-50",
      border: "border-emerald-200",
      text: "text-emerald-700",
      badge: "bg-emerald-100 text-emerald-600",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Legal & Regulatory Disclaimer Alert */}
      <div className="p-3.5 rounded-lg border border-amber-300 bg-amber-50 text-amber-800 text-xs flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-bold tracking-wide uppercase px-2 py-0.5 rounded bg-amber-200 text-amber-800">
            Investigator Notice
          </span>
          <span>
            Model scores and flagged typologies indicate pattern anomalies for human intelligence triage. They do not constitute legal determinations of money laundering.
          </span>
        </div>
        <span className="font-mono text-[11px] text-amber-700 ml-4 whitespace-nowrap">PMLA 2002 / RBI 2026</span>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((kpi, idx) => (
          <div
            key={idx}
            className={`p-4 rounded-xl border ${kpi.border} ${kpi.bg} shadow-sm`}
          >
            <div className={`text-xs font-semibold ${kpi.text}`}>{kpi.title}</div>
            <div className="text-2xl font-bold tracking-tight text-gray-900 mt-1.5 font-mono">{kpi.value}</div>
            <div className={`text-[11px] mt-1.5 px-2 py-0.5 rounded-full inline-block font-medium ${kpi.badge}`}>{kpi.subtext}</div>
          </div>
        ))}
      </div>

      {/* Transactions Table Section */}
      <div className="border border-gray-200 rounded-xl bg-white overflow-hidden shadow-sm">
        <div className="p-4 border-b border-gray-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-gray-50">
          <div>
            <h2 className="text-sm font-bold text-gray-900 tracking-tight">Real-Time Transaction Stream</h2>
            <p className="text-xs text-gray-500 mt-0.5">Live feed ingested across banking channels &amp; switches</p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setFilterSuspicious(!filterSuspicious)}
              className={`px-3 py-1.5 rounded text-xs font-medium border transition ${
                filterSuspicious
                  ? "bg-rose-50 border-rose-300 text-rose-700"
                  : "bg-white border-gray-300 text-gray-700 hover:bg-gray-50"
              }`}
            >
              {filterSuspicious ? "Showing Suspicious Only" : "Show All Transactions"}
            </button>
            <button
              onClick={loadData}
              className="px-3 py-1.5 rounded text-xs font-medium bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 transition"
            >
              Refresh
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-gray-50 text-gray-500 font-mono text-[11px] uppercase border-b border-gray-200">
              <tr>
                <th className="py-3 px-4">Txn ID</th>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">Remitter</th>
                <th className="py-3 px-4">Beneficiary</th>
                <th className="py-3 px-4 text-right">Amount (INR)</th>
                <th className="py-3 px-4">Channel</th>
                <th className="py-3 px-4">Pattern / Status</th>
                <th className="py-3 px-4 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 font-mono text-gray-700">
              {loading ? (
                <tr>
                  <td colSpan="8" className="text-center py-8 text-gray-400">
                    Loading transactions from banking engine...
                  </td>
                </tr>
              ) : transactions.length === 0 ? (
                <tr>
                  <td colSpan="8" className="text-center py-8 text-gray-400">
                    No transactions found in queue.
                  </td>
                </tr>
              ) : (
                transactions.map((tx) => (
                  <tr
                    key={tx.transaction_id}
                    className={`hover:bg-indigo-50/50 transition cursor-pointer ${
                      tx.is_suspicious ? "bg-rose-50/40" : "bg-white"
                    }`}
                    onClick={() => onSelectTransaction(tx)}
                  >
                    <td className="py-3 px-4 font-bold text-gray-900">{tx.transaction_id}</td>
                    <td className="py-3 px-4 text-gray-500">{tx.timestamp?.replace("T", " ").substring(0, 19)}</td>
                    <td className="py-3 px-4 text-indigo-600 font-semibold">{tx.sender_account_id}</td>
                    <td className="py-3 px-4 text-cyan-700 font-semibold">{tx.receiver_account_id}</td>
                    <td className="py-3 px-4 text-right font-bold text-gray-900">
                      ₹{parseFloat(tx.amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 text-gray-500">{tx.channel || "ONLINE"}</td>
                    <td className="py-3 px-4">
                      {tx.is_suspicious ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-700 border border-rose-200">
                          {tx.detected_patterns || "ANOMALY"}
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-100 text-emerald-700 border border-emerald-200">
                          NORMAL
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectTransaction(tx);
                        }}
                        className="text-xs text-indigo-600 hover:text-indigo-800 font-semibold underline"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
