import { apiClient } from './client'
import type {
  IdentifyCandidate,
  IdentifyFace,
  IdentifyFaceResult,
  IdentifyRequestQuery,
  IdentifyResponse,
} from './types'

interface BackendCandidate {
  rank: number
  faceId: string | null
  personId: string | null
  sampleId: string | null
  name: string | null
  score: number
  decision: string
  cropImageUrl: string | null
}

interface BackendFace {
  queryFaceId: string
  boundingBox: { x: number; y: number; width: number; height: number }
  qualityScore: number | null
  result: BackendCandidate | null
  candidates: BackendCandidate[]
}

interface BackendIdentifyResponse {
  requestId: string
  status: string
  decision: string | null
  faceCount: number | null
  queryImageUrl: string | null
  faces: BackendFace[]
  createdAt: string
  completedAt: string | null
}

function normalizeCandidate(c: BackendCandidate): IdentifyCandidate {
  return {
    rank: c.rank,
    faceId: c.faceId ?? '',
    personId: c.personId ?? '',
    sampleId: c.sampleId ?? '',
    name: c.name || undefined,
    score: c.score,
    decision: c.decision as IdentifyCandidate['decision'],
    cropImageUrl: c.cropImageUrl || undefined,
  }
}

export function normalizeIdentifyResponse(raw: unknown): IdentifyResponse {
  const r = raw as BackendIdentifyResponse

  const faces: IdentifyFace[] = (r.faces ?? []).map((f) => {
    const best = f.result ?? f.candidates[0]
    const result: IdentifyFaceResult = {
      status: (best?.decision || r.decision || 'no_match') as IdentifyFaceResult['status'],
      personId: best?.personId ?? '',
      faceId: best?.faceId ?? '',
      sampleId: best?.sampleId ?? '',
      name: best?.name || undefined,
      score: best?.score ?? 0,
      threshold: 0,
    }
    return {
      queryFaceId: f.queryFaceId,
      boundingBox: f.boundingBox,
      qualityScore: f.qualityScore ?? 0,
      result,
      candidates: f.candidates.map(normalizeCandidate),
    }
  })

  return {
    requestId: r.requestId,
    status: r.status,
    decision: r.decision || '',
    faceCount: r.faceCount ?? 0,
    queryImageUrl: r.queryImageUrl || '',
    faces,
    createdAt: r.createdAt,
  }
}

export function identify(file: File, options?: IdentifyRequestQuery): Promise<IdentifyResponse> {
  const formData = new FormData()
  formData.append('image', file)

  const searchParams = new URLSearchParams()
  if (options?.topK !== undefined) searchParams.set('topK', String(options.topK))
  if (options?.selectedFaceIndex !== undefined) searchParams.set('selectedFaceIndex', String(options.selectedFaceIndex))
  if (options?.threshold !== undefined) searchParams.set('threshold', String(options.threshold))

  const query = searchParams.toString()
  const url = query ? `/identify?${query}` : '/identify'

  return apiClient
    .post<BackendIdentifyResponse>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    .then((res) => normalizeIdentifyResponse(res.data))
}
