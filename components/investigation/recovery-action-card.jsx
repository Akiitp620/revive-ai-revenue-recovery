'use client';

import { Check, Ban, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatCurrency, formatPercentage } from '@/lib/utils/formatting';

export function RecoveryActionCard({ action, selected, onSelect }) {
  const isStop = action.id === 'STOP';
  const isBlocked = action.isAllowed === false;
  const isSelected = selected && !isBlocked;

  return (
    <button
      onClick={() => {
        if (!isBlocked) onSelect(action);
      }}
      disabled={isBlocked}
      className={cn(
        'group relative flex flex-col gap-3 rounded-xl border p-4 text-left transition-all duration-200',
        isSelected
          ? 'border-primary bg-primary/5 ring-1 ring-primary/30'
          : 'border-border bg-card hover:border-primary/30 hover:bg-accent/40',
        isStop && 'opacity-80',
        isBlocked && 'opacity-60 cursor-not-allowed hover:bg-card hover:border-border grayscale'
      )}
    >
      {action.recommended && !isBlocked && (
        <span className="absolute -top-2.5 left-4 inline-flex items-center gap-1 rounded-full bg-primary px-2 py-0.5 text-[10px] font-semibold text-primary-foreground">
          <Check className="h-2.5 w-2.5" /> Recommended
        </span>
      )}

      {isBlocked && (
        <span className="absolute -top-2.5 right-4 inline-flex items-center gap-1 rounded-full bg-destructive/10 border border-destructive/20 px-2 py-0.5 text-[10px] font-semibold text-destructive">
          <AlertCircle className="h-2.5 w-2.5" /> Policy Blocked
        </span>
      )}

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {isStop || isBlocked ? <Ban className="h-4 w-4 text-destructive" /> : <Check className="h-4 w-4 text-muted-foreground" />}
          <span className="text-sm font-semibold text-foreground">{action.label}</span>
        </div>
        {isSelected && (
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary">
            <Check className="h-3 w-3 text-primary-foreground" />
          </span>
        )}
      </div>

      {action.description && (
        <p className="text-xs text-muted-foreground">{action.description}</p>
      )}

      <div className="flex flex-col gap-2 border-t border-border pt-3">
        <div className="flex items-end justify-between">
          <div>
            <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Exp. Recovery</p>
            <p className={cn('text-sm font-semibold tabular-nums', isStop ? 'text-destructive' : 'text-foreground')}>
              {formatCurrency(action.expectedRecovery || 0)}
            </p>
          </div>
          <div className="text-right">
            <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Probability</p>
            <p className="text-sm font-semibold text-foreground tabular-nums">{formatPercentage(action.probability || 0)}</p>
          </div>
        </div>

        <div className="flex items-end justify-between border-t border-border/50 pt-2">
          <div>
            <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Cost</p>
            <p className="text-sm font-medium tabular-nums text-muted-foreground">
              {formatCurrency(action.interventionCost || 0)}
            </p>
          </div>
          <div className="text-right">
            <p className="text-[10px] font-medium uppercase tracking-wider text-primary/80">Net Recovery</p>
            <p className={cn('text-lg font-bold tabular-nums', isStop ? 'text-destructive' : 'text-success')}>
              {formatCurrency(action.expectedNetRecovery !== undefined ? action.expectedNetRecovery : (action.expectedRecovery || 0))}
            </p>
          </div>
        </div>
      </div>
    </button>
  );
}
