import { useQuery } from '@tanstack/react-query'
import { getHealth, getReady } from '@/api/health'

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
  })
}

export function useReady() {
  return useQuery({
    queryKey: ['ready'],
    queryFn: getReady,
  })
}
