import React from 'react';
import {
  ShieldCheck,
  Cpu,
  RotateCcw,
  LayoutDashboard,
  Inbox,
  Sparkles,
  CheckSquare,
  FileText,
  Radio,
  Database,
  HardDrive,
} from 'lucide-react';
import { SystemHealth } from '../types';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  pendingApprovalsCount: number;
  health: SystemHealth | null;
  onOpenResetModal: () => void;
  onOpenSessionModal: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  pendingApprovalsCount,
  health,
  onOpenResetModal,
  onOpenSessionModal,
}) => {
  const tabs = [
    { id: 'connect-business', label: 'Connect Business', icon: Database },
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'cases', label: 'Recovery Cases', icon: Inbox },
    { id: 'workspace', label: 'AI Copilot', icon: Sparkles },
    { id: 'approvals', label: 'Approval Center', icon: CheckSquare, badge: pendingApprovalsCount },
    { id: 'audit', label: 'Audit Log', icon: FileText },
    { id: 'integrations', label: 'Integrations & Diagnostics', icon: Radio },
  ];

  return (
    <header className="sticky top-0 z-40 border-b border-slate-800 glass-panel">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 p-0.5 shadow-lg shadow-indigo-500/20 flex items-center justify-center">
              <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-indigo-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-white via-slate-100 to-indigo-200 bg-clip-text text-transparent">
                  RecoverIQ
                </span>
                <span className="text-[10px] font-mono uppercase bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-1.5 py-0.5 rounded">
                  v1.0
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium hidden sm:block">
                AI Revenue Recovery Agent
              </p>
            </div>
          </div>

          {/* System Environment Pills */}
          <div className="hidden md:flex items-center gap-3">
            {/* Simulation Mode Pill */}
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-950/60 border border-indigo-700/50 text-[11px] text-indigo-300 font-medium">
              <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
              <span>SIMULATION SANDBOX</span>
            </div>

            {/* Ollama Local Status Pill */}
            <div
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[11px] font-medium ${
                health?.ollama_ok
                  ? 'bg-emerald-950/60 border-emerald-700/50 text-emerald-300'
                  : 'bg-amber-950/60 border-amber-700/50 text-amber-300'
              }`}
            >
              <Cpu className="w-3.5 h-3.5" />
              <span>
                {health?.ollama_ok ? `Ollama: ${health.ollama_model || 'gemma4:e2b'}` : 'Ollama Offline (Deterministic Fallback)'}
              </span>
              <span
                className={`w-2 h-2 rounded-full ${
                  health?.ollama_ok ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'
                }`}
              />
            </div>

            {/* Local Device Session Ledger Button */}
            <button
              onClick={onOpenSessionModal}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-950/70 hover:bg-indigo-900/80 text-indigo-300 hover:text-white border border-indigo-700/60 text-xs font-medium transition-all shadow-sm"
              title="Open Local Device Session & Action Ledger"
            >
              <HardDrive className="w-3.5 h-3.5 text-indigo-400" />
              <span>Device Session</span>
            </button>

            {/* Reset Demo Data Button */}
            <button
              onClick={onOpenResetModal}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 text-xs font-medium transition-all"
              title="Reset all database records to baseline demo state"
            >
              <RotateCcw className="w-3.5 h-3.5 text-slate-400" />
              <span>Reset Demo</span>
            </button>
          </div>
        </div>

        {/* Tab Navigation Row */}
        <div className="flex items-center gap-1 sm:gap-2 overflow-x-auto py-2 scrollbar-none border-t border-slate-800/60">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs sm:text-sm font-medium transition-all whitespace-nowrap ${
                  isActive
                    ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-transparent'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-400' : 'text-slate-500'}`} />
                <span>{tab.label}</span>
                {tab.badge !== undefined && tab.badge > 0 && (
                  <span className="ml-1 px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500 text-slate-950 font-mono">
                    {tab.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
};
