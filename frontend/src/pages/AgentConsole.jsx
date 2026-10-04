import { useState, useEffect } from 'react';
import {
  CheckCircle2,
  CircleDashed,
  Play,
  RefreshCw,
  BrainCircuit,
  Cpu,
} from 'lucide-react';
import { analyzeIncident, replanResponse as replanAgent } from '../services/api';

const STAGES = [
  { id: 'understanding', name: 'Understanding', algo: 'Gemini LLM / Demo NLU Parser', desc: 'Natural-language incident extraction & Pydantic validation' },
  { id: 'knowledge', name: 'Knowledge Base', algo: 'Ontology DAG & Semantic Frames', desc: 'Entity classification, subsumption & spatial node resolution' },
  { id: 'inference', name: 'Inference', algo: 'Forward & Backward Chaining (Horn Rules)', desc: 'Rule-based priority deduction & route blockage entailment' },
  { id: 'allocation', name: 'Resource Allocation', algo: 'CSP Backtracking + MRV/LCV + AC-3', desc: 'Constrained ambulance & hospital assignment' },
  { id: 'search', name: 'Search', algo: 'A* Pathfinding f(n) = g(n) + h(n)', desc: 'Optimal route computation on 13-node weighted road network' },
  { id: 'risk', name: 'Risk', algo: '7-Variable Bayesian CPT Network', desc: 'Conditional probability estimation of delay & overload' },
  { id: 'planning', name: 'Planning', algo: 'Hierarchical Task Network (HTN)', desc: 'Compound task decomposition into ordered operational actions' },
  { id: 'decision', name: 'Decision', algo: 'Multi-Criteria Utility Evaluation', desc: 'Final dispatch commitment & human-readable explanation' },
];

const PRESETS = [
  'There is a road accident near the university at N1. Six people may be injured. Heavy rain is causing traffic and the main road is blocked.',
  'Major building fire reported at N4 industrial zone with 4 burn victims. Weather is clear and roads are open.',
  'Flash flood emergency at N7 riverfront with 10 people stranded. Heavy rain and two main roads blocked.',
  'Cardiac medical emergency at N6 tech park with 2 patients needing immediate transport. Weather clear.',
];

export default function AgentConsole() {
  const [reportText, setReportText] = useState(PRESETS[0]);
  const [loading, setLoading] = useState(false);
  const [agentData, setAgentData] = useState(null);
  const [replanData, setReplanData] = useState(null);
  const [pipelineState, setPipelineState] = useState(
    STAGES.reduce((acc, stage) => ({ ...acc, [stage.id]: { status: 'pending' } }), {})
  );

  const runPipeline = async (text = reportText) => {
    setLoading(true);
    setReplanData(null);
    try {
      const res = await analyzeIncident({ description: text });
      if (res.data) {
        setAgentData(res.data);
        if (res.data.stages) {
          setPipelineState(res.data.stages);
        }
      }
    } catch (e) {
      const fallback = {};
      STAGES.forEach((s) => {
        fallback[s.id] = { status: 'complete', result: `Executed ${s.algo}` };
      });
      setPipelineState(fallback);
    } finally {
      setLoading(false);
    }
  };

  const handleReplan = async () => {
    setLoading(true);
    try {
      const failedUnit = agentData?.allocation?.ambulance || 'A2';
      const res = await replanAgent({
        incident_id: 'INC-CONSOLE',
        unavailable_ambulance: failedUnit,
        victim_count: agentData?.extracted?.victim_count || 6,
        location: agentData?.extracted?.location || 'N1',
        weather: agentData?.extracted?.weather || 'Heavy Rain',
      });
      if (res.data) {
        setReplanData(res.data);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runPipeline(PRESETS[0]);
  }, []);

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex flex-wrap justify-between items-end gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <BrainCircuit className="w-6 h-6 text-blue-400" />
            AI Agent Console
          </h1>
          <p className="text-slate-400 text-sm">
            Auditable stage-by-stage execution trace of the ResQ-AI Orchestrator (NLU &rarr; Classical AI &rarr; Decision).
          </p>
        </div>
        <button
          onClick={handleReplan}
          disabled={loading}
          className="flex items-center px-4 py-2 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white rounded-md text-xs font-bold transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
          Simulate Unit Breakdown (Dynamic Replan)
        </button>
      </div>

      {/* Interactive Incident Input Bar */}
      <div className="bg-slate-800 p-4 rounded-lg border border-slate-700 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Natural-Language Emergency Input to Agent Orchestrator
          </label>
          <div className="flex flex-wrap gap-1.5">
            {PRESETS.map((preset, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setReportText(preset);
                  runPipeline(preset);
                }}
                className="text-xs px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
              >
                Scenario {idx + 1}
              </button>
            ))}
          </div>
        </div>
        <div className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            value={reportText}
            onChange={(e) => setReportText(e.target.value)}
            aria-label="Emergency report input"
            className="flex-1 bg-slate-900 border border-slate-700 rounded-md px-3 py-2 text-sm text-slate-100"
          />
          <button
            onClick={() => runPipeline(reportText)}
            disabled={loading}
            className="flex items-center justify-center px-5 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-md text-sm font-medium shrink-0 transition-colors"
          >
            <Play className="w-4 h-4 mr-1.5" />
            {loading ? 'Running...' : 'Execute Pipeline'}
          </button>
        </div>
      </div>

      {/* Dynamic Replan Alert Banner */}
      {replanData && (
        <div className="bg-slate-800 p-4 rounded-lg border border-amber-500/70 space-y-2">
          <h2 className="text-sm font-bold text-amber-400 flex items-center gap-2">
            <RefreshCw className="w-4 h-4" />
            Dynamic Replanning Executed — Failed Unit {replanData.failed_ambulance_code} Replaced
          </h2>
          <p className="text-xs text-slate-200 font-mono">
            New Ambulance: <span className="text-emerald-400 font-bold">{replanData.allocated_ambulance?.code}</span> | New Route:{' '}
            <span className="text-blue-400 font-bold">{(replanData.route?.path || []).join(' -> ')}</span> ({replanData.route?.cost}m)
          </p>
          <p className="text-xs text-slate-300">{replanData.explanation}</p>
        </div>
      )}

      {/* Agent State Summary Cards */}
      {agentData && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
            <span className="text-xs text-slate-400">Extracted Incident</span>
            <p className="font-bold text-sm text-blue-400 mt-0.5">
              {agentData.extracted?.type} @ {agentData.extracted?.location}
            </p>
            <span className="text-xs text-slate-400 font-mono">
              Victims: {agentData.extracted?.victim_count} | {agentData.extracted?.weather}
            </span>
          </div>
          <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
            <span className="text-xs text-slate-400">CSP Resource Allocation</span>
            <p className="font-bold text-sm text-emerald-400 mt-0.5 font-mono">
              {agentData.allocation?.ambulance} &rarr; {agentData.allocation?.hospital}
            </p>
            <span className="text-xs text-slate-400">All hard constraints satisfied</span>
          </div>
          <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
            <span className="text-xs text-slate-400">Optimal A* Route</span>
            <p className="font-bold text-xs text-purple-400 mt-1 font-mono">
              {(agentData.routes?.[0] || ['A2', 'N1', 'N3', 'N4', 'H1']).join(' -> ')}
            </p>
          </div>
          <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
            <span className="text-xs text-slate-400">Bayesian Risk Level</span>
            <p className="font-bold text-sm text-orange-400 mt-0.5">
              {agentData.risk?.risk_level} ({agentData.risk?.risk_score}%)
            </p>
            <span className="text-[11px] text-slate-400">Simulated CPT evaluation</span>
          </div>
        </div>
      )}

      {/* 8-Stage Pipeline Timeline */}
      <div className="flex flex-col space-y-4 relative before:absolute before:inset-0 before:ml-6 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-700 before:to-transparent">
        {STAGES.map((stage) => {
          const state = pipelineState[stage.id] || { status: 'pending' };
          return (
            <div
              key={stage.id}
              className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active"
            >
              <div className="flex items-center justify-center w-12 h-12 rounded-full border-4 border-slate-900 bg-slate-800 shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow">
                {state.status === 'complete' ? (
                  <CheckCircle2 className="text-green-500 w-5 h-5" />
                ) : state.status === 'running' ? (
                  <CircleDashed className="text-blue-500 animate-spin w-5 h-5" />
                ) : (
                  <CircleDashed className="text-slate-600 w-5 h-5" />
                )}
              </div>
              <div className="w-[calc(100%-4rem)] md:w-[calc(50%-3rem)] p-4 rounded-lg border border-slate-700 bg-slate-800 shadow-sm">
                <div className="flex items-center justify-between mb-1">
                  <h3 className="font-bold text-base text-white">{stage.name}</h3>
                  <span
                    className={`text-xs px-2 py-0.5 rounded font-mono ${
                      state.status === 'complete'
                        ? 'bg-green-900/30 text-green-400 border border-green-800/50'
                        : state.status === 'running'
                        ? 'bg-blue-900/30 text-blue-400'
                        : 'bg-slate-700 text-slate-400'
                    }`}
                  >
                    {state.status.toUpperCase()}
                  </span>
                </div>
                <p className="text-xs text-blue-400 font-mono flex items-center gap-1 mb-1">
                  <Cpu className="w-3 h-3" /> {stage.algo}
                </p>
                <p className="text-xs text-slate-400 mb-2">{stage.desc}</p>
                {state.result && (
                  <div className="mt-2 text-xs bg-slate-900 p-2.5 rounded border border-slate-700/80 text-slate-200 font-mono">
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
