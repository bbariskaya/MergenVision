import { Link } from 'react-router-dom'
import { Activity, Camera, Scan, Users } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { StatCard } from '@/components/ui/StatCard'
import { PageHeader } from '@/components/ui/PageHeader'
import { LoadingState } from '@/components/ui/LoadingState'
import { ErrorState } from '@/components/ui/ErrorState'
import { useIdentificationRequests } from '@/hooks/useIdentificationRequests'
import { useStats } from '@/hooks/useStats'
import { useReady } from '@/hooks/useHealth'
import { formatDateTime } from '@/lib/formatters'

export function DashboardPage() {
  const stats = useStats()
  const requests = useIdentificationRequests({ limit: 5, offset: 0 })
  const ready = useReady()

  return (
    <div className="space-y-6">
      <PageHeader title="Dashboard" subtitle="Operasyonel özet ve hızlı işlemler" />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Toplam Kişi"
          value={stats.data?.personCount ?? 0}
          icon={Users}
          loading={stats.isLoading}
          testId="stat-person-count"
        />
        <StatCard
          title="Toplam Fotoğraf"
          value={stats.data?.photoCount ?? 0}
          icon={Camera}
          loading={stats.isLoading}
          testId="stat-photo-count"
        />
        <StatCard
          title="Yüz Örneği"
          value={stats.data?.faceSampleCount ?? 0}
          icon={Activity}
          loading={stats.isLoading}
          testId="stat-face-sample-count"
        />
        <StatCard
          title="Tanıma İsteği"
          value={stats.data?.identificationRequestCount ?? 0}
          icon={Scan}
          loading={stats.isLoading}
          testId="stat-identification-request-count"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="border-border bg-card lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-lg">Son Tanıma İstekleri</CardTitle>
            <Button variant="outline" size="sm" asChild>
              <Link to="/identification-requests">Tümünü Gör</Link>
            </Button>
          </CardHeader>
          <CardContent>
            {requests.isLoading ? (
              <LoadingState message="İstekler yükleniyor..." />
            ) : requests.isError ? (
              <ErrorState message="İstekler yüklenemedi." onRetry={() => requests.refetch()} />
            ) : requests.data?.items.length === 0 ? (
              <p className="py-8 text-center text-sm text-muted-foreground">Henüz tanıma isteği yok.</p>
            ) : (
              <div className="space-y-3">
                {requests.data?.items.map((request) => (
                  <Link
                    key={request.requestId}
                    to={`/identification-requests/${request.requestId}`}
                    className="flex items-center justify-between rounded-lg border border-border p-3 transition-colors hover:bg-muted/50"
                  >
                    <div>
                      <p className="text-sm font-medium">{request.requestId.slice(0, 8)}...</p>
                      <p className="text-xs text-muted-foreground">
                        {formatDateTime(request.completedAt ?? request.createdAt)}
                      </p>
                    </div>
                    <span
                      className="rounded-full px-2 py-0.5 text-xs font-medium"
                      data-testid="request-decision-badge"
                    >
                      {request.decision}
                    </span>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle className="text-lg">Sistem Durumu</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {ready.isLoading ? (
              <LoadingState message="Durum kontrol ediliyor..." />
            ) : ready.isError ? (
              <div className="rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
                Sistem hazır değil
              </div>
            ) : (
              <div className="rounded-lg bg-emerald-500/10 p-3 text-sm text-emerald-500">
                Tüm bağımlılıklar hazır
              </div>
            )}
            <div className="grid grid-cols-2 gap-2">
              <Button asChild>
                <Link to="/people">Yeni Kişi Ekle</Link>
              </Button>
              <Button variant="outline" asChild>
                <Link to="/identify">Yüz Tanıma Yap</Link>
              </Button>
              <Button variant="outline" asChild>
                <Link to="/identification-requests">Tüm İstekleri Gör</Link>
              </Button>
              <Button variant="outline" asChild>
                <Link to="/audit">Audit Log</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
