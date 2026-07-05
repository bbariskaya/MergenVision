import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Plus, Search } from 'lucide-react'
import * as z from 'zod'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { DataTable } from '@/components/ui/DataTable'
import { PageHeader } from '@/components/ui/PageHeader'
import { Pagination } from '@/components/ui/Pagination'
import { MaskedId } from '@/components/ui/MaskedId'
import { LoadingState } from '@/components/ui/LoadingState'
import { ErrorState } from '@/components/ui/ErrorState'
import { useCreatePerson, usePeople } from '@/hooks/usePeople'
import type { PersonResponse } from '@/api/types'
import type { DataTableColumn } from '@/components/ui/DataTable'

const personSchema = z.object({
  firstName: z.string().min(1, 'Ad gereklidir'),
  lastName: z.string().min(1, 'Soyad gereklidir'),
  nationalId: z.string().length(11, 'TC Kimlik No 11 haneli olmalıdır'),
  details: z.string().optional(),
})

type PersonFormValues = z.infer<typeof personSchema>

const LIMIT = 10

function parseDetails(value: string | undefined): Record<string, unknown> | undefined {
  if (!value || value.trim() === '') return undefined
  try {
    return JSON.parse(value) as Record<string, unknown>
  } catch {
    return { note: value }
  }
}

export function PeoplePage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [offset, setOffset] = useState(0)
  const [open, setOpen] = useState(false)

  const { data, isLoading, isError, refetch } = usePeople({ limit: LIMIT, offset })
  const createPerson = useCreatePerson()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
    setError,
  } = useForm<PersonFormValues>({
    resolver: zodResolver(personSchema),
    defaultValues: {
      firstName: '',
      lastName: '',
      nationalId: '',
      details: '',
    },
  })

  const filteredItems =
    data?.items.filter((person) => {
      const query = search.toLowerCase()
      const fullName = `${person.firstName} ${person.lastName}`.toLowerCase()
      return fullName.includes(query) || person.nationalIdMasked.includes(query)
    }) ?? []

  const columns: DataTableColumn<PersonResponse>[] = [
    { key: 'name', header: 'Ad Soyad', cell: (p) => `${p.firstName} ${p.lastName}` },
    { key: 'nationalId', header: 'Maskelenmiş TC', cell: (p) => <MaskedId value={p.nationalIdMasked} /> },
    { key: 'status', header: 'Durum', cell: (p) => (p.isActive ? 'Aktif' : 'Pasif') },
  ]

  const onSubmit = async (values: PersonFormValues) => {
    try {
      await createPerson.mutateAsync({
        firstName: values.firstName,
        lastName: values.lastName,
        nationalId: values.nationalId,
        details: parseDetails(values.details),
      })
      setOpen(false)
      reset()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Kişi oluşturulamadı.'
      setError('root', { message })
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Kişiler"
        subtitle="Kimlik platformuna kayıtlı kişiler"
        actions={
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button className="gap-2">
                <Plus className="h-4 w-4" />
                Yeni Kişi Ekle
              </Button>
            </DialogTrigger>
            <DialogContent className="border-border bg-card sm:max-w-md">
              <DialogHeader>
                <DialogTitle>Yeni Kişi Ekle</DialogTitle>
                <DialogDescription>
                  Yeni bir kişi kaydı oluşturun. TC kimlik numarası sadece oluşturulurken kullanılır.
                </DialogDescription>
              </DialogHeader>
              <form id="person-form" onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="firstName">Ad</Label>
                    <Input id="firstName" {...register('firstName')} />
                    {errors.firstName && (
                      <p className="text-xs text-destructive">{errors.firstName.message}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="lastName">Soyad</Label>
                    <Input id="lastName" {...register('lastName')} />
                    {errors.lastName && (
                      <p className="text-xs text-destructive">{errors.lastName.message}</p>
                    )}
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="nationalId">TC Kimlik No</Label>
                  <Input id="nationalId" maxLength={11} {...register('nationalId')} />
                  {errors.nationalId && (
                    <p className="text-xs text-destructive">{errors.nationalId.message}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="details">Detaylar (JSON veya metin)</Label>
                  <Textarea id="details" rows={3} {...register('details')} />
                </div>
                {errors.root && <p className="text-sm text-destructive">{errors.root.message}</p>}
              </form>
              <DialogFooter>
                <Button type="submit" form="person-form" disabled={createPerson.isPending}>
                  {createPerson.isPending ? 'Kaydediliyor...' : 'Kaydet'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        }
      />

      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Kişi ara..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
          data-testid="people-search"
        />
      </div>

      {isLoading ? (
        <LoadingState />
      ) : isError ? (
        <ErrorState message="Kişiler yüklenemedi." onRetry={() => refetch()} />
      ) : (
        <>
          <DataTable
            columns={columns}
            data={filteredItems}
            keyExtractor={(p) => p.personId}
            onRowClick={(p) => navigate(`/people/${p.personId}`)}
            testId="people-table"
            footer={
              <Pagination
                offset={data?.offset ?? 0}
                limit={data?.limit ?? LIMIT}
                total={data?.total ?? 0}
                onPageChange={setOffset}
              />
            }
          />
        </>
      )}
    </div>
  )
}
