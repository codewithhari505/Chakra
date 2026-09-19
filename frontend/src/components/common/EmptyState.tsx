import React from 'react';
import { Inbox } from 'lucide-react';

interface Props { title?: string; message?: string }

export default function EmptyState({ title = 'No data found', message = 'Try adjusting your filters.' }: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-2 text-center">
      <Inbox className="w-8 h-8 text-gray-300" />
      <div className="text-sm font-semibold text-gray-600">{title}</div>
      <p className="text-xs text-gray-400">{message}</p>
    </div>
  );
}
