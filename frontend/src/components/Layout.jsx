import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen bg-slate-950 text-slate-50 font-sans overflow-hidden">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header onToggleSidebar={() => setSidebarOpen((prev) => !prev)} />
        <main
          role="main"
          aria-label="ResQ-AI Workspace"
          className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8 bg-slate-900/95"
        >
          <Outlet />
        </main>
        <footer
          role="contentinfo"
          className="py-2.5 px-4 text-center text-xs text-slate-400 bg-slate-950 border-t border-slate-800 flex flex-wrap items-center justify-between gap-2"
        >
          <span>ResQ-AI — Classical &amp; Hybrid AI Emergency Decision-Support System</span>
          <span className="text-amber-400/90 font-medium">
            Educational simulation — not for real-world emergency dispatch.
          </span>
        </footer>
      </div>
    </div>
  );
}
