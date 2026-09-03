import { cn } from '@/lib/utils';

export function RecoveryEfficiency({ metrics }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {metrics.map((m) => (
        <div
          key={m.label}
          className={cn(
            'rounded-lg border border-border bg-background p-4',
            m.emphasis && 'border-primary/30 bg-primary/5'
          )}
        >
          <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">{m.label}</p>
          <p className={cn(
            'mt-2 text-xl font-bold tabular-nums',
            m.emphasis ? 'text-primary' : 'text-foreground'
          )}>
            {m.value}
          </p>
        </div>
      ))}
    </div>
  );
}
