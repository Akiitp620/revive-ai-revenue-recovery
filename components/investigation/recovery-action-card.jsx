'use client';

import { Check, Ban } from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatCurrency, formatPercentage } from '@/lib/utils/formatting';

export function RecoveryActionCard({ action, selected, onSelect }) {
  const isStop = action.id === 'STOP';

  return (
    <button
      onClick={() => onSelect(action)}
      className={cn(
        'group relative flex flex-col gap-3 rounded-xl border p-4 text-left transition-all duration-200',
        selected
          ? 'border-primary bg-primary/5 ring-1 ring-primary/30'
          : 'border-border bg-card hover:border-primary/30 hover:bg-accent/40',
        isStop && 'opacity-70'
      )}
    >
      {action.recommended && (
        <span className="absolute -top-2.5 left-4 inline-flex items-center gap-1 rounded-full bg-primary px-2 py-0.5 text-[10px] font-semibold text-primary-foreground">
          <Check className="h-2.5 w-2.5" /> Recommended
        </span>
      )}

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {isStop ? <Ban className="h-4 w-4 text-destructive" /> : <Check className="h-4 w-4 text-muted-foreground" />}
          <span className="text-sm font-semibold text-foreground">{action.label}</span>
        </div>
        {selected && (
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary">
            <Check className="h-3 w-3 text-primary-foreground" />
          </span>
        )}
      </div>

      <p className="text-xs text-muted-foreground">{action.description}</p>

      <div className="flex items-end justify-between border-t border-border pt-3">
        <div>
          <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Expected Recovery</p>
          <p className={cn('text-lg font-semibold tabular-nums', isStop ? 'text-destructive' : 'text-success')}>
            {formatCurrency(action.expectedRecovery)}
          </p>
        </div>
        <div className="text-right">
          <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Probability</p>
          <p className="text-sm font-semibold text-foreground tabular-nums">{formatPercentage(action.probability)}</p>
        </div>
      </div>
    </button>
  );
}
