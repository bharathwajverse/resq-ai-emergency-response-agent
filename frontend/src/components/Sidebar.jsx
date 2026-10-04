import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  AlertTriangle, 
  BrainCircuit, 
  Map, 
  Truck, 
  GitMerge, 
  ShieldAlert, 
  FlaskConical, 
  History 
} from 'lucide-react';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/report', icon: AlertTriangle, label: 'Report Emergency' },
  { to: '/agent', icon: BrainCircuit, label: 'AI Console' },
  { to: '/search', icon: Map, label: 'Route Search' },
  { to: '/allocation', icon: Truck, label: 'Resource Allocation' },
  { to: '/planning', icon: GitMerge, label: 'Planning' },
  { to: '/risk', icon: ShieldAlert, label: 'Risk Analysis' },
  { to: '/lab', icon: FlaskConical, label: 'Algorithms Lab' },
  { to: '/history', icon: History, label: 'Decision History' },
];

export default function Sidebar() {
  return (
    <aside className="w-64 bg-slate-800 border-r border-slate-700 hidden md:flex flex-col">
      <div className="h-16 flex items-center px-6 border-b border-slate-700">
        <h1 className="text-xl font-bold text-blue-400">ResQ-AI</h1>
      </div>
      <nav className="flex-1 overflow-y-auto py-4">
        <ul className="space-y-1 px-3">
          {navItems.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center px-3 py-2 rounded-md transition-colors ${
                    isActive 
                      ? 'bg-blue-600/20 text-blue-400' 
                      : 'text-slate-300 hover:bg-slate-700 hover:text-white'
                  }`
                }
              >
                <item.icon className="w-5 h-5 mr-3" />
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}
