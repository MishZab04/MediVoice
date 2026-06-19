import { User } from '@/types'

export function getAccessToken(): string | null {
  return localStorage.getItem('access_token')
}

export function getUser(): User | null {
  const raw = localStorage.getItem('user')
  if (!raw) return null
  try { return JSON.parse(raw) } catch { return null }
}

export function saveTokens(access: string, refresh: string, user: User) {
  localStorage.setItem('access_token', access)
  localStorage.setItem('refresh_token', refresh)
  localStorage.setItem('user', JSON.stringify(user))
}

export function clearTokens() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('user')
}

export function isAuthenticated(): boolean {
  return !!getAccessToken()
}

export function isAdmin(): boolean {
  return getUser()?.role === 'admin'
}
