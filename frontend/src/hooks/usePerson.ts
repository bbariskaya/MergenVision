import { useQuery } from '@tanstack/react-query'
import { getPerson } from '@/api/people'

export function usePerson(id: string | undefined) {
  return useQuery({
    queryKey: ['person', id],
    queryFn: () => getPerson(id!),
    enabled: Boolean(id),
  })
}
