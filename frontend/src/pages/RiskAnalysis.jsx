import { useState, useEffect } from 'react';
import { analyzeRisk } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';

export default function RiskAnalysis() {
  const [riskFactors, setRiskFactors] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await analyzeRisk({});
        if (res.data && Array.isArray(res.data.factors)) {
          setRiskFactors(res.data.factors);
          return;
        }
        if (res.data && Array.isArray(res.data)) {
          setRiskFactors(res.data);
          return;
        }
      } catch (e) {
        setRiskFactors([
          { name: 'Weather', risk: 80 },
          { name: 'Traffic', risk: 65 },
          { name: 'Time of Day', risk: 45 },
          { name: 'Hospital Load', risk: 90 },
          { name: 'Road Cond.', risk: 50 },
        ]);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold">Risk Analysis</h1>
          <p className="text-slate-400">Probabilistic models for decision reliability.</p>
        </div>
        <p className="text-xs text-orange-400 border border-orange-900/50 bg-orange-900/20 px-3 py-1 rounded">
          Simulated/Educational Probabilities
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <h2 className="text-lg font-semibold mb-4">Risk Factors Overview</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="80%" data={riskFactors}>
                <PolarGrid stroke="#334155" />
                <PolarAngleAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#64748b' }} />
                <Radar name="Risk Level" dataKey="risk" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.5} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <h2 className="text-lg font-semibold mb-4">Probability of Failure (by Factor)</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={riskFactors}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" stroke="#94a3b8" tick={{ fontSize: 12 }} />
                <YAxis stroke="#94a3b8" />
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
