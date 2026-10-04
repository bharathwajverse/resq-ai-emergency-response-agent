import { AlertCircle } from 'lucide-react';

export default function ErrorState({ message = 'Something went wrong', onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center p-8 bg-red-900/20 border border-red-900/50 rounded-lg text-red-400">
      <AlertCircle className="w-10 h-10 mb-3" />
      <p className="mb-4 text-center">{message}</p>
      {onRetry && (
        <button 
          onClick={onRetry}
          className="px-4 py-2 bg-red-800 hover:bg-red-700 text-white rounded transition-colors"
        >
          Try Again
        </button>
      )}
    </div>
  );
}
