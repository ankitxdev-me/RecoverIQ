import React from 'react';
import {
  AlertOctagon,
  TrendingUp,
  ShieldCheck,
  Sparkles,
  Inbox,
  CheckSquare,
  HelpCircle,
  Activity,
  ArrowRight,
  Database,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { DashboardSummary } from '../types';
import { MetricCard } from '../components/MetricCard';

interface DashboardPageProps {
  summary: DashboardSummary | null;
  onNavigateTab: (tab: string) => void;
  onSelectCaseId?: (caseId: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  summary,
  onNavigateTab,
  onSelectCaseId,
}) => {
  if (!summary) {
    return (
      <div className="py-24 text-center text-slate-500">
        <Activity className="w-8 h-8 animate-spin mx-auto mb-3 text-indigo-400" />
        <p>Loading recovery metrics...</p>
      </div>
    );
  }

  // Chart data: Cases by source type
  const typeChartData = [
    { name: 'Failed Payments', count: summary.cases_by_type['failed_payment'] || 0, fill: '#6366f1' },
    { name: 'Overdue Invoices', count: summary.cases_by_type['overdue_invoice'] || 0, fill: '#f59e0b' },
    { name: 'Abandoned Carts', count: summary.cases_by_type['abandoned_checkout'] || 0, fill: '#06b6d4' },
  ];

  // Chart data: Cases by priority
  const priorityChartData = [
    { name: 'Critical', value: summary.cases_by_priority['CRITICAL'] || 0, color: '#f43f5e' },
    { name: 'High', value: summary.cases_by_priority['HIGH'] || 0, color: '#f59e0b' },
    { name: 'Medium', value: summary.cases_by_priority['MEDIUM'] || 0, color: '#6366f1' },
    { name: 'Low', value: summary.cases_by_priority['LOW'] || 0, color: '#64748b' },
  ].filter((p) => p.value > 0);

  return (
    <div className="space-y-6">
      {/* Top Banner Notice: Zero Dummy Data vs Active Pipeline */}
      {summary.open_cases_count === 0 && summary.revenue_at_risk_cents === 0 ? (
        <div className="p-6 rounded-2xl glass-card border border-amber-500/30 bg-gradient-to-r from-amber-950/40 via-slate-900 to-indigo-950/40 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 shadow-xl">
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-xl bg-amber-500/20 text-amber-400 border border-amber-500/30 flex-shrink-0">
              <Database className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white">
                  Zero Dummy Data Policy Active
                </h2>
                <span className="text-[10px] font-mono uppercase bg-amber-500/20 text-amber-300 border border-amber-500/30 px-2 py-0.5 rounded-full">
                  Awaiting Business Data
                </span>
              </div>
              <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
                RecoverIQ does not show fabricated or dummy financial figures. Connect your business database (<code className="text-amber-200">.db</code>, <code className="text-amber-200">.sqlite</code>, <code className="text-amber-200">.json</code>) or link SaaS software (Stripe, Shopify, QuickBooks, Xero) on the Connect Business page. Gemma 4 will crawl your records and produce authentic recovery workflows.
              </p>
            </div>
          </div>
          <button
            onClick={() => onNavigateTab('connect-business')}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-white text-xs font-bold shadow-lg shadow-indigo-600/25 transition-all whitespace-nowrap self-stretch md:self-auto justify-center"
          >
            <span>Connect Business & Upload Data</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      ) : (
        <div className="p-4 rounded-xl glass-card border-indigo-500/30 flex items-center justify-between gap-4 bg-gradient-to-r from-indigo-950/40 via-slate-900/60 to-purple-950/30">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">
                Autonomous Revenue Recovery Pipeline Active
              </h2>
              <p className="text-xs text-slate-400">
                RecoverIQ continuously detects failed payments, overdue invoices, and abandoned carts
                under strict financial guardrails.
              </p>
            </div>
          </div>
          <button
            onClick={() => onNavigateTab('workspace')}
            className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition-all whitespace-nowrap"
          >
            <span>Ask AI Agent</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Primary KPI Grid (Distinct separation of Live vs Simulated) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Revenue at Risk */}
        <MetricCard
          title="Revenue at Risk"
          value={summary.revenue_at_risk_display}
          subtitle="Total unresolved across all cases"
          icon={AlertOctagon}
          badge="AT RISK"
          badgeColor="rose"
        />

        {/* Eligible for Recovery */}
        <MetricCard
          title="Eligible for Recovery"
          value={summary.eligible_recovery_display}
          subtitle="Passed cooldowns & retry limit checks"
          icon={TrendingUp}
          badge="ELIGIBLE"
          badgeColor="amber"
        />

        {/* Confirmed Live Recovered */}
        <MetricCard
          title="Confirmed Recovered (Live)"
          value={summary.confirmed_live_recovered_display}
          subtitle="Real gateway cleared transactions"
          icon={ShieldCheck}
          badge="LIVE PRODUCTION"
          badgeColor="emerald"
          accentBorder={true}
        />

        {/* Simulated Recovered Amount */}
        <MetricCard
          title="Simulated Recovered"
          value={summary.simulated_recovered_display}
          subtitle="Verified in test sandbox only"
          icon={Sparkles}
          badge="SANDBOX ONLY"
          badgeColor="purple"
        />
      </div>

      {/* Secondary Operational Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="glass-card p-5 rounded-xl flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400 font-medium">Open Cases</span>
            <div className="text-2xl font-bold font-mono text-white mt-1">
              {summary.open_cases_count}
            </div>
            <button
              onClick={() => onNavigateTab('cases')}
              className="text-xs text-indigo-400 hover:text-indigo-300 font-medium mt-1 inline-flex items-center gap-1"
            >
              <span>View all cases</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
          <div className="p-3 bg-indigo-950/60 border border-indigo-800/50 rounded-xl text-indigo-400">
            <Inbox className="w-6 h-6" />
          </div>
        </div>

        <div className="glass-card p-5 rounded-xl flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400 font-medium">Pending Human Approvals</span>
            <div className="text-2xl font-bold font-mono text-amber-300 mt-1">
              {summary.pending_approvals_count}
            </div>
            <button
              onClick={() => onNavigateTab('approvals')}
              className="text-xs text-amber-400 hover:text-amber-300 font-medium mt-1 inline-flex items-center gap-1"
            >
              <span>Review approval queue</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
          <div className="p-3 bg-amber-950/60 border border-amber-800/50 rounded-xl text-amber-400">
            <CheckSquare className="w-6 h-6" />
          </div>
        </div>

        <div className="glass-card p-5 rounded-xl flex items-center justify-between">
          <div>
            <div className="flex items-center gap-1 text-xs text-slate-400 font-medium">
              <span>Recovery Success Rate</span>
              <div
                className="group relative cursor-help"
                title={summary.recovery_denominator_explanation}
              >
                <HelpCircle className="w-3.5 h-3.5 text-slate-500" />
              </div>
            </div>
            <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
              {summary.recovery_success_rate_percent}%
            </div>
            <p className="text-[11px] text-slate-400 mt-1 truncate">
              {summary.recovery_denominator_explanation}
            </p>
          </div>
          <div className="p-3 bg-emerald-950/60 border border-emerald-800/50 rounded-xl text-emerald-400">
            <TrendingUp className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Visual Analytics Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Cases by Source Type */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Cases by Revenue Category</h3>
            <span className="text-xs text-slate-400">Distribution by source</span>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={typeChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" stroke="#64748b" fontSize={12} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={12} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderColor: '#334155',
                    borderRadius: '8px',
                    fontSize: '12px',
                    color: '#fff',
                  }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Priority Distribution Chart */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Priority Distribution</h3>
            <span className="text-xs text-slate-400">Scored based on Amount + Age</span>
          </div>
          <div className="h-64 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={priorityChartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={85}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {priorityChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderColor: '#334155',
                    borderRadius: '8px',
                    fontSize: '12px',
                    color: '#fff',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-4 text-xs">
            {priorityChartData.map((p) => (
              <div key={p.name} className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: p.color }} />
                <span className="text-slate-300 font-medium">{p.name}</span>
                <span className="text-slate-500 font-mono">({p.value})</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Activity Audit Feed */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-semibold text-white">Recent Recovery Activity</h3>
          </div>
          <button
            onClick={() => onNavigateTab('audit')}
            className="text-xs text-indigo-400 hover:text-indigo-300 font-medium inline-flex items-center gap-1"
          >
            <span>Full audit log</span>
            <ArrowRight className="w-3 h-3" />
          </button>
        </div>

        <div className="divide-y divide-slate-800/80">
          {summary.recent_activity.map((act) => (
            <div key={act.id} className="py-3 flex items-start justify-between gap-4 text-xs">
              <div className="flex items-start gap-3">
                <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-slate-800 text-slate-300 border border-slate-700">
                  {act.actor}
                </span>
                <div>
                  <p className="text-slate-200 font-medium">{act.description}</p>
                  {act.case_id && (
                    <button
                      onClick={() => onSelectCaseId && onSelectCaseId(act.case_id!)}
                      className="text-indigo-400 hover:underline font-mono text-[11px] mt-0.5 block"
                    >
                      {act.case_id}
                    </button>
                  )}
                </div>
              </div>
              <div className="text-right flex-shrink-0">
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-semibold border ${
                    act.is_simulated
                      ? 'bg-purple-950/60 text-purple-300 border-purple-800/60'
                      : 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60'
                  }`}
                >
                  {act.is_simulated ? 'SIMULATED' : 'LIVE'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
