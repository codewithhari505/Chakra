import React from 'react';
import { AlertTriangle } from 'lucide-react';

interface Props { message?: string; onRetry?: () => void }

export default function ErrorState({ message = 'Failed to load data.', onRetry }: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
      <AlertTriangle className="w-8 h-8 text-orange-400" />
      <div className="text-sm font-medium text-gray-700">{message}</div>
      <p className="text-xs text-gray-400">Check the API connection and try again.</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-2 px-4 py-2 text-xs font-semibold bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          Retry
        </button>
      )}
    </div>
  );
}
