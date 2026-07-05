import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Camera, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogTitle,
} from '@/components/ui/dialog'
import { PageHeader } from '@/components/ui/PageHeader'
import { ImagePreview } from '@/components/ui/ImagePreview'
import { LoadingState } from '@/components/ui/LoadingState'
import { ErrorState } from '@/components/ui/ErrorState'
import { EmptyState } from '@/components/ui/EmptyState'
import { usePhotos, useDeletePhoto } from '@/hooks/usePhotos'
import { usePerson } from '@/hooks/usePerson'
import { formatDateTime } from '@/lib/formatters'
import { toast } from 'sonner'

export function PersonPhotosPage() {
  const { personId } = useParams<{ personId: string }>()
  const [previewPhotoId, setPreviewPhotoId] = useState<string | null>(null)
  const person = usePerson(personId)
  const photos = usePhotos(personId)
  const deletePhoto = useDeletePhoto()

  const selectedPhoto = photos.data?.find((p) => p.photoId === previewPhotoId)

  const handleDelete = async (photoId: string) => {
    if (!personId) return
    try {
      await deletePhoto.mutateAsync({ personId, photoId })
      setPreviewPhotoId(null)
      toast.success('Fotoğraf silindi.')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Fotoğraf silinemedi.')
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" asChild aria-label="Geri">
          <Link to={`/people/${personId}`}>
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <PageHeader
          title={`${person.data?.firstName ?? ''} ${person.data?.lastName ?? ''} - Fotoğraflar`}
          subtitle="Tüm fotoğraflar ve önizlemeler"
        />
      </div>

      {photos.isLoading ? (
        <LoadingState />
      ) : photos.isError ? (
        <ErrorState message="Fotoğraflar yüklenemedi." onRetry={() => photos.refetch()} />
      ) : photos.data?.length === 0 ? (
        <EmptyState title="Fotoğraf yok" description="Bu kişiye ait fotoğraf bulunmuyor." icon={<Camera className="mb-2 h-8 w-8 text-muted-foreground" />} />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {photos.data?.map((photo) => (
            <Card
              key={photo.photoId}
              className="group cursor-pointer overflow-hidden border-border bg-card"
              onClick={() => setPreviewPhotoId(photo.photoId)}
            >
              <ImagePreview
                url={photo.imageUrl}
                alt="Kişi fotoğrafı"
                className="aspect-square"
                testId={`photo-preview-${photo.photoId}`}
              />
              <CardContent className="p-3">
                <p className="text-xs text-muted-foreground">{formatDateTime(photo.createdAt)}</p>
                <p className="text-xs text-muted-foreground">Sample: {photo.samples.length}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={Boolean(previewPhotoId)} onOpenChange={(open) => !open && setPreviewPhotoId(null)}>
        <DialogContent className="max-w-3xl border-border bg-card">
          <DialogTitle className="sr-only">Fotoğraf Önizleme</DialogTitle>
          {selectedPhoto && (
            <div className="space-y-4">
              <ImagePreview
                url={selectedPhoto.imageUrl}
                alt="Fotoğraf önizlemesi"
                className="max-h-[60vh] w-full rounded-lg object-contain"
              />
              <div className="flex items-center justify-between">
                <div className="text-sm text-muted-foreground">
                  <p>{formatDateTime(selectedPhoto.createdAt)}</p>
                  <p>Sample sayısı: {selectedPhoto.samples.length}</p>
                </div>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => handleDelete(selectedPhoto.photoId)}
                  disabled={deletePhoto.isPending}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Sil
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
