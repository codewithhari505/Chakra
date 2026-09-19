import React from 'react';
import { useApi } from '../hooks/useApi';
import { getOverview, getRiskDistribution } from '../services/analyticsService';
import StatCard from '../components/dashboard/StatCard';
import RiskDonutChart from '../components/dashboard/RiskDonutChart';
import ActivityChart from '../components/dashboard/ActivityChart';
import RecentAlertsTable from '../components/dashboard/RecentAlertsTable';
import { formatCurrency } from '../utils/formatters';
import { useAuth, PORTAL_CONFIGS } from '../context/AuthContext';
import { Building2, ShieldCheck, Landmark, AlertCircle, ArrowUpRight } from 'lucide-react';

export default function Dashboard() {
  const { portal, user } = useAuth();
  const config = PORTAL_CONFIGS[portal];
  const { data: overview, loading: ovLoading } = useApi(() => getOverview(), []);
  const { data: riskDist, loading: distLoading } = useApi(() => getRiskDistribution(), []);

  return (
    <div className="space-y-6 font-['Inter']">
      {/* Portal Operational Header Banner */}
      <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div
            className="w-12 h-12 rounded-xl flex items-center justify-center text-white shrink-0 shadow-sm"
            style={{ backgroundColor: config.primaryColor }}
          >
            {portal === 'bank' && <Building2 className="w-6 h-6" />}
            {portal === 'cybersecurity' && <ShieldCheck className="w-6 h-6" />}
            {portal === 'rbi' && <Landmark className="w-6 h-6" />}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-gray-900 font-['Poppins']">
                {config.name}
              </h2>
              <span className={`text-[10px] font-bold uppercase font-mono px-2 py-0.5 rounded-full border ${config.badgeColor}`}>
                {config.authority}
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-0.5 leading-relaxed max-w-2xl">
              {config.description}
            </p>
          </div>
        </div>

        <div className="text-right shrink-0 border-t sm:border-t-0 sm:border-l border-gray-100 pt-3 sm:pt-0 sm:pl-4">
          <div className="text-[10px] uppercase font-bold text-gray-400">Officer Clearance</div>
          <div className="text-xs font-bold text-gray-900 font-mono mt-0.5">{user?.clearanceLevel}</div>
          <div className="text-[11px] text-gray-500 font-mono mt-0.5">{user?.badge}</div>
        </div>
      </div>

      {/* Legal & Regulatory Disclaimer */}
      <div className="flex items-center gap-3 px-4 py-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800">
        <span className="font-bold uppercase tracking-wide bg-amber-200 text-amber-900 px-2 py-0.5 rounded shrink-0">
          Investigator Notice
        </span>
        <span className="text-[11px] leading-snug">
          Model scores indicate pattern anomalies for human intelligence triage. They do not constitute legal determinations of money laundering. — PMLA 2002 / RBI KYC 2026 / CERT-In Framework.
        </span>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Transactions"
          value={overview ? overview.total_transactions.toLocaleString('en-IN') : '—'}
          subtext="10,000 connected accounts"
          trend={8.4}
          loading={ovLoading}
          accent="gray"
        />
        <StatCard
          title="Suspicious Transactions"
          value={overview ? overview.suspicious_transactions.toLocaleString('en-IN') : '—'}
          subtext={`${overview?.suspicion_rate ?? 0}% anomaly rate`}
          trend={12.1}
          loading={ovLoading}
          accent="orange"
        />
        <StatCard
          title="High-Risk Accounts"
          value={overview ? overview.high_risk_accounts.toLocaleString('en-IN') : '—'}
          subtext="HIGH + CRITICAL risk entities"
          trend={5.6}
          loading={ovLoading}
          accent="orange"
        />
        <StatCard
          title="Open Investigations"
          value={overview ? overview.open_investigations.toLocaleString('en-IN') : '—'}
          subtext="NEW + ESCALATED caseload"
          trend={3.2}
          loading={ovLoading}
          accent="blue"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <ActivityChart />
        </div>
        <RiskDonutChart data={riskDist} loading={distLoading} />
      </div>

      {/* Recent Alerts Table */}
      <RecentAlertsTable />
    </div>
  );
}
