import React, { useState, useEffect } from "react";
import { fetchTransactionNetwork } from "../services/api";

export default function NetworkPage() {
  const [network, setNetwork] = useState(null);
  const [loading, setLoading] = useState(true);
  const [targetAccount, setTargetAccount] = useState("");
  const [selectedNode, setSelectedNode] = useState(null);

  useEffect(() => {
    loadGraph();
  }, []);

  async function loadGraph(account = null) {
    try {
      setLoading(true);
      const data = await fetchTransactionNetwork(account, 30);
      setNetwork(data);
      if (data.nodes?.length > 0) {
        setSelectedNode(data.nodes[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  function handleSearch(e) {
    e.preventDefault();
    if (targetAccount.trim()) {
      loadGraph(targetAccount.trim());
    } else {
      loadGraph(null);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-lg font-bold text-gray-900 tracking-tight">Graph Topology &amp; Cycle Detection</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            NetworkX multi-hop transaction graph visualizing circular fund cycles and layering funnels
          </p>
        </div>

        <form onSubmit={handleSearch} className="flex items-center gap-2">
          <input
            type="text"
            placeholder="Search Account ID (e.g. ACC03789)"
            value={targetAccount}
            onChange={(e) => setTargetAccount(e.target.value)}
            className="px-3 py-1.5 rounded-md bg-white border border-gray-300 text-xs font-mono text-gray-900 placeholder-gray-400 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-200 w-64"
          />
          <button
            type="submit"
            className="px-3.5 py-1.5 rounded-md bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700 transition shadow-sm"
          >
            Trace
          </button>
          <button
            type="button"
            onClick={() => {
              setTargetAccount("");
              loadGraph(null);
            }}
            className="px-3 py-1.5 rounded-md bg-white border border-gray-300 text-gray-600 text-xs hover:bg-gray-50 transition"
          >
            Reset
          </button>
        </form>
      </div>

      {/* Graph Visualizer & Details Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Network Visual Board */}
        <div className="lg:col-span-2 border border-gray-200 rounded-xl bg-white p-4 min-h-[480px] flex flex-col shadow-sm overflow-hidden">
          <div className="flex items-center justify-between border-b border-gray-100 pb-3 mb-4">
            <div className="flex items-center gap-2 text-xs font-mono text-gray-500">
              <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
              <span>Active Subgraph:</span>
              <span className="text-gray-900 font-bold">{network?.nodes_count || 0} Nodes</span>
              <span>/</span>
              <span className="text-gray-900 font-bold">{network?.edges_count || 0} Directed Transfers</span>
            </div>

            <div className="flex items-center gap-3 text-[11px] font-mono">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
                <span className="text-gray-500">Suspicious Transfer</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                <span className="text-gray-500">Normal Flow</span>
              </div>
            </div>
          </div>

          {loading ? (
            <div className="flex-1 flex items-center justify-center text-xs text-gray-400 font-mono">
              Computing graph topology and multi-hop paths...
            </div>
          ) : (
            <div className="flex-1 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 overflow-y-auto max-h-[420px] p-2">
              {network?.nodes?.map((node) => {
                const isSelected = selectedNode?.id === node.id;
                return (
                  <div
                    key={node.id}
                    onClick={() => setSelectedNode(node)}
                    className={`p-3 rounded-lg border text-left transition cursor-pointer flex flex-col justify-between ${
                      isSelected
                        ? "border-indigo-400 bg-indigo-50 shadow-sm shadow-indigo-200"
                        : node.is_suspicious
                        ? "border-rose-300 bg-rose-50 hover:bg-rose-100"
                        : "border-gray-200 bg-gray-50 hover:bg-gray-100"
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold text-gray-900">{node.id}</span>
                        {node.is_suspicious && (
                          <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>
                        )}
                      </div>
                      <div className="text-[10px] text-gray-500 mt-1 font-mono">
                        Tier: {node.risk_level || "MEDIUM"}
                      </div>
                    </div>
                    <div className={`mt-2 text-[10px] font-medium ${isSelected ? "text-indigo-600" : "text-gray-400"}`}>
                      Click to inspect
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right 1 Col: Selected Entity Topology Details */}
        <div className="border border-gray-200 rounded-xl bg-white p-5 space-y-4 shadow-sm">
          <h3 className="text-xs font-bold uppercase tracking-wider text-gray-500 border-b border-gray-100 pb-2">
            Node Topology Profiler
          </h3>

          {selectedNode ? (
            <div className="space-y-4 text-xs font-mono">
              <div>
                <span className="text-[10px] text-gray-400 block uppercase">Account ID</span>
                <span className="text-sm font-bold text-gray-900">{selectedNode.id}</span>
              </div>

              <div>
                <span className="text-[10px] text-gray-400 block uppercase mb-1">Topology Risk Status</span>
                <span
                  className={`px-2 py-0.5 rounded text-[11px] font-bold border ${
                    selectedNode.is_suspicious
                      ? "bg-rose-50 text-rose-700 border-rose-200"
                      : "bg-emerald-50 text-emerald-700 border-emerald-200"
                  }`}
                >
                  {selectedNode.is_suspicious ? "SUSPECT IN LAYERED NETWORK" : "NORMAL PARTICIPANT"}
                </span>
              </div>

              <div className="p-3 rounded-lg bg-gray-50 border border-gray-200 space-y-2">
                <div className="text-[11px] font-bold text-gray-700">Connected Edge Flows</div>
                <div className="max-h-48 overflow-y-auto space-y-2 text-[11px]">
                  {network?.edges
                    ?.filter((e) => e.source === selectedNode.id || e.target === selectedNode.id)
                    .map((edge) => (
                      <div key={edge.id} className="p-2 rounded bg-white border border-gray-200 shadow-sm">
                        <div className="flex items-center justify-between text-gray-500">
                          <span>{edge.source === selectedNode.id ? "OUTFLOW ➔" : "INFLOW ⬅"}</span>
                          <span className="text-gray-900 font-bold">₹{edge.amount.toLocaleString("en-IN")}</span>
                        </div>
                        <div className="text-[10px] text-gray-400 mt-1">
                          Counterparty: {edge.source === selectedNode.id ? edge.target : edge.source}
                        </div>
                        {edge.pattern !== "NORMAL" && (
                          <div className="text-[10px] text-rose-600 font-bold mt-0.5">
                            Typology: {edge.pattern}
                          </div>
                        )}
                      </div>
                    ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-xs text-gray-400 text-center py-12">
              Select an account node from the network graph to inspect connected transaction topology.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
