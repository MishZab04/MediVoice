'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import Image from 'next/image'
import { toast } from 'sonner'
import { Clock } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import api from '@/lib/api'
import { saveTokens } from '@/lib/auth'
import { AuthTokens } from '@/types'

type LoginError = { response?: { data?: { non_field_errors?: string[]; detail?: string } } }

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [pendingApproval, setPendingApproval] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setPendingApproval(false)
    setLoading(true)
    try {
      const { data } = await api.post<AuthTokens>('/auth/login/', { email, password })
      saveTokens(data.access, data.refresh, data.user)
      toast.success(`Welcome back, ${data.user.first_name}!`)
      router.push('/dashboard')
    } catch (err: unknown) {
      const errData = (err as LoginError)?.response?.data
      const msg = errData?.non_field_errors?.[0] ?? errData?.detail ?? ''
      if (msg.toLowerCase().includes('pending')) {
        setPendingApproval(true)
      } else {
        toast.error('Invalid email or password.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-muted/30 px-4">
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
              <h2 className="text-lg font-semibold tracking-tight">Sign in</h2>
              <p className="text-sm text-muted-foreground">Enter your credentials to continue</p>
            </div>

            {pendingApproval && (
              <div className="flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-3">
                <Clock className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium text-amber-900">Account pending approval</p>
                  <p className="text-amber-700 mt-0.5">Your account is awaiting admin approval. You will be able to sign in once approved.</p>
                </div>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="email">Email address</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoFocus
                  className="h-10"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="h-10"
                />
              </div>
              <Button
                type="submit"
                className="w-full h-10 font-semibold text-white"
                style={{ backgroundColor: '#00B89C' }}
                disabled={loading}
              >
                {loading ? 'Signing in…' : 'Sign in'}
              </Button>
            </form>

            <p className="text-sm text-center text-muted-foreground">
              Don&apos;t have an account?{' '}
              <Link href="/signup" className="font-medium hover:underline" style={{ color: '#00B89C' }}>
                Sign up
              </Link>
            </p>
          </CardContent>
        </Card>

        <p className="text-xs text-center text-muted-foreground">
          Admin accounts are managed by the system administrator.
        </p>
      </div>
    </div>
  )
}
