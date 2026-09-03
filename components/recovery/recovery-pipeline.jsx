import { cn } from '@/lib/utils';
import { formatCompactNumber } from '@/lib/utils/formatting';
import { ChevronRight } from 'lucide-react';

const COLOR_MAP = {
  success: 'text-success',
  warning: 'text-warning',
  destructive: 'text-destructive',
  info: 'text-primary',
  neutral: 'text-muted-foreground',
};

const DOT_MAP = {
  success: 'bg-success',
  warning: 'bg-warning',
  destructive: 'bg-destructive',
  info: 'bg-primary',
  neutral: 'bg-muted-foreground',
};

const BORDER_MAP = {
  success: 'border-success/20',
  warning: 'border-warning/20',
  destructive: 'border-destructive/20',
  info: 'border-primary/20',
  neutral: 'border-border',
};

export function RecoveryPipeline({ stages }) {
  return (
    <div className="flex flex-col gap-3 lg:flex-row lg:items-stretch">
      {stages.map((stage, index) => (
        <div key={stage.stage} className="flex flex-1 items-center gap-3 lg:flex-col">
          <div className={cn(
            'flex w-full flex-1 flex-col rounded-lg border bg-background p-4',
            BORDER_MAP[stage.color] || 'border-border'
          )}>
            <div className="flex items-center gap-2">
              <span className={cn('h-2 w-2 rounded-full', DOT_MAP[stage.color])} />
              <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">{stage.stage}</span>
            </div>
            <p className={cn('mt-2 text-xl font-bold tabular-nums', COLOR_MAP[stage.color])}>
              {formatCompactNumber(stage.count)}
            </p>
          </div>
          {index < stages.length - 1 && (
            <ChevronRight className="hidden h-4 w-4 shrink-0 text-muted-foreground lg:block" />
          )}
        </div>
      ))}
    </div>
  );
}
