export default function StatusBadge({ status, type = 'status' }) {
  let colorClass = 'bg-slate-700 text-slate-300';
  
  if (type === 'priority') {
    const s = String(status || '').toLowerCase();
    if (s.includes('crit') || s === 'p1' || s.includes('p1_')) colorClass = 'bg-red-900/50 text-red-400 border-red-800';
    else if (s.includes('high') || s === 'p2_high' || (s.includes('p2') && !s.includes('norm'))) colorClass = 'bg-orange-900/50 text-orange-400 border-orange-800';
    else if (s.includes('med') || s.includes('moderate')) colorClass = 'bg-yellow-900/50 text-yellow-400 border-yellow-800';
    else if (s.includes('low') || s.includes('norm') || s.includes('p3')) colorClass = 'bg-green-900/50 text-green-400 border-green-800';
  } else {
    // status
    const s = String(status || '').toLowerCase();
    if (['resolved', 'complete', 'success', 'available'].some(st => s.includes(st))) colorClass = 'bg-green-900/50 text-green-400 border-green-800';
    else if (s.includes('replan')) colorClass = 'bg-amber-900/50 text-amber-400 border-amber-800';
    else if (['active', 'running', 'pending', 'dispatched', 'reported'].some(st => s.includes(st))) colorClass = 'bg-blue-900/50 text-blue-400 border-blue-800';
    else if (['error', 'failed', 'maintenance', 'blocked', 'unavailable', 'shortage'].some(st => s.includes(st))) colorClass = 'bg-red-900/50 text-red-400 border-red-800';
  }

  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${colorClass}`}>
      {status}
    </span>
  );
}
