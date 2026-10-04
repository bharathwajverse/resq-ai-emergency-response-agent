import { useState, useEffect } from 'react';
import { solveCSP } from '../services/api';
import { Check, X } from 'lucide-react';

export default function ResourceAllocation() {
  const [data, setData] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await solveCSP({});
        if (res.data) {
          setData(res.data);
          return;
        }
      } catch (e) {
        // Mock CSP solver result
        setData({
          incident: 'IN-492 (Multi-vehicle crash)',
          selectedAmbulance: 'Ambulance A4',
          selectedHospital: 'City General (Trauma Center)',
          rejected: [
            { id: 'Ambulance A1', reason: 'Insufficient capacity (needs 2, has 1)' },
            { id: 'Ambulance A3', reason: 'Unavailable (currently dispatched)' },
            { id: 'St. Marys Hospital', reason: 'No trauma unit available' },
            { id: 'Mercy Clinic', reason: 'Distance exceeds critical threshold (>15mi)' }
          ]
        });
      }
    };
    fetchData();
  }, []);

  if (!data) return <div>Loading...</div>;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Resource Allocation (CSP)</h1>
      <p className="text-slate-400">Constraint Satisfaction Problem solver for optimal resource matching.</p>
      
      <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
        <h2 className="text-lg font-semibold mb-4 text-white">Current Assignment</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
           <div className="p-4 bg-slate-900 border border-slate-700 rounded-lg">
             <p className="text-sm text-slate-400">Target Incident</p>
             <p className="font-bold text-blue-400">{data.incident}</p>
           </div>
           <div className="p-4 bg-slate-900 border border-green-900 rounded-lg">
             <p className="text-sm text-slate-400">Dispatched Ambulance</p>
             <p className="font-bold text-green-400 flex items-center"><Check className="w-4 h-4 mr-2"/> {data.selectedAmbulance}</p>
           </div>
           <div className="p-4 bg-slate-900 border border-green-900 rounded-lg">
             <p className="text-sm text-slate-400">Destination Hospital</p>
             <p className="font-bold text-green-400 flex items-center"><Check className="w-4 h-4 mr-2"/> {data.selectedHospital}</p>
           </div>
        </div>
      </div>

      <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
        <h2 className="text-lg font-semibold mb-4 text-white">Constraint Evaluation (Rejected Alternatives)</h2>
        <div className="space-y-3">
          {data.rejected.map((item, i) => (
            <div key={i} className="flex items-start p-3 bg-slate-900 rounded border border-red-900/30">
              <X className="w-5 h-5 text-red-500 mr-3 mt-0.5" />
              <div>
                <p className="font-semibold text-slate-300">{item.id}</p>
                <p className="text-sm text-slate-500">Rejected: {item.reason}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
