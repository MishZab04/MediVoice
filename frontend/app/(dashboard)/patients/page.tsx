'use client'

import { useEffect, useState, useCallback } from 'react'
import Link from 'next/link'
import { Plus, Search, Mic2, MoreHorizontal } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger,
} from '@/components/ui/dialog'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table'
import { Card, CardContent } from '@/components/ui/card'
import api from '@/lib/api'
import { Patient, PaginatedResponse } from '@/types'

const LANGUAGE_LABELS: Record<string, string> = { en: 'English', fr: 'French', pcm: 'Pidgin' }
const SEX_LABELS: Record<string, string> = { male: 'Male', female: 'Female', other: 'Other' }

const EMPTY_FORM = {
  first_name: '', last_name: '', date_of_birth: '',
  sex: 'male', phone_number: '', location: '', language_preference: 'en',
}

export default function PatientsPage() {
  const [patients, setPatients] = useState<Patient[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [open, setOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState(EMPTY_FORM)

  const fetchPatients = useCallback(async (q = '') => {
    setLoading(true)
    try {
      const { data } = await api.get<PaginatedResponse<Patient>>(
        `/patients/${q ? `?search=${encodeURIComponent(q)}` : ''}`
      )
      setPatients(data.results ?? [])
    } catch {
      toast.error('Failed to load patients.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchPatients() }, [fetchPatients])

  // Debounced search
  useEffect(() => {
    const t = setTimeout(() => fetchPatients(search), 400)
    return () => clearTimeout(t)
  }, [search, fetchPatients])

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    setForm((p) => ({ ...p, [e.target.name]: e.target.value }))
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      await api.post('/patients/', form)
      toast.success('Patient added successfully.')
      setOpen(false)
      setForm(EMPTY_FORM)
      fetchPatients(search)
    } catch {
      toast.error('Failed to add patient.')
    } finally {
      setSaving(false)
    }
  }

  async function handleDeactivate(id: string) {
    try {
      await api.delete(`/patients/${id}/`)
      toast.success('Patient deactivated.')
      fetchPatients(search)
    } catch {
      toast.error('Failed to deactivate patient.')
    }
  }

  return (
    <div className="space-y-5 max-w-6xl">
      {/* Header */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="relative flex-1 min-w-48 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search patients…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>

        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button style={{ backgroundColor: '#00B89C' }} className="text-white">
              <Plus className="h-4 w-4 mr-2" /> Add Patient
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Add New Patient</DialogTitle>
            </DialogHeader>
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

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label>Date of birth</Label>
                  <Input name="date_of_birth" type="date" value={form.date_of_birth} onChange={handleChange} />
                </div>
                <div className="space-y-1.5">
                  <Label>Sex</Label>
                  <Select value={form.sex} onValueChange={(v) => setForm((p) => ({ ...p, sex: v }))}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="male">Male</SelectItem>
                      <SelectItem value="female">Female</SelectItem>
                      <SelectItem value="other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-1.5">
                <Label>Phone number <span className="text-muted-foreground text-xs">(optional)</span></Label>
                <Input name="phone_number" value={form.phone_number} onChange={handleChange} placeholder="+237 6XX XXX XXX" />
              </div>

              <div className="space-y-1.5">
                <Label>Location <span className="text-muted-foreground text-xs">(village/town)</span></Label>
                <Input name="location" value={form.location} onChange={handleChange} placeholder="e.g. Bafoussam" />
              </div>

              <div className="space-y-1.5">
                <Label>Preferred language</Label>
                <Select value={form.language_preference} onValueChange={(v) => setForm((p) => ({ ...p, language_preference: v }))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="en">English</SelectItem>
                    <SelectItem value="fr">French</SelectItem>
                    <SelectItem value="pcm">Pidgin English</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex gap-2 pt-1">
                <Button type="button" variant="outline" className="flex-1" onClick={() => setOpen(false)}>Cancel</Button>
                <Button type="submit" className="flex-1 text-white" style={{ backgroundColor: '#00B89C' }} disabled={saving}>
                  {saving ? 'Adding…' : 'Add Patient'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Sex</TableHead>
                <TableHead>Location</TableHead>
                <TableHead>Language</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
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
              ) : patients.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-12 text-muted-foreground">
                    {search ? 'No patients match your search.' : 'No patients yet. Add your first patient.'}
                  </TableCell>
                </TableRow>
              ) : (
                patients.map((p) => (
                  <TableRow key={p.id}>
                    <TableCell>
                      <Link href={`/patients/${p.id}`} className="font-medium hover:underline" style={{ color: '#00B89C' }}>
                        {p.full_name}
                      </Link>
                      {p.phone_number && (
                        <p className="text-xs text-muted-foreground">{p.phone_number}</p>
                      )}
                    </TableCell>
                    <TableCell className="text-sm">{SEX_LABELS[p.sex]}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{p.location || '—'}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs">{LANGUAGE_LABELS[p.language_preference]}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={p.is_active ? 'default' : 'secondary'}
                        className="text-xs"
                        style={p.is_active ? { backgroundColor: '#00B89C', color: '#fff' } : undefined}
                      >
                        {p.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem asChild>
                            <Link href={`/patients/${p.id}`}>View details</Link>
                          </DropdownMenuItem>
                          <DropdownMenuItem asChild>
                            <Link href={`/assessment/new?patient=${p.id}`}>
                              <Mic2 className="h-4 w-4 mr-2" /> Start assessment
                            </Link>
                          </DropdownMenuItem>
                          {p.is_active && (
                            <DropdownMenuItem
                              className="text-destructive"
                              onClick={() => handleDeactivate(p.id)}
                            >
                              Deactivate
                            </DropdownMenuItem>
                          )}
                        </DropdownMenuContent>
                      </DropdownMenu>
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
