import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { ArrowLeft, Camera, Pencil, Trash2, Upload } from 'lucide-react'
import * as z from 'zod'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import { PageHeader } from '@/components/ui/PageHeader'
import { ImagePreview } from '@/components/ui/ImagePreview'
import { MaskedId } from '@/components/ui/MaskedId'
import { LoadingState } from '@/components/ui/LoadingState'
import { ErrorState } from '@/components/ui/ErrorState'
import { EmptyState } from '@/components/ui/EmptyState'
import { FileUploadZone } from '@/components/ui/FileUploadZone'
import { useUpdatePerson, useDeletePerson } from '@/hooks/usePeople'
import { usePerson } from '@/hooks/usePerson'
import { useEnrollPhoto, usePhotos, useDeletePhoto } from '@/hooks/usePhotos'
import { useAudit } from '@/hooks/useAudit'
import { formatDateTime } from '@/lib/formatters'
import { toast } from 'sonner'

const editSchema = z.object({
  firstName: z.string().min(1, 'Ad gereklidir'),
  lastName: z.string().min(1, 'Soyad gereklidir'),
  details: z.string().optional(),
})

type EditFormValues = z.infer<typeof editSchema>

function parseDetails(value: string | undefined): Record<string, unknown> | undefined {
  if (!value || value.trim() === '') return undefined
  try {
    return JSON.parse(value) as Record<string, unknown>
  } catch {
    return { note: value }
  }
}

function stringifyDetails(details: Record<string, unknown> | undefined | null): string {
  if (!details) return ''
  try {
    return JSON.stringify(details, null, 2)
  } catch {
    return ''
  }
}

export function PersonDetailPage() {
  const { personId } = useParams<{ personId: string }>()
  const [activeTab, setActiveTab] = useState('photos')
  const [editOpen, setEditOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)

  const person = usePerson(personId)
  const photos = usePhotos(personId)
  const audit = useAudit({ entityId: personId, limit: 50, offset: 0 })
  const updatePerson = useUpdatePerson()
  const deletePerson = useDeletePerson()
  const enrollPhoto = useEnrollPhoto()
  const deletePhoto = useDeletePhoto()

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
  } = useForm<EditFormValues>({
    resolver: zodResolver(editSchema),
    values: {
      firstName: person.data?.firstName ?? '',
      lastName: person.data?.lastName ?? '',
      details: stringifyDetails(person.data?.details),
    },
  })

  const handleFileChange = (file: File | null) => {
    setSelectedFile(file)
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    setPreviewUrl(file ? URL.createObjectURL(file) : null)
  }

  const handleUpload = async () => {
    if (!personId || !selectedFile) return
    try {
      await enrollPhoto.mutateAsync({ personId, file: selectedFile })
      setSelectedFile(null)
      if (previewUrl) URL.revokeObjectURL(previewUrl)
      setPreviewUrl(null)
      toast.success('Fotoğraf yüklendi ve yüz kaydedildi.')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Fotoğraf yüklenemedi.')
    }
  }

  const handleDeletePhoto = async (photoId: string) => {
    if (!personId) return
    try {
      await deletePhoto.mutateAsync({ personId, photoId })
      toast.success('Fotoğraf silindi.')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Fotoğraf silinemedi.')
    }
  }

  const onEditSubmit = async (values: EditFormValues) => {
    if (!personId) return
    try {
      await updatePerson.mutateAsync({ id: personId, patch: { ...values, details: parseDetails(values.details) } })
      setEditOpen(false)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Güncellenemedi.'
      setError('root', { message })
    }
  }

  const handleDeletePerson = async () => {
    if (!personId) return
    try {
      await deletePerson.mutateAsync(personId)
      window.location.href = '/people'
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Kişi silinemedi.')
    }
  }

  if (person.isLoading) return <LoadingState />
  if (person.isError || !person.data) return <ErrorState message="Kişi yüklenemedi." onRetry={() => person.refetch()} />

  const p = person.data

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" asChild aria-label="Geri">
          <Link to="/people">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <PageHeader title={`${p.firstName} ${p.lastName}`} subtitle="Kişi detayları" />
      </div>

      <Card className="border-border bg-card">
        <CardContent className="p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="space-y-1">
              <h2 className="text-xl font-semibold">
                {p.firstName} {p.lastName}
              </h2>
              <MaskedId value={p.nationalIdMasked} />
              <p className="text-sm text-muted-foreground">
                Oluşturulma: {formatDateTime(p.createdAt)}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" size="sm" className="gap-2" onClick={() => setEditOpen(true)}>
                <Pencil className="h-4 w-4" />
                Düzenle
              </Button>
              <Button variant="destructive" size="sm" className="gap-2" onClick={() => setDeleteOpen(true)}>
                <Trash2 className="h-4 w-4" />
                Sil
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-muted">
          <TabsTrigger value="photos">Fotoğraflar</TabsTrigger>
          <TabsTrigger value="details">Detaylar</TabsTrigger>
          <TabsTrigger value="activity">Aktivite</TabsTrigger>
        </TabsList>

        <TabsContent value="photos" className="space-y-4">
          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle className="text-base">Fotoğraf Yükle</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <FileUploadZone
                value={selectedFile}
                onChange={handleFileChange}
                previewUrl={previewUrl ?? undefined}
                testId="photo-upload-zone"
              />
              <Button onClick={handleUpload} disabled={!selectedFile || enrollPhoto.isPending}>
                {enrollPhoto.isPending ? 'Yükleniyor...' : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    Yükle ve Kaydet
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {photos.isLoading ? (
            <LoadingState />
          ) : photos.isError ? (
            <ErrorState message="Fotoğraflar yüklenemedi." onRetry={() => photos.refetch()} />
          ) : photos.data?.length === 0 ? (
            <EmptyState title="Fotoğraf yok" description="Bu kişiye ait fotoğraf bulunmuyor." icon={<Camera className="mb-2 h-8 w-8 text-muted-foreground" />} />
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {photos.data?.map((photo) => (
                <Card key={photo.photoId} className="overflow-hidden border-border bg-card">
                  <ImagePreview
                    url={photo.imageUrl}
                    alt="Kişi fotoğrafı"
                    className="aspect-square"
                    testId={`photo-preview-${photo.photoId}`}
                  />
                  <CardContent className="p-3">
                    <p className="text-xs text-muted-foreground">{formatDateTime(photo.createdAt)}</p>
                    <p className="text-xs text-muted-foreground">Sample: {photo.samples.length}</p>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="mt-2 text-destructive"
                      onClick={() => handleDeletePhoto(photo.photoId)}
                      disabled={deletePhoto.isPending}
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      Sil
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="details">
          <Card className="border-border bg-card">
            <CardContent className="p-6">
              <pre className="overflow-auto rounded-md bg-muted p-4 text-xs">
                {stringifyDetails(p.details) || 'Detay yok.'}
              </pre>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="activity">
          <Card className="border-border bg-card">
            <CardContent className="p-6">
              {audit.isLoading ? (
                <LoadingState />
              ) : audit.data?.items.length === 0 ? (
                <EmptyState title="Aktivite yok" description="Bu kişiye ait kayıt bulunmuyor." />
              ) : (
                <div className="space-y-3">
                  {audit.data?.items.map((entry) => (
                    <div key={entry.auditId} className="rounded-lg border border-border p-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">{entry.action}</span>
                        <span className="text-xs text-muted-foreground">{formatDateTime(entry.createdAt)}</span>
                      </div>
                      <p className="text-xs text-muted-foreground">Actor: {entry.actor} • Outcome: {entry.outcome}</p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="border-border bg-card sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Kişiyi Düzenle</DialogTitle>
            <DialogDescription>Kişi bilgilerini güncelleyin.</DialogDescription>
          </DialogHeader>
          <form id="edit-person-form" onSubmit={handleSubmit(onEditSubmit)} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="edit-firstName">Ad</Label>
                <Input id="edit-firstName" {...register('firstName')} />
                {errors.firstName && <p className="text-xs text-destructive">{errors.firstName.message}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-lastName">Soyad</Label>
                <Input id="edit-lastName" {...register('lastName')} />
                {errors.lastName && <p className="text-xs text-destructive">{errors.lastName.message}</p>}
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-details">Detaylar</Label>
              <Textarea id="edit-details" rows={4} {...register('details')} />
            </div>
            {errors.root && <p className="text-sm text-destructive">{errors.root.message}</p>}
          </form>
          <DialogFooter>
            <Button type="submit" form="edit-person-form" disabled={updatePerson.isPending}>
              {updatePerson.isPending ? 'Kaydediliyor...' : 'Kaydet'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent className="border-border bg-card sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Kişiyi Sil</DialogTitle>
            <DialogDescription>
              {p.firstName} {p.lastName} kişisini silmek istediğinize emin misiniz? Bu işlem geri alınamaz.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteOpen(false)}>
              İptal
            </Button>
            <Button variant="destructive" onClick={handleDeletePerson} disabled={deletePerson.isPending}>
              {deletePerson.isPending ? 'Siliniyor...' : 'Sil'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
