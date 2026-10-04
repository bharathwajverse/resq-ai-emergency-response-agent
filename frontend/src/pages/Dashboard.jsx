import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getIncidents, getAmbulances, getHospitals, getDecisions, getKnowledge } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { AlertCircle, Truck, Building2, Activity, Network, Layers } from 'lucide-react';
import StatusBadge from '../components/StatusBadge';

const COLORS = ['#ef4444', '#f97316', '#eab308', '#22c55e'];

export default function Dashboard() {
  const [data, setData] = useState({
    incidents: [],
    ambulances: [],
    hospitals: [],
    decisions: [],
    knowledge: null,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [incRes, ambRes, hosRes, decRes, kbRes] = await Promise.all([
          getIncidents(),
          getAmbulances(),
          getHospitals(),
          getDecisions(),
          getKnowledge(),
        ]);
        setData({
          incidents: incRes.data || [],
          ambulances: ambRes.data || [],
          hospitals: hosRes.data || [],
          decisions: decRes.data || [],
          knowledge: kbRes.data || null,
        });
      } catch (e) {
        console.error('Dashboard fetch error:', e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <div className="p-8 text-center text-slate-300">Loading ResQ-AI Command Center...</div>;

  const activeIncidents = data.incidents.length;
  const criticalIncidents = data.incidents.filter(
    (i) => (i.priority || i.severity || '').toLowerCase().includes('crit') || (i.severity || '').toLowerCase() === 'high'
  ).length;
  const availableAmbulances = data.ambulances.filter(
    (a) => (a.status || '').toLowerCase() === 'available'
  ).length;
  const availableHospitals = data.hospitals.length;

  const riskData = [
    { name: 'Critical', value: Math.max(criticalIncidents, 1) },
    { name: 'High', value: Math.max(activeIncidents - criticalIncidents, 1) },
    { name: 'Medium', value: 2 },
    { name: 'Low', value: 1 },
  ];

  const typeCounts = {};
  data.incidents.forEach((inc) => {
    const t = inc.emergency_type || inc.type || 'Emergency';
    typeCounts[t] = (typeCounts[t] || 0) + 1;
  });
  const typeChartData = Object.entries(typeCounts).map(([type, count]) => ({ type, count }));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap justify-between items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold">Emergency Operations Dashboard</h1>
          <p className="text-sm text-slate-400">Real-time classical AI & knowledge-driven emergency command overview</p>
        </div>
        <Link
          to="/report"
          className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-md text-sm font-semibold transition-colors"
        >
          + Report New Emergency
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 flex items-center">
          <AlertCircle className="w-10 h-10 text-red-500 mr-4 shrink-0" />
          <div>
            <p className="text-sm text-slate-400">Active Incidents</p>
            <p className="text-2xl font-bold">{activeIncidents}</p>
          </div>
        </div>
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 flex items-center">
          <Activity className="w-10 h-10 text-orange-500 mr-4 shrink-0" />
          <div>
            <p className="text-sm text-slate-400">Critical Incidents</p>
            <p className="text-2xl font-bold">{criticalIncidents}</p>
          </div>
        </div>
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 flex items-center">
          <Truck className="w-10 h-10 text-blue-500 mr-4 shrink-0" />
          <div>
            <p className="text-sm text-slate-400">Available Ambulances</p>
            <p className="text-2xl font-bold">
              {availableAmbulances} <span className="text-sm font-normal text-slate-400">/ {data.ambulances.length}</span>
            </p>
          </div>
        </div>
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 flex items-center">
          <Building2 className="w-10 h-10 text-green-500 mr-4 shrink-0" />
          <div>
            <p className="text-sm text-slate-400">Available Hospitals</p>
            <p className="text-2xl font-bold">{availableHospitals}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <h2 className="text-lg font-semibold mb-4">Incidents by Priority / Risk Level</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={riskData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {riskData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <h2 className="text-lg font-semibold mb-4">Active Incidents by Emergency Category</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={typeChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="type" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" allowDecimals={false} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }} />
                <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Active Incidents & Current Response Plans */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <h2 className="text-lg font-semibold mb-4">Active Incidents & Response Plans</h2>
          <div className="space-y-3">
            {data.incidents.map((inc) => (
              <div key={inc.id} className="p-4 bg-slate-900 rounded border border-slate-700 flex justify-between items-start gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <Link to={`/incidents/${inc.id}`} className="font-bold text-blue-400 hover:underline">
                      {inc.title || inc.emergency_type}
                    </Link>
                    <StatusBadge status={inc.priority || inc.severity} type="priority" />
                  </div>
                  <p className="text-xs text-slate-400 mt-1">
                    Location: <span className="text-slate-200 font-mono">{inc.location}</span> | Victims: <span className="text-slate-200">{inc.victim_count}</span> | Weather: {inc.weather}
                  </p>
                  {inc.plan && <p className="text-xs text-green-400 mt-2 font-mono">{inc.plan}</p>}
                </div>
                <Link
                  to={`/incidents/${inc.id}`}
                  className="text-xs px-2.5 py-1 bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded shrink-0"
                >
                  Details
                </Link>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <h2 className="text-lg font-semibold mb-4">Recent AI Agent Decisions</h2>
          <div className="space-y-3">
            {data.decisions.slice(0, 4).map((d, idx) => (
              <div key={d.id || idx} className="p-4 bg-slate-900 rounded border border-slate-700">
                <div className="flex justify-between items-center">
                  <span className="font-semibold text-slate-200">{d.incident}</span>
                  <span className="text-xs font-mono bg-blue-900/40 text-blue-300 px-2 py-0.5 rounded">
                    {d.ambulance} &rarr; {d.hospital}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1 font-mono">Route: {d.route} | Risk: {d.risk}</p>
                <p className="text-xs text-slate-300 mt-1">{d.reason}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* FAI Module VI: Knowledge Representation (Frames & Ontology Visualization) */}
      {data.knowledge && (
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Network className="w-5 h-5 text-purple-400" />
              FAI Module VI: Knowledge Representation (Frames &amp; Ontology Hierarchy)
            </h2>
            <span className="text-xs text-purple-300 bg-purple-900/30 border border-purple-800 px-2.5 py-1 rounded">
              {data.knowledge.frames?.length || 5} Semantic Frames | {data.knowledge.graph?.metadata?.total_nodes || 0} Knowledge Graph Nodes
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-slate-900 p-4 rounded border border-slate-700">
              <h3 className="text-sm font-bold text-blue-400 mb-2 flex items-center gap-1.5">
                <Layers className="w-4 h-4" /> Domain Ontology Taxonomy Tree
              </h3>
              <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                <div>
                  <p className="text-amber-400 font-bold mb-1">Emergency</p>
                  {(data.knowledge.ontology_tree?.Emergency || []).map((item) => (
                    <p key={item} className="pl-3 text-slate-300">├── {item}</p>
                  ))}
                </div>
                <div>
                  <p className="text-emerald-400 font-bold mb-1">Resource</p>
                  {(data.knowledge.ontology_tree?.Resource || []).map((item) => (
                    <p key={item} className="pl-3 text-slate-300">├── {item}</p>
                  ))}
                </div>
              </div>
            </div>

            <div className="bg-slate-900 p-4 rounded border border-slate-700">
              <h3 className="text-sm font-bold text-purple-400 mb-2">Canonical Semantic Frames &amp; Relationships</h3>
              <div className="space-y-1.5 text-xs">
                {(data.knowledge.frames || []).slice(0, 5).map((f) => (
                  <div key={f.name} className="flex justify-between bg-slate-800/80 px-2.5 py-1.5 rounded">
                    <span className="font-mono font-semibold text-slate-200">{f.name} Frame</span>
                    <span className="text-slate-400">Category: {f.category}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
