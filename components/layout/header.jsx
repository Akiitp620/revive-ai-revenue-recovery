'use client';

import { useState } from 'react';
import { Menu, ChevronDown, Bell } from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  Sheet,
  SheetContent,
  SheetTrigger,
  SheetTitle,
} from '@/components/ui/sheet';
import { Sidebar } from '@/components/layout/sidebar';
import { MERCHANT } from '@/lib/utils/constants';

export function Header() {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <header className="flex h-16 items-center justify-between border-b border-border bg-card px-4 lg:px-6">
      <div className="flex items-center gap-3">
        <Sheet open={mobileNavOpen} onOpenChange={setMobileNavOpen}>
          <SheetTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden"
              aria-label="Open navigation menu"
            >
              <Menu className="h-5 w-5" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-60 p-0">
            <SheetTitle className="sr-only">Navigation</SheetTitle>
            <Sidebar onNavigate={() => setMobileNavOpen(false)} />
          </SheetContent>
        </Sheet>

        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-foreground">
            {MERCHANT.name}
          </span>
          <span className="flex items-center gap-1.5 rounded-full bg-warning/10 px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-warning ring-1 ring-warning/20">
            <span className="h-1.5 w-1.5 rounded-full bg-warning"></span>
            {MERCHANT.environment}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden items-center gap-2 rounded-lg border border-border bg-background px-3 py-1.5 sm:flex">
          <span className="h-2 w-2 rounded-full bg-success"></span>
          <span className="text-xs font-medium text-muted-foreground">
            System {MERCHANT.status}
          </span>
        </div>

        <Button
          variant="ghost"
          size="icon"
          className="relative"
          aria-label="Notifications"
        >
          <Bell className="h-4 w-4 text-muted-foreground" />
          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-primary"></span>
        </Button>

        <button
          className="flex items-center gap-2 rounded-lg p-1 pr-2 transition-colors hover:bg-accent"
          aria-label="User menu"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/15 text-xs font-bold text-primary ring-1 ring-primary/20">
            DM
          </div>
          <ChevronDown className="hidden h-3.5 w-3.5 text-muted-foreground sm:block" />
        </button>
      </div>
    </header>
  );
}
