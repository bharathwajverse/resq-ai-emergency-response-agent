import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

export const getIncidents = () => api.get('/api/incidents');
export const createIncident = (data) => api.post('/api/incidents', data);
export const getResources = () => api.get('/api/resources');
export const getAmbulances = () => api.get('/api/ambulances');
export const getHospitals = () => api.get('/api/hospitals');
export const getRoads = () => api.get('/api/roads');
export const analyzeIncident = (data) => api.post('/api/agent/analyze', data);
export const planResponse = (data) => api.post('/api/agent/plan', data);
export const replanResponse = (data) => api.post('/api/agent/replan', data);
export const runSearch = (data) => api.post('/api/search/run', data);
export const inferenceForward = (data) => api.post('/api/inference/forward', data);
export const inferenceBackward = (data) => api.post('/api/inference/backward', data);
export const solveCSP = (data) => api.post('/api/csp/solve', data);
export const analyzeRisk = (data) => api.post('/api/risk/analyze', data);
export const generatePlan = (data) => api.post('/api/planning/generate', data);
export const predictLearning = (data) => api.post('/api/learning/predict', data);
export const getDecisions = () => api.get('/api/decisions');
export const runLab = (data) => api.post('/api/lab/run', data);
export const checkHealth = () => api.get('/health');

export default api;
