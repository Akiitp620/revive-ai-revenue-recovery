import { CheckCircle2 } from 'lucide-react';

export function EvidenceList({ items }) {
  return (
    <ul className="space-y-3">
      {items.map((item, index) => (
        <li key={index} className="flex items-start gap-3">
          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" />
          <div>
            <p className="text-sm font-medium text-foreground">{item.label}</p>
            <p className="text-xs text-muted-foreground">{item.detail}</p>
          </div>
        </li>
      ))}
    </ul>
  );
}
