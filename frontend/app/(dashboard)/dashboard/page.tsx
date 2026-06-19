'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Users, Mic2, AlertTriangle, CalendarCheck, Plus, ArrowRight } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import api from '@/lib/api'
import { getUser } from '@/lib/auth'
import { AnalyticsSummary, AssessmentSession } from '@/types'

const LANGUAGE_LABELS: Record<string, string> = { en: 'English', fr: 'French', pcm: 'Pidgin' }

function StatCard({
  title, value, icon: Icon, color, loading,
}: {
  title: string
  value: number | undefined
  icon: React.ElementType
  color: string
  loading: boolean
}) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">{title}</p>
            {loading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <p className="text-3xl font-bold">{value ?? 0}</p>
            )}
          </div>
          <div className="h-12 w-12 rounded-full flex items-center justify-center" style={{ backgroundColor: color + '20' }}>
            <Icon className="h-6 w-6" style={{ color }} />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default function DashboardPage() {
  const user = getUser()
  const isAdmin = user?.role === 'admin'

  const [summary, setSummary] = useState<AnalyticsSummary | null>(null)
  const [recent, setRecent] = useState<AssessmentSession[]>([])
  const [loadingSummary, setLoadingSummary] = useState(true)
  const [loadingRecent, setLoadingRecent] = useState(true)

  useEffect(() => {
    api.get<AnalyticsSummary>('/analytics/summary/')
      .then((r) => setSummary(r.data))
      .finally(() => setLoadingSummary(false))

    api.get<AssessmentSession[]>('/assessment/sessions/')
      .then((r) => setRecent(r.data ?? []))
      .catch(() => setRecent([]))
      .finally(() => setLoadingRecent(false))
  }, [])

  const greeting = () => {
    const h = new Date().getHours()
    if (h < 12) return 'Good morning'
    if (h < 18) return 'Good afternoon'
    return 'Good evening'
  }

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">
            {greeting()}, {user?.first_name} 👋
          </h2>
          <p className="text-sm text-muted-foreground mt-0.5">
            {isAdmin ? 'System-wide overview' : 'Here\'s your activity summary'}
          </p>
        </div>
        <Button asChild style={{ backgroundColor: '#00B89C' }} className="text-white">
          <Link href="/assessment/new">
            <Plus className="h-4 w-4 mr-2" /> New Assessment
          </Link>
        </Button>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard title="Total Assessments" value={summary?.total_assessments} icon={Mic2}         color="#00B89C" loading={loadingSummary} />
        <StatCard title="Total Patients"     value={summary?.total_patients}    icon={Users}        color="#1B3A6B" loading={loadingSummary} />
        <StatCard title="Urgent Cases"       value={summary?.total_urgent}      icon={AlertTriangle} color="#f59e0b" loading={loadingSummary} />
        <StatCard title="Done This Week"     value={summary?.completed_this_week} icon={CalendarCheck} color="#6366f1" loading={loadingSummary} />
      </div>

      {/* Language breakdown + Recent assessments */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Language breakdown */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Assessments by Language</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {loadingSummary ? (
              [1,2,3].map((i) => <Skeleton key={i} className="h-8 w-full" />)
            ) : (
              Object.entries(summary?.by_language ?? {}).map(([lang, count]) => {
                const total = summary?.total_assessments || 1
                const pct = Math.round((count / total) * 100)
                return (
                  <div key={lang} className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">{LANGUAGE_LABELS[lang]}</span>
                      <span className="font-medium">{count}</span>
                    </div>
                    <div className="h-2 rounded-full bg-muted overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all"
                        style={{ width: `${pct}%`, backgroundColor: '#00B89C' }}
                      />
                    </div>
                  </div>
                )
              })
            )}
          </CardContent>
        </Card>

        {/* Recent assessments */}
        <Card className="lg:col-span-2">
          <CardHeader className="pb-3 flex flex-row items-center justify-between">
            <CardTitle className="text-base">Recent Assessments</CardTitle>
            <Button variant="ghost" size="sm" asChild className="text-xs">
              <Link href="/assessment">View all <ArrowRight className="h-3 w-3 ml-1" /></Link>
            </Button>
          </CardHeader>
          <CardContent>
            {loadingRecent ? (
              <div className="space-y-3">
                {[1,2,3].map((i) => <Skeleton key={i} className="h-12 w-full" />)}
              </div>
            ) : recent.length === 0 ? (
              <div className="text-center py-8 text-sm text-muted-foreground">
                No assessments yet.{' '}
                <Link href="/assessment/new" className="underline" style={{ color: '#00B89C' }}>
                  Start one
                </Link>
              </div>
            ) : (
              <div className="space-y-2">
                {recent.map((s) => (
                  <Link
                    key={s.id}
                    href={`/assessment/${s.id}`}
                    className="flex items-center justify-between p-3 rounded-lg hover:bg-muted/50 transition-colors group"
                  >
                    <div className="space-y-0.5">
                      <p className="text-sm font-medium">
                        {s.patient.first_name} {s.patient.last_name}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {LANGUAGE_LABELS[s.language]} · {new Date(s.started_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {s.assessment_priority === 'URGENT' && (
                        <Badge variant="destructive" className="text-xs">Urgent</Badge>
                      )}
                      <Badge
                        variant="outline"
                        className="text-xs capitalize"
                        style={s.status === 'completed' ? { borderColor: '#00B89C', color: '#00B89C' } : undefined}
                      >
                        {s.status.replace('_', ' ')}
                      </Badge>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Admin: top health workers */}
      {isAdmin && summary?.top_health_workers && summary.top_health_workers.length > 0 && (
        <Card>
          <CardHeader className="pb-3 flex flex-row items-center justify-between">
            <CardTitle className="text-base">Top Health Workers</CardTitle>
            <Button variant="ghost" size="sm" asChild className="text-xs">
              <Link href="/health-workers">Manage <ArrowRight className="h-3 w-3 ml-1" /></Link>
            </Button>
          </CardHeader>
          <CardContent>
            <div className="divide-y">
              {summary.top_health_workers.map((w, i) => (
                <div key={w.id} className="flex items-center gap-4 py-3">
                  <span className="text-sm text-muted-foreground w-5">{i + 1}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{w.name}</p>
                    <p className="text-xs text-muted-foreground truncate">{w.facility_name || w.email}</p>
                  </div>
                  <Badge variant="secondary">{w.assessment_count} sessions</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
