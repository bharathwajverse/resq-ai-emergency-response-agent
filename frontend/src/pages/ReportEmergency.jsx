import { useState } from 'react';
import { analyzeIncident, planResponse } from '../services/api';
import { Brain, GitBranch } from 'lucide-react';

export default function ReportEmergency() {
  const [formData, setFormData] = useState({
    type: 'Medical',
    description: '',
    location: '',
    victims: 1,
    weather: 'Clear',
    roadCondition: 'Good',
    severity: 'Medium'
  });
  
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

  const handleAction = async (actionFn, title) => {
    setLoading(true);
    try {
      const res = await actionFn(formData);
      setResult({ title, data: res.data });
    } catch (e) {
      // Mock result for demo if API fails
      setResult({ title, data: { status: 'Success', message: `Mock ${title} result generated based on input.` } });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Report Emergency</h1>
      
      <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-slate-400 mb-1">Natural Language Description</label>
            <textarea 
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows="4"
              className="w-full bg-slate-900 border border-slate-700 rounded-md p-3 text-slate-100 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              placeholder="E.g., Huge pileup on I-95 south, at least 3 cars involved, looks like multiple injuries..."
            ></textarea>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Emergency Type</label>
            <select name="type" value={formData.type} onChange={handleChange} className="w-full bg-slate-900 border border-slate-700 rounded-md p-2">
              <option>Medical</option>
              <option>Fire</option>
              <option>Traffic Accident</option>
              <option>Natural Disaster</option>
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
            <label className="block text-sm font-medium text-slate-400 mb-1">Location</label>
            <input type="text" name="location" value={formData.location} onChange={handleChange} className="w-full bg-slate-900 border border-slate-700 rounded-md p-2" />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Estimated Victims</label>
            <input type="number" name="victims" value={formData.victims} onChange={handleChange} className="w-full bg-slate-900 border border-slate-700 rounded-md p-2" />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Weather</label>
            <select name="weather" value={formData.weather} onChange={handleChange} className="w-full bg-slate-900 border border-slate-700 rounded-md p-2">
              <option>Clear</option>
              <option>Rain</option>
              <option>Snow</option>
              <option>Fog</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Road Condition</label>
            <select name="roadCondition" value={formData.roadCondition} onChange={handleChange} className="w-full bg-slate-900 border border-slate-700 rounded-md p-2">
              <option>Good</option>
              <option>Wet</option>
              <option>Icy</option>
              <option>Blocked</option>
            </select>
          </div>
        </div>

        <div className="mt-8 flex flex-wrap gap-4">
          <button 
            onClick={() => handleAction(analyzeIncident, 'Analysis')}
            disabled={loading}
            className="flex items-center px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-md font-medium transition-colors"
          >
            <Brain className="w-4 h-4 mr-2" />
            Analyze Emergency
          </button>
          
          <button 
            onClick={() => handleAction(planResponse, 'Response Plan')}
            disabled={loading}
            className="flex items-center px-6 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-md font-medium transition-colors"
          >
            <GitBranch className="w-4 h-4 mr-2" />
            Generate Response Plan
          </button>
        </div>
      </div>
      
      {result && (
        <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 mt-6">
          <h2 className="text-lg font-bold mb-4 text-blue-400">Result: {result.title}</h2>
          <pre className="bg-slate-900 p-4 rounded text-sm text-slate-300 overflow-x-auto">
            {JSON.stringify(result.data, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
