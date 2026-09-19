import React from 'react';
import { getRiskBadgeClasses } from '../../utils/formatters';
import type { RiskLevel } from '../../types';

interface Props {
  level?: RiskLevel | string | null;
  size?: 'sm' | 'md';
}

export default function RiskBadge({ level, size = 'md' }: Props) {
  if (!level) return <span className="text-gray-400 text-xs">—</span>;
  const cls = getRiskBadgeClasses(level);
  const sz = size === 'sm' ? 'text-[10px] px-1.5 py-0.5' : 'text-xs px-2 py-0.5';
  return (
    <span className={`inline-flex items-center rounded border font-semibold font-mono ${sz} ${cls}`}>
      {level}
    </span>
  );
}
