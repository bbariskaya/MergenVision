import { AlertCircle, RefreshCcw } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ErrorStateProps {
  message?: string
  onRetry?: () => void
  testId?: string
}

export function ErrorState({ message = 'Bir hata oluştu.', onRetry, testId }: ErrorStateProps) {
  return (
    <div
      className="flex h-48 flex-col items-center justify-center rounded-lg border border-destructive/50 bg-card p-6 text-center"
      data-testid={testId}
    >
      <AlertCircle className="mb-2 h-8 w-8 text-destructive" />
      <p className="text-sm text-destructive">{message}</p>
      {onRetry && (
        <Button variant="outline" size="sm" className="mt-4 gap-2" onClick={onRetry}>
          <RefreshCcw className="h-4 w-4" />
          Tekrar Dene
        </Button>
      )}
    </div>
  )
}
