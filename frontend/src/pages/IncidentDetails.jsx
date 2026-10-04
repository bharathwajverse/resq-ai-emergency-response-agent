import { useParams, Link } from 'react-router-dom';
import { Brain } from 'lucide-react';
import StatusBadge from '../components/StatusBadge';

export default function IncidentDetails() {
  const { id } = useParams();

  // Mock data since no API available
  const incident = {
    id,
    type: 'Traffic Accident',
    description: 'Major collision on Highway 101, multiple lanes blocked.',
    location: 'Highway 101 Northbound',
    severity: 'High',
    victims: 3,
    weather: 'Clear',
    status: 'Active',
    plan: 'Dispatch Ambulance A2 and A5 to Highway 101 Northbound. Alert City Gen Hospital for 3 incoming trauma patients.',
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Incident Details: #{id}</h1>
        <Link to="/agent" className="flex items-center px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-md border border-slate-600 transition-colors">
          <Brain className="w-4 h-4 mr-2 text-blue-400" />
          View Agent Console
        </Link>
      </div>

      <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 space-y-4">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-slate-400">Type</p>
            <p className="font-semibold text-lg">{incident.type}</p>
          </div>
          <div>
            <p className="text-slate-400">Status</p>
            <StatusBadge status={incident.status} />
          </div>
          <div>
            <p className="text-slate-400">Severity</p>
            <StatusBadge status={incident.severity} type="priority" />
          </div>
          <div>
            <p className="text-slate-400">Location</p>
            <p>{incident.location}</p>
          </div>
          <div>
            <p className="text-slate-400">Estimated Victims</p>
            <p>{incident.victims}</p>
          </div>
          <div>
            <p className="text-slate-400">Weather</p>
            <p>{incident.weather}</p>
          </div>
        </div>
        
        <div className="pt-4 border-t border-slate-700">
          <p className="text-slate-400">Description</p>
          <p className="mt-1">{incident.description}</p>
        </div>

        <div className="pt-4 border-t border-slate-700">
          <p className="text-slate-400">Response Plan</p>
          <p className="mt-1 text-blue-300 bg-blue-900/20 p-3 rounded">{incident.plan}</p>
        </div>
      </div>
    </div>
  );
}
