import { Loader2 } from 'lucide-react'

interface LoadingStateProps {
  message?: string
  testId?: string
}

export function LoadingState({ message = 'Yükleniyor...', testId }: LoadingStateProps) {
  return (
    <div
      className="flex h-48 flex-col items-center justify-center rounded-lg border border-border bg-card text-muted-foreground"
      data-testid={testId}
    >
      <Loader2 className="mb-2 h-8 w-8 animate-spin" />
      <p className="text-sm">{message}</p>
    </div>
  )
}
