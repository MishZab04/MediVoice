'use client'

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { toast } from 'sonner'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import api from '@/lib/api'
import { Patient, PaginatedResponse } from '@/types'

export default function NewAssessmentPage() {
  const router = useRouter()
  const params = useSearchParams()

  const [patients, setPatients] = useState<Patient[]>([])
  const [loading, setLoading] = useState(true)
  const [starting, setStarting] = useState(false)
  const [patientId, setPatientId] = useState(params.get('patient') ?? '')
  const [language, setLanguage] = useState('en')

  useEffect(() => {
    api.get<PaginatedResponse<Patient>>('/patients/?ordering=-created_at')
      .then((r) => {
        const active = r.data.results.filter((p) => p.is_active)
        setPatients(active)
        // If patient pre-selected from query param, set their language preference
        if (params.get('patient')) {
          const pre = active.find((p) => p.id === params.get('patient'))
          if (pre) setLanguage(pre.language_preference)
        }
      })
      .catch(() => toast.error('Failed to load patients.'))
      .finally(() => setLoading(false))
  }, [params])

  // Auto-fill language when patient changes
  function handlePatientChange(id: string) {
    setPatientId(id)
    const p = patients.find((x) => x.id === id)
    if (p) setLanguage(p.language_preference)
  }

  async function handleStart(e: React.FormEvent) {
    e.preventDefault()
    if (!patientId) { toast.error('Please select a patient.'); return }
    setStarting(true)
    try {
      const { data } = await api.post('/assessment/start/', {
        patient_id: patientId,
        language,
      })
      const audioParam = data.audio_url ? `?audio=${encodeURIComponent(data.audio_url)}` : ''
      router.push(`/assessment/${data.session_id}${audioParam}`)
    } catch {
      toast.error('Failed to start assessment.')
      setStarting(false)
    }
  }

  return (
    <div className="max-w-md mx-auto">
      <Card>
        <CardHeader>
          <CardTitle>Start New Assessment</CardTitle>
          <p className="text-sm text-muted-foreground">
            Select a patient and language to begin the AI-guided voice interview.
          </p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleStart} className="space-y-5">
            <div className="space-y-1.5">
              <Label>Patient</Label>
              {loading ? <Skeleton className="h-10 w-full" /> : (
                <Select value={patientId} onValueChange={handlePatientChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a patient…" />
                  </SelectTrigger>
                  <SelectContent>
                    {patients.length === 0 ? (
                      <SelectItem value="none" disabled>No active patients</SelectItem>
                    ) : (
                      patients.map((p) => (
                        <SelectItem key={p.id} value={p.id}>{p.full_name}</SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
              )}
            </div>

            <div className="space-y-1.5">
              <Label>Interview language</Label>
              <Select value={language} onValueChange={setLanguage}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="en">English</SelectItem>
                  <SelectItem value="fr">French</SelectItem>
                  <SelectItem value="pcm">Pidgin English</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                Auto-filled from patient&apos;s preferred language.
              </p>
            </div>

            <Button
              type="submit"
              className="w-full text-white font-semibold"
              style={{ backgroundColor: '#00B89C' }}
              disabled={starting || !patientId}
            >
              {starting ? 'Starting…' : 'Start Assessment'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
