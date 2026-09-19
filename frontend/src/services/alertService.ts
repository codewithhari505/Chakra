import api from './api';
import type { Alert, PaginatedResponse } from '../types';

export async function fetchAlerts(
  page = 1,
  page_size = 50,
  filters: { status?: string; risk_level?: string } = {}
): Promise<PaginatedResponse<Alert>> {
  const params: Record<string, any> = { page, page_size };
  if (filters.status) params.status = filters.status;
  if (filters.risk_level) params.risk_level = filters.risk_level;
  const res = await api.get('/api/v1/alerts', { params });
  return res.data;
}

export async function getAlert(id: string): Promise<Alert> {
  const res = await api.get(`/api/v1/alerts/${id}`);
  return res.data;
}

export async function updateAlert(
  id: string,
  update: { status?: string; assigned_to?: string; investigation_notes?: string; resolution?: string }
): Promise<Alert> {
  const res = await api.patch(`/api/v1/alerts/${id}`, update);
  return res.data;
}
