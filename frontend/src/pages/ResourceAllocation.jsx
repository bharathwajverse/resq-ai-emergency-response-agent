import { useState, useEffect } from 'react';
import { solveCSP, replanResponse } from '../services/api';
import { Check, X, RefreshCw, Play } from 'lucide-react';

export default function ResourceAllocation() {
  const [victims, setVictims] = useState(6);
  const [location, setLocation] = useState('N1');
  const [severity, setSeverity] = useState('High');
  const [data, setData] = useState(null);
  const [replanData, setReplanData] = useState(null);

  const runSolver = async (vc = victims, loc = location, sev = severity) => {
    setReplanData(null);
    try {
      const res = await solveCSP({ victim_count: Number(vc), location: loc, severity: sev });
      setData(res.data);
    } catch (e) {
      console.error('CSP solve error:', e);
    }
  };

  useEffect(() => {
    runSolver(6, 'N1', 'High');
  }, []);

  const handleSimulateBreakdown = async () => {
    try {
      const ambCode =
        replanData?.allocated_ambulance?.code ||
        replanData?.ambulance?.code ||
        data?.assignment?.ambulance ||
        'A2';
      const cleanCode = String(ambCode).split(' ')[0].split('+')[0];
      const res = await replanResponse({
        incident_id: 'INC-101',
        failed_ambulance_code: cleanCode,
        victim_count: victims,
        location: location,
        reason: `${cleanCode} unavailable — dynamic CSP reallocation triggered`,
      });
      setReplanData(res.data);
    } catch (e) {
      console.error('Replan error:', e);
    }
  };

  if (!data) return <div className="p-8 text-center text-slate-400">Running CSP Solver...</div>;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex flex-wrap justify-between items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold">Resource Allocation (FAI Module IV — CSP &amp; Backtracking)</h1>
          <p className="text-slate-400 text-sm">
            Backtracking search with Minimum Remaining Values (MRV), Least Constraining Value (LCV), and AC-3 propagation
          </p>
        </div>
        <button
          onClick={handleSimulateBreakdown}
          className="flex items-center px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-md text-xs font-bold"
        >
          <RefreshCw className="w-4 h-4 mr-1.5" />
          Simulate Selected Ambulance Unavailable (Replan)
        </button>
      </div>

      {/* Interactive CSP Input Controls */}
      <div className="bg-slate-800 p-4 rounded-lg border border-slate-700 grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
        <div>
          <label className="block text-xs text-slate-400 mb-1">Victim Count (Constraint: Cap &ge; Victims)</label>
          <input
            type="number"
            min="1"
            max="30"
            value={victims}
            onChange={(e) => setVictims(Number(e.target.value))}
            className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">Incident Node</label>
          <select value={location} onChange={(e) => setLocation(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm">
            {['N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'N7', 'N8'].map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">Severity</label>
          <select value={severity} onChange={(e) => setSeverity(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm">
            <option>Low</option>
            <option>Medium</option>
            <option>High</option>
            <option>Critical</option>
          </select>
        </div>
        <button
          onClick={() => runSolver(victims, location, severity)}
          className="flex justify-center items-center px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded text-sm font-medium"
        >
          <Play className="w-4 h-4 mr-1.5" /> Solve CSP
        </button>
      </div>

      <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
        <h2 className="text-lg font-semibold mb-4 text-white">Satisfied CSP Assignment</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-slate-900 border border-slate-700 rounded-lg">
            <p className="text-sm text-slate-400">Target Incident</p>
            <p className="font-bold text-blue-400">{data.incident}</p>
          </div>
          <div className="p-4 bg-slate-900 border border-green-900 rounded-lg">
            <p className="text-sm text-slate-400">Dispatched Ambulance</p>
            <p className="font-bold text-green-400 flex items-center">
              <Check className="w-4 h-4 mr-2" /> {data.selectedAmbulance}
            </p>
          </div>
          <div className="p-4 bg-slate-900 border border-green-900 rounded-lg">
            <p className="text-sm text-slate-400">Destination Hospital</p>
            <p className="font-bold text-green-400 flex items-center">
              <Check className="w-4 h-4 mr-2" /> {data.selectedHospital}
            </p>
          </div>
        </div>
        {data.explanation && (
          <p className="mt-4 text-xs text-slate-300 bg-slate-900 p-3 rounded border border-slate-700 font-mono">
            {data.explanation} (Nodes explored: {data.nodes_explored}, Backtracks: {data.backtracks})
          </p>
        )}
      </div>

      {replanData && (
        <div className="bg-slate-800 p-6 rounded-lg border border-amber-500/60 space-y-2">
          <h3 className="text-md font-bold text-amber-400">Dynamic Replanning Result (Unavailable Ambulance Replaced)</h3>
          <p className="text-sm text-slate-200">
            New Ambulance Assigned: <span className="font-bold text-green-400">{replanData.allocated_ambulance?.code}</span> | New Route:{' '}
            <span className="font-mono text-blue-400">{(replanData.route?.path || []).join(' -> ')}</span>
          </p>
          <p className="text-xs text-slate-300">{replanData.explanation}</p>
        </div>
      )}

      <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
        <h2 className="text-lg font-semibold mb-4 text-white">Constraint Propagation &amp; Rejected Alternatives</h2>
        <div className="space-y-3">
          {(data.rejected || []).map((item, i) => (
            <div key={i} className="flex items-start p-3 bg-slate-900 rounded border border-red-900/30">
              <X className="w-5 h-5 text-red-500 mr-3 mt-0.5 shrink-0" />
              <div>
                <p className="font-semibold text-slate-300">{item.id || item.candidate}</p>
                <p className="text-sm text-slate-400">Rejected: {item.reason}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
