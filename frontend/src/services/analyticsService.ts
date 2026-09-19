import api from './api';
import type { OverviewStats, RiskDistribution, NetworkGraph, HealthResponse } from '../types';

export async function getHealth(): Promise<HealthResponse> {
  const res = await api.get('/health');
  return res.data;
}

export async function getOverview(): Promise<OverviewStats> {
  const res = await api.get('/api/v1/analytics/overview');
  return res.data;
}

export async function getRiskDistribution(): Promise<RiskDistribution> {
  const res = await api.get('/api/v1/analytics/risk-distribution');
  return res.data;
}

export async function getTransactionNetwork(account_id?: string, limit_nodes = 50): Promise<NetworkGraph> {
  const params: Record<string, any> = { limit_nodes };
  if (account_id) params.account_id = account_id;
  const res = await api.get('/api/v1/analytics/transaction-network', { params });
  return res.data;
}
