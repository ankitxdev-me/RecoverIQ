import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  badge?: string;
  badgeColor?: 'emerald' | 'amber' | 'indigo' | 'purple' | 'slate' | 'rose';
  accentBorder?: boolean;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  badge,
  badgeColor = 'indigo',
  accentBorder = false,
}) => {
  const badgeClasses = {
    emerald: 'bg-emerald-950/80 text-emerald-300 border-emerald-700/60',
    amber: 'bg-amber-950/80 text-amber-300 border-amber-700/60',
    indigo: 'bg-indigo-950/80 text-indigo-300 border-indigo-700/60',
    purple: 'bg-purple-950/80 text-purple-300 border-purple-700/60',
    rose: 'bg-rose-950/80 text-rose-300 border-rose-700/60',
    slate: 'bg-slate-800 text-slate-300 border-slate-700',
  }[badgeColor];

  return (
    <div
      className={`glass-card p-5 rounded-xl flex flex-col justify-between transition-all duration-200 ${
        accentBorder ? 'border-indigo-500/30 ring-1 ring-indigo-500/20' : ''
      }`}
    >
      <div className="flex items-start justify-between mb-3">
        <span className="text-sm font-medium text-slate-400">{title}</span>
        <div className="p-2 rounded-lg bg-slate-800/80 border border-slate-700/50 text-indigo-400">
          <Icon className="w-5 h-5" />
        </div>
      </div>

      <div className="mt-1">
        <div className="text-2xl lg:text-3xl font-bold tracking-tight text-white font-mono">{value}</div>
        <div className="flex items-center justify-between mt-2">
          {subtitle && <p className="text-xs text-slate-400 line-clamp-1">{subtitle}</p>}
          {badge && (
            <span className={`text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full border ${badgeClasses}`}>
              {badge}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
