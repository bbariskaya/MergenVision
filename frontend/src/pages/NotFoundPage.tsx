import { Home } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <div className="flex min-h-[calc(100vh-8rem)] flex-col items-center justify-center rounded-lg border border-border bg-card p-6 text-center">
      <h1 className="text-6xl font-bold text-primary">404</h1>
      <p className="mt-4 text-xl font-semibold">Sayfa bulunamadı</p>
      <p className="mt-2 max-w-sm text-sm text-muted-foreground">
        Aradığınız sayfa mevcut değil veya taşınmış olabilir.
      </p>
      <Button asChild className="mt-6 gap-2">
        <Link to="/">
          <Home className="h-4 w-4" />
          Dashboard'a Dön
        </Link>
      </Button>
    </div>
  )
}
