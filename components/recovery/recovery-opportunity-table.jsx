'use client';

import Link from 'next/link';
import { ChevronRight } from 'lucide-react';
import { formatCurrency, formatPercentage } from '@/lib/utils/formatting';
import { StatusBadge } from '@/components/shared/status-badge';

export function RecoveryOpportunityTable({ data }) {
  return (
    <div className="overflow-x-auto scrollbar-thin">
      <table className="w-full min-w-[760px] text-left">
        <thead>
          <tr className="border-b border-border">
            <th className="pb-3 pl-1 pr-4 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Transaction</th>
            <th className="px-4 pb-3 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Amount</th>
            <th className="px-4 pb-3 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Probability</th>
            <th className="px-4 pb-3 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Expected Recovery</th>
            <th className="px-4 pb-3 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Action</th>
            <th className="px-4 pb-3 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Status</th>
            <th className="pb-3 pl-4 pr-1" />
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {data.map((item) => (
            <tr key={item.transactionId} className="group transition-colors hover:bg-accent/50">
              <td className="py-3.5 pl-1 pr-4">
                <Link href={`/payments/${item.transactionId}`} className="text-xs font-semibold text-foreground transition-colors hover:text-primary">
                  {item.transactionId}
                </Link>
              </td>
              <td className="whitespace-nowrap px-4 py-3.5 text-xs font-medium text-foreground tabular-nums">{formatCurrency(item.amount)}</td>
              <td className="px-4 py-3.5">
                <div className="flex items-center gap-2">
                  <div className="h-1.5 w-12 overflow-hidden rounded-full bg-muted">
                    <div className="h-full rounded-full bg-primary" style={{ width: `${item.recoveryProbability}%` }} />
                  </div>
                  <span className="text-xs font-medium text-foreground tabular-nums">{formatPercentage(item.recoveryProbability)}</span>
                </div>
              </td>
              <td className="whitespace-nowrap px-4 py-3.5 text-xs font-semibold text-success tabular-nums">{formatCurrency(item.expectedRecovery)}</td>
              <td className="whitespace-nowrap px-4 py-3.5 text-xs text-foreground">{item.recommendedAction}</td>
              <td className="px-4 py-3.5"><StatusBadge status={item.status} /></td>
              <td className="py-3.5 pl-4 pr-1"><ChevronRight className="h-4 w-4 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
