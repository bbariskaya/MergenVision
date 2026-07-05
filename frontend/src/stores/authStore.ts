import { create } from 'zustand'

const STORAGE_KEY = 'mv-token'

function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(STORAGE_KEY)
}

type AuthState = {
  token: string | null
  isAuthenticated: boolean
  login: (token: string) => void
  logout: () => void
}

const initialToken = getStoredToken()

export const useAuthStore = create<AuthState>((set) => ({
  token: initialToken,
  isAuthenticated: Boolean(initialToken),
  login: (token) => {
    localStorage.setItem(STORAGE_KEY, token)
    set({ token, isAuthenticated: true })
  },
  logout: () => {
    localStorage.removeItem(STORAGE_KEY)
    set({ token: null, isAuthenticated: false })
  },
}))
