import { Activity, Database, HardDrive, RefreshCcw, Server } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { PageHeader } from '@/components/ui/PageHeader'
import { LoadingState } from '@/components/ui/LoadingState'
import { ErrorState } from '@/components/ui/ErrorState'
import { useHealth, useReady } from '@/hooks/useHealth'
import { cn } from '@/lib/utils'
import type { LucideIcon } from 'lucide-react'

interface DependencyCardProps {
  name: string
  status: string
  icon: LucideIcon
}

function DependencyCard({ name, status, icon: Icon }: DependencyCardProps) {
  const isOk = status === 'ok'
  return (
    <Card className="border-border bg-card">
      <CardContent className="flex items-center gap-4 p-6">
        <div
          className={cn(
            'flex h-12 w-12 shrink-0 items-center justify-center rounded-full',
            isOk ? 'bg-emerald-500/10' : 'bg-destructive/10'
          )}
        >
          <Icon className={cn('h-6 w-6', isOk ? 'text-emerald-500' : 'text-destructive')} />
        </div>
        <div>
          <p className="font-medium">{name}</p>
          <p className={cn('text-sm', isOk ? 'text-emerald-500' : 'text-destructive')}>{status}</p>
        </div>
      </CardContent>
    </Card>
  )
}

export function SystemHealthPage() {
  const health = useHealth()
  const ready = useReady()

  const handleRefresh = () => {
    health.refetch()
    ready.refetch()
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Sistem Sağlığı"
        subtitle="Bağımlılık ve runtime durumu"
        actions={
          <Button variant="outline" className="gap-2" onClick={handleRefresh}>
            <RefreshCcw className="h-4 w-4" />
            Yenile
          </Button>
        }
      />

      <Card className="border-border bg-card">
        <CardContent className="flex items-center justify-between p-6">
          <div className="flex items-center gap-4">
            <Activity
              className={cn(
                'h-8 w-8',
                health.data?.status === 'ok' ? 'text-emerald-500' : 'text-destructive'
              )}
            />
            <div>
              <p className="font-medium">/health Durumu</p>
              <p
                className={cn(
                  'text-sm',
                  health.data?.status === 'ok' ? 'text-emerald-500' : 'text-destructive'
                )}
              >
                {health.data?.status ?? 'Bilinmiyor'}
              </p>
            </div>
          </div>
          <div
            className={cn(
              'rounded-full px-3 py-1 text-sm font-medium',
              health.data?.status === 'ok'
                ? 'bg-emerald-500/10 text-emerald-500'
                : 'bg-destructive/10 text-destructive'
            )}
            data-testid="health-status-badge"
          >
            {health.data?.status === 'ok' ? 'Canlı' : 'Sorunlu'}
          </div>
        </CardContent>
      </Card>

      {ready.isLoading ? (
        <LoadingState />
      ) : ready.isError ? (
        <ErrorState message="Bağımlılık durumu yüklenemedi." onRetry={() => ready.refetch()} />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <DependencyCard
            name="PostgreSQL"
            status={ready.data?.dependencies.postgresql ?? 'unknown'}
            icon={Database}
          />
          <DependencyCard
            name="Qdrant"
            status={ready.data?.dependencies.qdrant ?? 'unknown'}
            icon={Server}
          />
          <DependencyCard
            name="MinIO"
            status={ready.data?.dependencies.minio ?? 'unknown'}
            icon={HardDrive}
          />
          <DependencyCard
            name="TensorRT Runtime"
            status={ready.data?.dependencies.tensorrtRuntime ?? 'unknown'}
            icon={Activity}
          />
        </div>
      )}
    </div>
  )
}
