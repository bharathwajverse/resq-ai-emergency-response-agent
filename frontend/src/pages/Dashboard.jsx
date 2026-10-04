import { useState, useEffect } from 'react';
import { getIncidents, getAmbulances, getHospitals, getDecisions } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { AlertCircle, Truck, Building2, Activity } from 'lucide-react';

const COLORS = ['#ef4444', '#f97316', '#eab308', '#22c55e'];

export default function Dashboard() {
  const [data, setData] = useState({ incidents: [], ambulances: [], hospitals: [], decisions: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // In a real app we'd fetch from APIs. Here we use mock data if API fails.
    const fetchData = async () => {
      try {
        const [incRes, ambRes, hosRes, decRes] = await Promise.all([
          getIncidents().catch(() => ({ data: [{ id: 1, type: 'Fire', priority: 'Critical' }] })),
          getAmbulances().catch(() => ({ data: [1,2,3] })),
          getHospitals().catch(() => ({ data: [1,2] })),
          getDecisions().catch(() => ({ data: [{ id: 1, incident: 'Fire at Main St', action: 'Dispatch A1' }] }))
        ]);
        setData({
          incidents: incRes.data,
          ambulances: ambRes.data,
          hospitals: hosRes.data,
          decisions: decRes.data
        });
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const riskData = [
    { name: 'Critical', value: 2 },
    { name: 'High', value: 5 },
    { name: 'Medium', value: 3 },
    { name: 'Low', value: 8 },
  ];

  if (loading) return <div className="p-8 text-center">Loading Dashboard...</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 flex items-center">
          <AlertCircle className="w-10 h-10 text-red-500 mr-4" />
          <div>
            <p className="text-sm text-slate-400">Active Incidents</p>
            <p className="text-2xl font-bold">{data.incidents.length || 15}</p>
          </div>
        </div>
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 flex items-center">
          <Activity className="w-10 h-10 text-orange-500 mr-4" />
          <div>
            <p className="text-sm text-slate-400">Critical Incidents</p>
            <p className="text-2xl font-bold">4</p>
          </div>
        </div>
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 flex items-center">
          <Truck className="w-10 h-10 text-blue-500 mr-4" />
          <div>
            <p className="text-sm text-slate-400">Available Ambulances</p>
            <p className="text-2xl font-bold">{data.ambulances.length || 8}</p>
          </div>
        </div>
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 flex items-center">
          <Building2 className="w-10 h-10 text-green-500 mr-4" />
          <div>
            <p className="text-sm text-slate-400">Available Hospitals</p>
            <p className="text-2xl font-bold">{data.hospitals.length || 3}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <h2 className="text-lg font-semibold mb-4">Incidents by Risk Level</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={riskData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {riskData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                  itemStyle={{ color: '#f8fafc' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
        
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
          <h2 className="text-lg font-semibold mb-4">Recent AI Decisions</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-slate-400 uppercase bg-slate-700">
                <tr>
                  <th className="px-4 py-3 rounded-tl-lg">Incident</th>
                  <th className="px-4 py-3 rounded-tr-lg">Action</th>
                </tr>
              </thead>
              <tbody>
                {data.decisions.length > 0 ? (
                  data.decisions.map((d, i) => (
                    <tr key={i} className="border-b border-slate-700">
                      <td className="px-4 py-3">{d.incident}</td>
                      <td className="px-4 py-3 text-blue-400">{d.action}</td>
                    </tr>
                  ))
                ) : (
                  <tr className="border-b border-slate-700">
                    <td className="px-4 py-3">Fire at Main St</td>
                    <td className="px-4 py-3 text-blue-400">Dispatched A1 to City Hospital via Route 3</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
