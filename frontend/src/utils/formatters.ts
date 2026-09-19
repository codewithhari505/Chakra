import type { RiskLevel } from '../types';

export function formatCurrency(amount: number, currency = 'INR'): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(amount);
}

export function formatDate(iso?: string | null): string {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatDateShort(iso?: string | null): string {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

export function timeAgo(iso?: string | null): string {
  if (!iso) return '—';
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

export function getRiskBadgeClasses(level?: RiskLevel | string | null): string {
  switch (level) {
    case 'CRITICAL': return 'bg-red-50 text-red-700 border-red-200';
    case 'HIGH':     return 'bg-orange-100 text-orange-700 border-orange-300';
    case 'MEDIUM':   return 'bg-orange-50 text-orange-600 border-orange-200';
    case 'LOW':      return 'bg-blue-50 text-blue-700 border-blue-200';
    default:         return 'bg-gray-100 text-gray-600 border-gray-200';
  }
}

export function getRiskBarColor(level?: RiskLevel | string | null): string {
  switch (level) {
    case 'CRITICAL': return 'bg-red-500';
    case 'HIGH':     return 'bg-orange-500';
    case 'MEDIUM':   return 'bg-orange-400';
    case 'LOW':      return 'bg-blue-500';
    default:         return 'bg-gray-400';
  }
}

export function scoreToLevel(score: number): RiskLevel {
  if (score >= 80) return 'CRITICAL';
  if (score >= 60) return 'HIGH';
  if (score >= 30) return 'MEDIUM';
  return 'LOW';
}

export function getStatusBadgeClasses(status: string): string {
  switch (status) {
    case 'NEW':          return 'bg-blue-50 text-blue-700 border-blue-200';
    case 'UNDER_REVIEW': return 'bg-orange-50 text-orange-600 border-orange-200';
    case 'ESCALATED':    return 'bg-red-50 text-red-700 border-red-200';
    case 'CLOSED':       return 'bg-gray-100 text-gray-600 border-gray-200';
    default:             return 'bg-gray-100 text-gray-600 border-gray-200';
  }
}
