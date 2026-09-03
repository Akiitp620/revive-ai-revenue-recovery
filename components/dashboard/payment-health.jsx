'use client';

import { ArrowDown, Minus } from 'lucide-react';
import { cn } from '@/lib/utils';

function Sparkline({ data, warning }) {
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * 100;
    const y = 28 - ((value - min) / range) * 22;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg viewBox="0 0 100 32" className="h-8 w-20" preserveAspectRatio="none" aria-hidden="true">
      <polyline fill="none" stroke={warning ? 'hsl(var(--warning))' : 'hsl(var(--success))'} strokeWidth="2" points={points} vectorEffect="non-scaling-stroke" />
    </svg>
  );
}

export function PaymentHealth({ data }) {
  return (
    <div className="divide-y divide-border">
      {data.map((item) => {
        const warning = item.health === 'warning';
        return (
          <div key={item.method} className="flex items-center justify-between gap-4 py-3.5 first:pt-0 last:pb-0">
            <div className="flex min-w-0 items-center gap-3">
              <div className={cn('h-2 w-2 rounded-full', warning ? 'bg-warning' : 'bg-success')} />
              <span className="text-sm font-medium text-foreground">{item.method}</span>
            </div>
            <div className="flex items-center gap-4">
              <Sparkline data={item.sparkline} warning={warning} />
              <div className="min-w-[52px] text-right">
                <p className="text-sm font-semibold text-foreground tabular-nums">{item.successRate}%</p>
                <div className={cn('flex items-center justify-end gap-0.5 text-[10px]', warning ? 'text-destructive' : 'text-muted-foreground')}>
                  {item.trend === 0 ? <Minus className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />}
                  {item.trend === 0 ? 'stable' : `${Math.abs(item.trend)}%`}
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
