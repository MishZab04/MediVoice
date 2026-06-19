'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import api from '@/lib/api'
import { isAdmin } from '@/lib/auth'
import { AnalyticsSummary, DailyCount } from '@/types'

const TEAL = '#00B89C'
const NAVY = '#1B3A6B'
const AMBER = '#f59e0b'
const INDIGO = '#6366f1'

const PIE_COLORS = [TEAL, NAVY, AMBER]

export default function AnalyticsPage() {
  const router = useRouter()

  useEffect(() => {
    if (!isAdmin()) { router.replace('/dashboard'); return }
  }, [router])

  const [summary, setSummary] = useState<AnalyticsSummary | null>(null)
  const [daily, setDaily] = useState<DailyCount[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.get<AnalyticsSummary>('/analytics/summary/'),
      api.get<DailyCount[]>('/analytics/daily/?days=30'),
    ])
      .then(([s, d]) => { setSummary(s.data); setDaily(d.data) })
      .catch(() => toast.error('Failed to load analytics.'))
      .finally(() => setLoading(false))
  }, [])

  // Language pie data
  const languagePie = summary ? [
    { name: 'English', value: summary.by_language.en },
    { name: 'French',  value: summary.by_language.fr },
    { name: 'Pidgin',  value: summary.by_language.pcm },
  ].filter((d) => d.value > 0) : []

  // Status bar data
  const statusBar = summary ? [
    { name: 'Completed',   value: summary.by_status.completed,   fill: TEAL },
    { name: 'In Progress', value: summary.by_status.in_progress, fill: AMBER },
    { name: 'Abandoned',   value: summary.by_status.abandoned,   fill: '#94a3b8' },
  ] : []

  // Format daily dates
  const dailyFormatted = daily.map((d) => ({
    ...d,
    date: new Date(d.date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' }),
  }))

  if (loading) {
    return (
      <div className="space-y-6 max-w-5xl">
        {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-64 w-full" />)}
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-5xl">

      {/* Summary numbers */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total Assessments', value: summary?.total_assessments, color: TEAL },
          { label: 'Total Patients',    value: summary?.total_patients,    color: NAVY },
          { label: 'Health Workers',    value: summary?.total_health_workers, color: INDIGO },
          { label: 'Urgent Cases',      value: summary?.total_urgent,      color: AMBER },
        ].map((s) => (
          <Card key={s.label}>
            <CardContent className="pt-5 pb-5">
              <p className="text-sm text-muted-foreground">{s.label}</p>
              <p className="text-3xl font-bold mt-1" style={{ color: s.color }}>{s.value ?? 0}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Daily trend */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Completed Assessments — Last 30 Days</CardTitle>
        </CardHeader>
        <CardContent>
          {dailyFormatted.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-10">No data yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={dailyFormatted} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke={TEAL} strokeWidth={2} dot={false} name="Assessments" />
              </LineChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Language breakdown */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Assessments by Language</CardTitle>
          </CardHeader>
          <CardContent>
            {languagePie.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-10">No data yet.</p>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={languagePie} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={false}>
                    {languagePie.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Status breakdown */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Assessments by Status</CardTitle>
          </CardHeader>
          <CardContent>
            {statusBar.every((s) => s.value === 0) ? (
              <p className="text-sm text-muted-foreground text-center py-10">No data yet.</p>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={statusBar} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]} name="Count">
                    {statusBar.map((s, i) => <Cell key={i} fill={s.fill} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Top health workers */}
      {summary?.top_health_workers && summary.top_health_workers.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Top Health Workers by Assessments</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart
                layout="vertical"
                data={summary.top_health_workers.map((w) => ({ name: w.name, count: w.assessment_count }))}
                margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                <XAxis type="number" tick={{ fontSize: 11 }} allowDecimals={false} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={120} />
                <Tooltip />
                <Bar dataKey="count" fill={NAVY} radius={[0, 4, 4, 0]} name="Assessments" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
