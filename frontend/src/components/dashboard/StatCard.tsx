import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface Props {
  title: string;
  value: string | number;
  subtext?: string;
  trend?: number;
  loading?: boolean;
  accent?: 'blue' | 'orange' | 'green' | 'gray';
}

const ACCENTS = {
  blue:   'border-blue-200 bg-blue-50',
  orange: 'border-orange-200 bg-orange-50',
  green:  'border-green-200 bg-green-50',
  gray:   'border-gray-200 bg-white',
};

export default function StatCard({ title, value, subtext, trend, loading, accent = 'gray' }: Props) {
  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-5 animate-pulse space-y-3">
        <div className="h-3 bg-gray-100 rounded w-2/3" />
        <div className="h-7 bg-gray-100 rounded w-1/2" />
        <div className="h-3 bg-gray-100 rounded w-1/3" />
      </div>
    );
  }

  return (
    <div className={`border rounded-xl p-5 space-y-1.5 ${ACCENTS[accent]}`}>
      <div className="text-xs font-medium text-gray-500 font-['Inter'] uppercase tracking-wide">{title}</div>
      <div className="text-2xl font-semibold text-gray-900 font-['Poppins']">{value}</div>
      <div className="flex items-center gap-1.5">
        {trend !== undefined && (
          <span className={`flex items-center gap-0.5 text-xs font-semibold ${trend >= 0 ? 'text-orange-500' : 'text-green-600'}`}>
            {trend >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
            {Math.abs(trend).toFixed(1)}%
          </span>
        )}
        {subtext && <span className="text-xs text-gray-400 font-['Inter']">{subtext}</span>}
      </div>
    </div>
  );
}
