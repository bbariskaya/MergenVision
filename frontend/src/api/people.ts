import { apiClient } from './client'
import type {
  PaginatedList,
  PeopleListParams,
  PersonCreateInput,
  PersonResponse,
  PersonUpdateInput,
} from './types'

export function createPerson(input: PersonCreateInput): Promise<PersonResponse> {
  return apiClient.post<PersonResponse>('/people', input).then((res) => res.data)
}

export function getPeople(params?: PeopleListParams): Promise<PaginatedList<PersonResponse>> {
  const searchParams = new URLSearchParams()
  if (params?.limit !== undefined) searchParams.set('limit', String(params.limit))
  if (params?.offset !== undefined) searchParams.set('offset', String(params.offset))
  const query = searchParams.toString()
  const url = query ? `/people?${query}` : '/people'
  return apiClient.get<PaginatedList<PersonResponse>>(url).then((res) => res.data)
}

export function getPerson(id: string): Promise<PersonResponse> {
  return apiClient.get<PersonResponse>(`/people/${id}`).then((res) => res.data)
}

export function updatePerson(id: string, patch: PersonUpdateInput): Promise<PersonResponse> {
  return apiClient.patch<PersonResponse>(`/people/${id}`, patch).then((res) => res.data)
}

export function deletePerson(id: string): Promise<void> {
  return apiClient.delete(`/people/${id}`).then(() => undefined)
}
