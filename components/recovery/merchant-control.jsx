import { formatCurrency } from '@/lib/utils/formatting';
import { ShieldCheck } from 'lucide-react';

export function MerchantControl({ policy }) {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {policy.allowedActions.map((action) => (
          <span key={action} className="inline-flex items-center gap-1.5 rounded-full bg-muted px-3 py-1 text-xs font-medium text-foreground">
            {action}
          </span>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="rounded-lg border border-border bg-background p-3">
          <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Human Approval Required</p>
          <p className="mt-1 text-sm font-semibold text-foreground tabular-nums">Above {formatCurrency(policy.humanApprovalAbove)}</p>
        </div>
        <div className="rounded-lg border border-border bg-background p-3">
          <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Policy Version</p>
          <p className="mt-1 text-sm font-semibold text-foreground">{policy.version}</p>
        </div>
      </div>

      <div className="flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-2.5">
        <ShieldCheck className="h-4 w-4 text-success" />
        <span className="text-xs text-muted-foreground">
          All recovery actions are bounded by merchant-defined policy rules
        </span>
      </div>
    </div>
  );
}
