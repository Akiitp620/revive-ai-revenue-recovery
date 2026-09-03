'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  CreditCard,
  RefreshCw,
  BarChart3,
  Settings,
  BookOpen,
  Activity,
} from 'lucide-react';

import { cn } from '@/lib/utils';
import { NAV_ITEMS, BOTTOM_NAV_ITEMS } from '@/lib/utils/constants';

const ICON_MAP = {
  LayoutDashboard,
  CreditCard,
  RefreshCw,
  BarChart3,
  Settings,
  BookOpen,
};

export function Sidebar({ onNavigate }) {
  const pathname = usePathname();

  return (
    <aside className="flex h-full w-60 flex-col border-r border-border bg-card">
      <div className="flex h-16 items-center gap-2.5 border-b border-border px-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 ring-1 ring-primary/20">
          <Activity className="h-5 w-5 text-primary" />
        </div>
        <div className="flex flex-col leading-none">
          <span className="text-base font-bold tracking-tight text-foreground">
            REVIVE
          </span>
          <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
            Revenue Recovery
          </span>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-1 px-3 py-4">
        <span className="mb-1 px-3 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
          Workspace
        </span>
        {NAV_ITEMS.map((item) => {
          const Icon = ICON_MAP[item.icon];
          const isActive =
            item.href === '/'
              ? pathname === '/'
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={cn(
                'group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200',
                isActive
                  ? 'bg-primary/10 text-primary ring-1 ring-primary/20'
                  : 'text-muted-foreground hover:bg-accent hover:text-foreground'
              )}
            >
              <Icon
                className={cn(
                  'h-4 w-4 transition-colors',
                  isActive
                    ? 'text-primary'
                    : 'text-muted-foreground group-hover:text-foreground'
                )}
              />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="flex flex-col gap-1 border-t border-border px-3 py-4">
        {BOTTOM_NAV_ITEMS.map((item) => {
          const Icon = ICON_MAP[item.icon];
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className="group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground transition-all duration-200 hover:bg-accent hover:text-foreground"
            >
              <Icon className="h-4 w-4 text-muted-foreground group-hover:text-foreground" />
              {item.label}
            </Link>
          );
        })}
      </div>

      <div className="border-t border-border px-5 py-3">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span className="h-2 w-2 rounded-full bg-success"></span>
          <span className="font-medium text-foreground/70">Operational</span>
          <span className="ml-auto text-[10px] uppercase tracking-wider">
            v0.1.0
          </span>
        </div>
      </div>
    </aside>
  );
}
