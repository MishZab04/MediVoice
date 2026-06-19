'use client'

import { useState } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import api from '@/lib/api'
import { getUser, saveTokens } from '@/lib/auth'

export default function ProfilePage() {
  const user = getUser()
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({
    first_name: user?.first_name ?? '',
    last_name: user?.last_name ?? '',
    phone_number: user?.phone_number ?? '',
    facility_name: user?.facility_name ?? '',
  })

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    setForm((p) => ({ ...p, [e.target.name]: e.target.value }))
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      const { data } = await api.patch('/auth/me/', form)
      // Update stored user
      const access = localStorage.getItem('access_token') ?? ''
      const refresh = localStorage.getItem('refresh_token') ?? ''
      saveTokens(access, refresh, data)
      toast.success('Profile updated.')
    } catch {
      toast.error('Failed to update profile.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-lg space-y-6">
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle>My Profile</CardTitle>
            <Badge
              className="text-white capitalize"
              style={{ backgroundColor: user?.role === 'admin' ? '#1B3A6B' : '#00B89C' }}
            >
              {user?.role?.replace('_', ' ')}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">{user?.email}</p>
        </CardHeader>
        <Separator />
        <CardContent className="pt-5">
          <form onSubmit={handleSave} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>First name</Label>
                <Input name="first_name" value={form.first_name} onChange={handleChange} required />
              </div>
              <div className="space-y-1.5">
                <Label>Last name</Label>
                <Input name="last_name" value={form.last_name} onChange={handleChange} required />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>Phone number</Label>
              <Input name="phone_number" value={form.phone_number} onChange={handleChange} placeholder="+237 6XX XXX XXX" />
            </div>
            <div className="space-y-1.5">
              <Label>Health facility</Label>
              <Input name="facility_name" value={form.facility_name} onChange={handleChange} placeholder="e.g. Yaoundé Central Hospital" />
            </div>
            <Button type="submit" className="w-full text-white" style={{ backgroundColor: '#00B89C' }} disabled={saving}>
              {saving ? 'Saving…' : 'Save changes'}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-5 space-y-2">
          <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide">Account info</p>
          <div className="text-sm space-y-1">
            <p><span className="text-muted-foreground">Email: </span>{user?.email}</p>
            <p><span className="text-muted-foreground">Role: </span><span className="capitalize">{user?.role?.replace('_', ' ')}</span></p>
            <p><span className="text-muted-foreground">Member since: </span>
              {user?.date_joined ? new Date(user.date_joined).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' }) : '—'}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
