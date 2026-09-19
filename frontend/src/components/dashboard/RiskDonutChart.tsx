import React from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import type { RiskDistribution } from '../../types';

interface Props { data?: RiskDistribution | null; loading?: boolean }

const COLORS: Record<string, string> = {
  LOW: '#2563EB',
  MEDIUM: '#F97316',
  HIGH: '#EA580C',
  CRITICAL: '#DC2626',
};

export default function RiskDonutChart({ data, loading }: Props) {
  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-5 h-64 animate-pulse flex items-center justify-center">
        <div className="w-32 h-32 rounded-full border-8 border-gray-100" />
      </div>
    );
  }

  const txns = data?.transactions ?? {};
  const chartData = Object.entries(txns).map(([level, count]) => ({ name: level, value: count }));

  if (!chartData.length) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-5 h-64 flex items-center justify-center text-sm text-gray-400">
        No risk data available
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <div className="text-sm font-semibold text-gray-900 font-['Poppins'] mb-1">Risk Distribution</div>
      <div className="text-xs text-gray-400 font-['Inter'] mb-3">Transaction risk level breakdown</div>
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie data={chartData} cx="50%" cy="50%" innerRadius={52} outerRadius={80} paddingAngle={3} dataKey="value">
            {chartData.map((entry) => (
              <Cell key={entry.name} fill={COLORS[entry.name] ?? '#94A3B8'} />
            ))}
          </Pie>
          <Tooltip
            formatter={(val: number) => [val.toLocaleString('en-IN'), 'Transactions']}
            contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #E5E7EB' }}
          />
          <Legend formatter={(v) => <span className="text-xs text-gray-600 font-['Inter']">{v}</span>} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
