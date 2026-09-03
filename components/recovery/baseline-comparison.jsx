import { formatCurrency } from '@/lib/utils/formatting';
import { ArrowUpRight } from 'lucide-react';

export function BaselineComparison({ data }) {
  const { baseline, revive, difference, improvement } = data;
  const maxValue = Math.max(baseline.recovered, revive.recovered);

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Baseline</p>
          <p className="mt-1 text-sm font-medium text-foreground">{baseline.label}</p>
          <p className="mt-3 text-2xl font-bold text-muted-foreground tabular-nums">{formatCurrency(baseline.recovered, { compact: true })}</p>
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-muted">
            <div className="h-full rounded-full bg-muted-foreground/40" style={{ width: `${(baseline.recovered / maxValue) * 100}%` }} />
          </div>
        </div>

        <div className="rounded-lg border border-primary/30 bg-primary/5 p-4">
          <div className="flex items-center justify-between">
            <p className="text-[10px] font-medium uppercase tracking-wider text-primary">REVIVE</p>
            <span className="inline-flex items-center gap-0.5 text-xs font-medium text-success">
              <ArrowUpRight className="h-3.5 w-3.5" />
              {improvement}%
            </span>
          </div>
          <p className="mt-1 text-sm font-medium text-foreground">{revive.label}</p>
          <p className="mt-3 text-2xl font-bold text-success tabular-nums">{formatCurrency(revive.recovered, { compact: true })}</p>
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-muted">
            <div className="h-full rounded-full bg-success" style={{ width: `${(revive.recovered / maxValue) * 100}%` }} />
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between rounded-lg border border-success/20 bg-success/5 px-4 py-3">
        <div>
          <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Incremental Recovery</p>
          <p className="mt-0.5 text-lg font-bold text-success tabular-nums">+{formatCurrency(difference, { compact: true })}</p>
        </div>
        <div className="text-right">
          <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Recovery Improvement</p>
          <p className="mt-0.5 text-lg font-bold text-foreground tabular-nums">+{improvement}%</p>
        </div>
      </div>

      <p className="text-center text-[10px] text-muted-foreground">
        SIMULATION — Values are simulated demo data, not production benchmark results
      </p>
    </div>
  );
}
