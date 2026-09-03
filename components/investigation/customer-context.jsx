import { formatCurrency } from '@/lib/utils/formatting';

export function CustomerContext({ customer }) {
  const items = [
    { label: 'Successful Payments', value: customer.successfulPayments },
    { label: 'Previous Recovery Rate', value: `${customer.previousRecoveryRate}%` },
    { label: 'Average Transaction', value: formatCurrency(customer.averageTransaction) },
    { label: 'Customer Since', value: customer.customerSince },
    { label: 'Customer Segment', value: customer.segment, badge: true },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {items.map((item) => (
        <div key={item.label} className="rounded-lg border border-border bg-background p-3">
          <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">{item.label}</p>
          {item.badge ? (
            <span className="mt-1.5 inline-flex rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary ring-1 ring-primary/20">
              {item.value}
            </span>
          ) : (
            <p className="mt-1 text-sm font-semibold text-foreground tabular-nums">{item.value}</p>
          )}
        </div>
      ))}
    </div>
  );
}
