import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import ReportEmergency from './pages/ReportEmergency';
import IncidentDetails from './pages/IncidentDetails';
import AgentConsole from './pages/AgentConsole';
import RouteSearch from './pages/RouteSearch';
import ResourceAllocation from './pages/ResourceAllocation';
import Planning from './pages/Planning';
import RiskAnalysis from './pages/RiskAnalysis';
import AlgorithmsLab from './pages/AlgorithmsLab';
import DecisionHistory from './pages/DecisionHistory';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="report" element={<ReportEmergency />} />
          <Route path="incidents/:id" element={<IncidentDetails />} />
          <Route path="agent" element={<AgentConsole />} />
          <Route path="search" element={<RouteSearch />} />
          <Route path="allocation" element={<ResourceAllocation />} />
          <Route path="planning" element={<Planning />} />
          <Route path="risk" element={<RiskAnalysis />} />
          <Route path="lab" element={<AlgorithmsLab />} />
          <Route path="history" element={<DecisionHistory />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
