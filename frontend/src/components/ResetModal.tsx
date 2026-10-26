import React, { useState } from 'react';
import { AlertTriangle, RotateCcw, X, Check } from 'lucide-react';
import { api } from '../api/client';

interface ResetModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const ResetModal: React.FC<ResetModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleReset = async () => {
    setLoading(true);
    setError(null);
    try {
      await api.resetDemoData();
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to reset demo data');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="glass-panel w-full max-w-md rounded-2xl border border-slate-700/80 shadow-2xl p-6 text-slate-100 animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2.5 text-amber-400">
            <AlertTriangle className="w-5 h-5" />
            <h3 className="font-semibold text-base text-white">Reset Demo Environment</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="py-4 space-y-3">
          <p className="text-sm text-slate-300">
            This will wipe the current working state and re-seed all deterministic demo records:
          </p>
          <ul className="text-xs text-slate-400 space-y-1.5 list-disc list-inside bg-slate-900/60 p-3 rounded-lg border border-slate-800 font-mono">
            <li>Failed payment (Acme Corp, $1,450.00)</li>
            <li>Overdue invoice (Global Tech, $3,200.00, 35d overdue)</li>
            <li>Abandoned checkout (Sarah Jenkins, $349.00)</li>
            <li>Case requiring approval (Enterprise Cloud, $12,500.00)</li>
            <li>Simulated verified recovery (Nexus Software, $720.00)</li>
            <li>Resolved settled case (Apex Dynamics, $850.00)</li>
          </ul>
          {error && (
            <div className="p-3 bg-rose-950/80 border border-rose-800 text-rose-300 text-xs rounded-lg">
              {error}
            </div>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
          <button
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 rounded-xl text-sm font-medium text-slate-300 hover:bg-slate-800 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleReset}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/30 transition-all disabled:opacity-50"
          >
            {loading ? (
              <RotateCcw className="w-4 h-4 animate-spin" />
            ) : (
              <Check className="w-4 h-4" />
            )}
            <span>Confirm Reset</span>
          </button>
        </div>
      </div>
    </div>
  );
};
