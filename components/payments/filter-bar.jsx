'use client';

import { Search, X } from 'lucide-react';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';

const STATUS_OPTIONS = [
  { value: 'all', label: 'All Statuses' },
  { value: 'READY', label: 'Ready' },
  { value: 'AWAITING_APPROVAL', label: 'Awaiting Approval' },
  { value: 'EXECUTING', label: 'Executing' },
  { value: 'RECOVERED', label: 'Recovered' },
  { value: 'STOPPED', label: 'Stopped' },
];

const METHOD_OPTIONS = [
  { value: 'all', label: 'All Methods' },
  { value: 'UPI', label: 'UPI' },
  { value: 'Cards', label: 'Cards' },
  { value: 'Netbanking', label: 'Netbanking' },
  { value: 'Wallet', label: 'Wallet' },
];

const FAILURE_OPTIONS = [
  { value: 'all', label: 'All Failures' },
  { value: 'Temporary Decline', label: 'Temporary Decline' },
  { value: 'Payment Method Issue', label: 'Payment Method Issue' },
  { value: 'Repeated Failure', label: 'Repeated Failure' },
  { value: 'Hard Decline', label: 'Hard Decline' },
  { value: 'Insufficient Funds', label: 'Insufficient Funds' },
  { value: 'Unknown Failure', label: 'Unknown Failure' },
];

const PROBABILITY_OPTIONS = [
  { value: 'all', label: 'Any Probability' },
  { value: 'high', label: 'High (70%+)' },
  { value: 'medium', label: 'Medium (40-69%)' },
  { value: 'low', label: 'Low (below 40%)' },
];

export function FilterBar({ filters, onChange, onClear, hasActiveFilters }) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="relative min-w-[200px] flex-1">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search transaction or customer..."
          value={filters.search}
          onChange={(e) => onChange({ ...filters, search: e.target.value })}
          className="h-9 pl-9"
        />
      </div>

      <Select
        value={filters.status}
        onValueChange={(value) => onChange({ ...filters, status: value })}
      >
        <SelectTrigger className="h-9 w-[150px]">
          <SelectValue placeholder="Status" />
        </SelectTrigger>
        <SelectContent>
          {STATUS_OPTIONS.map((opt) => (
            <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={filters.method}
        onValueChange={(value) => onChange({ ...filters, method: value })}
      >
        <SelectTrigger className="h-9 w-[150px]">
          <SelectValue placeholder="Method" />
        </SelectTrigger>
        <SelectContent>
          {METHOD_OPTIONS.map((opt) => (
            <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={filters.failure}
        onValueChange={(value) => onChange({ ...filters, failure: value })}
      >
        <SelectTrigger className="h-9 w-[170px]">
          <SelectValue placeholder="Failure" />
        </SelectTrigger>
        <SelectContent>
          {FAILURE_OPTIONS.map((opt) => (
            <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={filters.probability}
        onValueChange={(value) => onChange({ ...filters, probability: value })}
      >
        <SelectTrigger className="h-9 w-[160px]">
          <SelectValue placeholder="Probability" />
        </SelectTrigger>
        <SelectContent>
          {PROBABILITY_OPTIONS.map((opt) => (
            <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
          ))}
        </SelectContent>
      </Select>

      {hasActiveFilters && (
        <Button variant="ghost" size="sm" className="h-9 gap-1.5 text-xs" onClick={onClear}>
          <X className="h-3.5 w-3.5" />
          Clear
        </Button>
      )}
    </div>
  );
}
