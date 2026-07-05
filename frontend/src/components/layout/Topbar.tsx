import { useNavigate } from 'react-router-dom'
import { LogOut } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/stores/authStore'
import { MobileSidebar } from './MobileSidebar'
import { ThemeToggle } from './ThemeToggle'

export function Topbar() {
  const logout = useAuthStore((state) => state.logout)
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border bg-card px-4 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="md:hidden">
          <MobileSidebar />
        </div>
        <span className="text-base font-semibold tracking-tight">
          INTERPROBE MergenVision
        </span>
      </div>

      <div className="flex items-center gap-2">
        <ThemeToggle />
        <span className="hidden text-sm text-muted-foreground sm:inline">
          Operator
        </span>
        <Button
          variant="ghost"
          size="icon"
          onClick={handleLogout}
          aria-label="Logout"
          data-testid="logout-button"
        >
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </header>
  )
}
