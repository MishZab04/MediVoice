'use client'

import { Menu } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'
import { ThemeToggle } from './ThemeToggle'
import { Sidebar } from './Sidebar'
import { getUser } from '@/lib/auth'
import { useState } from 'react'

interface TopbarProps {
  title: string
}

export function Topbar({ title }: TopbarProps) {
  const user = getUser()
  const [open, setOpen] = useState(false)

  return (
    <header className="h-14 border-b bg-background flex items-center px-4 gap-4 sticky top-0 z-10">
      {/* Mobile menu */}
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetTrigger asChild>
          <Button variant="ghost" size="icon" className="lg:hidden">
            <Menu className="h-5 w-5" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="p-0 w-64">
          <Sidebar onNavigate={() => setOpen(false)} />
        </SheetContent>
      </Sheet>

      {/* Page title */}
      <h1 className="text-base font-semibold flex-1">{title}</h1>

      {/* Right side */}
      <div className="flex items-center gap-2">
        <ThemeToggle />
        <div className="hidden sm:flex flex-col items-end">
          <p className="text-sm font-medium leading-tight">
            {user?.first_name} {user?.last_name}
          </p>
          <p className="text-xs text-muted-foreground capitalize">{user?.role?.replace('_', ' ')}</p>
        </div>
      </div>
    </header>
  )
}
