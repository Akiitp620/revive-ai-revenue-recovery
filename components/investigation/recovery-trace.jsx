import { ArrowRight } from 'lucide-react';
import { cn } from '@/lib/utils';

export function RecoveryTrace({ steps, currentStep }) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      {steps.map((step, index) => {
        const isActive = index === currentStep;
        const isPast = index < currentStep;
        return (
          <div key={step} className="flex items-center gap-2">
            <span className={cn(
              'rounded-lg px-3 py-1.5 text-xs font-medium transition-colors',
              isActive
                ? 'bg-primary text-primary-foreground'
                : isPast
                  ? 'bg-success/10 text-success'
                  : 'bg-muted text-muted-foreground'
            )}>
              {step}
            </span>
            {index < steps.length - 1 && <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />}
          </div>
        );
      })}
    </div>
  );
}
