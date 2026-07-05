import { apiClient } from './client'
import type { AuditListParams, AuditLogEntry, PaginatedList } from './types'

export function getAuditLogs(params?: AuditListParams): Promise<PaginatedList<AuditLogEntry>> {
  const searchParams = new URLSearchParams()
  if (params?.entityType) searchParams.set('entityType', params.entityType)
  if (params?.entityId) searchParams.set('entityId', params.entityId)
  if (params?.action) searchParams.set('action', params.action)
  if (params?.limit !== undefined) searchParams.set('limit', String(params.limit))
  if (params?.offset !== undefined) searchParams.set('offset', String(params.offset))
  const query = searchParams.toString()
  const url = query ? `/audit?${query}` : '/audit'
  return apiClient.get<PaginatedList<AuditLogEntry>>(url).then((res) => res.data)
}
