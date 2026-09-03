'use client';

import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { formatCurrency } from '@/lib/utils/formatting';

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;

  return (
    <div className="rounded-lg border border-border bg-popover px-3 py-2.5 shadow-xl">
      <p className="mb-2 text-[11px] font-medium text-muted-foreground">{label}</p>
      {payload.map((entry) => (
        <div key={entry.dataKey} className="flex items-center justify-between gap-6 py-0.5 text-xs">
          <span className="flex items-center gap-1.5 text-muted-foreground">
            <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: entry.color }} />
            {entry.name}
          </span>
          <span className="font-medium text-foreground tabular-nums">{formatCurrency(entry.value, { compact: true })}</span>
        </div>
      ))}
    </div>
  );
}

export function RevenueTrendChart({ data }) {
  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 12, right: 12, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="hsl(var(--border))" strokeDasharray="3 3" vertical={false} opacity={0.6} />
          <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }} dy={8} />
          <YAxis axisLine={false} tickLine={false} tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }} tickFormatter={(value) => formatCurrency(value, { compact: true })} width={48} />
          <Tooltip content={<ChartTooltip />} cursor={{ stroke: 'hsl(var(--border))' }} />
          <Legend verticalAlign="top" align="right" height={32} iconType="circle" iconSize={6} wrapperStyle={{ fontSize: '11px', color: 'hsl(var(--muted-foreground))' }} />
          <Line type="monotone" dataKey="atRisk" name="Revenue at Risk" stroke="hsl(var(--chart-3))" strokeWidth={2} dot={false} activeDot={{ r: 4, fill: 'hsl(var(--chart-3))', stroke: 'hsl(var(--card))', strokeWidth: 2 }} />
          <Line type="monotone" dataKey="recovered" name="Recovered Revenue" stroke="hsl(var(--chart-2))" strokeWidth={2} dot={false} activeDot={{ r: 4, fill: 'hsl(var(--chart-2))', stroke: 'hsl(var(--card))', strokeWidth: 2 }} />
          <Line type="monotone" dataKey="baseline" name="Baseline Recovery" stroke="hsl(var(--muted-foreground))" strokeWidth={1.5} strokeDasharray="5 5" dot={false} activeDot={{ r: 4, fill: 'hsl(var(--muted-foreground))', stroke: 'hsl(var(--card))', strokeWidth: 2 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
