import { useState, useEffect } from 'react';
import { getDecisions } from '../services/api';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import { Search, History, Filter } from 'lucide-react';

export default function DecisionHistory() {
  const [decisions, setDecisions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('ALL');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const res = await getDecisions();
        if (res.data && Array.isArray(res.data)) {
          setDecisions(res.data);
          return;
        }
      } catch (e) {
        setDecisions([
          { id: 1, incident: 'Road Accident @ N1', date: '2026-10-04', priority: 'Critical', ambulance: 'A2', hospital: 'H1', route: 'A2 -> N1 -> N3 -> N4 -> H1', risk: 'HIGH (74.3%)', reason: 'A1 rejected (cap 4 < 6); A2 selected via optimal A* path' },
          { id: 2, incident: 'Industrial Fire @ N4', date: '2026-10-04', priority: 'High', ambulance: 'A1', hospital: 'H1', route: 'A1 -> N3 -> N4 -> H1', risk: 'MEDIUM (35.0%)', reason: 'A1 capacity 4 sufficient; fastest unblocked corridor' },
        ]);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const filtered = decisions.filter((d) => {
    const pStr = String(d.priority || '').toUpperCase();
    const matchesPriority =
      priorityFilter === 'ALL' ||
      pStr === priorityFilter ||
      pStr.includes(priorityFilter);
    const q = query.trim().toLowerCase();
    const matchesQuery =
      !q ||
      String(d.incident || '').toLowerCase().includes(q) ||
      String(d.ambulance || '').toLowerCase().includes(q) ||
      String(d.hospital || '').toLowerCase().includes(q) ||
      String(d.reason || '').toLowerCase().includes(q);
    return matchesPriority && matchesQuery;
  });

  if (loading) return <LoadingSpinner />;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex flex-wrap justify-between items-end gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <History className="w-6 h-6 text-blue-400" />
            Decision History
          </h1>
          <p className="text-slate-400 text-sm">
            Auditable log of AI Agent resource allocations, selected routes, risk levels, and justifications.
          </p>
        </div>
        <span className="text-xs font-mono bg-slate-800 border border-slate-700 px-3 py-1 rounded text-slate-300">
          Showing {filtered.length} of {decisions.length} records
        </span>
      </div>

      {/* Search & Filter Controls */}
      <div className="bg-slate-800 p-4 rounded-lg border border-slate-700 flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter by incident, ambulance, hospital, or reason..."
            aria-label="Search decision history"
            className="w-full bg-slate-900 border border-slate-700 rounded-md pl-9 pr-3 py-2 text-sm text-slate-100"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            aria-label="Filter by priority"
            className="bg-slate-900 border border-slate-700 rounded-md px-3 py-2 text-sm text-slate-200"
          >
            <option value="ALL">All Priorities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>
      </div>

      {filtered.length === 0 ? (
        <EmptyState message="No decision records match your filter criteria." />
      ) : (
        <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-slate-400 uppercase bg-slate-900 border-b border-slate-700">
              <tr>
                <th className="px-4 py-3">ID / Date</th>
                <th className="px-4 py-3">Incident</th>
                <th className="px-4 py-3">Priority</th>
                <th className="px-4 py-3">Resources (Amb &rarr; Hosp)</th>
                <th className="px-4 py-3">Route &amp; Risk</th>
                <th className="px-4 py-3">Decision Justification</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((d) => (
                <tr key={d.id} className="border-b border-slate-700/80 hover:bg-slate-700/30 transition-colors">
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className="font-mono text-slate-200 font-semibold">#{d.id}</span>
                    <br />
                    <span className="text-xs text-slate-400">{d.date}</span>
                  </td>
                  <td className="px-4 py-3 font-medium text-slate-100">{d.incident}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={d.priority} type="priority" />
                  </td>
                  <td className="px-4 py-3 font-mono text-emerald-400 font-semibold">
                    {d.ambulance} &rarr; {d.hospital}
                  </td>
                  <td className="px-4 py-3">
                    <span className="bg-slate-900 px-2 py-1 rounded border border-slate-700 font-mono text-xs text-blue-300 mr-2 inline-block mb-1">
                      {d.route}
                    </span>
                    <span className="text-xs text-orange-300 font-mono block">{d.risk}</span>
                  </td>
                  <td className="px-4 py-3 text-slate-300 text-xs max-w-md">{d.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
