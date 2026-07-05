import { PackageOpen } from 'lucide-react'
import type { ReactNode } from 'react'

interface EmptyStateProps {
  title?: string
  description?: string
  icon?: ReactNode
  testId?: string
}

export function EmptyState({
  title = 'Veri bulunamadı',
  description = 'Listelenecek öğe yok.',
  icon,
  testId,
}: EmptyStateProps) {
  return (
    <div
      className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border bg-card p-8 text-center"
      data-testid={testId}
    >
      {icon ?? <PackageOpen className="mb-2 h-8 w-8 text-muted-foreground" />}
      <h3 className="text-base font-medium">{title}</h3>
      <p className="mt-1 text-sm text-muted-foreground">{description}</p>
    </div>
  )
}
