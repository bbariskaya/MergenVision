import { beforeEach, describe, expect, it } from 'vitest'
import { useAuthStore } from './authStore'

describe('authStore', () => {
  beforeEach(() => {
    localStorage.clear()
    useAuthStore.setState({ token: null, isAuthenticated: false })
  })

  it('starts unauthenticated without a token', () => {
    const state = useAuthStore.getState()
    expect(state.token).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })

  it('logs in and persists the token', () => {
    useAuthStore.getState().login('admin-token')

    const state = useAuthStore.getState()
    expect(state.token).toBe('admin-token')
    expect(state.isAuthenticated).toBe(true)
    expect(localStorage.getItem('mv-token')).toBe('admin-token')
  })

  it('logs out and removes the token', () => {
    useAuthStore.getState().login('admin-token')
    useAuthStore.getState().logout()

    const state = useAuthStore.getState()
    expect(state.token).toBeNull()
    expect(state.isAuthenticated).toBe(false)
    expect(localStorage.getItem('mv-token')).toBeNull()
  })
})
