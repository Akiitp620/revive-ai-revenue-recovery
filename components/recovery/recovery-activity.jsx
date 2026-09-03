import Link from 'next/link';
import { formatCurrency } from '@/lib/utils/formatting';
import { cn } from '@/lib/utils';

const OUTCOME_STYLES = {
  Recovered: 'text-success',
  Stopped: 'text-destructive',
  Failed: 'text-destructive',
};

export function RecoveryActivity({ data }) {
  return (
    <div className="overflow-x-auto scrollbar-thin">
      <table className="w-full min-w-[640px] text-left">
        <thead>
          <tr className="border-b border-border">
            <th className="pb-3 pl-1 pr-4 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Time</th>
            <th className="px-4 pb-3 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Transaction</th>
            <th className="px-4 pb-3 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Action</th>
            <th className="px-4 pb-3 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Outcome</th>
            <th className="px-4 pb-3 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Recovered</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {data.map((item, i) => (
            <tr key={i} className="transition-colors hover:bg-accent/50">
              <td className="whitespace-nowrap py-3 pl-1 pr-4 text-xs text-muted-foreground tabular-nums">{item.time}</td>
              <td className="px-4 py-3">
                <Link href={`/payments/${item.transactionId}`} className="text-xs font-semibold text-foreground transition-colors hover:text-primary">
                  {item.transactionId}
                </Link>
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-xs text-foreground">{item.action}</td>
              <td className={cn('whitespace-nowrap px-4 py-3 text-xs font-medium', OUTCOME_STYLES[item.outcome] || 'text-muted-foreground')}>
                {item.outcome}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-xs font-semibold text-foreground tabular-nums">
                {item.recoveredAmount > 0 ? formatCurrency(item.recoveredAmount) : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
