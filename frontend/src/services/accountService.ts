import api from './api';
import type { Account, PaginatedResponse, Transaction } from '../types';

export async function fetchAccounts(
  page = 1,
  page_size = 50,
  filters: { risk_level?: string; is_flagged?: boolean } = {}
): Promise<PaginatedResponse<Account>> {
  const params: Record<string, any> = { page, page_size, ...filters };
  Object.keys(params).forEach((k) => params[k] === undefined && delete params[k]);
  const res = await api.get('/api/v1/accounts', { params });
  return res.data;
}

export async function getAccount(id: string): Promise<Account> {
  const res = await api.get(`/api/v1/accounts/${id}`);
  return res.data;
}

export async function getAccountTransactions(
  id: string,
  page = 1,
  page_size = 20
): Promise<PaginatedResponse<Transaction>> {
  const res = await api.get(`/api/v1/accounts/${id}/transactions`, { params: { page, page_size } });
  return res.data;
}
