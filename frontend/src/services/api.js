import axios from 'axios';

// Detect whether we are running in local development or deployed to cloud (e.g. Vercel)
const isLocalhost =
  typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' ||
   window.location.hostname === '127.0.0.1');

// Deployed Render backend URL
const CLOUD_BACKEND_URL = 'https://resq-ai-backend-dtg6.onrender.com';

// If VITE_API_URL is configured use it; otherwise auto-route to localhost or Render
const defaultBaseUrl = isLocalhost ? 'http://localhost:8000' : CLOUD_BACKEND_URL;

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || defaultBaseUrl,
  timeout: 45000,
});

export const getIncidents = () => api.get('/api/incidents');
export const getIncidentById = (id) => api.get(`/api/incidents/${id}`);
export const createIncident = (data) => api.post('/api/incidents', data);
export const getResources = () => api.get('/api/resources');
export const getAmbulances = () => api.get('/api/ambulances');
export const getHospitals = () => api.get('/api/hospitals');
export const getRoads = () => api.get('/api/roads');
export const getGraph = () => api.get('/api/graph');
export const getKnowledge = () => api.get('/api/knowledge');
export const analyzeIncident = (data) => api.post('/api/agent/analyze', data);
export const planResponse = (data) => api.post('/api/agent/plan', data);
export const replanResponse = (data) => api.post('/api/agent/replan', data);
export const replanAgent = replanResponse;
export const runSearch = (data) => api.post('/api/search/run', data);
export const inferenceForward = (data) => api.post('/api/inference/forward', data);
export const inferenceBackward = (data) => api.post('/api/inference/backward', data);
export const solveCSP = (data) => api.post('/api/csp/solve', data);
export const analyzeRisk = (data) => api.post('/api/risk/analyze', data);
export const generatePlan = (data) => api.post('/api/planning/generate', data);
export const predictLearning = (data) => api.post('/api/learning/predict', data);
export const getDecisionTree = () => api.get('/api/learning/tree');
export const getDecisions = () => api.get('/api/decisions');
export const runLab = (data) => api.post('/api/lab/run', data);
export const checkHealth = () => api.get('/health');

export default api;
