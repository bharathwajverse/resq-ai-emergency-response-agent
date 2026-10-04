import { useState, useEffect } from 'react';
import { getDecisions } from '../services/api';
import StatusBadge from '../components/StatusBadge';

export default function DecisionHistory() {
  const [decisions, setDecisions] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await getDecisions();
        if (res.data && Array.isArray(res.data)) {
          setDecisions(res.data);
          return;
        }
      } catch (e) {
        setDecisions([
          { id: 1, incident: 'Fire on 5th Ave', date: '2023-11-01', priority: 'High', ambulance: 'A1', hospital: 'City Gen', route: 'R-4', risk: 'Medium', reason: 'Closest available with burn unit' },
          { id: 2, incident: 'Traffic Accident I-95', date: '2023-11-02', priority: 'Critical', ambulance: 'A3', hospital: 'Trauma Center', route: 'R-1', risk: 'High', reason: 'High severity, fastest route clear' },
          { id: 3, incident: 'Medical Emergency', date: '2023-11-03', priority: 'Low', ambulance: 'A2', hospital: 'St. Marys', route: 'R-7', risk: 'Low', reason: 'Standard protocol' }
        ]);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Decision History</h1>
      <p className="text-slate-400">Audit log of past AI-driven resource allocations.</p>

      <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-slate-400 uppercase bg-slate-900 border-b border-slate-700">
            <tr>
              <th className="px-4 py-3">ID / Date</th>
              <th className="px-4 py-3">Incident</th>
              <th className="px-4 py-3">Priority</th>
              <th className="px-4 py-3">Resources (Amb/Hosp)</th>
              <th className="px-4 py-3">Route / Risk</th>
              <th className="px-4 py-3">Decision Reason</th>
            </tr>
          </thead>
          <tbody>
            {decisions.map(d => (
              <tr key={d.id} className="border-b border-slate-700 hover:bg-slate-750">
                <td className="px-4 py-3">
                  <span className="font-mono text-slate-300">#{d.id}</span>
                  <br/>
                  <span className="text-xs text-slate-500">{d.date}</span>
                </td>
                <td className="px-4 py-3 font-medium">{d.incident}</td>
                <td className="px-4 py-3"><StatusBadge status={d.priority} type="priority" /></td>
                <td className="px-4 py-3 text-slate-300">
                  {d.ambulance} &rarr; {d.hospital}
                </td>
                <td className="px-4 py-3">
                  <span className="bg-slate-900 px-2 py-1 rounded border border-slate-700 mr-2">{d.route}</span>
                  <span className="text-xs">{d.risk}</span>
                </td>
                <td className="px-4 py-3 text-slate-400 italic text-xs">{d.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
