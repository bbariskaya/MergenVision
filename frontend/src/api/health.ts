import { apiClient } from './client'
import type { HealthReady, HealthStatus } from './types'

export function getHealth(): Promise<HealthStatus> {
  return apiClient.get<HealthStatus>('/health').then((res) => res.data)
}

export function getReady(): Promise<HealthReady> {
  return apiClient.get<HealthReady>('/ready').then((res) => res.data)
}
