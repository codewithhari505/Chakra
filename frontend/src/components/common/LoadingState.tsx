import React from 'react';

export function LoadingTable({ rows = 8, cols = 6 }: { rows?: number; cols?: number }) {
  return (
    <div className="animate-pulse space-y-2 p-4">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4">
          {Array.from({ length: cols }).map((_, j) => (
            <div key={j} className="h-4 bg-gray-100 rounded flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}

export function LoadingCards({ count = 4 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="bg-white border border-gray-200 rounded-xl p-5 animate-pulse space-y-3">
          <div className="h-3 bg-gray-100 rounded w-2/3" />
          <div className="h-7 bg-gray-100 rounded w-1/2" />
          <div className="h-3 bg-gray-100 rounded w-1/3" />
        </div>
      ))}
    </div>
  );
}

export function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center py-16">
      <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
    </div>
  );
}
