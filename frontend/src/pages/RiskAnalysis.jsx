import { useState, useEffect } from 'react';
import { analyzeRisk } from '../services/api';
import { Play, ShieldAlert } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';

const DEFAULT_FACTORS = [
  { name: 'Weather', risk: 78 },
  { name: 'Traffic', risk: 72 },
  { name: 'Travel Delay', risk: 88 },
  { name: 'Victim Severity', risk: 90 },
  { name: 'Hospital Load', risk: 38 },
];

export default function RiskAnalysis() {
  const [weather, setWeather] = useState('Heavy Rain');
  const [roadCondition, setRoadCondition] = useState('Blocked');
  const [victims, setVictims] = useState(6);
  const [severity, setSeverity] = useState('High');
  const [riskData, setRiskData] = useState({
    overall_risk: 0.743,
    risk_score: 74.3,
    risk_level: 'HIGH',
    weather_risk: 0.78,
    traffic_risk: 0.85,
    travel_delay_probability: 0.88,
    high_severity_probability: 0.90,
    hospital_overload_probability: 0.38,
    factors: DEFAULT_FACTORS,
    disclaimer: 'Simulated / Educational Probabilities — not for real-world emergency dispatch.',
  });

  const runRiskEngine = async (w = weather, rc = roadCondition, vc = victims, sev = severity) => {
    try {
      const res = await analyzeRisk({
        weather: w,
        road_condition: rc,
        victim_count: Number(vc),
        severity: sev,
      });
      if (res.data) {
        setRiskData({
          ...res.data,
          factors:
            Array.isArray(res.data.factors) && res.data.factors.length > 0
              ? res.data.factors
              : DEFAULT_FACTORS,
        });
      }
    } catch (e) {
      // Keep existing state on error
    }
  };

  useEffect(() => {
    runRiskEngine();
  }, []);

  const riskFactors = riskData.factors && riskData.factors.length > 0 ? riskData.factors : DEFAULT_FACTORS;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex flex-wrap justify-between items-end gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <ShieldAlert className="w-6 h-6 text-orange-400" />
            Risk Analysis (FAI Module VIII — Bayesian Reasoning)
          </h1>
          <p className="text-slate-400 text-sm">
            Conditional Probability Table (CPT) inference over 7 stochastic emergency variables.
          </p>
        </div>
        <p className="text-xs text-orange-400 border border-orange-900/50 bg-orange-900/20 px-3 py-1 rounded font-semibold">
          Simulated/Educational Probabilities
        </p>
      </div>

      {/* Interactive Bayesian Evidence Controls */}
      <div className="bg-slate-800 p-4 rounded-lg border border-slate-700 grid grid-cols-1 md:grid-cols-5 gap-4 items-end">
        <div>
          <label className="block text-xs text-slate-400 mb-1">Weather Evidence</label>
          <select value={weather} onChange={(e) => setWeather(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm">
            <option>Clear</option>
            <option>Rain</option>
            <option>Heavy Rain</option>
            <option>Fog</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">Road Condition</label>
          <select value={roadCondition} onChange={(e) => setRoadCondition(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm">
            <option>Clear</option>
            <option>Wet</option>
            <option>Blocked</option>
            <option>Flooded</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">Victim Count</label>
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
          <label className="block text-xs text-slate-400 mb-1">Reported Severity</label>
          <select value={severity} onChange={(e) => setSeverity(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm">
            <option>Low</option>
            <option>Medium</option>
            <option>High</option>
            <option>Critical</option>
          </select>
        </div>
        <button
          onClick={() => runRiskEngine(weather, roadCondition, victims, severity)}
          className="flex justify-center items-center px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded text-sm font-medium"
        >
          <Play className="w-4 h-4 mr-1.5" /> Evaluate CPT
        </button>
      </div>

      {/* Conditional Probability Readout Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
          <p className="text-xs text-slate-400 font-mono">P(Delay | Weather, Traffic)</p>
          <p className="text-2xl font-bold text-blue-400">
            {Math.round((riskData.travel_delay_probability || 0) * 100)}%
          </p>
        </div>
        <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
          <p className="text-xs text-slate-400 font-mono">P(High Severity | Victims)</p>
          <p className="text-2xl font-bold text-purple-400">
            {Math.round((riskData.high_severity_probability || 0) * 100)}%
          </p>
        </div>
        <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
          <p className="text-xs text-slate-400 font-mono">P(Hospital Overload | Load)</p>
          <p className="text-2xl font-bold text-amber-400">
            {Math.round((riskData.hospital_overload_probability || 0) * 100)}%
          </p>
        </div>
        <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
          <p className="text-xs text-slate-400 font-mono">Composite Response Risk</p>
          <p className="text-2xl font-bold text-red-400">
            {riskData.risk_score}% ({riskData.risk_level})
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <h2 className="text-lg font-semibold mb-4">Risk Factors Overview</h2>
          <div className="h-72">
            {riskFactors.length >= 3 && (
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="80%" data={riskFactors}>
                  <PolarGrid stroke="#334155" />
                  <PolarAngleAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#64748b' }} />
                  <Radar name="Risk Level" dataKey="risk" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.5} />
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }} />
                </RadarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <h2 className="text-lg font-semibold mb-4">Conditional Risk Probability (by Factor)</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={riskFactors}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" stroke="#94a3b8" tick={{ fontSize: 12 }} />
                <YAxis stroke="#94a3b8" domain={[0, 100]} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }} />
                <Bar dataKey="risk" fill="#ef4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
