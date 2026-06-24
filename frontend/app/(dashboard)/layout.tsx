'use client'

import { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { Sidebar } from '@/components/layout/Sidebar'
import { Topbar } from '@/components/layout/Topbar'
import { isAuthenticated } from '@/lib/auth'

const pageTitles: Record<string, string> = {
  '/dashboard':      'Dashboard',
  '/patients':       'Patients',
  '/assessment':     'Assessments',
  '/assessment/new': 'New Assessment',
  '/analytics':      'Analytics',
  '/health-workers': 'Health Workers',
  '/profile':        'My Profile',
}

function getTitle(pathname: string): string {
  if (pageTitles[pathname]) return pageTitles[pathname]
  if (pathname.startsWith('/assessment/') && pathname.endsWith('/report')) return 'Assessment Report'
  if (pathname.startsWith('/assessment/')) return 'Assessment'
  if (pathname.startsWith('/patients/')) return 'Patient Details'
  return 'MediVoice'
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace('/login')
    }
  }, [router])

  if (!isAuthenticated()) return null

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar — desktop only */}
      <aside className="hidden lg:flex lg:w-64 lg:flex-col flex-shrink-0">
        <Sidebar />
      </aside>

      {/* Main content */}
      <div className="flex flex-col flex-1 overflow-hidden">
        <Topbar title={getTitle(pathname)} />
        <main className="flex-1 overflow-y-auto p-6 bg-muted/30">
          {children}
        </main>
      </div>
    </div>
  )
}
