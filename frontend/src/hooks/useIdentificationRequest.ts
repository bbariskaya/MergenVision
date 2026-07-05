import { useQuery } from '@tanstack/react-query'
import { getIdentificationRequest } from '@/api/requests'

export function useIdentificationRequest(id: string | undefined) {
  return useQuery({
    queryKey: ['identification-request', id],
    queryFn: () => getIdentificationRequest(id!),
    enabled: Boolean(id),
  })
}
