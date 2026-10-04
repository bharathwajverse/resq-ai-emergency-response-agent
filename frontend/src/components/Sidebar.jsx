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
  History,
  X,
  ShieldCheck,
} from 'lucide-react';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', module: 'Overview & KB' },
  { to: '/report', icon: AlertTriangle, label: 'Report Emergency', module: 'NLU & Dispatch' },
  { to: '/agent', icon: BrainCircuit, label: 'AI Agent Console', module: 'Orchestrator' },
  { to: '/search', icon: Map, label: 'Route Search', module: 'FAI Mod II & III' },
  { to: '/allocation', icon: Truck, label: 'Resource Allocation', module: 'FAI Mod IV (CSP)' },
  { to: '/planning', icon: GitMerge, label: 'Planning', module: 'FAI Mod VII' },
  { to: '/risk', icon: ShieldAlert, label: 'Risk Analysis', module: 'FAI Mod VIII' },
  { to: '/lab', icon: FlaskConical, label: 'Algorithms Lab', module: '22 FAI Algorithms' },
  { to: '/history', icon: History, label: 'Decision History', module: 'Audit Log' },
];

export default function Sidebar({ isOpen = false, onClose = () => {} }) {
  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/60 backdrop-blur-xs md:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      <aside
        aria-label="Primary Navigation"
        className={`fixed md:static inset-y-0 left-0 z-40 w-68 bg-slate-900 border-r border-slate-800 flex flex-col transform transition-transform duration-200 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        <div className="h-16 flex items-center justify-between px-5 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-600/20 border border-blue-500/40 flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-white leading-none">ResQ-AI</h1>
              <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider">
                FAI Decision Agent
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close navigation menu"
            className="md:hidden p-1.5 text-slate-400 hover:text-white rounded-md hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto py-4">
          <ul className="space-y-1 px-3">
            {navItems.map((item) => (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  onClick={onClose}
                  className={({ isActive }) =>
                    `flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                        : 'text-slate-300 hover:bg-slate-800/80 hover:text-white border border-transparent'
                    }`
                  }
                >
                  <span className="flex items-center">
                    <item.icon className="w-4 h-4 mr-3 shrink-0" />
                    {item.label}
                  </span>
                  <span className="text-[10px] font-mono text-slate-400 bg-slate-800/90 px-1.5 py-0.5 rounded">
                    {item.module}
                  </span>
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <div className="p-4 border-t border-slate-800 bg-slate-950/50 text-xs text-slate-400 space-y-1">
          <div className="flex items-center justify-between">
            <span>Architecture</span>
            <span className="font-mono text-emerald-400">Classical + NLU</span>
          </div>
          <div className="flex items-center justify-between">
            <span>Road Graph</span>
            <span className="font-mono text-slate-300">13 Nodes / 17 Edges</span>
          </div>
        </div>
      </aside>
    </>
  );
}
