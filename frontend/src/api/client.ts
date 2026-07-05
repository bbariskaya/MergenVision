import axios from 'axios'

const STORAGE_KEY = 'mv-token'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem(STORAGE_KEY)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
  }
  return config
})

export class ApiError extends Error {
  status: number
  details?: Record<string, unknown>

  constructor(status: number, message: string, details?: Record<string, unknown>) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.details = details
  }
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError
}

apiClient.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (axios.isAxiosError(error)) {
      const response = error.response
      const status = response?.status ?? 0
      const data = response?.data as unknown
      const message =
        typeof data === 'object' && data !== null && typeof (data as Record<string, unknown>).detail === 'string'
          ? ((data as Record<string, unknown>).detail as string)
          : error.message
      const details = typeof data === 'object' && data !== null ? (data as Record<string, unknown>) : undefined
      return Promise.reject(new ApiError(status, message, details))
    }
    return Promise.reject(error)
  }
)
