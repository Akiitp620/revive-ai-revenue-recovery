import { formatCurrency } from '@/lib/utils/formatting';
import { ShieldCheck, AlertTriangle } from 'lucide-react';

export function PolicyCard({ policy, amount }) {
  const requiresApproval = policy.requiresApproval;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-lg border border-border bg-background p-3">
          <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Max Auto Retries</p>
          <p className="mt-1 text-sm font-semibold text-foreground tabular-nums">{policy.maxAutomaticRetries}</p>
        </div>
        <div className="rounded-lg border border-border bg-background p-3">
          <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Max Auto Recovery</p>
          <p className="mt-1 text-sm font-semibold text-foreground tabular-nums">{formatCurrency(policy.maxAutomaticRecoveryValue)}</p>
        </div>
        <div className="rounded-lg border border-border bg-background p-3">
          <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Approval Above</p>
          <p className="mt-1 text-sm font-semibold text-foreground tabular-nums">{formatCurrency(policy.humanApprovalAbove)}</p>
        </div>
        <div className="rounded-lg border border-border bg-background p-3">
          <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Allowed Actions</p>
          <p className="mt-1 text-sm font-semibold text-foreground">{policy.allowedActions.join(', ')}</p>
        </div>
      </div>

      <div className={`flex items-center gap-3 rounded-lg border p-3 ${requiresApproval ? 'border-warning/30 bg-warning/5' : 'border-success/30 bg-success/5'}`}>
        {requiresApproval ? (
          <AlertTriangle className="h-5 w-5 shrink-0 text-warning" />
        ) : (
          <ShieldCheck className="h-5 w-5 shrink-0 text-success" />
        )}
        <div>
          <p className="text-sm font-medium text-foreground">
            {requiresApproval ? 'Human approval required' : 'Auto-execution permitted'}
          </p>
          <p className="text-xs text-muted-foreground">
            {requiresApproval
              ? policy.reason || `Transaction requires manual review`
              : 'Transaction is within automatic recovery limits'}
          </p>
        </div>
      </div>
    </div>
  );
}
