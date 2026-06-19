// ── Auth ──────────────────────────────────────────────────────────────────────

export interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  role: 'admin' | 'health_worker'
  phone_number: string
  facility_name: string
  date_joined: string
}

export interface AuthTokens {
  access: string
  refresh: string
  user: User
}

// ── Patients ──────────────────────────────────────────────────────────────────

export interface Patient {
  id: string
  first_name: string
  last_name: string
  full_name: string
  date_of_birth: string | null
  sex: 'male' | 'female' | 'other'
  phone_number: string
  location: string
  language_preference: 'en' | 'fr' | 'pcm'
  is_active: boolean
  created_at: string
}

// ── Assessment ────────────────────────────────────────────────────────────────

export type Language = 'en' | 'fr' | 'pcm'
export type AssessmentStatus = 'in_progress' | 'completed' | 'abandoned'
export type AssessmentPriority = 'NORMAL' | 'URGENT'

export interface AssessmentSession {
  id: string
  patient: Patient
  health_worker: User
  language: Language
  status: AssessmentStatus
  assessment_priority: AssessmentPriority
  assessment_report: string
  started_at: string
  completed_at: string | null
}

// ── Analytics ─────────────────────────────────────────────────────────────────

export interface AnalyticsSummary {
  total_assessments: number
  total_patients: number
  total_urgent: number
  completed_this_week: number
  by_language: { en: number; fr: number; pcm: number }
  by_status: { completed: number; in_progress: number; abandoned: number }
  total_health_workers: number | null
  top_health_workers: TopWorker[] | null
}

export interface TopWorker {
  id: string
  name: string
  email: string
  facility_name: string
  assessment_count: number
}

export interface DailyCount {
  date: string
  count: number
}

// ── Pagination ────────────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}
