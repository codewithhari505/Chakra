import React from 'react';
import { useApi } from '../hooks/useApi';
import { getOverview, getRiskDistribution } from '../services/analyticsService';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from 'recharts';
import { LoadingCards } from '../components/common/LoadingState';

const PATTERNS = [
  { name: 'Structuring / Smurfing', value: 38, color: '#DC2626' },
  { name: 'Layering Chain', value: 27, color: '#EA580C' },
  { name: 'Rapid Velocity Burst', value: 21, color: '#F97316' },
  { name: 'Circular Transfer', value: 18, color: '#FB923C' },
  { name: 'Unusual Counterparty', value: 14, color: '#2563EB' },
  { name: 'High Fan-Out Hub', value: 9, color: '#3B82F6' },
];

export default function Analytics() {
  const { data: overview, loading } = useApi(() => getOverview(), []);
  const { data: riskDist } = useApi(() => getRiskDistribution(), []);

  const riskData = riskDist ? Object.entries(riskDist.transactions).map(([level, count]) => ({ level, count })) : [];
  const RISK_COLORS: Record<string, string> = { LOW: '#2563EB', MEDIUM: '#F97316', HIGH: '#EA580C', CRITICAL: '#DC2626' };

  return (
    <div className="space-y-6">
      {/* KPI Summary */}
      {loading ? <LoadingCards count={4} /> : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'Total Transactions', val: overview?.total_transactions?.toLocaleString('en-IN') ?? '—' },
            { label: 'Suspicious Rate', val: `${overview?.suspicion_rate ?? 0}%` },
            { label: 'High-Risk Accounts', val: overview?.high_risk_accounts?.toLocaleString('en-IN') ?? '—' },
            { label: 'Open Cases', val: overview?.open_investigations?.toLocaleString('en-IN') ?? '—' },
          ].map(({ label, val }) => (
            <div key={label} className="bg-white border border-gray-200 rounded-xl p-5">
              <div className="text-xs text-gray-500 font-['Inter'] uppercase tracking-wide">{label}</div>
              <div className="text-2xl font-bold text-gray-900 font-mono mt-1.5">{val}</div>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Distribution Chart */}
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <div className="text-sm font-semibold text-gray-900 font-['Poppins'] mb-1">Transaction Risk Distribution</div>
          <div className="text-xs text-gray-400 font-['Inter'] mb-4">Count by risk tier</div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={riskData} margin={{ left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" vertical={false} />
              <XAxis dataKey="level" tick={{ fontSize: 11, fill: '#94A3B8', fontFamily: 'Inter' }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fontSize: 11, fill: '#94A3B8' }} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #E5E7EB' }} />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {riskData.map((entry) => (
                  <Cell key={entry.level} fill={RISK_COLORS[entry.level] ?? '#94A3B8'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Pattern Distribution */}
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="text-sm font-semibold text-gray-900 font-['Poppins']">Suspicious Pattern Distribution</div>
              <div className="text-xs text-gray-400 font-['Inter'] mt-0.5">Detected AML typologies</div>
            </div>
            <span className="text-[10px] bg-orange-50 text-orange-600 border border-orange-200 px-2 py-0.5 rounded font-mono">DEMO DATA</span>
          </div>
          <div className="space-y-3">
            {PATTERNS.map((p) => (
              <div key={p.name}>
                <div className="flex items-center justify-between text-xs mb-1 font-['Inter']">
                  <span className="text-gray-600">{p.name}</span>
                  <span className="font-semibold text-gray-800">{p.value}%</span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full rounded-full transition-all" style={{ width: `${p.value}%`, background: p.color }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Network Stats */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <div className="text-sm font-semibold text-gray-900 font-['Poppins'] mb-4">Network Statistics</div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Account Nodes', val: '10,000', desc: 'Total monitored accounts' },
            { label: 'Transaction Edges', val: '20,000', desc: 'Seeded into graph engine' },
            { label: 'Suspicious Rate', val: `${overview?.suspicion_rate ?? 0}%`, desc: 'Pattern anomaly baseline' },
            { label: 'Graph Cycles', val: 'Active', desc: 'NetworkX cycle detection' },
          ].map(({ label, val, desc }) => (
            <div key={label} className="p-4 bg-gray-50 border border-gray-100 rounded-xl">
              <div className="text-[10px] text-gray-400 uppercase tracking-wide font-['Inter']">{label}</div>
              <div className="text-xl font-bold text-gray-900 font-mono mt-1">{val}</div>
              <div className="text-[10px] text-gray-400 mt-0.5 font-['Inter']">{desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
