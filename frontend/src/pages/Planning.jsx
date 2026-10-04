import { useState, useEffect } from 'react';
import { generatePlan } from '../services/api';
import { GitCommit, ArrowDown } from 'lucide-react';

export default function Planning() {
  const [data, setData] = useState(null);

  useEffect(() => {
    const fetchPlan = async () => {
      try {
        const res = await generatePlan({});
        if (res.data) {
          setData(res.data);
          return;
        }
      } catch (e) {
        // Mock fallback
        setData({
          initialState: 'Incident reported, no resources dispatched',
          goal: 'Victims treated, site secured, resources returned',
          actions: [
            { id: 1, action: 'Verify Incident', status: 'done', dependencies: [] },
            { id: 2, action: 'Dispatch Ambulance A2', status: 'done', dependencies: [1] },
            { id: 3, action: 'Notify Police for Traffic Control', status: 'done', dependencies: [1] },
            { id: 4, action: 'Ambulance en route to scene', status: 'active', dependencies: [2] },
            { id: 5, action: 'Treat victims on site', status: 'pending', dependencies: [4] },
            { id: 6, action: 'Transport to City General Hospital', status: 'pending', dependencies: [5] },
            { id: 7, action: 'Hospital Admission', status: 'pending', dependencies: [6] }
          ]
        });
      }
    };
    fetchPlan();
  }, []);

  if (!data) return <div className="p-8 text-center text-slate-400">Loading plan...</div>;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Hierarchical Response Plan</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
          <h3 className="text-sm text-slate-400 mb-1">Initial State</h3>
          <p className="font-semibold">{data.initialState}</p>
        </div>
        <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
          <h3 className="text-sm text-slate-400 mb-1">Goal</h3>
          <p className="font-semibold text-green-400">{data.goal}</p>
        </div>
      </div>

      <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 flex flex-col items-center">
        <h2 className="text-lg font-bold w-full mb-6 text-center text-slate-300">Final Response Plan (Tree)</h2>
        <div className="w-full max-w-lg">
          {data.actions.map((step, index) => (
            <div key={step.id} className="flex items-center relative mb-6">
              {/* Connector line */}
              {index < data.actions.length - 1 && (
                <div className="absolute top-8 left-3 w-0.5 h-6 bg-slate-700 flex items-center justify-center">
                   <ArrowDown className="w-3 h-3 text-slate-500 absolute bottom-0 -mb-2 bg-slate-800 rounded-full" />
                </div>
              )}
              
              <div className={`w-6 h-6 rounded-full flex items-center justify-center mr-4 z-10 ${
                step.status === 'done' ? 'bg-green-500' :
                step.status === 'active' ? 'bg-blue-500 animate-pulse' : 'bg-slate-600'
              }`}>
                <GitCommit className="w-4 h-4 text-white" />
              </div>
              
              <div className={`flex-1 p-3 rounded border ${
                step.status === 'done' ? 'bg-slate-900 border-green-900/50 text-slate-300' :
                step.status === 'active' ? 'bg-blue-900/20 border-blue-500/50 text-blue-100 font-bold' : 
                'bg-slate-900 border-slate-800 text-slate-500'
              }`}>
                <div className="flex justify-between items-center">
                  <span>{step.action}</span>
                  {step.dependencies && step.dependencies.length > 0 && (
                     <span className="text-xs text-slate-500 font-mono">Depends: [{step.dependencies.join(',')}]</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
