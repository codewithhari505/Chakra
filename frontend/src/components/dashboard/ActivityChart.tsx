import React, { useMemo } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

function generateMockData() {
  const now = new Date();
  return Array.from({ length: 30 }, (_, i) => {
    const d = new Date(now);
    d.setDate(d.getDate() - (29 - i));
    const normal = 500 + Math.round(Math.random() * 300);
    const suspicious = 20 + Math.round(Math.random() * 60);
    return {
      date: d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' }),
      normal,
      suspicious,
    };
  });
}

export default function ActivityChart() {
  const data = useMemo(() => generateMockData(), []);

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="text-sm font-semibold text-gray-900 font-['Poppins']">Transaction Activity</div>
          <div className="text-xs text-gray-400 font-['Inter'] mt-0.5">30-day volume overview</div>
        </div>
        <span className="text-[10px] bg-orange-50 text-orange-600 border border-orange-200 px-2 py-0.5 rounded font-mono">DEMO DATA</span>
      </div>
      <ResponsiveContainer width="100%" height={180}>
        <AreaChart data={data} margin={{ left: -10, right: 4, top: 4, bottom: 0 }}>
          <defs>
            <linearGradient id="normalGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#2563EB" stopOpacity={0.15} />
              <stop offset="95%" stopColor="#2563EB" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="suspGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#F97316" stopOpacity={0.2} />
              <stop offset="95%" stopColor="#F97316" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" vertical={false} />
          <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#94A3B8' }} tickLine={false} axisLine={false} interval={4} />
          <YAxis tick={{ fontSize: 10, fill: '#94A3B8' }} tickLine={false} axisLine={false} />
          <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #E5E7EB' }} />
          <Area type="monotone" dataKey="normal" name="Normal" stroke="#2563EB" strokeWidth={2} fill="url(#normalGrad)" />
          <Area type="monotone" dataKey="suspicious" name="Suspicious" stroke="#F97316" strokeWidth={2} fill="url(#suspGrad)" />
        </AreaChart>
      </ResponsiveContainer>
      <div className="flex items-center gap-4 mt-2 text-xs font-['Inter']">
        <span className="flex items-center gap-1.5 text-gray-500"><span className="w-3 h-0.5 bg-blue-600 inline-block" /> Normal</span>
        <span className="flex items-center gap-1.5 text-gray-500"><span className="w-3 h-0.5 bg-orange-500 inline-block" /> Suspicious</span>
      </div>
    </div>
  );
}
