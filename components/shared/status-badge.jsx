import { cn } from '@/lib/utils';
import { RECOVERY_STATUS } from '@/lib/utils/constants';

const VARIANT_STYLES = {
  success: 'bg-success/10 text-success ring-1 ring-success/20',
  warning: 'bg-warning/10 text-warning ring-1 ring-warning/20',
  destructive: 'bg-destructive/10 text-destructive ring-1 ring-destructive/20',
  info: 'bg-primary/10 text-primary ring-1 ring-primary/20',
  neutral: 'bg-muted text-muted-foreground ring-1 ring-border',
};

export function StatusBadge({ status, variant, label, className }) {
  const resolvedVariant =
    variant || (RECOVERY_STATUS[status] && RECOVERY_STATUS[status].variant) || 'neutral';
  const resolvedLabel = label || (RECOVERY_STATUS[status] && RECOVERY_STATUS[status].label) || status;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium',
        VARIANT_STYLES[resolvedVariant],
        className
      )}
    >
      <span className={cn(
        'h-1.5 w-1.5 rounded-full',
        resolvedVariant === 'success' && 'bg-success',
        resolvedVariant === 'warning' && 'bg-warning',
        resolvedVariant === 'destructive' && 'bg-destructive',
        resolvedVariant === 'info' && 'bg-primary',
        resolvedVariant === 'neutral' && 'bg-muted-foreground',
      )} />
      {resolvedLabel}
    </span>
  );
}
