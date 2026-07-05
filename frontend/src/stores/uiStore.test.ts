import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { useUIStore } from './uiStore'

describe('uiStore', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.classList.remove('light')
    useUIStore.setState({ sidebarOpen: true, theme: 'dark' })
  })

  afterEach(() => {
    document.documentElement.classList.remove('light')
  })

  it('defaults to dark theme and open sidebar', () => {
    const state = useUIStore.getState()
    expect(state.theme).toBe('dark')
    expect(state.sidebarOpen).toBe(true)
  })

  it('toggles theme and updates the html class', () => {
    useUIStore.getState().toggleTheme()

    const state = useUIStore.getState()
    expect(state.theme).toBe('light')
    expect(document.documentElement.classList.contains('light')).toBe(true)

    useUIStore.getState().toggleTheme()

    expect(useUIStore.getState().theme).toBe('dark')
    expect(document.documentElement.classList.contains('light')).toBe(false)
  })

  it('toggles sidebar open state', () => {
    useUIStore.getState().toggleSidebar()
    expect(useUIStore.getState().sidebarOpen).toBe(false)

    useUIStore.getState().toggleSidebar()
    expect(useUIStore.getState().sidebarOpen).toBe(true)
  })

  it('persists theme preference', () => {
    useUIStore.getState().toggleTheme()
    expect(localStorage.getItem('mv-theme')).toContain('light')
  })
})
