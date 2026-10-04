import { Loader2 } from 'lucide-react';

export default function LoadingSpinner({ message = 'Loading...' }) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-slate-400">
      <Loader2 className="w-8 h-8 animate-spin mb-4 text-blue-500" />
      <p>{message}</p>
    </div>
  );
}
