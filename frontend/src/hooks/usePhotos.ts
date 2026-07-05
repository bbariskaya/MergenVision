import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { deletePhoto, getPhotos, uploadPhoto } from '@/api/photos'

export function usePhotos(personId: string | undefined) {
  return useQuery({
    queryKey: ['people', personId, 'photos'],
    queryFn: () => getPhotos(personId!),
    enabled: Boolean(personId),
  })
}

export function useEnrollPhoto() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ personId, file }: { personId: string; file: File }) => uploadPhoto(personId, file),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['people', variables.personId, 'photos'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}

export function useDeletePhoto() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ personId, photoId }: { personId: string; photoId: string }) =>
      deletePhoto(personId, photoId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['people', variables.personId, 'photos'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}
