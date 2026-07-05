import { apiClient } from './client'
import { normalizeIdentifyResponse } from './identify'
import type {
  IdentificationRequestListParams,
  IdentificationRequestSummary,
  IdentifyResponse,
  PaginatedList,
} from './types'

export function getIdentificationRequests(
  params?: IdentificationRequestListParams
): Promise<PaginatedList<IdentificationRequestSummary>> {
  const searchParams = new URLSearchParams()
  if (params?.limit !== undefined) searchParams.set('limit', String(params.limit))
  if (params?.offset !== undefined) searchParams.set('offset', String(params.offset))
  const query = searchParams.toString()
  const url = query ? `/identification-requests?${query}` : '/identification-requests'
  return apiClient.get<PaginatedList<IdentificationRequestSummary>>(url).then((res) => res.data)
}

export function getIdentificationRequest(id: string): Promise<IdentifyResponse> {
  return apiClient
    .get<unknown>(`/identification-requests/${id}`)
    .then((res) => normalizeIdentifyResponse(res.data))
}
