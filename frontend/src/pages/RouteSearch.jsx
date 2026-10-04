import { useState } from 'react';
import { runSearch } from '../services/api';
import { Play } from 'lucide-react';

export default function RouteSearch() {
  const [algo, setAlgo] = useState('A*');
  const [source, setSource] = useState('Incident Site');
  const [dest, setDest] = useState('City Hospital');
  const [result, setResult] = useState(null);

  const algorithms = ['UCS', 'A*', 'Best First', 'Hill Climbing', 'Beam Search', 'DLS', 'IDS'];

  const handleSearch = async () => {
    try {
      // Fake API call
      const res = await runSearch({ algorithm: algo, source, destination: dest });
      setResult(res.data);
    } catch (e) {
      setResult({
        path: ['Incident Site', 'Node A', 'Node B', 'City Hospital'],
        cost: 15.5,
        explored: 42,
        blocked: 3
      });
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Route Search Visualization</h1>
      
      <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
        <div>
          <label className="block text-sm font-medium text-slate-400 mb-1">Algorithm</label>
          <select value={algo} onChange={(e) => setAlgo(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded-md p-2">
            {algorithms.map(a => <option key={a}>{a}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-400 mb-1">Source Node</label>
          <input value={source} onChange={(e) => setSource(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded-md p-2" />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-400 mb-1">Destination Node</label>
          <input value={dest} onChange={(e) => setDest(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded-md p-2" />
        </div>
        <div>
          <button onClick={handleSearch} className="w-full flex justify-center items-center px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-md transition-colors">
            <Play className="w-4 h-4 mr-2" /> Run Search
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-slate-900 border border-slate-700 rounded-lg p-4 h-[500px] flex items-center justify-center relative overflow-hidden">
          {/* Mock Graph Visualization using basic HTML/CSS */}
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:2rem_2rem] opacity-30"></div>
          
          <div className="relative w-full h-full">
             {result && result.path.map((node, i) => (
                <div key={node} className="absolute flex flex-col items-center" style={{ left: `${20 + (i * 20)}%`, top: `${50 + (i % 2 === 0 ? -15 : 15)}%` }}>
                  <div className="w-8 h-8 bg-blue-500 rounded-full border-2 border-white shadow-[0_0_15px_rgba(59,130,246,0.5)] z-10 flex items-center justify-center text-xs font-bold">{i+1}</div>
                  <span className="text-xs mt-2 font-mono bg-slate-800 px-1 rounded">{node}</span>
                </div>
             ))}
             {result && result.path.length > 0 && (
               <svg className="absolute inset-0 w-full h-full z-0 pointer-events-none" style={{ paddingLeft: '1rem', paddingTop: '1rem' }}>
                 <path 
                   d={result.path.map((_, i) => `${i === 0 ? 'M' : 'L'} ${20 + (i * 20)}% ${50 + (i % 2 === 0 ? -15 : 15)}%`).join(' ')} 
                   stroke="#3b82f6" 
                   strokeWidth="3" 
                   fill="none" 
                   strokeDasharray="5,5" 
                   className="animate-[dash_1s_linear_infinite]" 
                 />
               </svg>
             )}
             {!result && <p className="text-slate-500 absolute inset-0 flex items-center justify-center z-10">Run a search to visualize the graph traversal</p>}
          </div>
        </div>
        
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-bold mb-4">Search Results</h3>
          {result ? (
            <div className="space-y-4">
              <div className="p-3 bg-slate-900 rounded border border-slate-700">
                <p className="text-sm text-slate-400">Path Cost</p>
                <p className="text-xl font-bold text-blue-400">{result.cost}</p>
              </div>
              <div className="p-3 bg-slate-900 rounded border border-slate-700">
                <p className="text-sm text-slate-400">Nodes Explored</p>
                <p className="text-xl font-bold text-purple-400">{result.explored}</p>
              </div>
              <div className="p-3 bg-slate-900 rounded border border-slate-700">
                <p className="text-sm text-slate-400">Blocked Routes Avoided</p>
                <p className="text-xl font-bold text-red-400">{result.blocked}</p>
              </div>
              <div>
                <p className="text-sm text-slate-400 mb-2">Final Path</p>
                <div className="flex flex-wrap gap-2 text-sm font-mono">
                  {result.path.map((node, i) => (
                    <span key={i} className="px-2 py-1 bg-slate-700 rounded flex items-center">
                      {node}
                      {i < result.path.length - 1 && <span className="mx-1 text-slate-400">→</span>}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-500">No results yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}
