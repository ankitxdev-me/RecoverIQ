import React, { useState, useEffect } from 'react';
import {
  Search,
  Filter,
  CreditCard,
  FileText,
  ShoppingCart,
  ArrowUpDown,
  RefreshCw,
  ExternalLink,
  Database,
} from 'lucide-react';
import { RecoveryCase } from '../types';
import { api } from '../api/client';
import { PriorityBadge } from '../components/PriorityBadge';
import { StatusBadge } from '../components/StatusBadge';

interface CasesPageProps {
  onSelectCase: (c: RecoveryCase) => void;
  selectedCaseId?: string | null;
  onNavigateTab?: (tab: string) => void;
}

export const CasesPage: React.FC<CasesPageProps> = ({ onSelectCase, selectedCaseId, onNavigateTab }) => {
  const [cases, setCases] = useState<RecoveryCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [sourceType, setSourceType] = useState<string>('');
  const [priorityFilter, setPriorityFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [sortBy, setSortBy] = useState('priority_score');

  const fetchCases = async () => {
    setLoading(true);
    try {
      const data = await api.getCases({
        search: search || undefined,
        source_type: sourceType || undefined,
        priority: priorityFilter || undefined,
        status: statusFilter || undefined,
        sort_by: sortBy,
      });
      setCases(data);
    } catch (err) {
      console.error('Failed to load cases', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, [search, sourceType, priorityFilter, statusFilter, sortBy]);

  const sourceTabs = [
    { id: '', label: 'All Cases', icon: null },
    { id: 'failed_payment', label: 'Failed Payments', icon: CreditCard },
    { id: 'overdue_invoice', label: 'Overdue Invoices', icon: FileText },
    { id: 'abandoned_checkout', label: 'Abandoned Carts', icon: ShoppingCart },
  ];

  return (
    <div className="space-y-6">
      {/* Top Filter & Search Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Source Type Filter Tabs */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-slate-900 border border-slate-800 overflow-x-auto">
          {sourceTabs.map((tab) => {
            const Icon = tab.icon;
            const isSelected = sourceType === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setSourceType(tab.id)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
                  isSelected
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                {Icon && <Icon className="w-3.5 h-3.5" />}
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Refresh button */}
        <button
          onClick={fetchCases}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 hover:bg-slate-800 self-start md:self-auto transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Secondary Search and Dropdown Controls */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
        <div className="sm:col-span-2 relative">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
          <input
            type="text"
            placeholder="Search by case ID, customer name, email, or invoice..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-900/90 border border-slate-800 rounded-xl text-xs sm:text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </div>

        {/* Priority Filter */}
        <div>
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="w-full px-3 py-2 bg-slate-900/90 border border-slate-800 rounded-xl text-xs sm:text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Priorities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>

        {/* Sort Filter */}
        <div>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="w-full px-3 py-2 bg-slate-900/90 border border-slate-800 rounded-xl text-xs sm:text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="priority_score">Sort: Highest Priority Score</option>
            <option value="amount">Sort: Largest Amount</option>
            <option value="created_at">Sort: Most Recent</option>
          </select>
        </div>
      </div>

      {/* Cases Table */}
      <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs sm:text-sm">
            <thead className="bg-slate-950/80 border-b border-slate-800 text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
              <tr>
                <th className="py-3.5 px-4">Case ID</th>
                <th className="py-3.5 px-4">Customer</th>
                <th className="py-3.5 px-4">Amount</th>
                <th className="py-3.5 px-4">Priority</th>
                <th className="py-3.5 px-4">Lifecycle Status</th>
                <th className="py-3.5 px-4">Recommended Next Action</th>
                <th className="py-3.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {loading && cases.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-500">
                    Loading recovery cases...
                  </td>
                </tr>
              ) : cases.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-16 text-center">
                    <div className="max-w-md mx-auto space-y-3">
                      <div className="w-12 h-12 rounded-2xl bg-indigo-950/60 border border-indigo-800/50 mx-auto flex items-center justify-center text-indigo-400">
                        <Database className="w-6 h-6" />
                      </div>
                      <div className="space-y-1">
                        <p className="text-slate-200 font-semibold text-sm">
                          Zero Dummy Data Policy Active
                        </p>
                        <p className="text-slate-400 text-xs">
                          No recovery cases exist yet. Connect your business database or software to crawl live transactions and generate actual recovery workflows.
                        </p>
                      </div>
                      {onNavigateTab && (
                        <button
                          onClick={() => onNavigateTab('connect-business')}
                          className="mt-3 inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/30 transition-all"
                        >
                          <span>Connect Business & Upload Data</span>
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ) : (
                cases.map((c) => {
                  const isSelected = selectedCaseId === c.id;
                  return (
                    <tr
                      key={c.id}
                      onClick={() => onSelectCase(c)}
                      className={`hover:bg-slate-800/40 cursor-pointer transition-colors ${
                        isSelected ? 'bg-indigo-950/30 ring-1 ring-inset ring-indigo-500/40' : ''
                      }`}
                    >
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-bold text-indigo-300">{c.id}</span>
                        </div>
                        <span className="text-[10px] text-slate-400 block font-mono">
                          {c.source_type.replace('_', ' ')}
                        </span>
                      </td>

                      <td className="py-3.5 px-4">
                        <span className="font-medium text-slate-200 block">{c.customer?.name}</span>
                        <span className="text-[11px] text-slate-400 font-mono">{c.customer?.email}</span>
                      </td>

                      <td className="py-3.5 px-4">
                        <span className="font-mono font-bold text-white text-sm">
                          ${(c.amount_cents / 100).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                        </span>
                        <span className="text-[10px] text-slate-500 ml-1 font-mono">{c.currency}</span>
                      </td>

                      <td className="py-3.5 px-4">
                        <PriorityBadge priority={c.priority} score={c.priority_score} showScore={true} />
                      </td>

                      <td className="py-3.5 px-4">
                        <StatusBadge status={c.status} />
                      </td>

                      <td className="py-3.5 px-4">
                        <span className="font-mono text-xs text-indigo-300 bg-indigo-950/60 px-2 py-1 rounded border border-indigo-800/50">
                          {c.recommended_action || 'EVALUATE'}
                        </span>
                      </td>

                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectCase(c);
                          }}
                          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
                          title="Inspect case details"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
