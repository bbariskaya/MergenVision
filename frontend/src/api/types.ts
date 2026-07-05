export interface PersonCreateInput {
  firstName: string
  lastName: string
  nationalId: string
  details?: Record<string, unknown> | null
}

export interface PersonUpdateInput {
  firstName?: string
  lastName?: string
  nationalId?: string
  details?: Record<string, unknown> | null
  isActive?: boolean
}

export interface PersonResponse {
  personId: string
  firstName: string
  lastName: string
  nationalIdMasked: string
  details: Record<string, unknown>
  isActive: boolean
  createdAt: string
  updatedAt: string
}

export interface BoundingBox {
  x: number
  y: number
  width: number
  height: number
}

export interface FaceSampleResponse {
  sampleId: string
  faceId: string
  cropImageUrl: string
  qualityScore: number
  isActive: boolean
}

export interface PhotoResponse {
  photoId: string
  personId: string
  imageUrl: string
  samples: FaceSampleResponse[]
  isActive: boolean
  createdAt: string
}

export interface PhotoEnrollmentResponse {
  photoId: string
  personId: string
  faceId: string
  sampleId: string
  qdrantPointId: string
  imageUrl: string
  cropImageUrl: string
  modelName: string
  modelVersion: string
  embeddingDimension: number
  qualityScore: number
  isIndexed: boolean
  createdAt: string
}

export interface IdentifyRequestQuery {
  topK?: number
  selectedFaceIndex?: number
  threshold?: number
}

export interface IdentifyFaceResult {
  status: 'matched' | 'possible_match' | 'no_match'
  personId: string
  faceId: string
  sampleId: string
  name?: string
  score: number
  threshold: number
}

export interface IdentifyCandidate {
  rank: number
  faceId: string
  personId: string
  sampleId: string
  name?: string
  score: number
  decision: 'matched' | 'possible_match' | 'no_match'
  cropImageUrl?: string
}

export interface IdentifyFace {
  queryFaceId: string
  boundingBox: BoundingBox
  qualityScore: number
  result: IdentifyFaceResult
  candidates: IdentifyCandidate[]
}

export interface IdentifyResponse {
  requestId: string
  status: string
  decision: string
  faceCount: number
  queryImageUrl: string
  faces: IdentifyFace[]
  createdAt: string
  completedAt?: string
}

export interface IdentificationRequestSummary {
  requestId: string
  status: string
  decision: string
  faceCount: number
  topK: number
  threshold?: number
  createdAt: string
  completedAt?: string
}

export interface PaginatedList<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}

export interface AuditLogEntry {
  auditId: string
  action: string
  entityType: string
  entityId: string
  actor: string
  outcome: string
  metadata: Record<string, unknown>
  createdAt: string
}

export interface StatsResponse {
  personCount: number
  photoCount: number
  faceSampleCount: number
  identificationRequestCount: number
}

export interface HealthReadyDependencies {
  postgresql: string
  qdrant: string
  minio: string
  tensorrtRuntime: string
}

export interface HealthReady {
  status: 'ready'
  dependencies: HealthReadyDependencies
}

export interface HealthStatus {
  status: 'ok'
}

export interface PeopleListParams {
  limit?: number
  offset?: number
}

export interface IdentificationRequestListParams {
  limit?: number
  offset?: number
}

export interface AuditListParams {
  entityType?: string
  entityId?: string
  action?: string
  limit?: number
  offset?: number
}
