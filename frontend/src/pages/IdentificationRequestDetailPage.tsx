import { useParams, Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { PageHeader } from '@/components/ui/PageHeader'
import { ImagePreview } from '@/components/ui/ImagePreview'
import { LoadingState } from '@/components/ui/LoadingState'
import { ErrorState } from '@/components/ui/ErrorState'
import { DecisionBadge, FaceResult } from '@/components/FaceResult'
import { useIdentificationRequest } from '@/hooks/useIdentificationRequest'

export function IdentificationRequestDetailPage() {
  const { requestId } = useParams<{ requestId: string }>()
  const request = useIdentificationRequest(requestId)

  if (request.isLoading) return <LoadingState />
  if (request.isError || !request.data) {
    return <ErrorState message="İstek detayı yüklenemedi." onRetry={() => request.refetch()} />
  }

  const data = request.data

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" asChild aria-label="Geri">
          <Link to="/identification-requests">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <PageHeader title="Tanıma İsteği Detayı" subtitle={`ID: ${requestId}`} />
      </div>

      <Card className="border-border bg-card">
        <CardContent className="p-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <p className="text-sm text-muted-foreground">Durum</p>
              <p className="font-medium">{data.status}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Karar</p>
              <DecisionBadge decision={data.decision} />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Yüz Sayısı</p>
              <p className="font-medium">{data.faceCount}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">TopK</p>
              <p className="font-medium">{data.faces[0]?.candidates.length ?? 0}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="border-border bg-card lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-base">Sorgu Görseli</CardTitle>
          </CardHeader>
          <CardContent>
            <ImagePreview
              url={data.queryImageUrl}
              alt="Sorgu görseli"
              className="aspect-square w-full rounded-lg"
            />
          </CardContent>
        </Card>

        <div className="space-y-4 lg:col-span-2">
          {data.faces.map((face) => (
            <FaceResult
              key={face.queryFaceId}
              face={face}
              title={`Yüz #${face.queryFaceId.slice(0, 8)}`}
              showCandidatesLabel={false}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
