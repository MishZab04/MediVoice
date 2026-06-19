'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Plus } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import api from '@/lib/api'
import { AssessmentSession } from '@/types'

const LANGUAGE_LABELS: Record<string, string> = { en: 'English', fr: 'French', pcm: 'Pidgin' }

export default function AssessmentsPage() {
  const [sessions, setSessions] = useState<AssessmentSession[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<AssessmentSession[]>('/assessment/sessions/')
      .then((r) => setSessions(r.data))
      .catch(() => toast.error('Failed to load assessments.'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="space-y-5 max-w-6xl">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">{sessions.length} total sessions</p>
        <Button asChild style={{ backgroundColor: '#00B89C' }} className="text-white">
          <Link href="/assessment/new"><Plus className="h-4 w-4 mr-2" />New Assessment</Link>
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Patient</TableHead>
                <TableHead>Language</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Priority</TableHead>
                <TableHead>Date</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 6 }).map((_, j) => (
                      <TableCell key={j}><Skeleton className="h-5 w-full" /></TableCell>
                    ))}
                  </TableRow>
                ))
              ) : sessions.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-12 text-muted-foreground">
                    No assessments yet.{' '}
                    <Link href="/assessment/new" className="underline" style={{ color: '#00B89C' }}>Start one</Link>
                  </TableCell>
                </TableRow>
              ) : (
                sessions.map((s) => (
                  <TableRow key={s.id}>
                    <TableCell className="font-medium">
                      {s.patient.first_name} {s.patient.last_name}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs">{LANGUAGE_LABELS[s.language]}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline" className="text-xs capitalize"
                        style={s.status === 'completed' ? { borderColor: '#00B89C', color: '#00B89C' } : undefined}
                      >
                        {s.status.replace('_', ' ')}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {s.assessment_priority === 'URGENT'
                        ? <Badge variant="destructive" className="text-xs">Urgent</Badge>
                        : <span className="text-xs text-muted-foreground">Normal</span>}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {new Date(s.started_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button asChild variant="ghost" size="sm" className="text-xs">
                        <Link href={s.status === 'completed' ? `/assessment/${s.id}/report` : `/assessment/${s.id}`}>
                          {s.status === 'completed' ? 'View report' : 'Continue'}
                        </Link>
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
