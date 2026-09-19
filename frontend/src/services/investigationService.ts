import api from './api';
import type { InvestigationSummary, AuditTrail } from '../types';

export async function getInvestigationSummary(): Promise<InvestigationSummary> {
  const res = await api.get('/api/v1/investigations/summary');
  return res.data;
}

export async function assignAlert(alert_id: string, assigned_investigator: string, notes?: string) {
  const res = await api.post('/api/v1/investigations/assign', { alert_id, assigned_investigator, notes });
  return res.data;
}

export async function escalateAlert(alert_id: string, assigned_investigator: string, escalation_reason: string) {
  const res = await api.post('/api/v1/investigations/escalate', { alert_id, assigned_investigator, escalation_reason });
  return res.data;
}

export async function closeCase(alert_id: string, resolution: string, investigation_notes: string, officer_name: string) {
  const res = await api.post('/api/v1/investigations/close', { alert_id, resolution, investigation_notes, officer_name });
  return res.data;
}

export async function generateEDD(account_id: string, risk_level: string, typology: string) {
  const res = await api.post('/api/v1/investigations/edd', { account_id, risk_level, typology });
  return res.data;
}

export async function getAuditTrail(alert_id: string): Promise<AuditTrail> {
  const res = await api.get(`/api/v1/investigations/${alert_id}/audit-trail`);
  return res.data;
}
