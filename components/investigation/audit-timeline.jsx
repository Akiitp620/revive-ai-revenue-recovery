import { cn } from '@/lib/utils';

export function AuditTimeline({ events }) {
  return (
    <div className="relative space-y-0">
      {events.map((event, index) => {
        const isLast = index === events.length - 1;
        return (
          <div key={index} className="flex gap-4">
            <div className="flex flex-col items-center">
              <div className={cn(
                'mt-1 h-2.5 w-2.5 rounded-full ring-2',
                event.status === 'done'
                  ? 'bg-success ring-success/20'
                  : event.status === 'current'
                    ? 'bg-primary ring-primary/30'
                    : 'bg-muted-foreground ring-muted-foreground/20'
              )} />
              {!isLast && <div className="w-px flex-1 bg-border" style={{ minHeight: '32px' }} />}
            </div>
            <div className={cn('pb-6', isLast && 'pb-0')}>
              <p className="text-xs font-medium text-foreground">{event.event}</p>
              <p className="text-[11px] text-muted-foreground tabular-nums">{event.time}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
