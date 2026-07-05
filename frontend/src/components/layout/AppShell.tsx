import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'

export function AppShell() {
  return (
    <div className="min-h-screen bg-background">
      <Topbar />

      <aside className="fixed bottom-0 left-0 top-16 hidden w-[260px] border-r border-border bg-card md:block">
        <Sidebar />
      </aside>

      <main className="min-h-[calc(100vh-4rem)] bg-background p-6 md:ml-[260px]">
        <div className="mx-auto max-w-7xl">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
