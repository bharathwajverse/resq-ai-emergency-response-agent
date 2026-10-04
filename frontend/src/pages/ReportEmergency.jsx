import { useState } from 'react';
import { analyzeIncident, createIncident, planResponse, replanResponse } from '../services/api';
import { Brain, GitBranch, RefreshCw, CheckCircle2 } from 'lucide-react';

const DEMO_SCENARIOS = [
  {
    label: 'Scenario 1: Road Accident (6 victims, Heavy Rain, Road N1-N2 Blocked)',
    type: 'Traffic Accident',
    description: 'There is a road accident near N1 University. 6 people are injured. Heavy rain is causing traffic and main road N1-N2 is blocked.',
    location: 'N1',
    victims: 6,
    weather: 'Heavy Rain',
    roadCondition: 'Blocked',
    severity: 'High',
  },
  {
    label: 'Scenario 2: Warehouse Fire (4 victims, Clear Weather, Road Clear)',
    type: 'Fire',
    description: 'Commercial warehouse fire at Midtown N4. 4 victims require burn unit transport. Normal clear weather and road clear.',
    location: 'N4',
    victims: 4,
    weather: 'Clear',
    roadCondition: 'Clear',
    severity: 'Medium',
  },
  {
    label: 'Scenario 3: Flash Flood Disaster (10 victims, Heavy Rain, Two Roads Blocked)',
    type: 'Natural Disaster',
    description: 'Massive flash flood near River Bridge N2. 10 people affected, heavy rain, two roads blocked.',
    location: 'N2',
    victims: 10,
    weather: 'Heavy Rain',
    roadCondition: 'Flooded',
    severity: 'Critical',
  },
  {
    label: 'Scenario 4: Medical Emergency (2 victims, Clear Weather, Road Clear)',
    type: 'Medical Emergency',
    description: 'Cardiac medical emergency near West Suburban Ring N8. 2 victims, clear weather and road clear.',
    location: 'N8',
    victims: 2,
    weather: 'Clear',
    roadCondition: 'Clear',
    severity: 'High',
  },
  {
    label: 'Scenario 5: Multi-Incident Contention (6 victims at N1 + 4 victims at N4)',
    type: 'Traffic Accident',
    description: 'Simultaneous multi-vehicle pileup at N1 with 6 victims requiring immediate ALS trauma dispatch under fleet contention.',
    location: 'N1',
    victims: 6,
    weather: 'Rain',
    roadCondition: 'Clear',
    severity: 'Critical',
  },
];

export default function ReportEmergency() {
  const [formData, setFormData] = useState(DEMO_SCENARIOS[0]);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [planResult, setPlanResult] = useState(null);
  const [replanResult, setReplanResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === 'victims' ? Number(value) : value,
    }));
  };

  const handlePresetChange = (e) => {
    const idx = Number(e.target.value);
    if (DEMO_SCENARIOS[idx]) {
      setFormData(DEMO_SCENARIOS[idx]);
      setAnalysisResult(null);
      setPlanResult(null);
      setReplanResult(null);
    }
  };

  const handleAnalyze = async () => {
    setLoading(true);
    setReplanResult(null);
    try {
      const res = await analyzeIncident({
        text: formData.description,
        ...formData,
      });
      setAnalysisResult(res.data);
    } catch (e) {
      console.error('Analyze error:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleGeneratePlan = async () => {
    setLoading(true);
    setReplanResult(null);
    try {
      const created = await createIncident({
        title: `${formData.type} at ${formData.location}`,
        emergency_type: formData.type,
        description: formData.description,
        location: formData.location,
        victim_count: Number(formData.victims),
        weather: formData.weather,
        road_condition: formData.roadCondition,
        severity: formData.severity,
      });
      const incId = created.data.id;
      const planRes = await planResponse({ incident_id: incId });
      setPlanResult(planRes.data);
    } catch (e) {
      console.error('Generate plan error:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerReplan = async () => {
    if (!planResult) return;
    setLoading(true);
    try {
      const currentAmb =
        planResult.allocated_ambulance?.code ||
        planResult.ambulance?.code ||
        'A2';
      const repRes = await replanResponse({
        incident_id: planResult.incident_id,
        failed_ambulance_code: currentAmb.split('+')[0],
        reason: `Simulated breakdown of ${currentAmb} en route`,
      });
      setReplanResult(repRes.data);
    } catch (e) {
      console.error('Replan error:', e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex flex-wrap justify-between items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold">Report Emergency &amp; Autonomous AI Dispatch</h1>
          <p className="text-sm text-slate-400">
            Submit a natural-language emergency report or select one of the 5 official FAI demo scenarios
          </p>
        </div>
      </div>

      <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 space-y-6">
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-blue-400 mb-2">
            Quick Load Official Demo Scenario (R6 Verification)
          </label>
          <select
            onChange={handlePresetChange}
            className="w-full bg-slate-900 border border-slate-700 rounded-md p-2.5 text-sm text-slate-200"
          >
            {DEMO_SCENARIOS.map((scen, idx) => (
              <option key={idx} value={idx}>
                {scen.label}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Natural Language Emergency Report (LLM / Deterministic NLU Input)
            </label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows="3"
              className="w-full bg-slate-900 border border-slate-700 rounded-md p-3 text-slate-100 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Emergency Type</label>
            <select name="type" value={formData.type} onChange={handleChange} className="w-full bg-slate-900 border border-slate-700 rounded-md p-2">
              <option>Traffic Accident</option>
              <option>Fire</option>
              <option>Natural Disaster</option>
              <option>Medical Emergency</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Severity</label>
            <select name="severity" value={formData.severity} onChange={handleChange} className="w-full bg-slate-900 border border-slate-700 rounded-md p-2">
              <option>Low</option>
              <option>Medium</option>
              <option>High</option>
              <option>Critical</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Graph Node Location</label>
            <select name="location" value={formData.location} onChange={handleChange} className="w-full bg-slate-900 border border-slate-700 rounded-md p-2">
              <option value="N1">N1 (Downtown / University Junction)</option>
              <option value="N2">N2 (River Bridge)</option>
              <option value="N3">N3 (North Bypass)</option>
              <option value="N4">N4 (Midtown Industrial)</option>
              <option value="N5">N5 (East Valley)</option>
              <option value="N6">N6 (Tech Park)</option>
              <option value="N7">N7 (Harbor District)</option>
              <option value="N8">N8 (West Suburban Ring)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Estimated Victims</label>
            <input
              type="number"
              name="victims"
              min="1"
              max="50"
              value={formData.victims}
              onChange={handleChange}
              className="w-full bg-slate-900 border border-slate-700 rounded-md p-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Weather Condition</label>
            <select name="weather" value={formData.weather} onChange={handleChange} className="w-full bg-slate-900 border border-slate-700 rounded-md p-2">
              <option>Clear</option>
              <option>Rain</option>
              <option>Heavy Rain</option>
              <option>Fog</option>
              <option>Snow</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Road Condition</label>
            <select name="roadCondition" value={formData.roadCondition} onChange={handleChange} className="w-full bg-slate-900 border border-slate-700 rounded-md p-2">
              <option>Clear</option>
              <option>Wet</option>
              <option>Blocked</option>
              <option>Flooded</option>
            </select>
          </div>
        </div>

        <div className="flex flex-wrap gap-4 pt-2">
          <button
            onClick={handleAnalyze}
            disabled={loading}
            className="flex items-center px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-md font-medium transition-colors"
          >
            <Brain className="w-4 h-4 mr-2" />
            Analyze Emergency
          </button>

          <button
            onClick={handleGeneratePlan}
            disabled={loading}
            className="flex items-center px-6 py-2.5 bg-purple-600 hover:bg-purple-500 text-white rounded-md font-medium transition-colors"
          >
            <GitBranch className="w-4 h-4 mr-2" />
            Generate Response Plan
          </button>
        </div>
      </div>

      {/* Analysis Output */}
      {analysisResult && (
        <div className="bg-slate-800 p-6 rounded-lg border border-blue-800/60 space-y-4">
          <h2 className="text-lg font-bold text-blue-400 flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5" /> NLU Extraction &amp; Classical Inference Analysis
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div className="bg-slate-900 p-3 rounded border border-slate-700">
              <span className="text-xs text-slate-400">Extracted Type</span>
              <p className="font-bold">{analysisResult.extracted?.type}</p>
            </div>
            <div className="bg-slate-900 p-3 rounded border border-slate-700">
              <span className="text-xs text-slate-400">Location &amp; Victims</span>
              <p className="font-bold">{analysisResult.extracted?.location} ({analysisResult.extracted?.victim_count} victims)</p>
            </div>
            <div className="bg-slate-900 p-3 rounded border border-slate-700">
              <span className="text-xs text-slate-400">CSP Allocation</span>
              <p className="font-bold text-green-400">
                {analysisResult.allocation?.ambulance} &rarr; {analysisResult.allocation?.hospital}
              </p>
            </div>
            <div className="bg-slate-900 p-3 rounded border border-slate-700">
              <span className="text-xs text-slate-400">Bayesian Risk Level</span>
              <p className="font-bold text-orange-400">
                {analysisResult.risk?.risk_level} ({analysisResult.risk?.risk_score}%)
              </p>
            </div>
          </div>
          <p className="text-sm text-slate-300 bg-slate-900 p-3 rounded border border-slate-700">
            {analysisResult.explanation}
          </p>
        </div>
      )}

      {/* Full 11-Stage Response Plan Output + Dynamic Replanning Trigger */}
      {planResult && (
        <div className="bg-slate-800 p-6 rounded-lg border border-purple-800/60 space-y-4">
          <div className="flex flex-wrap justify-between items-center gap-4">
            <h2 className="text-lg font-bold text-purple-400">
              11-Stage Autonomous Agent Response Plan (ID: {planResult.incident_id})
            </h2>
            <button
              onClick={handleTriggerReplan}
              disabled={loading}
              className="flex items-center px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded text-xs font-bold transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
              Simulate Ambulance Breakdown (Trigger Dynamic Replan)
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-sm">
            <div className="bg-slate-900 p-3 rounded border border-slate-700">
              <span className="text-xs text-slate-400">Inferred Priority</span>
              <p className="font-bold text-red-400">{planResult.priority}</p>
            </div>
            <div className="bg-slate-900 p-3 rounded border border-slate-700">
              <span className="text-xs text-slate-400">Allocated Ambulance</span>
              <p className="font-bold text-green-400">
                {planResult.allocated_ambulance?.code} (Cap: {planResult.allocated_ambulance?.capacity})
              </p>
            </div>
            <div className="bg-slate-900 p-3 rounded border border-slate-700">
              <span className="text-xs text-slate-400">Allocated Hospital</span>
              <p className="font-bold text-blue-400">
                {planResult.allocated_hospital?.code} ({planResult.allocated_hospital?.name})
              </p>
            </div>
            <div className="bg-slate-900 p-3 rounded border border-slate-700">
              <span className="text-xs text-slate-400">A* Route &amp; Cost</span>
              <p className="font-mono text-xs font-bold text-emerald-400">
                {(planResult.route?.path || []).join(' -> ')} ({planResult.route?.cost}m)
              </p>
            </div>
          </div>

          <div className="bg-slate-900 p-3 rounded border border-slate-700 text-sm text-slate-300">
            {planResult.explanation}
          </div>
        </div>
      )}

      {/* Replanned Output */}
      {replanResult && (
        <div className="bg-slate-800 p-6 rounded-lg border border-amber-500/70 space-y-3">
          <h3 className="text-md font-bold text-amber-400 flex items-center gap-2">
            <RefreshCw className="w-4 h-4" /> Dynamic Replanning Executed (Failed Unit: {replanResult.failed_ambulance_code})
          </h3>
          <p className="text-sm text-slate-200">
            <strong>New Allocated Ambulance:</strong>{' '}
            <span className="text-green-400 font-mono">{replanResult.allocated_ambulance?.code}</span> |{' '}
            <strong>Updated Route:</strong>{' '}
            <span className="text-blue-400 font-mono">{(replanResult.route?.path || []).join(' -> ')}</span>
          </p>
          <p className="text-xs text-slate-300 bg-slate-900 p-3 rounded">{replanResult.explanation}</p>
        </div>
      )}
    </div>
  );
}
