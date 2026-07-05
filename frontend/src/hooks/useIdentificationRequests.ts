import { useQuery } from '@tanstack/react-query'
import { getIdentificationRequests } from '@/api/requests'
import type { IdentificationRequestListParams } from '@/api/types'

export function useIdentificationRequests(params?: IdentificationRequestListParams) {
  return useQuery({
    queryKey: ['identification-requests', params],
    queryFn: () => getIdentificationRequests(params),
  })
}
