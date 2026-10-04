import { useState, useEffect } from 'react';
import { runSearch, getGraph } from '../services/api';
import { Play } from 'lucide-react';

export default function RouteSearch() {
  const [algo, setAlgo] = useState('A*');
  const [source, setSource] = useState('A2');
  const [dest, setDest] = useState('H1');
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [result, setResult] = useState(null);

  const algorithms = ['UCS', 'A*', 'Best First', 'Hill Climbing', 'Beam Search', 'DLS', 'IDS'];

  useEffect(() => {
    const init = async () => {
      try {
        const [gRes, sRes] = await Promise.all([
          getGraph(),
          runSearch({ algorithm: 'A*', start_node: 'A2', goal_node: 'H1' }),
        ]);
        if (gRes.data) setGraphData(gRes.data);
        if (sRes.data) setResult(sRes.data);
      } catch (e) {
        console.error('RouteSearch init error:', e);
      }
    };
    init();
  }, []);

  const handleSearch = async () => {
    try {
      const res = await runSearch({ algorithm: algo, start_node: source, goal_node: dest });
      setResult(res.data);
    } catch (e) {
      console.error('Search error:', e);
    }
  };

  const nodeMap = {};
  (graphData.nodes || []).forEach((n) => {
    nodeMap[n.id] = n;
  });

  // Scale node (x, y) in [0..14, 0..10] to SVG viewBox [0..700, 0..440]
  const scaleX = (x) => 50 + (Number(x || 0) / 13.0) * 600;
  const scaleY = (y) => 390 - (Number(y || 0) / 10.0) * 340;

  const isEdgeOnPath = (u, v) => {
    if (!result || !Array.isArray(result.path)) return false;
    for (let i = 0; i < result.path.length - 1; i++) {
      const a = result.path[i];
      const b = result.path[i + 1];
      if ((a === u && b === v) || (a === v && b === u)) return true;
    }
    return false;
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Emergency Road Network &amp; Route Search (Modules II &amp; III)</h1>
        <p className="text-sm text-slate-400">
          Interactive 13-node weighted graph executing UCS, DLS, IDS, A*, Best-First, Hill Climbing, and Beam Search
        </p>
      </div>

      <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
        <div>
          <label className="block text-sm font-medium text-slate-400 mb-1">Search Algorithm</label>
          <select value={algo} onChange={(e) => setAlgo(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded-md p-2">
            {algorithms.map((a) => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-400 mb-1">Source Node</label>
          <select value={source} onChange={(e) => setSource(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded-md p-2">
            {(graphData.nodes || []).map((n) => (
              <option key={n.id} value={n.id}>{n.id} — {n.name}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-400 mb-1">Destination Node</label>
          <select value={dest} onChange={(e) => setDest(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded-md p-2">
            {(graphData.nodes || []).map((n) => (
              <option key={n.id} value={n.id}>{n.id} — {n.name}</option>
            ))}
          </select>
        </div>
        <div>
          <button
            onClick={handleSearch}
            className="w-full flex justify-center items-center px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-md font-medium transition-colors"
          >
            <Play className="w-4 h-4 mr-2" /> Run Search
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-slate-900 border border-slate-700 rounded-lg p-4 h-[480px] flex flex-col justify-between">
          <svg viewBox="0 0 700 440" className="w-full h-full">
            {/* Render all 17 Road Edges */}
            {(graphData.edges || []).map((edge, idx) => {
              const u = nodeMap[edge.source];
              const v = nodeMap[edge.target];
              if (!u || !v) return null;
              const x1 = scaleX(u.x);
              const y1 = scaleY(u.y);
              const x2 = scaleX(v.x);
              const y2 = scaleY(v.y);
              const active = isEdgeOnPath(edge.source, edge.target);
              return (
                <g key={idx}>
                  <line
                    x1={x1}
                    y1={y1}
                    x2={x2}
                    y2={y2}
                    stroke={edge.is_blocked ? '#ef4444' : active ? '#3b82f6' : '#334155'}
                    strokeWidth={active ? 4 : 2}
                    strokeDasharray={edge.is_blocked ? '6,4' : undefined}
                  />
                  <text
                    x={(x1 + x2) / 2}
                    y={(y1 + y2) / 2 - 4}
                    fill={edge.is_blocked ? '#f87171' : '#94a3b8'}
                    fontSize="10"
                    textAnchor="middle"
                  >
                    {edge.is_blocked ? 'BLOCKED' : `${edge.distance}km`}
                  </text>
                </g>
              );
            })}

            {/* Render all 13 Road Nodes */}
            {(graphData.nodes || []).map((node) => {
              const cx = scaleX(node.x);
              const cy = scaleY(node.y);
              const inPath = result?.path?.includes(node.id);
              const fill =
                node.id.startsWith('H')
                  ? '#10b981'
                  : node.id.startsWith('A')
                  ? '#f59e0b'
                  : inPath
                  ? '#3b82f6'
                  : '#475569';
              return (
                <g key={node.id}>
                  <circle
                    cx={cx}
                    cy={cy}
                    r={inPath ? 16 : 13}
                    fill={fill}
                    stroke={inPath ? '#ffffff' : '#1e293b'}
                    strokeWidth={inPath ? 3 : 1.5}
                  />
                  <text x={cx} y={cy + 4} fill="#ffffff" fontSize="10" fontWeight="bold" textAnchor="middle">
                    {node.id}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-bold mb-4">Search Telemetry</h3>
          {result ? (
            <div className="space-y-4">
              <div className="p-3 bg-slate-900 rounded border border-slate-700">
                <p className="text-xs text-slate-400">Algorithm</p>
                <p className="text-sm font-bold text-emerald-400">{result.algorithm_name || algo}</p>
              </div>
              <div className="p-3 bg-slate-900 rounded border border-slate-700">
                <p className="text-xs text-slate-400">Total Traversal Cost</p>
                <p className="text-xl font-bold text-blue-400">{result.cost}</p>
              </div>
              <div className="p-3 bg-slate-900 rounded border border-slate-700">
                <p className="text-xs text-slate-400">Nodes Explored</p>
                <p className="text-xl font-bold text-purple-400">{result.nodes_explored ?? result.explored}</p>
              </div>
              <div className="p-3 bg-slate-900 rounded border border-slate-700">
                <p className="text-xs text-slate-400">Blocked Edges in Network</p>
                <p className="text-xl font-bold text-red-400">{result.blocked}</p>
              </div>
              <div>
                <p className="text-xs text-slate-400 mb-2">Computed Path Sequence</p>
                <div className="flex flex-wrap gap-1.5 text-xs font-mono">
                  {(result.path || []).map((n, i) => (
                    <span key={i} className="bg-blue-900/40 border border-blue-700 text-blue-200 px-2 py-1 rounded">
                      {n}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <p className="text-slate-400 text-sm">Select nodes and click Run Search.</p>
          )}
        </div>
      </div>
    </div>
  );
}
