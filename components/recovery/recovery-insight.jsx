import { Sparkles } from 'lucide-react';
import { formatCurrency } from '@/lib/utils/formatting';

export function RecoveryInsight({ insight }) {
  return (
    <div className="space-y-4">
      <div className="flex items-start gap-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10">
          <Sparkles className="h-4 w-4 text-primary" />
        </div>
        <p className="text-sm leading-relaxed text-foreground">{insight.text}</p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div className="rounded-lg border border-border bg-background p-3">
          <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Revenue Opportunity</p>
          <p className="mt-1 text-base font-bold text-success tabular-nums">{formatCurrency(insight.revenueOpportunity, { compact: true })}</p>
        </div>
        <div className="rounded-lg border border-border bg-background p-3">
          <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Affected Segment</p>
          <p className="mt-1 text-sm font-semibold text-foreground">{insight.affectedSegment}</p>
        </div>
        <div className="rounded-lg border border-border bg-background p-3">
          <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Recommended Focus</p>
          <p className="mt-1 text-sm font-semibold text-foreground">{insight.recommendedFocus}</p>
        </div>
      </div>
    </div>
  );
}
