import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { DataTable } from '@/components/ui/DataTable'
import { PageHeader } from '@/components/ui/PageHeader'
import { Pagination } from '@/components/ui/Pagination'
import { ImagePreview } from '@/components/ui/ImagePreview'
import { LoadingState } from '@/components/ui/LoadingState'
import { ErrorState } from '@/components/ui/ErrorState'
import { useIdentificationRequests } from '@/hooks/useIdentificationRequests'
import { formatDateTime, formatScore } from '@/lib/formatters'
import { cn } from '@/lib/utils'
import type { IdentificationRequestSummary } from '@/api/types'
import type { DataTableColumn } from '@/components/ui/DataTable'

const LIMIT = 10

function DecisionBadge({ decision }: { decision: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        decision === 'matched' && 'bg-emerald-500/10 text-emerald-500',
        decision === 'possible_match' && 'bg-amber-500/10 text-amber-500',
        decision === 'no_match' && 'bg-destructive/10 text-destructive',
        decision === 'single_face' && 'bg-primary/10 text-primary',
        decision === 'multiple_faces' && 'bg-primary/10 text-primary',
        decision === 'no_face' && 'bg-muted text-muted-foreground'
      )}
      data-testid="request-decision-badge"
    >
      {decision}
    </span>
  )
}

export function IdentificationRequestsPage() {
  const navigate = useNavigate()
  const [offset, setOffset] = useState(0)
  const { data, isLoading, isError, refetch } = useIdentificationRequests({ limit: LIMIT, offset })

  const columns: DataTableColumn<IdentificationRequestSummary>[] = [
    {
      key: 'thumbnail',
      header: 'Görsel',
      cell: () => (
        <div className="h-10 w-10 overflow-hidden rounded-md bg-muted">
          <ImagePreview url="/media/query-images/placeholder.jpg" alt="Sorgu küçük resmi" className="h-10 w-10" />
        </div>
      ),
    },
    {
      key: 'date',
      header: 'Tarih',
      cell: (r) => formatDateTime(r.completedAt ?? r.createdAt),
    },
    {
      key: 'decision',
      header: 'Karar',
      cell: (r) => <DecisionBadge decision={r.decision} />,
    },
    {
      key: 'faces',
      header: 'Yüz Sayısı',
      cell: (r) => r.faceCount,
    },
    {
      key: 'topK',
      header: 'TopK',
      cell: (r) => r.topK,
    },
    {
      key: 'threshold',
      header: 'Eşik',
      cell: (r) => (r.threshold ? formatScore(r.threshold) : '-'),
    },
    {
      key: 'actions',
      header: '',
      cell: (r) => (
        <Button
          variant="ghost"
          size="icon"
          onClick={(e) => {
            e.stopPropagation()
            navigate(`/identification-requests/${r.requestId}`)
          }}
          aria-label="Detay"
        >
          <Eye className="h-4 w-4" />
        </Button>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <PageHeader title="Tanıma İstekleri" subtitle="Geçmiş tanıma istekleri ve sonuçları" />

      {isLoading ? (
        <LoadingState />
      ) : isError ? (
        <ErrorState message="İstekler yüklenemedi." onRetry={() => refetch()} />
      ) : (
        <DataTable
          columns={columns}
          data={data?.items ?? []}
          keyExtractor={(r) => r.requestId}
          onRowClick={(r) => navigate(`/identification-requests/${r.requestId}`)}
          testId="identification-requests-table"
          footer={
            <Pagination
              offset={data?.offset ?? 0}
              limit={data?.limit ?? LIMIT}
              total={data?.total ?? 0}
              onPageChange={setOffset}
            />
          }
        />
      )}
    </div>
  )
}
