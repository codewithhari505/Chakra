import React, { useState, useCallback, useEffect } from 'react';
import ReactFlow, {
  Background, Controls, MiniMap,
  addEdge, useNodesState, useEdgesState,
  type Connection, type Edge, type Node,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Search, RefreshCw } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { getTransactionNetwork } from '../services/analyticsService';
import { LoadingSpinner } from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import RiskBadge from '../components/common/RiskBadge';
import { formatCurrency } from '../utils/formatters';
import type { GraphNode } from '../types';

const RISK_NODE_COLORS: Record<string, string> = {
  CRITICAL: '#DC2626',
  HIGH: '#EA580C',
  MEDIUM: '#F97316',
  LOW: '#2563EB',
};

function toReactFlow(nodes: GraphNode[], edges: any[]) {
  const cols = Math.ceil(Math.sqrt(nodes.length));
  const rfNodes: Node[] = nodes.map((n, i) => ({
    id: n.id,
    data: { label: n.id, risk_level: n.risk_level, is_suspicious: n.is_suspicious },
    position: { x: (i % cols) * 160, y: Math.floor(i / cols) * 100 },
    style: {
      background: n.is_suspicious ? '#FFF7ED' : '#EFF6FF',
      border: `2px solid ${RISK_NODE_COLORS[n.risk_level] ?? '#2563EB'}`,
      borderRadius: 10,
      fontSize: 10,
      fontFamily: 'Inter, sans-serif',
      fontWeight: 600,
      color: '#111827',
      padding: '6px 10px',
      width: 130,
    },
  }));

  const rfEdges: Edge[] = edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    label: formatCurrency(e.amount),
    labelStyle: { fontSize: 9, fill: '#64748B' },
    style: { stroke: e.is_suspicious ? '#F97316' : '#93C5FD', strokeWidth: e.is_suspicious ? 2 : 1 },
    markerEnd: { type: MarkerType.ArrowClosed, color: e.is_suspicious ? '#F97316' : '#93C5FD' },
    data: e,
  }));

  return { rfNodes, rfEdges };
}

export default function NetworkAnalysis() {
  const [search, setSearch] = useState('');
  const [queryAccount, setQueryAccount] = useState<string | undefined>(undefined);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState<any>(null);

  const { data, loading, error, refetch } = useApi(
    () => getTransactionNetwork(queryAccount, 50),
    [queryAccount]
  );

  useEffect(() => {
    if (!data) return;
    const { rfNodes, rfEdges } = toReactFlow(data.nodes, data.edges);
    setNodes(rfNodes);
    setEdges(rfEdges);
  }, [data]);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setQueryAccount(search.trim() || undefined);
  }

  function onNodeClick(_: any, node: Node) {
    setSelectedNode(node.data);
  }

  return (
    <div className="space-y-4 h-full">
      {/* Controls */}
      <div className="bg-white border border-gray-200 rounded-xl p-4 flex flex-wrap gap-3 items-center">
        <form onSubmit={handleSearch} className="flex items-center gap-2 flex-1 min-w-[220px]">
          <div className="relative flex-1 max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search account (e.g. ACC00001)"
              className="w-full pl-9 pr-3 py-1.5 text-sm bg-gray-50 border border-gray-200 rounded-lg font-['Inter'] focus:outline-none focus:border-blue-400"
            />
          </div>
          <button type="submit" className="px-3 py-1.5 bg-blue-600 text-white text-xs font-semibold rounded-lg hover:bg-blue-700 transition">Trace</button>
          <button type="button" onClick={() => { setSearch(''); setQueryAccount(undefined); }} className="px-3 py-1.5 bg-white border border-gray-200 text-gray-600 text-xs rounded-lg hover:bg-gray-50 transition">Reset</button>
        </form>

        <div className="flex items-center gap-3 text-xs font-['Inter'] text-gray-500">
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-blue-500 border-2 border-blue-500" /> Normal</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-orange-500 border-2 border-orange-500" /> Suspicious</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-red-600 border-2 border-red-600" /> Critical</span>
        </div>

        <div className="text-xs text-gray-400 font-['Inter']">
          {data?.nodes_count ?? 0} nodes · {data?.edges_count ?? 0} edges
        </div>

        <button onClick={refetch} className="p-1.5 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 transition">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 h-[560px]">
        {/* Graph */}
        <div className="lg:col-span-3 bg-white border border-gray-200 rounded-xl overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center h-full"><LoadingSpinner /></div>
          ) : error ? (
            <ErrorState message="Failed to load network graph" onRetry={refetch} />
          ) : (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onNodeClick={onNodeClick}
              fitView
              attributionPosition="bottom-left"
            >
              <Background color="#F1F5F9" gap={16} />
              <Controls />
              <MiniMap nodeColor={(n) => RISK_NODE_COLORS[n.data?.risk_level] ?? '#2563EB'} />
            </ReactFlow>
          )}
        </div>

        {/* Node Detail Panel */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-4 overflow-y-auto">
          <div className="text-sm font-semibold text-gray-900 font-['Poppins']">Node Inspector</div>
          {selectedNode ? (
            <div className="space-y-3 text-xs font-['Inter']">
              <div>
                <div className="text-[10px] text-gray-400 uppercase tracking-wide mb-1">Account ID</div>
                <div className="font-mono font-bold text-gray-900 text-sm">{selectedNode.label}</div>
              </div>
              <div>
                <div className="text-[10px] text-gray-400 uppercase tracking-wide mb-1">Risk Level</div>
                <RiskBadge level={selectedNode.risk_level} />
              </div>
              <div>
                <div className="text-[10px] text-gray-400 uppercase tracking-wide mb-1">Suspicious</div>
                <span className={`font-semibold ${selectedNode.is_suspicious ? 'text-orange-600' : 'text-gray-500'}`}>
                  {selectedNode.is_suspicious ? 'Yes — pattern anomaly' : 'No'}
                </span>
              </div>
              <div className="pt-3 border-t border-gray-100">
                <div className="text-[10px] text-gray-400 uppercase tracking-wide mb-2">Connected Edges</div>
                <div className="space-y-1.5 max-h-64 overflow-y-auto">
                  {(data?.edges ?? []).filter((e) => e.source === selectedNode.label || e.target === selectedNode.label).slice(0, 10).map((e) => (
                    <div key={e.id} className="p-2 bg-gray-50 rounded-lg border border-gray-100 text-[10px]">
                      <div className="flex justify-between text-gray-600">
                        <span>{e.source === selectedNode.label ? '↑ Out' : '↓ In'}</span>
                        <span className="font-semibold text-gray-800">{formatCurrency(e.amount)}</span>
                      </div>
                      <div className="text-gray-400 mt-0.5">{e.source === selectedNode.label ? e.target : e.source}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-xs text-gray-400 font-['Inter'] text-center py-8">
              Click a node in the graph to inspect its connections and risk profile.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
