import React from 'react';
import { AlertCircle, AlertTriangle, ArrowDown, ArrowUp } from 'lucide-react';

interface PriorityBadgeProps {
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | string;
  score?: number;
  showScore?: boolean;
}

export const PriorityBadge: React.FC<PriorityBadgeProps> = ({ priority, score, showScore = false }) => {
  switch (priority.toUpperCase()) {
    case 'CRITICAL':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-950/80 text-rose-300 border border-rose-800/80 shadow-[0_0_12px_rgba(244,63,94,0.25)]">
          <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
          <span>CRITICAL</span>
          {showScore && score !== undefined && <span className="opacity-80 font-mono">({score})</span>}
        </span>
      );
    case 'HIGH':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-950/80 text-amber-300 border border-amber-800/80 shadow-[0_0_10px_rgba(245,158,11,0.2)]">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
          <span>HIGH</span>
          {showScore && score !== undefined && <span className="opacity-80 font-mono">({score})</span>}
        </span>
      );
    case 'MEDIUM':
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-950/70 text-indigo-300 border border-indigo-800/60">
          <ArrowUp className="w-3.5 h-3.5 text-indigo-400" />
          <span>MEDIUM</span>
          {showScore && score !== undefined && <span className="opacity-80 font-mono">({score})</span>}
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-800/80 text-slate-300 border border-slate-700/60">
          <ArrowDown className="w-3.5 h-3.5 text-slate-400" />
          <span>LOW</span>
          {showScore && score !== undefined && <span className="opacity-80 font-mono">({score})</span>}
        </span>
      );
  }
};
