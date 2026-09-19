import api from './api';
import type { PaginatedResponse, Transaction, RiskAnalysis } from '../types';

export interface TransactionFilters {
  risk_level?: string;
  is_suspicious?: boolean;
  sender_account?: string;
  receiver_account?: string;
}

export async function fetchTransactions(
  page = 1,
  page_size = 50,
  filters: TransactionFilters = {}
): Promise<PaginatedResponse<Transaction>> {
  const params: Record<string, any> = { page, page_size, ...filters };
  Object.keys(params).forEach((k) => params[k] === undefined && delete params[k]);
  const res = await api.get('/api/v1/transactions', { params });
  return res.data;
}

export async function getTransaction(id: string): Promise<Transaction> {
  const res = await api.get(`/api/v1/transactions/${id}`);
  return res.data;
}

export async function analyzeTransaction(tx: Partial<Transaction>): Promise<{ status: string; analysis: RiskAnalysis }> {
  const res = await api.post('/api/v1/transactions/analyze', { transaction: tx, include_graph: false, include_explanation: true });
  return res.data;
}
