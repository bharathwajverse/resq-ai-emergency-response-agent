import { useState, useEffect } from 'react';
import { generatePlan } from '../services/api';
import { GitCommit, ArrowDown, Play } from 'lucide-react';

export default function Planning() {
  const [paradigm, setParadigm] = useState('Hierarchical');
  const [emergencyType, setEmergencyType] = useState('Road accident');
  const [data, setData] = useState(null);

  const runPlanner = async (selectedParadigm = paradigm, selectedType = emergencyType) => {
    try {
      const res = await generatePlan({
        paradigm: selectedParadigm,
        emergency_type: selectedType,
        start_node: 'Central_Base',
        destination_node: 'Accident_Site',
      });
      if (res.data) setData(res.data);
    } catch (e) {
      console.error('Planning error:', e);
    }
  };

  useEffect(() => {
    runPlanner('Hierarchical', 'Road accident');
  }, []);

  if (!data) return <div className="p-8 text-center text-slate-400">Generating AI Response Plan...</div>;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex flex-wrap justify-between items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold">Automated Response Planning (FAI Module VII)</h1>
          <p className="text-sm text-slate-400">
            Compare Hierarchical Task Network (HTN), State-Space STRIPS, and Partial-Order Planning (POP)
          </p>
        </div>
      </div>

      {/* Paradigm Selector */}
      <div className="bg-slate-800 p-4 rounded-lg border border-slate-700 grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
        <div>
          <label className="block text-xs text-slate-400 mb-1">Planning Paradigm</label>
          <select
            value={paradigm}
            onChange={(e) => {
              setParadigm(e.target.value);
              runPlanner(e.target.value, emergencyType);
            }}
            className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm"
          >
            <option value="Hierarchical">Hierarchical Task Network (HTN)</option>
            <option value="State-Space">State-Space Planning (STRIPS BFS/Heuristic)</option>
            <option value="Partial-Order">Partial-Order Planning (POP with Causal Links)</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">Emergency Domain Protocol</label>
          <select
            value={emergencyType}
            onChange={(e) => {
              setEmergencyType(e.target.value);
              runPlanner(paradigm, e.target.value);
            }}
            className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm"
          >
            <option value="Road accident">Road Accident Trauma Protocol</option>
            <option value="Fire">Fire &amp; Burn Response Protocol</option>
            <option value="Flood">Flash Flood Rescue Protocol</option>
            <option value="Medical emergency">Cardiac ALS Protocol</option>
          </select>
        </div>
        <button
          onClick={() => runPlanner(paradigm, emergencyType)}
          className="flex justify-center items-center px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded text-sm font-medium"
        >
          <Play className="w-4 h-4 mr-1.5" /> Generate Plan
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
          <h3 className="text-sm text-slate-400 mb-1">Initial State</h3>
          <p className="font-semibold text-sm">{data.initialState}</p>
        </div>
        <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
          <h3 className="text-sm text-slate-400 mb-1">Goal State</h3>
          <p className="font-semibold text-green-400 text-sm">{data.goal}</p>
        </div>
      </div>

      <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 flex flex-col items-center">
        <h2 className="text-lg font-bold w-full mb-6 text-center text-slate-200">
          {data.paradigm} Plan Execution Graph ({data.actions?.length || 0} Actions, Est. {data.estimated_duration_minutes} min)
        </h2>
        <div className="w-full max-w-2xl">
          {(data.actions || []).map((step, index) => (
            <div key={step.id || index} className="flex items-center relative mb-6">
              {index < data.actions.length - 1 && (
                <div className="absolute top-8 left-3 w-0.5 h-6 bg-slate-700 flex items-center justify-center">
                  <ArrowDown className="w-3 h-3 text-slate-500 absolute bottom-0 -mb-2 bg-slate-800 rounded-full" />
                </div>
              )}

              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center mr-4 z-10 shrink-0 ${
                  step.status === 'done'
                    ? 'bg-green-500'
                    : step.status === 'active'
                    ? 'bg-blue-500'
                    : 'bg-slate-600'
                }`}
              >
                <GitCommit className="w-4 h-4 text-white" />
              </div>

              <div
                className={`flex-1 p-3 rounded border ${
                  step.status === 'done'
                    ? 'bg-slate-900 border-green-900/50 text-slate-200'
                    : step.status === 'active'
                    ? 'bg-blue-900/20 border-blue-500/50 text-blue-100 font-bold'
                    : 'bg-slate-900 border-slate-700 text-slate-300'
                }`}
              >
                <div className="flex justify-between items-center gap-2">
                  <span className="text-sm">{step.action}</span>
                  {step.dependencies && step.dependencies.length > 0 && (
                    <span className="text-xs text-slate-400 font-mono shrink-0">
                      Depends on Step: [{step.dependencies.join(', ')}]
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Show POP Causal Links when Partial-Order is active */}
      {data.causal_links && data.causal_links.length > 0 && (
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <h3 className="text-md font-bold mb-3 text-purple-400">Partial-Order Causal Links (Protected Preconditions)</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs font-mono">
            {data.causal_links.map((cl, idx) => (
              <div key={idx} className="bg-slate-900 p-2.5 rounded border border-slate-700">
                <span className="text-blue-400">{cl.source_action}</span> &mdash;[{' '}
                <span className="text-amber-300">{cl.condition}</span> ]&rarr;{' '}
                <span className="text-green-400">{cl.target_action}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
