/**
 * Frontend API Service — communicates with FastAPI backend.
 */

const API_BASE = "/api/v1";

export async function fetchAnalyticsOverview() {
  const res = await fetch(`${API_BASE}/analytics/overview`);
  if (!res.ok) throw new Error("Failed to fetch analytics overview");
  return res.json();
}

export async function fetchRiskDistribution() {
  const res = await fetch(`${API_BASE}/analytics/risk-distribution`);
  if (!res.ok) throw new Error("Failed to fetch risk distribution");
  return res.json();
}

export async function fetchTransactionNetwork(accountId = null, limitNodes = 30) {
  const url = accountId
    ? `${API_BASE}/analytics/transaction-network?account_id=${accountId}&limit_nodes=${limitNodes}`
    : `${API_BASE}/analytics/transaction-network?limit_nodes=${limitNodes}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch transaction network");
  return res.json();
}

export async function fetchTransactions(page = 1, pageSize = 20, filters = {}) {
  const params = new URLSearchParams({ page, page_size: pageSize });
  if (filters.risk_level) params.append("risk_level", filters.risk_level);
  if (filters.is_suspicious !== undefined) params.append("is_suspicious", filters.is_suspicious);

  const res = await fetch(`${API_BASE}/transactions?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch transactions");
  return res.json();
}

export async function fetchAlerts(page = 1, pageSize = 20, status = null) {
  const params = new URLSearchParams({ page, page_size: pageSize });
  if (status) params.append("status", status);

  const res = await fetch(`${API_BASE}/alerts?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch alerts");
  return res.json();
}

export async function updateAlertStatus(alertId, updateData) {
  const res = await fetch(`${API_BASE}/alerts/${alertId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updateData),
  });
  if (!res.ok) throw new Error("Failed to update alert");
  return res.json();
}

export async function analyzeTransaction(transactionPayload) {
  const res = await fetch(`${API_BASE}/transactions/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      transaction: transactionPayload,
      include_graph: true,
      include_explanation: true,
    }),
  });
  if (!res.ok) throw new Error("Failed to analyze transaction");
  return res.json();
}
