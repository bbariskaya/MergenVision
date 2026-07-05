import { apiClient } from './client'
import type { FaceSampleResponse, PhotoEnrollmentResponse, PhotoResponse } from './types'

export function uploadPhoto(personId: string, file: File): Promise<PhotoEnrollmentResponse> {
  const formData = new FormData()
  formData.append('image', file)
  return apiClient
    .post<PhotoEnrollmentResponse>(`/people/${personId}/photos`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    .then((res) => res.data)
}

function normalizeSample(raw: unknown): FaceSampleResponse {
  const s = raw as Partial<FaceSampleResponse>
  return {
    sampleId: s.sampleId ?? '',
    faceId: s.faceId ?? '',
    cropImageUrl: s.cropImageUrl ?? '',
    qualityScore: s.qualityScore ?? 0,
    isActive: s.isActive ?? true,
  }
}

function normalizePhoto(raw: unknown): PhotoResponse {
  const p = raw as Partial<PhotoResponse> & { originalImageUrl?: string }
  return {
    photoId: p.photoId ?? '',
    personId: p.personId ?? '',
    imageUrl: p.imageUrl || p.originalImageUrl || '',
    samples: Array.isArray(p.samples) ? p.samples.map(normalizeSample) : [],
    isActive: p.isActive ?? true,
    createdAt: p.createdAt ?? new Date().toISOString(),
  }
}

export function getPhotos(personId: string): Promise<PhotoResponse[]> {
  return apiClient
    .get<PhotoResponse[] | { items?: PhotoResponse[] }>(`/people/${personId}/photos`)
    .then((res) => {
      const raw = res.data
      const items = Array.isArray(raw) ? raw : raw?.items ?? []
      return items.map(normalizePhoto)
    })
}

export function deletePhoto(personId: string, photoId: string): Promise<void> {
  return apiClient.delete(`/people/${personId}/photos/${photoId}`).then(() => undefined)
}
