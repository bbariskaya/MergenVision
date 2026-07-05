import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ChevronLeft, ChevronRight } from 'lucide-react'

interface PaginationProps {
  offset: number
  limit: number
  total: number
  onPageChange: (offset: number) => void
  testId?: string
}

export function Pagination({ offset, limit, total, onPageChange, testId }: PaginationProps) {
  const currentPage = Math.floor(offset / limit) + 1
  const totalPages = Math.max(1, Math.ceil(total / limit))
  const canGoPrevious = offset > 0
  const canGoNext = offset + limit < total

  const handleInputChange = (value: string) => {
    const page = Number(value)
    if (Number.isNaN(page)) return
    const clamped = Math.min(Math.max(1, page), totalPages)
    onPageChange((clamped - 1) * limit)
  }

  return (
    <div className="flex items-center justify-between gap-4" data-testid={testId}>
      <div className="text-sm text-muted-foreground">
        {total} kayıttan {offset + 1}-{Math.min(offset + limit, total)} arası
      </div>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="icon"
          onClick={() => onPageChange(Math.max(0, offset - limit))}
          disabled={!canGoPrevious}
          aria-label="Önceki sayfa"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Sayfa</span>
          <Input
            type="number"
            min={1}
            max={totalPages}
            value={currentPage}
            onChange={(e) => handleInputChange(e.target.value)}
            className="h-9 w-16 text-center"
            aria-label="Sayfa numarası"
          />
          <span className="text-sm text-muted-foreground">/ {totalPages}</span>
        </div>
        <Button
          variant="outline"
          size="icon"
          onClick={() => onPageChange(offset + limit)}
          disabled={!canGoNext}
          aria-label="Sonraki sayfa"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
