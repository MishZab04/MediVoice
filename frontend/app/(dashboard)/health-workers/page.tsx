'use client'

import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { Plus, Search, MoreHorizontal } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import api from '@/lib/api'
import { isAdmin, getUser } from '@/lib/auth'
import { User, PaginatedResponse } from '@/types'

const EMPTY_FORM = { first_name: '', last_name: '', email: '', password: '', phone_number: '', facility_name: '' }

function StatusBadge({ worker }: { worker: User }) {
  if (!worker.is_active) {
    return <Badge variant="secondary" className="text-xs">Inactive</Badge>
  }
  if (!worker.is_approved) {
    return (
      <Badge className="text-xs text-white" style={{ backgroundColor: '#f59e0b' }}>
        Pending
      </Badge>
    )
  }
  return (
    <Badge className="text-xs text-white" style={{ backgroundColor: '#00B89C' }}>
      Active
    </Badge>
  )
}

export default function HealthWorkersPage() {
  const router = useRouter()

  useEffect(() => {
    if (!isAdmin()) { router.replace('/dashboard'); return }
  }, [router])

  const [workers, setWorkers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [open, setOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState(EMPTY_FORM)

  const fetchWorkers = useCallback(async (q = '') => {
    setLoading(true)
    try {
      const { data } = await api.get<PaginatedResponse<User>>(
        `/auth/users/${q ? `?search=${encodeURIComponent(q)}` : ''}`
      )
      setWorkers(data.results ?? [])
    } catch {
      toast.error('Failed to load health workers.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchWorkers() }, [fetchWorkers])
  useEffect(() => {
    const t = setTimeout(() => fetchWorkers(search), 400)
    return () => clearTimeout(t)
  }, [search, fetchWorkers])

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    setForm((p) => ({ ...p, [e.target.name]: e.target.value }))
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      await api.post('/auth/users/', form)
      toast.success('Health worker created.')
      setOpen(false)
      setForm(EMPTY_FORM)
      fetchWorkers(search)
    } catch {
      toast.error('Failed to create health worker.')
    } finally {
      setSaving(false)
    }
  }

  async function handleApprove(id: string) {
    try {
      await api.post(`/auth/users/${id}/approve/`)
      toast.success('User approved successfully.')
      fetchWorkers(search)
    } catch {
      toast.error('Failed to approve user.')
    }
  }

  async function handleDeactivate(id: string) {
    try {
      await api.delete(`/auth/users/${id}/`)
      toast.success('Account deactivated.')
      fetchWorkers(search)
    } catch {
      toast.error('Failed to deactivate.')
    }
  }

  const me = getUser()

  return (
    <div className="space-y-5 max-w-5xl">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="relative flex-1 min-w-48 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search workers…" value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
        </div>

        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button style={{ backgroundColor: '#00B89C' }} className="text-white">
              <Plus className="h-4 w-4 mr-2" /> Add Health Worker
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-md">
            <DialogHeader><DialogTitle>Add Health Worker</DialogTitle></DialogHeader>
            <form onSubmit={handleCreate} className="space-y-4 pt-2">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label>First name</Label>
                  <Input name="first_name" value={form.first_name} onChange={handleChange} required placeholder="John" />
                </div>
                <div className="space-y-1.5">
                  <Label>Last name</Label>
                  <Input name="last_name" value={form.last_name} onChange={handleChange} required placeholder="Doe" />
                </div>
              </div>
              <div className="space-y-1.5">
                <Label>Email</Label>
                <Input name="email" type="email" value={form.email} onChange={handleChange} required placeholder="worker@example.com" />
              </div>
              <div className="space-y-1.5">
                <Label>Password</Label>
                <Input name="password" type="password" value={form.password} onChange={handleChange} required minLength={8} placeholder="Min. 8 characters" />
              </div>
              <div className="space-y-1.5">
                <Label>Phone <span className="text-muted-foreground text-xs">(optional)</span></Label>
                <Input name="phone_number" value={form.phone_number} onChange={handleChange} placeholder="+237 6XX XXX XXX" />
              </div>
              <div className="space-y-1.5">
                <Label>Facility <span className="text-muted-foreground text-xs">(optional)</span></Label>
                <Input name="facility_name" value={form.facility_name} onChange={handleChange} placeholder="e.g. Bafoussam District Hospital" />
              </div>
              <div className="flex gap-2 pt-1">
                <Button type="button" variant="outline" className="flex-1" onClick={() => setOpen(false)}>Cancel</Button>
                <Button type="submit" className="flex-1 text-white" style={{ backgroundColor: '#00B89C' }} disabled={saving}>
                  {saving ? 'Creating…' : 'Create'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Facility</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                Array.from({ length: 4 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 5 }).map((_, j) => (
                      <TableCell key={j}><Skeleton className="h-5 w-full" /></TableCell>
                    ))}
                  </TableRow>
                ))
              ) : workers.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-12 text-muted-foreground">
                    No health workers found.
                  </TableCell>
                </TableRow>
              ) : (
                workers.map((w) => (
                  <TableRow key={w.id}>
                    <TableCell className="font-medium">{w.first_name} {w.last_name}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{w.email}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{w.facility_name || '—'}</TableCell>
                    <TableCell><StatusBadge worker={w} /></TableCell>
                    <TableCell className="text-right">
                      {w.id !== me?.id && (
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            {!w.is_approved && w.is_active && (
                              <DropdownMenuItem onClick={() => handleApprove(w.id)} style={{ color: '#00B89C' }}>
                                Approve account
                              </DropdownMenuItem>
                            )}
                            {w.is_active && (
                              <DropdownMenuItem className="text-destructive" onClick={() => handleDeactivate(w.id)}>
                                Deactivate account
                              </DropdownMenuItem>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      )}
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
