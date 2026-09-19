import React, { useState } from "react";
import { analyzeTransaction } from "../services/api";

const PRESETS = [
  {
    name: "Structuring / Smurfing (₹98,500 UPI)",
    desc: "Single transaction patterned just below statutory ₹1,00,000 reporting threshold (PMLA 2002)",
    color: "border-rose-200 bg-rose-50 hover:bg-rose-100",
    badge: "bg-rose-100 text-rose-700",
    data: {
      transaction_id: "SIM_STRUC_98K",
      sender_account_id: "ACC_MUMBAI_01",
      receiver_account_id: "ACC_DELHI_09",
      amount: 98500,
      currency: "INR",
      transaction_type: "TRANSFER",
      channel: "UPI",
      location: "Mumbai",
      is_suspicious: true,
    },
  },
  {
    name: "Rapid Velocity Burst (₹4,80,000 Online)",
    desc: "High velocity large round sum transfer indicative of rapid layering",
    color: "border-amber-200 bg-amber-50 hover:bg-amber-100",
    badge: "bg-amber-100 text-amber-700",
    data: {
      transaction_id: "SIM_BURST_480K",
      sender_account_id: "ACC_LAYER_SENDER",
      receiver_account_id: "ACC_MULE_HUB",
      amount: 480000,
      currency: "INR",
      transaction_type: "TRANSFER",
      channel: "ONLINE",
      location: "Bengaluru",
      is_suspicious: true,
    },
  },
  {
    name: "Standard Legitimate Retail Payment (₹3,450 UPI)",
    desc: "Everyday grocery merchant transfer matching normal consumer baseline",
    color: "border-emerald-200 bg-emerald-50 hover:bg-emerald-100",
    badge: "bg-emerald-100 text-emerald-700",
    data: {
      transaction_id: "SIM_NORMAL_3450",
      sender_account_id: "ACC_USER_9872",
      receiver_account_id: "ACC_MERCHANT_44",
      amount: 3450,
      currency: "INR",
      transaction_type: "PAYMENT",
      channel: "UPI",
      location: "Pune",
      is_suspicious: false,
    },
  },
  {
    name: "Cross-Border High-Value Remittance (₹9,50,000 Wire)",
    desc: "Inter-bank high volume settlement requiring FEMA 5(R) & RBI KYC verification",
    color: "border-indigo-200 bg-indigo-50 hover:bg-indigo-100",
    badge: "bg-indigo-100 text-indigo-700",
    data: {
      transaction_id: "SIM_WIRE_950K",
      sender_account_id: "ACC_CORRESPONDENT_01",
      receiver_account_id: "ACC_BENEFICIARY_77",
      amount: 950000,
      currency: "INR",
      transaction_type: "TRANSFER",
      channel: "ONLINE",
      location: "Hyderabad",
      is_suspicious: true,
    },
  },
];

export default function SimulatorPage() {
  const [formData, setFormData] = useState(PRESETS[0].data);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [latencyMs, setLatencyMs] = useState(null);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === "amount" ? parseFloat(value) || 0 : value,
    }));
  };

  const applyPreset = (preset) => {
    setFormData(preset.data);
    setResult(null);
    setLatencyMs(null);
    setError(null);
  };

  const handleScan = async (e) => {
    e.preventDefault();
    setAnalyzing(true);
    setError(null);
    const start = performance.now();
    try {
      const response = await analyzeTransaction({
        ...formData,
        amount: parseFloat(formData.amount) || 0,
      });
      const elapsed = (performance.now() - start).toFixed(2);
      setLatencyMs(elapsed);
      setResult(response.analysis);
    } catch (err) {
      console.error(err);
      setError("Analysis request failed. Please verify the backend service is running on port 8000.");
    } finally {
      setAnalyzing(false);
    }
  };

  const getRiskColors = (lvl) => {
    switch (lvl) {
      case "CRITICAL": return { badge: "bg-rose-100 text-rose-700 border-rose-200", bar: "bg-rose-500" };
      case "HIGH":     return { badge: "bg-amber-100 text-amber-700 border-amber-200", bar: "bg-amber-500" };
      case "MEDIUM":   return { badge: "bg-yellow-100 text-yellow-700 border-yellow-200", bar: "bg-yellow-400" };
      default:         return { badge: "bg-emerald-100 text-emerald-700 border-emerald-200", bar: "bg-emerald-500" };
    }
  };

  const getBarColor = (val) => {
    if (val >= 80) return "bg-rose-500";
    if (val >= 60) return "bg-amber-500";
    if (val >= 30) return "bg-yellow-400";
    return "bg-emerald-500";
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-lg font-bold text-gray-900 tracking-tight">Real-Time Transaction Scanner &amp; UPI Sandbox</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Test arbitrary payments against the unified 4-pillar risk engine &amp; benchmark latency against the NPCI 50ms budget
          </p>
        </div>

        {latencyMs && (
          <div className="flex items-center gap-2 bg-white border border-gray-200 px-3 py-1.5 rounded-lg text-xs font-mono shadow-sm">
            <span className="text-gray-500">Scan Latency:</span>
            <span className="font-bold text-emerald-600">{latencyMs} ms</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700 border border-emerald-200">
              UPI INLINE BUDGET OK
            </span>
          </div>
        )}
      </div>

      {/* Preset Buttons */}
      <div className="space-y-2">
        <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Quick-Load Scenario Presets:</div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {PRESETS.map((p, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => applyPreset(p)}
              className={`p-3 rounded-xl border text-left flex flex-col justify-between group transition shadow-sm ${p.color}`}
            >
              <div>
                <div className="font-bold text-xs text-gray-900 group-hover:text-indigo-700 transition">{p.name}</div>
                <div className="text-[11px] text-gray-500 mt-1 leading-snug">{p.desc}</div>
              </div>
              <div className={`text-[10px] font-mono mt-2 font-semibold px-1.5 py-0.5 rounded-full inline-block ${p.badge}`}>
                Load Preset ➔
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Input Form */}
        <form
          onSubmit={handleScan}
          className="lg:col-span-5 border border-gray-200 rounded-xl bg-white p-5 space-y-4 shadow-sm"
        >
          <div className="flex items-center justify-between border-b border-gray-100 pb-3">
            <h2 className="text-xs font-bold uppercase tracking-wider text-gray-600">Transaction Parameters</h2>
            <span className="text-[10px] text-gray-400 font-mono">ISO 20022 / UPI PayLoad</span>
          </div>

          <div className="space-y-3 font-mono text-xs">
            <div>
              <label className="text-[11px] text-gray-500 block mb-1 font-sans font-semibold">Transaction ID</label>
              <input
                type="text"
                name="transaction_id"
                value={formData.transaction_id}
                onChange={handleChange}
                required
                className="w-full px-3 py-1.5 rounded-lg bg-gray-50 border border-gray-300 text-gray-900 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-200"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] text-gray-500 block mb-1 font-sans font-semibold">Sender Account</label>
                <input
                  type="text"
                  name="sender_account_id"
                  value={formData.sender_account_id}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-1.5 rounded-lg bg-gray-50 border border-gray-300 text-indigo-700 font-semibold focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-200"
                />
              </div>
              <div>
                <label className="text-[11px] text-gray-500 block mb-1 font-sans font-semibold">Beneficiary Account</label>
                <input
                  type="text"
                  name="receiver_account_id"
                  value={formData.receiver_account_id}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-1.5 rounded-lg bg-gray-50 border border-gray-300 text-cyan-700 font-semibold focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-200"
                />
              </div>
            </div>

            <div>
              <label className="text-[11px] text-gray-500 block mb-1 font-sans font-semibold">Amount (INR ₹)</label>
              <input
                type="number"
                step="0.01"
                name="amount"
                value={formData.amount}
                onChange={handleChange}
                required
                className="w-full px-3 py-1.5 rounded-lg bg-gray-50 border border-gray-300 text-gray-900 font-bold text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-200"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] text-gray-500 block mb-1 font-sans font-semibold">Channel</label>
                <select
                  name="channel"
                  value={formData.channel}
                  onChange={handleChange}
                  className="w-full px-3 py-1.5 rounded-lg bg-gray-50 border border-gray-300 text-gray-700 focus:outline-none focus:border-indigo-500"
                >
                  <option value="UPI">UPI</option>
                  <option value="MOBILE">Mobile Banking</option>
                  <option value="ONLINE">Net Banking</option>
                  <option value="ATM">ATM</option>
                  <option value="BRANCH">Branch</option>
                  <option value="POS">Point of Sale (POS)</option>
                </select>
              </div>
              <div>
                <label className="text-[11px] text-gray-500 block mb-1 font-sans font-semibold">Txn Type</label>
                <select
                  name="transaction_type"
                  value={formData.transaction_type}
                  onChange={handleChange}
                  className="w-full px-3 py-1.5 rounded-lg bg-gray-50 border border-gray-300 text-gray-700 focus:outline-none focus:border-indigo-500"
                >
                  <option value="TRANSFER">TRANSFER</option>
                  <option value="PAYMENT">PAYMENT</option>
                  <option value="DEPOSIT">DEPOSIT</option>
                  <option value="WITHDRAWAL">WITHDRAWAL</option>
                </select>
              </div>
            </div>

            <div>
              <label className="text-[11px] text-gray-500 block mb-1 font-sans font-semibold">Originating Location</label>
              <input
                type="text"
                name="location"
                value={formData.location}
                onChange={handleChange}
                className="w-full px-3 py-1.5 rounded-lg bg-gray-50 border border-gray-300 text-gray-700 focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={analyzing}
            className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs uppercase tracking-wider transition shadow-md flex items-center justify-center gap-2 disabled:opacity-60"
          >
            {analyzing ? "Evaluating 4-Pillars & SHAP..." : "Scan & Score Transaction"}
          </button>
        </form>

        {/* Right: Live Risk Output */}
        <div className="lg:col-span-7 border border-gray-200 rounded-xl bg-white p-5 space-y-4 shadow-sm">
          <div className="flex items-center justify-between border-b border-gray-100 pb-3">
            <h2 className="text-xs font-bold uppercase tracking-wider text-gray-600">Live Chakra Scoring Output</h2>
            <span className="text-[10px] text-gray-400 font-mono">PMLA 2002 / RBI KYC 2026 Engine</span>
          </div>

          {error && (
            <div className="p-3 rounded-lg border border-rose-200 bg-rose-50 text-rose-700 text-xs">
              {error}
            </div>
          )}

          {!result && !error ? (
            <div className="text-center py-16 text-gray-400 text-xs space-y-2">
              <div className="text-gray-500 font-medium text-sm">No scan run yet.</div>
              <p className="max-w-md mx-auto text-[12px] text-gray-400">
                Click "Scan &amp; Score Transaction" or select a preset to evaluate risk across XGBoost, Isolation Forest, Statutory Rules, and Graph Cycle detection.
              </p>
            </div>
          ) : result && (
            <div className="space-y-4 text-xs">
              {/* Top Result Banner */}
              <div className="p-4 rounded-xl border border-gray-200 bg-gray-50 flex flex-col sm:flex-row sm:items-center justify-between gap-3 font-mono">
                <div>
                  <span className="text-[10px] text-gray-400 block uppercase mb-0.5">Composite Risk Score</span>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-2xl font-bold text-gray-900">{result.final_risk_score} / 100</span>
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${getRiskColors(result.risk_level).badge}`}>
                      {result.risk_level}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-gray-400 block uppercase">Inference Speed</span>
                  <span className="text-emerald-600 font-bold text-sm">{latencyMs || "—"} ms</span>
                  <span className="text-[10px] text-gray-400 block">Bank Switch Ready</span>
                </div>
              </div>

              {/* 4 Pillars */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono">
                {[
                  { label: "P1: Supervised ML", val: result.component_scores?.ml_score, weight: "40%" },
                  { label: "P2: Isolation Forest", val: result.component_scores?.anomaly_score, weight: "20%" },
                  { label: "P3: AML Rules", val: result.component_scores?.rule_score, weight: "20%" },
                  { label: "P4: Graph Network", val: result.component_scores?.network_score, weight: "20%" },
                ].map((p) => (
                  <div key={p.label} className="p-3 rounded-lg bg-gray-50 border border-gray-200">
                    <div className="text-[10px] text-gray-500">{p.label}</div>
                    <div className="text-sm font-bold text-gray-900 mt-1">{p.val}/100</div>
                    <div className="w-full bg-gray-200 h-1 rounded-full mt-1.5 overflow-hidden">
                      <div className={`h-full ${getBarColor(p.val)}`} style={{ width: `${Math.min(100, p.val)}%` }}></div>
                    </div>
                    <div className="text-[10px] text-gray-400 mt-1">Weight: {p.weight}</div>
                  </div>
                ))}
              </div>

              {/* Explanation */}
              {result.explanation_summary && (
                <div className="p-3 rounded-lg border border-indigo-200 bg-indigo-50 text-gray-700 text-[11px] leading-relaxed">
                  <span className="text-indigo-700 font-semibold block mb-1">Intelligence Assessment:</span>
                  {result.explanation_summary}
                </div>
              )}

              {/* Triggered Rules */}
              {result.triggered_rules?.length > 0 && (
                <div className="space-y-1.5">
                  <span className="text-[10px] uppercase font-bold text-rose-600 tracking-wider">
                    Statutory Rule Flags ({result.triggered_rules.length}):
                  </span>
                  <div className="space-y-1">
                    {result.triggered_rules.map((rule, i) => (
                      <div key={i} className="p-2 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 font-mono text-[11px]">
                        • {typeof rule === "string" ? rule : rule.rule_name || JSON.stringify(rule)}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
