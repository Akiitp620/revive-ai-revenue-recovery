'use client';

import { ArrowDownRight, ArrowUpRight, Wallet, ShieldCheck, Activity, TrendingUp } from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatCurrency } from '@/lib/utils/formatting';

const ICONS = {
  risk: Wallet,
  recoverable: ShieldCheck,
  recovered: Activity,
  incremental: TrendingUp,
};

export function MetricCard({ label, value, trend, trendLabel, caption, icon, accent = false }) {
  const Icon = icon ? ICONS[icon] : null;
  const positive = trend >= 0;

  return (
    <div className="group relative overflow-hidden rounded-xl border border-border bg-card p-5 transition-all duration-200 hover:border-primary/30 hover:bg-accent/40">
      {accent && (
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary to-transparent opacity-70" />
      )}
      <div className="flex items-start justify-between gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-muted">
          {Icon && <Icon className="h-4 w-4 text-muted-foreground" />}
        </div>
        {trend !== undefined && (
          <div className={cn(
            'flex items-center gap-0.5 text-xs font-medium',
            positive ? 'text-success' : 'text-destructive'
          )}>
            {positive ? <ArrowUpRight className="h-3.5 w-3.5" /> : <ArrowDownRight className="h-3.5 w-3.5" />}
            {Math.abs(trend)}%
          </div>
        )}
      </div>
      <div className="mt-4">
        <p className="text-xs font-medium text-muted-foreground">{label}</p>
        <p className="mt-1 text-2xl font-semibold tracking-tight text-foreground tabular-nums lg:text-[30px]">
          {typeof value === 'number' ? formatCurrency(value, { compact: true }) : value}
        </p>
        {(trendLabel || caption) && (
          <p className="mt-1 text-[11px] text-muted-foreground">
            {trendLabel || caption}
          </p>
        )}
      </div>
    </div>
  );
}
