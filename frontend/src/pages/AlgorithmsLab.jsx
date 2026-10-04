import { useState, useEffect } from 'react';
import { runLab } from '../services/api';
import { Beaker, Play } from 'lucide-react';

const ALGORITHMS = [
  'A*',
  'UCS',
  'DLS',
  'IDS',
  'Best First',
  'Hill Climbing',
  'Beam Search',
  'CSP',
  'Backtracking',
  'MCTS',
  'Alpha-Beta',
  'Forward Chaining',
  'Backward Chaining',
  'Resolution',
  'Knowledge Base',
  'Frames',
  'Ontology',
  'State-Space Planning',
  'Partial-Order Planning',
  'Hierarchical Planning',
  'Bayesian Reasoning',
  'Decision Tree',
  'AI Agent Orchestration',
];

const SCENARIOS = [
  'Scenario 1 (Road Accident, 6 Victims, Heavy Rain, Road Blocked)',
  'Scenario 2 (Warehouse Fire, 4 Victims, Clear Weather)',
  'Scenario 3 (Flash Flood, 10 Victims, Two Roads Blocked)',
  'Scenario 4 (Cardiac Medical Emergency, 2 Victims)',
  'Scenario 5 (Multi-Incident Fleet Contention)',
];

export default function AlgorithmsLab() {
  const [algo, setAlgo] = useState('A*');
  const [scenario, setScenario] = useState(SCENARIOS[0]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const executeAlgorithm = async (selectedAlgo = algo, selectedScenario = scenario) => {
    setLoading(true);
    try {
      const res = await runLab({ algorithm: selectedAlgo, scenario: selectedScenario });
      setResult(res.data);
    } catch (e) {
      console.error('Lab execution error:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    executeAlgorithm('A*', SCENARIOS[0]);
  }, []);

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center">
          <Beaker className="w-6 h-6 mr-2 text-purple-400" />
          AI Algorithms Lab (All 22 FAI Syllabus Modules Executable)
        </h1>
        <p className="text-slate-400 text-sm">
          Interactive execution bench for Search, CSP, Game Trees, FOL Inference, Knowledge Representation, Planning, Bayesian Risk &amp; Decision Trees
        </p>
      </div>

      <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
        <div>
          <label className="block text-sm font-medium text-slate-400 mb-1">Select FAI Algorithm / Module</label>
          <select
            value={algo}
            onChange={(e) => {
              setAlgo(e.target.value);
              executeAlgorithm(e.target.value, scenario);
            }}
            className="w-full bg-slate-900 border border-slate-700 rounded-md p-2"
          >
            {ALGORITHMS.map((a) => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-400 mb-1">Emergency Scenario</label>
          <select
            value={scenario}
            onChange={(e) => {
              setScenario(e.target.value);
              executeAlgorithm(algo, e.target.value);
            }}
            className="w-full bg-slate-900 border border-slate-700 rounded-md p-2"
          >
            {SCENARIOS.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
        <div>
          <button
            onClick={() => executeAlgorithm(algo, scenario)}
            disabled={loading}
            className="w-full flex justify-center items-center px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white rounded-md font-medium transition-colors"
          >
            <Play className="w-4 h-4 mr-2" /> {loading ? 'Executing...' : 'Run Algorithm'}
          </button>
        </div>
      </div>

      {result && (
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-bold text-white">Live Execution Telemetry</h2>
            <span className="text-xs px-2.5 py-1 rounded bg-green-900/40 text-green-400 border border-green-800 font-mono">
              Status: {result.status}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-slate-900 p-4 rounded border border-slate-700">
              <span className="text-xs text-slate-500 uppercase">Algorithm / Module</span>
              <p className="font-bold text-blue-400">{result.algorithm}</p>
              <p className="text-xs text-slate-400 mt-1 font-mono">{result.input}</p>
            </div>
            <div className="bg-slate-900 p-4 rounded border border-slate-700">
              <span className="text-xs text-slate-500 uppercase">Time &amp; Space Complexity</span>
              <p className="font-mono text-sm text-orange-400 mt-1">{result.complexity}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-slate-900 p-4 rounded border border-slate-700">
              <span className="text-xs text-slate-500">Nodes / States Explored</span>
              <p className="font-bold text-xl text-purple-400">{result.explored}</p>
            </div>
            <div className="bg-slate-900 p-4 rounded border border-slate-700">
              <span className="text-xs text-slate-500">Solution Cost / Metric</span>
              <p className="font-bold text-lg text-emerald-400">{result.cost}</p>
            </div>
            <div className="bg-slate-900 p-4 rounded border border-slate-700 md:col-span-2">
              <span className="text-xs text-slate-500">Computed Path / Solution Output</span>
              <p className="font-mono text-sm mt-1 bg-slate-800 p-2 rounded text-slate-200">{result.solution}</p>
            </div>
          </div>

          <div className="bg-slate-900 p-4 rounded border border-slate-700">
            <span className="text-xs text-slate-500 uppercase">Algorithmic Trace &amp; Explanation</span>
            <p className="text-sm mt-1 text-slate-300">{result.explanation}</p>
          </div>
        </div>
      )}
    </div>
  );
}
