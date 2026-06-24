'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import Image from 'next/image'
import { toast } from 'sonner'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import api from '@/lib/api'
import { saveTokens } from '@/lib/auth'
import { AuthTokens } from '@/types'

export default function SignUpPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    phone_number: '',
    facility_name: '',
  })

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await api.post<AuthTokens>('/auth/signup/', form)
      saveTokens(data.access, data.refresh, data.user)
      toast.success('Account created! Welcome to MediVoice.')
      router.push('/dashboard')
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { email?: string[] } } })
        ?.response?.data?.email?.[0] ?? 'Could not create account. Please try again.'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-muted/30 px-4 py-10">
      <div className="w-full max-w-sm space-y-6">

        {/* Brand */}
        <div className="flex flex-col items-center gap-3">
          <div className="rounded-2xl overflow-hidden shadow-sm ring-1 ring-black/5">
            <Image src="/medivoice_logo.png" alt="MediVoice" width={72} height={72} priority />
          </div>
          <div className="text-center">
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              MediVoice
            </h1>
            <p className="text-xs text-muted-foreground mt-0.5">Your Voice. Better Healthcare.</p>
          </div>
        </div>

        {/* Card */}
        <Card className="shadow-md border-0">
          <CardContent className="pt-6 pb-6 px-6 space-y-5">
            <div className="space-y-0.5">
              <h2 className="text-lg font-semibold tracking-tight">Create account</h2>
              <p className="text-sm text-muted-foreground">Register as a health worker</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label htmlFor="first_name">First name</Label>
                  <Input id="first_name" name="first_name" placeholder="John"
                    value={form.first_name} onChange={handleChange} required className="h-10" />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="last_name">Last name</Label>
                  <Input id="last_name" name="last_name" placeholder="Doe"
                    value={form.last_name} onChange={handleChange} required className="h-10" />
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="email">Email address</Label>
                <Input id="email" name="email" type="email" placeholder="you@example.com"
                  value={form.email} onChange={handleChange} required className="h-10" />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="password">Password</Label>
                <Input id="password" name="password" type="password" placeholder="Min. 8 characters"
                  value={form.password} onChange={handleChange} required minLength={8} className="h-10" />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="phone_number">Phone number <span className="text-muted-foreground">(optional)</span></Label>
                <Input id="phone_number" name="phone_number" placeholder="+237 6XX XXX XXX"
                  value={form.phone_number} onChange={handleChange} className="h-10" />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="facility_name">Health facility <span className="text-muted-foreground">(optional)</span></Label>
                <Input id="facility_name" name="facility_name" placeholder="e.g. Yaoundé Central Hospital"
                  value={form.facility_name} onChange={handleChange} className="h-10" />
              </div>

              <Button
                type="submit"
                className="w-full h-10 font-semibold text-white"
                style={{ backgroundColor: '#00B89C' }}
                disabled={loading}
              >
                {loading ? 'Creating account…' : 'Create account'}
              </Button>
            </form>

            <p className="text-sm text-center text-muted-foreground">
              Already have an account?{' '}
              <Link href="/login" className="font-medium hover:underline" style={{ color: '#00B89C' }}>
                Sign in
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
