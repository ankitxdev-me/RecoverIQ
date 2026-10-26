import React from 'react';
import {
  Clock,
  CheckCircle2,
  AlertCircle,
  Play,
  RotateCw,
  Sparkles,
  ShieldAlert,
  Send,
} from 'lucide-react';

interface StatusBadgeProps {
  status: string;
  isSimulated?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, isSimulated = false }) => {
  const norm = status.toUpperCase();

  if (norm === 'RECOVERED_LIVE') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-950/90 text-emerald-300 border border-emerald-600/80 shadow-[0_0_12px_rgba(16,185,129,0.3)]">
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
        <span>RECOVERED (LIVE)</span>
      </span>
    );
  }

  if (norm === 'RECOVERED_SIMULATED') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-950/90 text-purple-300 border border-purple-600/70 shadow-[0_0_12px_rgba(168,85,247,0.25)]">
        <Sparkles className="w-3.5 h-3.5 text-purple-400" />
        <span>RECOVERED (SIMULATED)</span>
      </span>
    );
  }

  if (norm === 'PENDING_APPROVAL') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-950/80 text-amber-300 border border-amber-700/80 animate-pulse">
        <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
        <span>APPROVAL REQUIRED</span>
      </span>
    );
  }

  if (norm === 'APPROVED') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-cyan-950/80 text-cyan-300 border border-cyan-700/60">
        <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />
        <span>APPROVED</span>
      </span>
    );
  }

  if (norm === 'EXECUTING') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-indigo-950/90 text-indigo-300 border border-indigo-700/80">
        <Play className="w-3.5 h-3.5 text-indigo-400 animate-spin" />
        <span>EXECUTING</span>
      </span>
    );
  }

  if (norm === 'VERIFYING') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-950/80 text-blue-300 border border-blue-700/80">
        <RotateCw className="w-3.5 h-3.5 text-blue-400 animate-spin" />
        <span>VERIFYING RECEIPT</span>
      </span>
    );
  }

  if (norm === 'ACTION_REQUIRED') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-orange-950/70 text-orange-300 border border-orange-800/60">
        <Send className="w-3.5 h-3.5 text-orange-400" />
        <span>ACTION REQUIRED</span>
      </span>
    );
  }

  if (norm === 'DETECTED') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-950/60 text-blue-300 border border-blue-800/50">
        <Clock className="w-3.5 h-3.5 text-blue-400" />
        <span>DETECTED</span>
      </span>
    );
  }

  if (norm === 'FAILED' || norm === 'VERIFIED_FAILURE') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-red-950/80 text-red-300 border border-red-800/60">
        <AlertCircle className="w-3.5 h-3.5 text-red-400" />
        <span>FAILED</span>
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">
      <span>{status}</span>
    </span>
  );
};
