import { cn } from '@/lib/utils';
import { ShieldCheck } from 'lucide-react';

const STATUS_DOT = {
  destructive: 'bg-destructive',
  warning: 'bg-warning',
  neutral: 'bg-muted-foreground',
};

export function RecoveryGuardrails({ rules }) {
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {rules.map((r) => (
          <div key={r.rule} className="flex items-center justify-between rounded-lg border border-border bg-background p-3">
            <div className="flex items-center gap-2.5">
              <ShieldCheck className="h-4 w-4 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">{r.rule}</span>
            </div>
            <div className="flex items-center gap-2">
              {r.status && (
                <span className={cn('h-1.5 w-1.5 rounded-full', STATUS_DOT[r.status] || STATUS_DOT.neutral)} />
              )}
              <span className="text-xs font-semibold text-foreground">{r.value}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
