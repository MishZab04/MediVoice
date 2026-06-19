'use client'

import { Suspense, useEffect, useRef, useState, useCallback } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import { Mic, MicOff, Volume2, Loader2, CheckCircle } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import api from '@/lib/api'

const LANGUAGE_LABELS: Record<string, string> = { en: 'English', fr: 'French', pcm: 'Pidgin' }
const API_BASE = process.env.NEXT_PUBLIC_API_URL?.replace('/api/v1', '') || 'http://127.0.0.1:8000'

type Phase = 'loading' | 'playing' | 'idle' | 'recording' | 'transcribing' | 'thinking' | 'done'

interface SessionState {
  sessionId: string
  patientName: string
  language: string
  turn: number
  questionText: string
  audioUrl: string | null
  status: 'in_progress' | 'completed'
}

function AssessmentPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const searchParams = useSearchParams()

  const [session, setSession] = useState<SessionState | null>(null)
  const [phase, setPhase] = useState<Phase>('loading')
  const [transcript, setTranscript] = useState('')

  const audioRef = useRef<HTMLAudioElement | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const streamRef = useRef<MediaStream | null>(null)

  // Load session detail to restore in-progress session
  const loadSession = useCallback(async () => {
    try {
      const { data } = await api.get(`/assessment/sessions/${id}/`)
      if (data.status === 'completed') {
        router.replace(`/assessment/${id}/report`)
        return
      }
      const turn = data.responses?.length ?? 0
      // Audio URL: prefer query param (fresh start), else derive from known filename pattern
      const paramAudio = searchParams.get('audio')
      const derivedAudio = `${API_BASE}/media/tts/dynamic_${id}_${turn}.mp3`
      const audioUrl = paramAudio ? decodeURIComponent(paramAudio) : derivedAudio

      setSession({
        sessionId: id,
        patientName: `${data.patient.first_name} ${data.patient.last_name}`,
        language: data.language,
        turn,
        questionText: data.current_question,
        audioUrl,
        status: data.status,
      })
      // Auto-play the current question
      playAudioOnLoad(audioUrl)
    } catch {
      toast.error('Failed to load session.')
    }
  }, [id, router, searchParams]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { loadSession() }, [loadSession])

  function stopAudio() {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.src = ''
      audioRef.current = null
    }
  }

  function playAudioOnLoad(url: string | null) {
    if (!url) { setPhase('idle'); return }
    const fullUrl = url.startsWith('http') ? url : `${API_BASE}${url}`
    const audio = new Audio(fullUrl)
    audioRef.current = audio
    // Set handlers before play() to avoid race conditions
    audio.onended = () => setPhase('idle')
    audio.onerror = () => setPhase('idle')
    setPhase('playing')
    audio.play().catch(() => setPhase('idle'))
  }

  function playAudio(url: string | null) {
    if (!url) { setPhase('idle'); return }
    const fullUrl = url.startsWith('http') ? url : `${API_BASE}${url}`
    const audio = new Audio(fullUrl)
    audioRef.current = audio
    audio.onended = () => setPhase('idle')
    audio.onerror = () => setPhase('idle')
    setPhase('playing')
    audio.play().catch(() => setPhase('idle'))
  }

  // Start recording — also stops any playing audio so the user doesn't have to wait
  async function startRecording() {
    stopAudio()
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      // Use timeslice so data is collected every 250ms, not only on stop
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm'
      const recorder = new MediaRecorder(stream, { mimeType })
      mediaRecorderRef.current = recorder
      chunksRef.current = []

      recorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data) }
      recorder.start(250)
      setPhase('recording')
      setTranscript('')
    } catch {
      toast.error('Microphone access denied. Please allow microphone in your browser settings.')
      setPhase('idle')
    }
  }

  // Stop recording and submit
  async function stopRecording() {
    const recorder = mediaRecorderRef.current
    if (!recorder || recorder.state === 'inactive') return
    setPhase('transcribing')

    recorder.onstop = async () => {
      // Stop mic stream
      streamRef.current?.getTracks().forEach((t) => t.stop())

      const blob = new Blob(chunksRef.current, { type: 'audio/webm' })

      if (blob.size === 0) {
        toast.error('No audio captured. Please try recording again.')
        setPhase('idle')
        return
      }

      const formData = new FormData()
      formData.append('audio', blob, 'answer.webm')
      formData.append('language', session?.language ?? 'en')

      // Step 1: Transcribe audio
      let text = ''
      try {
        const { data: sttData } = await api.post<{ text: string }>('/voice/transcribe/', formData)
        text = sttData.text.trim()
      } catch (err: unknown) {
        const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
        toast.error(detail ? `Transcription failed: ${detail}` : 'Transcription failed — check microphone or server logs.')
        setPhase('idle')
        return
      }

      if (!text) {
        toast.error('No speech detected. Please speak clearly and try again.')
        setPhase('idle')
        return
      }

      setTranscript(text)
      setPhase('thinking')

      // Step 2: Submit answer to AI engine
      try {
        const { data: respondData } = await api.post('/assessment/respond/', {
          session_id: session?.sessionId,
          answer_text: text,
        })

        if (respondData.status === 'completed') {
          setPhase('done')
          if (respondData.completion_audio_url) {
            playAudio(respondData.completion_audio_url)
            setTimeout(() => router.push(`/assessment/${id}/report`), 6000)
          } else {
            setTimeout(() => router.push(`/assessment/${id}/report`), 2000)
          }
          return
        }

        // Continue interview
        setSession((prev) => prev ? {
          ...prev,
          turn: respondData.turn,
          questionText: respondData.question_text,
          audioUrl: respondData.audio_url,
        } : prev)

        playAudio(respondData.audio_url)

      } catch (err: unknown) {
        const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
        toast.error(detail ? `Assessment error: ${detail}` : 'Failed to submit answer — please try again.')
        setPhase('idle')
      }
    }

    recorder.stop()
  }

  if (!session) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="max-w-xl mx-auto space-y-4">
      {/* Session info */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <p className="font-semibold text-lg">{session.patientName}</p>
          <p className="text-sm text-muted-foreground">Turn {session.turn + 1}</p>
        </div>
        <Badge variant="outline">{LANGUAGE_LABELS[session.language]}</Badge>
      </div>

      {/* Question card */}
      <Card className="border-2" style={{ borderColor: '#00B89C22' }}>
        <CardContent className="pt-6 pb-6 space-y-6">
          {/* Question text */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Volume2 className="h-4 w-4 shrink-0" style={{ color: '#00B89C' }} />
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Question</span>
              {phase === 'playing' && (
                <span className="flex gap-0.5 ml-1">
                  {[1,2,3].map((i) => (
                    <span key={i} className="w-1 rounded-full animate-bounce bg-teal-500"
                      style={{ height: `${8 + i * 3}px`, animationDelay: `${i * 0.1}s` }} />
                  ))}
                </span>
              )}
            </div>
            <p className="text-lg font-medium leading-relaxed">{session.questionText}</p>
          </div>

          {/* Replay button */}
          {phase === 'idle' && session.audioUrl && (
            <Button variant="outline" size="sm" onClick={() => playAudio(session.audioUrl)}
              className="gap-2 text-xs">
              <Volume2 className="h-3.5 w-3.5" /> Replay question
            </Button>
          )}

          {/* Transcript preview */}
          {transcript && (
            <div className="rounded-lg bg-muted px-4 py-3 text-sm text-muted-foreground">
              <span className="font-medium text-foreground">Heard: </span>{transcript}
            </div>
          )}

          {/* Done state */}
          {phase === 'done' && (
            <div className="flex flex-col items-center gap-3 py-4">
              <CheckCircle className="h-10 w-10" style={{ color: '#00B89C' }} />
              <p className="font-medium text-center">Assessment complete! Generating report…</p>
            </div>
          )}

          {/* Record button */}
          {phase !== 'done' && (
            <div className="flex flex-col items-center gap-3 pt-2">
              <button
                onClick={phase === 'recording' ? stopRecording : startRecording}
                disabled={phase === 'transcribing' || phase === 'thinking' || phase === 'loading'}
                className="relative w-20 h-20 rounded-full flex items-center justify-center transition-all focus:outline-none disabled:opacity-40"
                style={{
                  backgroundColor: phase === 'recording' ? '#ef4444' : '#00B89C',
                  boxShadow: phase === 'recording'
                    ? '0 0 0 12px rgba(239,68,68,0.2), 0 0 0 24px rgba(239,68,68,0.08)'
                    : '0 0 0 12px rgba(0,184,156,0.15)',
                }}
              >
                {(phase === 'transcribing' || phase === 'thinking') ? (
                  <Loader2 className="h-7 w-7 text-white animate-spin" />
                ) : phase === 'recording' ? (
                  <MicOff className="h-7 w-7 text-white" />
                ) : (
                  <Mic className="h-7 w-7 text-white" />
                )}
              </button>
              <p className="text-sm text-muted-foreground text-center">
                {phase === 'playing'      && 'Audio playing — tap mic to record now'}
                {phase === 'idle'         && "Tap the mic to record the patient's answer"}
                {phase === 'recording'    && 'Recording… tap again when done'}
                {phase === 'transcribing' && 'Converting speech to text… (first run may take ~30s)'}
                {phase === 'thinking'     && 'AI is generating next question…'}
                {phase === 'loading'      && 'Loading session…'}
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default function AssessmentPageWrapper() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center h-64"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" /></div>}>
      <AssessmentPage />
    </Suspense>
  )
}
