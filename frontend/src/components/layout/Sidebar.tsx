import { NavLink } from 'react-router-dom'
import {
  Activity,
  ClipboardList,
  FileText,
  LayoutDashboard,
  Scan,
  Users,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/people', label: 'People', icon: Users },
  { to: '/identify', label: 'Identify', icon: Scan },
  {
    to: '/identification-requests',
    label: 'Identification Requests',
    icon: ClipboardList,
  },
  { to: '/audit', label: 'Audit Log', icon: FileText },
  { to: '/health', label: 'System Health', icon: Activity },
]

export function Sidebar() {
  return (
    <nav className="flex h-full flex-col gap-2 p-4">
      <div className="mb-6 px-2 text-lg font-semibold tracking-tight">
        MergenVision
      </div>
      {navItems.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.to === '/'}
          className={({ isActive }) =>
            cn(
              'relative flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background',
              isActive
                ? 'bg-primary text-primary-foreground before:absolute before:left-0 before:top-1/2 before:h-6 before:w-1 before:-translate-y-1/2 before:rounded-r-full before:bg-primary-foreground'
                : 'text-muted-foreground hover:bg-muted hover:text-foreground'
            )
          }
        >
          <item.icon className="h-4 w-4" />
          {item.label}
        </NavLink>
      ))}
    </nav>
  )
}
