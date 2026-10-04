import { Bell } from 'lucide-react';

export default function Header() {
  return (
    <header className="h-16 bg-slate-800 border-b border-slate-700 flex items-center justify-between px-6">
      <div className="flex items-center">
        <h2 className="text-lg font-semibold md:hidden text-blue-400 mr-4">ResQ-AI</h2>
        <span className="text-slate-400 text-sm hidden sm:block">AI-Powered Emergency Response System</span>
      </div>
      <div className="flex items-center">
        <button className="p-2 text-slate-400 hover:text-white rounded-full hover:bg-slate-700 transition-colors">
          <Bell className="w-5 h-5" />
        </button>
      </div>
    </header>
  );
}
