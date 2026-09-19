import React from 'react';
import { getStatusBadgeClasses } from '../../utils/formatters';

interface Props { status: string }

export default function StatusBadge({ status }: Props) {
  const cls = getStatusBadgeClasses(status);
  const labels: Record<string, string> = {
    NEW: 'New',
    UNDER_REVIEW: 'Under Review',
    ESCALATED: 'Escalated',
    CLOSED: 'Closed',
  };
  return (
    <span className={`inline-flex items-center rounded border text-xs px-2 py-0.5 font-semibold ${cls}`}>
      {labels[status] ?? status}
    </span>
  );
}
