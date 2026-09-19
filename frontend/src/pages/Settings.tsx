import React from 'react';
import { useApi } from '../hooks/useApi';
import { getHealth } from '../services/analyticsService';
import { CheckCircle, XCircle, Server, Database, Cpu } from 'lucide-react';

export default function Settings() {
  const { data: health, loading, refetch } = useApi(() => getHealth(), []);

  return (
    <div className="space-y-6 max-w-3xl">
      {/* API Health */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="text-sm font-semibold text-gray-900 font-['Poppins']">System Health</div>
          <button onClick={refetch} className="text-xs text-blue-600 font-medium hover:underline font-['Inter']">Refresh</button>
        </div>

        {loading ? (
          <div className="animate-pulse space-y-3">
            {[1, 2, 3].map((i) => <div key={i} className="h-10 bg-gray-100 rounded-lg" />)}
          </div>
        ) : health ? (
          <div className="space-y-3">
            {[
              {
                icon: Server,
                label: 'API Service',
                value: `v${health.version}`,
                status: health.status === 'healthy',
                statusText: health.status,
              },
              {
                icon: Database,
                label: 'Database Connection',
                value: 'SQLite (Dev Mode)',
                status: health.database === 'connected',
                statusText: health.database,
              },
            ].map(({ icon: Icon, label, value, status, statusText }) => (
              <div key={label} className="flex items-center justify-between p-3.5 bg-gray-50 border border-gray-100 rounded-xl">
                <div className="flex items-center gap-3">
                  <Icon className="w-4 h-4 text-gray-500" />
                  <div>
                    <div className="text-sm font-semibold text-gray-800 font-['Inter']">{label}</div>
                    <div className="text-xs text-gray-400">{value}</div>
                  </div>
                </div>
                <div className="flex items-center gap-1.5">
                  {status ? <CheckCircle className="w-4 h-4 text-green-500" /> : <XCircle className="w-4 h-4 text-red-500" />}
                  <span className={`text-xs font-semibold font-['Inter'] capitalize ${status ? 'text-green-600' : 'text-red-500'}`}>{statusText}</span>
                </div>
              </div>
            ))}

            {/* Models */}
            <div className="p-3.5 bg-gray-50 border border-gray-100 rounded-xl">
              <div className="flex items-center gap-3 mb-3">
                <Cpu className="w-4 h-4 text-gray-500" />
                <div className="text-sm font-semibold text-gray-800 font-['Inter']">ML Models</div>
              </div>
              <div className="space-y-2">
                {Object.entries(health.models_loaded).map(([model, loaded]) => (
                  <div key={model} className="flex items-center justify-between text-xs font-['Inter']">
                    <span className="text-gray-600 font-mono">{model}</span>
                    <div className="flex items-center gap-1">
                      {loaded ? <CheckCircle className="w-3.5 h-3.5 text-green-500" /> : <XCircle className="w-3.5 h-3.5 text-red-500" />}
                      <span className={loaded ? 'text-green-600' : 'text-red-500'}>{loaded ? 'Loaded' : 'Not loaded'}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-sm text-red-600 font-['Inter']">
            <XCircle className="w-4 h-4" /> API is offline or unreachable
          </div>
        )}
      </div>

      {/* Regulatory Info */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <div className="text-sm font-semibold text-gray-900 font-['Poppins'] mb-3">Regulatory Configuration</div>
        <div className="space-y-2 text-xs font-['Inter']">
          {[
            ['Framework', 'PMLA 2002 §35A + PML Rules 2005'],
            ['KYC Directive', 'RBI KYC Amendment Directions 2026'],
            ['FEMA', 'FEMA 5(R) — Cross-Border Transactions'],
            ['UPI Latency Budget', 'NPCI 50ms Inline Scoring Constraint'],
            ['Reporting Threshold', '₹1,00,000 (Structuring Detection)'],
            ['UBO Disclosure', '10% beneficial ownership threshold'],
          ].map(([label, val]) => (
            <div key={label} className="flex items-start justify-between gap-4 py-2 border-b border-gray-50 last:border-0">
              <span className="text-gray-500 shrink-0">{label}</span>
              <span className="text-gray-800 font-medium text-right">{val}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Risk Weights */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <div className="text-sm font-semibold text-gray-900 font-['Poppins'] mb-3">4-Pillar Risk Weight Configuration</div>
        <div className="space-y-2">
          {[
            { label: 'P1: Supervised ML (XGBoost)', weight: 40, color: 'bg-blue-500' },
            { label: 'P2: Isolation Forest Anomaly', weight: 20, color: 'bg-orange-400' },
            { label: 'P3: Regulatory Rules Engine', weight: 20, color: 'bg-orange-500' },
            { label: 'P4: NetworkX Graph Analysis', weight: 20, color: 'bg-blue-400' },
          ].map(({ label, weight, color }) => (
            <div key={label}>
              <div className="flex justify-between text-xs font-['Inter'] mb-1">
                <span className="text-gray-600">{label}</span>
                <span className="font-semibold text-gray-800">{weight}%</span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div className={`h-full rounded-full ${color}`} style={{ width: `${weight}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
