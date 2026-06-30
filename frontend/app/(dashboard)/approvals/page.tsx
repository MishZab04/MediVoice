'use client'

import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { Clock, CheckCircle2, UserCheck } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import api from '@/lib/api'
import { isAdmin } from '@/lib/auth'
import { User, PaginatedResponse } from '@/types'

export default function ApprovalsPage() {
  const router = useRouter()

  useEffect(() => {
    if (!isAdmin()) { router.replace('/dashboard'); return }
  }, [router])

  const [pending, setPending] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [approving, setApproving] = useState<string | null>(null)

  const fetchPending = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get<PaginatedResponse<User>>('/auth/users/?approved=false')
      // filter client-side in case backend doesn't support the query param yet
      const unapproved = (data.results ?? []).filter((u) => !u.is_approved && u.is_active)
      setPending(unapproved)
    } catch {
      toast.error('Failed to load pending approvals.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchPending() }, [fetchPending])

  async function handleApprove(user: User) {
    setApproving(user.id)
    try {
      await api.post(`/auth/users/${user.id}/approve/`)
      toast.success(`${user.first_name} ${user.last_name} has been approved.`)
      fetchPending()
    } catch {
      toast.error('Failed to approve user.')
    } finally {
      setApproving(null)
    }
  }

  return (
    <div className="space-y-5 max-w-4xl">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold tracking-tight">Approvals</h2>
        <p className="text-sm text-muted-foreground mt-0.5">
          Review and approve health worker accounts that are waiting for access.
        </p>
      </div>

      {/* Empty state */}
      {!loading && pending.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 gap-3">
            <div className="h-14 w-14 rounded-full flex items-center justify-center" style={{ backgroundColor: '#00B89C20' }}>
              <CheckCircle2 className="h-7 w-7" style={{ color: '#00B89C' }} />
            </div>
            <p className="text-sm font-medium">All caught up!</p>
            <p className="text-xs text-muted-foreground">No health worker accounts are pending approval.</p>
          </CardContent>
        </Card>
      )}

      {/* Pending table */}
      {(loading || pending.length > 0) && (
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Facility</TableHead>
                  <TableHead>Registered</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  Array.from({ length: 3 }).map((_, i) => (
                    <TableRow key={i}>
                      {Array.from({ length: 6 }).map((_, j) => (
                        <TableCell key={j}><Skeleton className="h-5 w-full" /></TableCell>
                      ))}
                    </TableRow>
                  ))
                ) : (
                  pending.map((u) => (
                    <TableRow key={u.id}>
                      <TableCell className="font-medium">{u.first_name} {u.last_name}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">{u.email}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">{u.facility_name || '—'}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {new Date(u.date_joined).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <Badge className="text-xs text-white gap-1" style={{ backgroundColor: '#f59e0b' }}>
                          <Clock className="h-3 w-3" /> Pending
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          size="sm"
                          className="text-white gap-1.5"
                          style={{ backgroundColor: '#00B89C' }}
                          disabled={approving === u.id}
                          onClick={() => handleApprove(u)}
                        >
                          <UserCheck className="h-4 w-4" />
                          {approving === u.id ? 'Approving…' : 'Approve'}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
