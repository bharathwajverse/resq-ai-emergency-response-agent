import { useState, useEffect } from 'react';
import { CheckCircle2, CircleDashed, AlertCircle } from 'lucide-react';
import { analyzeIncident } from '../services/api';

const stages = [
  { id: 'understanding', name: 'Understanding', desc: 'NLP classification & NER' },
  { id: 'knowledge', name: 'Knowledge Base', desc: 'Forward/Backward chaining' },
  { id: 'inference', name: 'Inference', desc: 'Rules evaluation' },
  { id: 'allocation', name: 'Resource Allocation', desc: 'Constraint Satisfaction' },
  { id: 'search', name: 'Search', desc: 'A* Pathfinding' },
  { id: 'risk', name: 'Risk', desc: 'Probabilistic simulation' },
  { id: 'planning', name: 'Planning', desc: 'Hierarchical Task Network' },
  { id: 'decision', name: 'Decision', desc: 'Final response action' },
];

export default function AgentConsole() {
  const [pipelineState, setPipelineState] = useState(
    stages.reduce((acc, stage) => ({ ...acc, [stage.id]: { status: 'pending' } }), {})
  );

  useEffect(() => {
    const fetchConsoleData = async () => {
      try {
        const res = await analyzeIncident({});
        if (res.data && res.data.stages) {
          setPipelineState(res.data.stages);
        }
      } catch (e) {
        runDemo();
      }
    };

    // Simulate pipeline run for demonstration
    const runDemo = async () => {
      let delay = 0;
      for (const stage of stages) {
        delay += 800;
        setTimeout(() => {
          setPipelineState(prev => ({ ...prev, [stage.id]: { status: 'running' } }));
        }, delay - 400);
        
        setTimeout(() => {
          setPipelineState(prev => ({ ...prev, [stage.id]: { status: 'complete', result: `Processed ${stage.name}` } }));
        }, delay);
      }
    };
    
    fetchConsoleData();
  }, []);

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">AI Agent Console</h1>
      <p className="text-slate-400">Visualizing the internal reasoning pipeline of the ResQ-AI agent.</p>

      <div className="flex flex-col space-y-4 relative before:absolute before:inset-0 before:ml-6 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-700 before:to-transparent">
        {stages.map((stage, index) => {
          const state = pipelineState[stage.id];
          return (
            <div key={stage.id} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
              <div className="flex items-center justify-center w-12 h-12 rounded-full border-4 border-slate-900 bg-slate-800 shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow">
                {state.status === 'complete' ? <CheckCircle2 className="text-green-500" /> : 
                 state.status === 'running' ? <CircleDashed className="text-blue-500 animate-spin" /> : 
                 <CircleDashed className="text-slate-600" />}
              </div>
              <div className="w-[calc(100%-4rem)] md:w-[calc(50%-3rem)] p-4 rounded-lg border border-slate-700 bg-slate-800 shadow-sm">
                <div className="flex items-center justify-between mb-1">
                  <h3 className="font-bold text-lg">{stage.name}</h3>
                  <span className={`text-xs px-2 py-1 rounded ${
                    state.status === 'complete' ? 'bg-green-900/30 text-green-400' : 
                    state.status === 'running' ? 'bg-blue-900/30 text-blue-400' : 'bg-slate-700 text-slate-400'
                  }`}>
                    {state.status.toUpperCase()}
                  </span>
                </div>
                <p className="text-sm text-slate-400 mb-2">{stage.desc}</p>
                {state.result && (
                  <div className="mt-2 text-sm bg-slate-900 p-2 rounded text-slate-300 font-mono">
                    {state.result}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
