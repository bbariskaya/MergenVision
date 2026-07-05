import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type Theme = 'dark' | 'light'

type UIState = {
  sidebarOpen: boolean
  theme: Theme
  toggleTheme: () => void
  setSidebarOpen: (open: boolean) => void
  toggleSidebar: () => void
}

function applyThemeClass(theme: Theme) {
  if (typeof document !== 'undefined') {
    document.documentElement.classList.toggle('light', theme === 'light')
  }
}

export const useUIStore = create<UIState>()(
  persist(
    (set, get) => ({
      sidebarOpen: true,
      theme: 'dark',
      toggleTheme: () => {
        const next = get().theme === 'dark' ? 'light' : 'dark'
        set({ theme: next })
        applyThemeClass(next)
      },
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      toggleSidebar: () => set({ sidebarOpen: !get().sidebarOpen }),
    }),
    {
      name: 'mv-theme',
      partialize: (state) => ({ theme: state.theme }),
      onRehydrateStorage: () => (state) => {
        if (state) applyThemeClass(state.theme)
      },
    }
  )
)
