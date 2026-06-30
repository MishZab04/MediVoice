'use client'

import Link from 'next/link'
import Image from 'next/image'
import { usePathname, useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import {
  LayoutDashboard,
  Users,
  Mic2,
  BarChart3,
  UserCog,
  UserCheck,
  User,
  LogOut,
} from 'lucide-react'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'
import { getUser, clearTokens } from '@/lib/auth'
import api from '@/lib/api'

const navItems = [
  { label: 'Dashboard',      href: '/dashboard',       icon: LayoutDashboard, adminOnly: false },
  { label: 'Patients',       href: '/patients',         icon: Users,           adminOnly: false },
  { label: 'Assessments',    href: '/assessment',       icon: Mic2,            adminOnly: false },
  { label: 'Analytics',      href: '/analytics',        icon: BarChart3,       adminOnly: true  },
  { label: 'Health Workers', href: '/health-workers',   icon: UserCog,         adminOnly: true  },
  { label: 'Approvals',      href: '/approvals',        icon: UserCheck,       adminOnly: true  },
]

interface SidebarProps {
  onNavigate?: () => void
}

export function Sidebar({ onNavigate }: SidebarProps) {
  const pathname = usePathname()
  const router = useRouter()
  const user = getUser()
  const isAdmin = user?.role === 'admin'
  const [pendingCount, setPendingCount] = useState(0)

  useEffect(() => {
    if (!isAdmin) return
    api.get<{ pending_approvals: number }>('/analytics/summary/')
      .then((r) => setPendingCount(r.data.pending_approvals ?? 0))
      .catch(() => {})
  }, [isAdmin])

  async function handleLogout() {
    try {
      const refresh = localStorage.getItem('refresh_token')
      if (refresh) await api.post('/auth/logout/', { refresh })
    } catch { /* ignore */ }
    clearTokens()
    toast.success('Logged out successfully.')
    router.push('/login')
  }

  const visible = navItems.filter((item) => !item.adminOnly || isAdmin)

  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: '#1B3A6B' }}>
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-white/10">
        <div className="rounded-xl overflow-hidden flex-shrink-0">
          <Image src="/medivoice_logo.png" alt="MediVoice" width={36} height={36} />
        </div>
        <div>
          <p className="text-white font-bold text-base leading-tight">MediVoice</p>
          <p className="text-white/50 text-[11px]">
            {isAdmin ? 'Administrator' : 'Health Worker'}
          </p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {visible.map((item) => {
          const active = pathname === item.href || pathname.startsWith(item.href + '/')
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                active
                  ? 'text-white'
                  : 'text-white/60 hover:text-white hover:bg-white/10'
              )}
              style={active ? { backgroundColor: '#00B89C' } : undefined}
            >
              <item.icon className="h-4 w-4 flex-shrink-0" />
              <span className="flex-1">{item.label}</span>
              {item.href === '/approvals' && pendingCount > 0 && (
                <span className="ml-auto text-xs font-semibold rounded-full px-1.5 py-0.5 min-w-5 text-center text-white" style={{ backgroundColor: '#f59e0b' }}>
                  {pendingCount}
                </span>
              )}
            </Link>
          )
        })}
      </nav>

      {/* User + Logout */}
      <div className="px-3 py-4 border-t border-white/10 space-y-1">
        <Link
          href="/profile"
          onClick={onNavigate}
          className={cn(
            'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
            pathname === '/profile'
              ? 'text-white'
              : 'text-white/60 hover:text-white hover:bg-white/10'
          )}
          style={pathname === '/profile' ? { backgroundColor: '#00B89C' } : undefined}
        >
          <User className="h-4 w-4 flex-shrink-0" />
          Profile
        </Link>

        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-white/60 hover:text-white hover:bg-white/10 transition-colors"
        >
          <LogOut className="h-4 w-4 flex-shrink-0" />
          Log out
        </button>

        {/* User info chip */}
        <div className="mt-3 px-3 py-2.5 rounded-lg bg-white/5">
          <p className="text-white text-sm font-medium truncate">
            {user?.first_name} {user?.last_name}
          </p>
          <p className="text-white/50 text-xs truncate">{user?.email}</p>
        </div>
      </div>
    </div>
  )
}
