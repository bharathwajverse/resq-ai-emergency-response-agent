import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

export default function Layout() {
  return (
    <div className="flex h-screen bg-slate-900 text-slate-50 font-sans overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header />
        <main className="flex-1 overflow-auto p-4 md:p-6 bg-slate-900">
          <Outlet />
        </main>
        <footer className="py-2 text-center text-xs text-slate-500 border-t border-slate-800">
          Educational simulation — not for real-world emergency dispatch.
        </footer>
      </div>
    </div>
  );
}
