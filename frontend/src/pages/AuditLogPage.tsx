import { useState } from 'react'
import { Search } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { DataTable } from '@/components/ui/DataTable'
import { PageHeader } from '@/components/ui/PageHeader'
import { Pagination } from '@/components/ui/Pagination'
import { LoadingState } from '@/components/ui/LoadingState'
import { ErrorState } from '@/components/ui/ErrorState'
import { MetadataTree } from '@/components/ui/MetadataTree'
import { useAudit } from '@/hooks/useAudit'
import { formatDateTime } from '@/lib/formatters'
import type { AuditLogEntry } from '@/api/types'
import type { DataTableColumn } from '@/components/ui/DataTable'

const LIMIT = 10

export function AuditLogPage() {
  const [entityType, setEntityType] = useState('')
  const [action, setAction] = useState('')
  const [entityId, setEntityId] = useState('')
  const [offset, setOffset] = useState(0)

  const { data, isLoading, isError, refetch } = useAudit({
    entityType: entityType || undefined,
    action: action || undefined,
    entityId: entityId || undefined,
    limit: LIMIT,
    offset,
  })

  const columns: DataTableColumn<AuditLogEntry>[] = [
    { key: 'createdAt', header: 'Zaman', cell: (r) => formatDateTime(r.createdAt) },
    { key: 'action', header: 'Aksiyon', cell: (r) => <span className="font-medium">{r.action}</span> },
    { key: 'entityType', header: 'Entity Type', cell: (r) => r.entityType },
    { key: 'entityId', header: 'Entity ID', cell: (r) => <span className="truncate font-mono text-xs">{r.entityId}</span> },
    { key: 'actor', header: 'Actor', cell: (r) => r.actor },
    { key: 'outcome', header: 'Outcome', cell: (r) => r.outcome },
    {
      key: 'metadata',
      header: 'Metadata',
      cell: (r) => <MetadataTree metadata={r.metadata} />,
    },
  ]

  return (
    <div className="space-y-6">
      <PageHeader title="Audit Log" subtitle="Sistemdeki işlem kayıtları" />

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Entity Type"
            value={entityType}
            onChange={(e) => setEntityType(e.target.value)}
            className="pl-9"
            data-testid="audit-entity-type-filter"
          />
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Aksiyon"
            value={action}
            onChange={(e) => setAction(e.target.value)}
            className="pl-9"
            data-testid="audit-action-filter"
          />
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Entity ID"
            value={entityId}
            onChange={(e) => setEntityId(e.target.value)}
            className="pl-9"
            data-testid="audit-entity-id-filter"
          />
        </div>
      </div>

      {isLoading ? (
        <LoadingState />
      ) : isError ? (
        <ErrorState message="Audit log yüklenemedi." onRetry={() => refetch()} />
      ) : (
        <DataTable
          columns={columns}
          data={data?.items ?? []}
          keyExtractor={(r) => r.auditId}
          testId="audit-log-table"
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
