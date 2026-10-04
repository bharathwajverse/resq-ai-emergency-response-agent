import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Menu, Activity, PlusCircle, FlaskConical } from 'lucide-react';
import { checkHealth } from '../services/api';

export default function Header({ onToggleSidebar = () => {} }) {
  const [backendOnline, setBackendOnline] = useState(true);

  useEffect(() => {
    let mounted = true;
    checkHealth()
      .then(() => {
        if (mounted) setBackendOnline(true);
      })
      .catch(() => {
        if (mounted) setBackendOnline(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <header
      role="banner"
      className="h-16 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-4 md:px-6 shrink-0"
    >
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          aria-label="Toggle navigation menu"
          className="md:hidden p-2 text-slate-300 hover:text-white rounded-md hover:bg-slate-800"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div>
          <h2 className="text-sm md:text-base font-semibold text-slate-100">
            Intelligent Emergency Response &amp; Resource Planning Agent
          </h2>
          <p className="text-xs text-slate-400 hidden sm:block">
            Fundamentals of Artificial Intelligence (FAI) — Hybrid Symbolic &amp; Probabilistic Reasoning
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <span
          className={`hidden sm:inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border font-mono ${
            backendOnline
              ? 'bg-emerald-950/60 border-emerald-700/60 text-emerald-300'
              : 'bg-amber-950/60 border-amber-700/60 text-amber-300'
          }`}
        >
          <Activity className="w-3.5 h-3.5" />
          {backendOnline ? 'Engine Online (Demo NLU Ready)' : 'Offline Simulation Fallback'}
        </span>

        <Link
          to="/lab"
          className="hidden lg:inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
        >
          <FlaskConical className="w-3.5 h-3.5 text-purple-400" />
          Algorithms Lab
        </Link>

        <Link
          to="/report"
          className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md bg-blue-600 hover:bg-blue-500 text-white font-medium transition-colors"
        >
          <PlusCircle className="w-3.5 h-3.5" />
          New Emergency
        </Link>
      </div>
    </header>
  );
}
