import { useState } from 'react'
import { Scan } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { PageHeader } from '@/components/ui/PageHeader'
import { FileUploadZone } from '@/components/ui/FileUploadZone'
import { ImagePreview } from '@/components/ui/ImagePreview'
import { LoadingState } from '@/components/ui/LoadingState'
import { EmptyState } from '@/components/ui/EmptyState'
import { FaceResult } from '@/components/FaceResult'
import { useIdentify } from '@/hooks/useIdentify'

export function IdentifyPage() {
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [topK, setTopK] = useState(5)
  const [threshold, setThreshold] = useState(0.6)
  const identify = useIdentify()

  const handleFileChange = (selected: File | null) => {
    setFile(selected)
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    setPreviewUrl(selected ? URL.createObjectURL(selected) : null)
    identify.reset()
  }

  const handleIdentify = async () => {
    if (!file) return
    await identify.mutateAsync({ file, options: { topK, threshold } })
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Yüz Tanıma" subtitle="Bir görsel yükleyerek kişi tanıma yapın" />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-1">
          <FileUploadZone
            value={file}
            onChange={handleFileChange}
            previewUrl={previewUrl ?? undefined}
            testId="identify-upload-zone"
          />

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle className="text-base">Ayarlar</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label htmlFor="topK">Aday Sayısı (topK)</Label>
                  <span className="text-sm font-medium">{topK}</span>
                </div>
                <Slider
                  id="topK"
                  min={1}
                  max={20}
                  step={1}
                  value={[topK]}
                  onValueChange={(value) => setTopK(value[0] ?? 5)}
                />
              </div>
              <div className="space-y-3">
                <Label htmlFor="threshold">Eşik Değeri</Label>
                <Input
                  id="threshold"
                  type="number"
                  min={0}
                  max={1}
                  step={0.05}
                  value={threshold}
                  onChange={(e) => setThreshold(Number(e.target.value))}
                />
              </div>
              <Button
                className="w-full gap-2"
                onClick={handleIdentify}
                disabled={!file || identify.isPending}
                data-testid="identify-button"
              >
                <Scan className="h-4 w-4" />
                {identify.isPending ? 'Tanımlanıyor...' : 'Tanımla'}
              </Button>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4 lg:col-span-2">
          {identify.isPending ? (
            <LoadingState message="Tanıma işlemi devam ediyor..." />
          ) : identify.isError ? (
            <EmptyState title="Tanıma başarısız" description={identify.error instanceof Error ? identify.error.message : 'Bir hata oluştu.'} />
          ) : identify.data ? (
            <>
              <Card className="border-border bg-card">
                <CardHeader>
                  <CardTitle className="text-base">Sorgu Görseli</CardTitle>
                </CardHeader>
                <CardContent>
                  <ImagePreview
                    url={identify.data.queryImageUrl}
                    alt="Sorgu görseli"
                    className="aspect-video w-full rounded-lg"
                  />
                  <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">Durum</p>
                      <p className="font-medium">{identify.data.status}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Yüz Sayısı</p>
                      <p className="font-medium">{identify.data.faceCount}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Karar</p>
                      <p className="font-medium">{identify.data.decision}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {identify.data.faces.map((face) => (
                <FaceResult key={face.queryFaceId} face={face} />
              ))}
            </>
          ) : (
            <EmptyState
              title="Henüz sorgu yapılmadı"
              description="Bir görsel yükleyip Tanımla butonuna basın."
              icon={<Scan className="mb-2 h-8 w-8 text-muted-foreground" />}
            />
          )}
        </div>
      </div>
    </div>
  )
}
