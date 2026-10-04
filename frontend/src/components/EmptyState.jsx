import { FolderOpen } from 'lucide-react';

export default function EmptyState({ message = 'No data available', icon: Icon = FolderOpen }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-slate-500 bg-slate-800/50 rounded-lg border border-slate-700 border-dashed">
      <Icon className="w-12 h-12 mb-4 opacity-50" />
      <p>{message}</p>
    </div>
  );
}
