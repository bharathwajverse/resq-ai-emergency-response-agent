import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Brain, RefreshCw } from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import { getIncidentById, getIncidents, planResponse, replanResponse } from '../services/api';

export default function IncidentDetails() {
  const { id } = useParams();
  const [incident, setIncident] = useState(null);
  const [planData, setPlanData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadIncident = async () => {
      try {
        const res = await getIncidentById(id);
        setIncident(res.data);
      } catch (err) {
        try {
          const listRes = await getIncidents();
          const first = (listRes.data || [])[0];
          if (first) setIncident(first);
        } catch (e) {
          console.error(e);
        }
      } finally {
        setLoading(false);
      }
    };
    loadIncident();
  }, [id]);

  const handleDispatchPlan = async () => {
    if (!incident) return;
    const res = await planResponse({ incident_id: incident.id });
    setPlanData(res.data);
  };

  const handleReplan = async () => {
    if (!incident) return;
    const ambCode = planData?.allocated_ambulance?.code || (typeof incident.ambulance === 'string' ? incident.ambulance : incident.ambulance?.code) || 'A2';
    const cleanCode = String(ambCode).split(' ')[0].split('+')[0];
    const res = await replanResponse({
      incident_id: incident.id,
      failed_ambulance_code: cleanCode,
      reason: `Unit ${cleanCode} mechanical failure mid-route`,
    });
    setPlanData(res.data);
  };

  if (loading) return <div className="p-8 text-center text-slate-400">Loading Incident #{id}...</div>;
  if (!incident) return <div className="p-8 text-center text-red-400">Incident not found.</div>;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex flex-wrap justify-between items-center gap-4">
        <h1 className="text-2xl font-bold">Incident Details: #{incident.id}</h1>
        <div className="flex gap-3">
          <button
            onClick={handleDispatchPlan}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-md text-sm font-medium"
          >
            Run AI Dispatch Plan
          </button>
          <button
            onClick={handleReplan}
            className="flex items-center px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-md text-sm font-medium"
          >
            <RefreshCw className="w-4 h-4 mr-1.5" /> Replan
          </button>
          <Link to="/agent" className="flex items-center px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-md border border-slate-600 text-sm">
            <Brain className="w-4 h-4 mr-2 text-blue-400" />
            Agent Console
          </Link>
        </div>
      </div>

      <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 space-y-4">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
          <div>
            <p className="text-slate-400">Emergency Type</p>
            <p className="font-semibold text-lg">{incident.emergency_type || incident.type}</p>
          </div>
          <div>
            <p className="text-slate-400">Status</p>
            <StatusBadge status={incident.status} />
          </div>
          <div>
            <p className="text-slate-400">Priority / Severity</p>
            <StatusBadge status={incident.priority || incident.severity} type="priority" />
          </div>
          <div>
            <p className="text-slate-400">Location Node</p>
            <p className="font-mono font-bold">{incident.location}</p>
          </div>
          <div>
            <p className="text-slate-400">Estimated Victims</p>
            <p className="font-bold">{incident.victim_count ?? incident.victims}</p>
          </div>
          <div>
            <p className="text-slate-400">Weather / Road</p>
            <p>{incident.weather} / {incident.road_condition || 'Clear'}</p>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-700">
          <p className="text-slate-400 text-sm">Description</p>
          <p className="mt-1">{incident.description}</p>
        </div>

        <div className="pt-4 border-t border-slate-700">
          <p className="text-slate-400 text-sm">Active Response Plan</p>
          <p className="mt-1 text-blue-300 bg-blue-900/20 p-3 rounded font-mono text-sm">
            {planData ? planData.explanation : incident.plan}
          </p>
        </div>
      </div>
    </div>
  );
}
