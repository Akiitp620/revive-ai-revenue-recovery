import { AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function ErrorState({ title, description, onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10 ring-1 ring-destructive/20">
        <AlertCircle className="h-6 w-6 text-destructive" />
      </div>
      <div>
        <p className="text-sm font-medium text-foreground">
          {title || 'Unable to load data'}
        </p>
        {description && (
          <p className="mt-1 text-xs text-muted-foreground">{description}</p>
        )}
      </div>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry} className="mt-2">
          Retry
        </Button>
      )}
    </div>
  );
}
