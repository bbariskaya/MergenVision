import { apiClient } from './client'
import type { StatsResponse } from './types'

export function getStats(): Promise<StatsResponse> {
  return apiClient.get<StatsResponse>('/stats').then((res) => res.data)
}
