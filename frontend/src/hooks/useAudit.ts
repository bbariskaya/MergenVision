import { useQuery } from '@tanstack/react-query'
import { getAuditLogs } from '@/api/audit'
import type { AuditListParams } from '@/api/types'

export function useAudit(params?: AuditListParams) {
  return useQuery({
    queryKey: ['audit', params],
    queryFn: () => getAuditLogs(params),
  })
}
