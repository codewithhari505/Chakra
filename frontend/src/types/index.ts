export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type AlertStatus = 'NEW' | 'UNDER_REVIEW' | 'ESCALATED' | 'CLOSED';

export interface Transaction {
  id?: number;
  transaction_id: string;
  sender_account_id: string;
  receiver_account_id: string;
  amount: number;
  currency: string;
  transaction_type: string;
  timestamp: string;
  location?: string;
  channel?: string;
  device_id?: string;
  merchant_category?: string;
  is_suspicious: boolean;
  risk_score?: number;
  risk_level?: RiskLevel;
  detected_patterns?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Account {
  id?: number;
  account_id: string;
  account_type: string;
  country: string;
  city?: string;
  registration_date?: string;
  is_flagged: boolean;
  risk_score?: number;
  risk_level?: RiskLevel;
  total_transactions: number;
  total_inflow: number;
  total_outflow: number;
  unique_senders: number;
  unique_receivers: number;
  degree: number;
  in_degree: number;
  out_degree: number;
  cycle_count: number;
}

export interface Alert {
  id?: number;
  alert_id: string;
  transaction_id?: string;
  account_id?: string;
  risk_score?: number;
  risk_level?: RiskLevel;
  alert_type?: string;
  detected_patterns?: string;
  explanation?: string;
  top_features?: Record<string, number>;
  status: AlertStatus;
  assigned_to?: string;
  investigation_notes?: string;
  resolution?: string;
  created_at?: string;
  updated_at?: string;
  reviewed_at?: string;
  closed_at?: string;
}

export interface PaginatedResponse<T> {
  total: number;
  page: number;
  page_size: number;
  items: T[];
}

export interface HealthResponse {
  status: string;
  version: string;
  database: string;
  models_loaded: Record<string, boolean>;
  debug_mode: boolean;
}

export interface OverviewStats {
  total_transactions: number;
  suspicious_transactions: number;
  high_risk_accounts: number;
  open_investigations: number;
  suspicion_rate: number;
}

export interface RiskDistribution {
  transactions: Partial<Record<RiskLevel, number>>;
  accounts: Partial<Record<RiskLevel, number>>;
}

export interface GraphNode {
  id: string;
  label: string;
  is_suspicious: boolean;
  risk_level: string;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  amount: number;
  timestamp: string;
  is_suspicious: boolean;
  pattern: string;
}

export interface NetworkGraph {
  status: string;
  nodes_count: number;
  edges_count: number;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface RiskAnalysis {
  transaction_id: string;
  final_risk_score: number;
  risk_level: RiskLevel;
  component_scores: {
    ml_score: number;
    anomaly_score: number;
    rule_score: number;
    network_score: number;
  };
  triggered_rules: Array<string | { rule_name: string; severity: string; description?: string }>;
  feature_attributions: Record<string, number>;
  explanation_summary: string;
}

export interface InvestigationSummary {
  active_cases: number;
  pending_triage: number;
  escalated_cases: number;
  closed_cases: number;
  caseload_breakdown: Record<string, number>;
}

export interface AuditEvent {
  timestamp: string;
  action: string;
  actor: string;
  previous_status?: string;
  new_status?: string;
  notes?: string;
}

export interface AuditTrail {
  alert_id: string;
  total_events: number;
  events: AuditEvent[];
}
