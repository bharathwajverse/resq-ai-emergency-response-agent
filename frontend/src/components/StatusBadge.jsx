export default function StatusBadge({ status, type = 'status' }) {
  let colorClass = 'bg-slate-700 text-slate-300';
  
  if (type === 'priority') {
    const s = String(status || '').toLowerCase();
    if (s.includes('crit')) colorClass = 'bg-red-900/50 text-red-400 border-red-800';
    else if (s.includes('high')) colorClass = 'bg-orange-900/50 text-orange-400 border-orange-800';
    else if (s.includes('med')) colorClass = 'bg-yellow-900/50 text-yellow-400 border-yellow-800';
    else if (s.includes('low')) colorClass = 'bg-green-900/50 text-green-400 border-green-800';
  } else {
    // status
    if (['Resolved', 'Complete', 'Success'].includes(status)) colorClass = 'bg-green-900/50 text-green-400 border-green-800';
    else if (['Active', 'Running', 'Pending'].includes(status)) colorClass = 'bg-blue-900/50 text-blue-400 border-blue-800';
    else if (['Error', 'Failed'].includes(status)) colorClass = 'bg-red-900/50 text-red-400 border-red-800';
  }

  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${colorClass}`}>
      {status}
    </span>
  );
}
