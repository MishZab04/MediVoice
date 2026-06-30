'use client'

import { useState } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { toast } from 'sonner'
import { CheckCircle2, Clock } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import api from '@/lib/api'

export default function SignUpPage() {
  const [loading, setLoading] = useState(false)
  const [submitted, setSubmitted] = useState(false)
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
      await api.post('/auth/signup/', form)
      setSubmitted(true)
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
            <h1 className="text-2xl font-bold tracking-tight text-foreground">MediVoice</h1>
            <p className="text-xs text-muted-foreground mt-0.5">Your Voice. Better Healthcare.</p>
          </div>
        </div>

        {submitted ? (
          /* Pending approval state */
          <Card className="shadow-md border-0">
            <CardContent className="pt-8 pb-8 px-6 flex flex-col items-center text-center gap-4">
              <div className="h-14 w-14 rounded-full flex items-center justify-center" style={{ backgroundColor: '#00B89C20' }}>
                <Clock className="h-7 w-7" style={{ color: '#00B89C' }} />
              </div>
              <div className="space-y-1">
                <h2 className="text-lg font-semibold">Account submitted!</h2>
                <p className="text-sm text-muted-foreground">
                  Your account is pending admin approval. You will be able to log in once an administrator reviews and approves your registration.
                </p>
              </div>
              <div className="w-full pt-2 space-y-2 text-sm text-muted-foreground">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 shrink-0" style={{ color: '#00B89C' }} />
                  <span>Account created for <strong>{form.email}</strong></span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 shrink-0 text-amber-500" />
                  <span>Waiting for admin approval</span>
                </div>
              </div>
              <Link href="/login" className="w-full">
                <Button variant="outline" className="w-full mt-2">Back to login</Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          /* Registration form */
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
        )}
      </div>
    </div>
  )
}
