import { http, HttpResponse } from 'msw'
import type {
  AuditLogEntry,
  HealthStatus,
  IdentificationRequestSummary,
  IdentifyCandidate,
  IdentifyFace,
  IdentifyResponse,
  PaginatedList,
  PersonResponse,
  PhotoEnrollmentResponse,
  PhotoResponse,
  StatsResponse,
} from '@/api/types'

const MODEL_NAME = 'arcface_w600k_r50_batch'
const MODEL_VERSION = 'batch'
const EMBEDDING_DIMENSION = 512

const MATCHED_THRESHOLD = 0.6
const POSSIBLE_MATCH_THRESHOLD = 0.4

interface MockSample {
  sampleId: string
  faceId: string
  qdrantPointId: string
  personId: string
  photoId: string
  cropImageUrl: string
  modelName: string
  modelVersion: string
  embeddingDimension: number
  qualityScore: number
  isActive: boolean
}

interface MockPhoto {
  photoId: string
  personId: string
  imageUrl: string
  isActive: boolean
  createdAt: string
  samples: MockSample[]
}

interface MockPerson {
  personId: string
  firstName: string
  lastName: string
  nationalId: string
  details: Record<string, unknown>
  isActive: boolean
  createdAt: string
  updatedAt: string
}

interface StoredRequest {
  requestId: string
  summary: IdentificationRequestSummary
  full: IdentifyResponse
}

function randomUUID(): string {
  return crypto.randomUUID()
}

function now(): string {
  return new Date().toISOString()
}

function maskNationalId(nationalId: string): string {
  return `******${nationalId.slice(-4)}`
}

function toPersonResponse(person: MockPerson): PersonResponse {
  return {
    personId: person.personId,
    firstName: person.firstName,
    lastName: person.lastName,
    nationalIdMasked: maskNationalId(person.nationalId),
    details: person.details,
    isActive: person.isActive,
    createdAt: person.createdAt,
    updatedAt: person.updatedAt,
  }
}

function toPhotoResponse(photo: MockPhoto): PhotoResponse {
  return {
    photoId: photo.photoId,
    personId: photo.personId,
    imageUrl: photo.imageUrl,
    isActive: photo.isActive,
    createdAt: photo.createdAt,
    samples: photo.samples
      .filter((sample) => sample.isActive)
      .map((sample) => ({
        sampleId: sample.sampleId,
        faceId: sample.faceId,
        cropImageUrl: sample.cropImageUrl,
        qualityScore: sample.qualityScore,
        isActive: sample.isActive,
      })),
  }
}

function toEnrollmentResponse(photo: MockPhoto, sample: MockSample): PhotoEnrollmentResponse {
  return {
    photoId: photo.photoId,
    personId: photo.personId,
    faceId: sample.faceId,
    sampleId: sample.sampleId,
    qdrantPointId: sample.qdrantPointId,
    imageUrl: photo.imageUrl,
    cropImageUrl: sample.cropImageUrl,
    modelName: sample.modelName,
    modelVersion: sample.modelVersion,
    embeddingDimension: sample.embeddingDimension,
    qualityScore: sample.qualityScore,
    isIndexed: true,
    createdAt: photo.createdAt,
  }
}

function qualityFromFile(file: File): number {
  const seed = file.size % 1300
  return Math.round((0.85 + seed / 10000) * 100) / 100
}

const people: MockPerson[] = [
  { personId: randomUUID(), firstName: 'Ahmet', lastName: 'Yılmaz', nationalId: '12345678901', details: { department: 'Güvenlik' }, isActive: true, createdAt: now(), updatedAt: now() },
  { personId: randomUUID(), firstName: 'Ayşe', lastName: 'Kaya', nationalId: '98765432109', details: { department: 'Operasyon' }, isActive: true, createdAt: now(), updatedAt: now() },
  { personId: randomUUID(), firstName: 'Mehmet', lastName: 'Demir', nationalId: '45678901234', details: { department: 'İnsan Kaynakları' }, isActive: true, createdAt: now(), updatedAt: now() },
  { personId: randomUUID(), firstName: 'Elif', lastName: 'Şahin', nationalId: '56789012345', details: { department: 'Teknik' }, isActive: true, createdAt: now(), updatedAt: now() },
  { personId: randomUUID(), firstName: 'Barış', lastName: 'Özcan', nationalId: '10987654321', details: { department: 'Mühendislik' }, isActive: true, createdAt: now(), updatedAt: now() },
].sort((a, b) => a.firstName.localeCompare(b.firstName))

const photos: MockPhoto[] = []
const samples: MockSample[] = []

function createMockPhoto(personId: string, index: number): MockPhoto {
  const photoId = randomUUID()
  const sampleCount = index % 2 === 0 ? 2 : 1
  const photoSamples: MockSample[] = []

  for (let i = 0; i < sampleCount; i++) {
    const sampleId = randomUUID()
    const faceId = randomUUID()
    const sample: MockSample = {
      sampleId,
      faceId,
      qdrantPointId: randomUUID(),
      personId,
      photoId,
      cropImageUrl: `/media/face-crops/${personId}/${sampleId}/crop.jpg`,
      modelName: MODEL_NAME,
      modelVersion: MODEL_VERSION,
      embeddingDimension: EMBEDDING_DIMENSION,
      qualityScore: Math.round((0.87 + (i * 0.04)) * 100) / 100,
      isActive: true,
    }
    photoSamples.push(sample)
    samples.push(sample)
  }

  return {
    photoId,
    personId,
    imageUrl: `/media/people-photos/${personId}/${photoId}/original.jpg`,
    isActive: true,
    createdAt: now(),
    samples: photoSamples,
  }
}

people.forEach((person, index) => {
  const count = (index % 3) + 1
  for (let i = 0; i < count; i++) {
    photos.push(createMockPhoto(person.personId, i))
  }
})

const storedRequests: StoredRequest[] = []

function generateCandidates(
  topK: number,
  matchedThreshold: number,
  possibleMatchThreshold: number
): IdentifyCandidate[] {
  const activePeople = people.filter((p) => p.isActive)
  if (activePeople.length === 0) return []

  const candidates: IdentifyCandidate[] = []
  const count = Math.min(topK, activePeople.length)

  for (let i = 0; i < count; i++) {
    const person = activePeople[i]
    const photo = photos.find((p) => p.personId === person.personId && p.isActive)
    const sample = photo?.samples.find((s) => s.isActive)
    if (!sample) continue

    const score = i === 0 ? 0.73 : i === 1 ? 0.45 : i === 2 ? 0.35 : Math.max(0.1, 0.25 - i * 0.02)
    const decision: IdentifyCandidate['decision'] =
      score >= matchedThreshold ? 'matched' : score >= possibleMatchThreshold ? 'possible_match' : 'no_match'

    candidates.push({
      rank: candidates.length + 1,
      faceId: sample.faceId,
      personId: person.personId,
      sampleId: sample.sampleId,
      name: `${person.firstName} ${person.lastName}`,
      score,
      decision,
    })
  }

  return candidates
}

function runIdentification(
  _file: File,
  topK: number,
  matchedThreshold: number,
  possibleMatchThreshold: number
): IdentifyResponse {
  const requestId = randomUUID()
  const queryFaceId = randomUUID()
  const candidates = generateCandidates(topK, matchedThreshold, possibleMatchThreshold)
  const best = candidates[0]

  const resultStatus: IdentifyFace['result']['status'] = best
    ? best.decision
    : 'no_match'

  const face: IdentifyFace = {
    queryFaceId,
    boundingBox: { x: 120, y: 90, width: 140, height: 140 },
    qualityScore: 0.91,
    result: best
      ? {
          status: resultStatus,
          personId: best.personId,
          faceId: best.faceId,
          sampleId: best.sampleId,
          name: best.name,
          score: best.score,
          threshold: matchedThreshold,
        }
      : {
          status: 'no_match',
          personId: '',
          faceId: '',
          sampleId: '',
          name: '',
          score: 0,
          threshold: matchedThreshold,
        },
    candidates,
  }

  const response: IdentifyResponse = {
    requestId,
    status: 'completed',
    decision: 'single_face',
    faceCount: 1,
    queryImageUrl: `/media/query-images/${requestId}/query.jpg`,
    faces: [face],
    createdAt: now(),
    completedAt: now(),
  }

  const summary: IdentificationRequestSummary = {
    requestId,
    status: 'completed',
    decision: 'single_face',
    faceCount: 1,
    topK,
    threshold: matchedThreshold,
    createdAt: now(),
    completedAt: now(),
  }

  storedRequests.push({ requestId, summary, full: response })
  audit('identify', 'identification_request', requestId, 'success', { topK, faceCount: 1 })

  return response
}

const auditLog: AuditLogEntry[] = []

function audit(
  action: string,
  entityType: string,
  entityId: string,
  outcome: string,
  metadata: Record<string, unknown> = {}
): void {
  auditLog.unshift({
    auditId: randomUUID(),
    action,
    entityType,
    entityId,
    actor: 'system',
    outcome,
    metadata,
    createdAt: now(),
  })
}

const seededAuditEntries: Omit<AuditLogEntry, 'auditId' | 'createdAt'>[] = [
  { action: 'person_created', entityType: 'person', entityId: people[0]?.personId ?? 'na', actor: 'operator-1', outcome: 'success', metadata: { source: 'ui' } },
  { action: 'person_created', entityType: 'person', entityId: people[1]?.personId ?? 'na', actor: 'operator-1', outcome: 'success', metadata: { source: 'ui' } },
  { action: 'photo_enrolled', entityType: 'person_photo', entityId: 'seed', actor: 'system', outcome: 'success', metadata: { autoIndexed: true } },
  { action: 'photo_enrolled', entityType: 'person_photo', entityId: 'seed', actor: 'system', outcome: 'success', metadata: { autoIndexed: true } },
  { action: 'identify', entityType: 'identification_request', entityId: 'seed', actor: 'operator-2', outcome: 'success', metadata: { topK: 5 } },
  { action: 'identify', entityType: 'identification_request', entityId: 'seed', actor: 'operator-2', outcome: 'success', metadata: { topK: 5 } },
  { action: 'person_updated', entityType: 'person', entityId: people[2]?.personId ?? 'na', actor: 'operator-1', outcome: 'success', metadata: { fields: ['details'] } },
  { action: 'photo_deleted', entityType: 'person_photo', entityId: 'seed', actor: 'operator-1', outcome: 'success', metadata: { reason: 'operator_request' } },
  { action: 'identify', entityType: 'identification_request', entityId: 'seed', actor: 'operator-3', outcome: 'no_match', metadata: { topK: 5 } },
  { action: 'person_created', entityType: 'person', entityId: people[3]?.personId ?? 'na', actor: 'operator-2', outcome: 'success', metadata: { source: 'import' } },
  { action: 'person_updated', entityType: 'person', entityId: people[4]?.personId ?? 'na', actor: 'operator-3', outcome: 'success', metadata: { fields: ['isActive'] } },
  { action: 'health_check', entityType: 'system', entityId: 'ready', actor: 'monitor', outcome: 'success', metadata: {} },
  { action: 'identify', entityType: 'identification_request', entityId: 'seed', actor: 'operator-1', outcome: 'possible_match', metadata: { topK: 10 } },
]

seededAuditEntries.forEach((entry) => audit(entry.action, entry.entityType, entry.entityId, entry.outcome, entry.metadata))

// Seed one completed identification request so E2E listing/detail tests run deterministically
runIdentification(new File([], 'seed.jpg', { type: 'image/jpeg' }), 5, MATCHED_THRESHOLD, POSSIBLE_MATCH_THRESHOLD)

function paginate<T>(items: T[], limit: number, offset: number): PaginatedList<T> {
  const safeLimit = Math.max(1, limit)
  const safeOffset = Math.max(0, offset)
  const total = items.length
  const sliced = items.slice(safeOffset, safeOffset + safeLimit)
  return { items: sliced, total, limit: safeLimit, offset: safeOffset }
}

function base64ToUint8Array(base64: string): Uint8Array {
  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i)
  }
  return bytes
}

const transparentGif = base64ToUint8Array(
  'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
)

const API_BASE = ((import.meta.env.VITE_API_BASE_URL as string | undefined) || 'http://localhost:8000').replace(/\/$/, '')

function endpoint(path: string): string {
  return `${API_BASE}${path}`
}

export const handlers = [
  http.get(endpoint('/health'), () => {
    return HttpResponse.json<HealthStatus>({ status: 'ok' })
  }),

  http.get(endpoint('/ready'), () => {
    return HttpResponse.json({
      status: 'ready',
      dependencies: {
        postgresql: 'ok',
        qdrant: 'ok',
        minio: 'ok',
        tensorrtRuntime: 'ok',
      },
    })
  }),

  http.get(endpoint('/stats'), () => {
    const stats: StatsResponse = {
      personCount: people.filter((p) => p.isActive).length,
      photoCount: photos.filter((p) => p.isActive).length,
      faceSampleCount: samples.filter((s) => s.isActive).length,
      identificationRequestCount: storedRequests.length,
    }
    return HttpResponse.json(stats)
  }),

  http.get(endpoint('/people'), ({ request }) => {
    const url = new URL(request.url)
    const limit = Number(url.searchParams.get('limit') ?? '20')
    const offset = Number(url.searchParams.get('offset') ?? '0')
    const active = people.filter((p) => p.isActive).map(toPersonResponse)
    return HttpResponse.json<PaginatedList<PersonResponse>>(paginate(active, limit, offset))
  }),

  http.post(endpoint('/people'), async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>
    const firstName = typeof body.firstName === 'string' ? body.firstName.trim() : ''
    const lastName = typeof body.lastName === 'string' ? body.lastName.trim() : ''
    const nationalId = typeof body.nationalId === 'string' ? body.nationalId.trim() : ''

    if (!firstName || !lastName || !nationalId) {
      return HttpResponse.json({ detail: 'firstName, lastName and nationalId are required.' }, { status: 400 })
    }

    const existing = people.find((p) => p.nationalId === nationalId && p.isActive)
    if (existing) {
      return HttpResponse.json({ detail: 'A person with this national ID already exists.' }, { status: 409 })
    }

    const person: MockPerson = {
      personId: randomUUID(),
      firstName,
      lastName,
      nationalId,
      details: typeof body.details === 'object' && body.details !== null ? (body.details as Record<string, unknown>) : {},
      isActive: true,
      createdAt: now(),
      updatedAt: now(),
    }
    people.push(person)
    audit('person_created', 'person', person.personId, 'success', { source: 'ui' })

    return HttpResponse.json<PersonResponse>(toPersonResponse(person), { status: 201 })
  }),

  http.get(endpoint('/people/:personId'), ({ params }) => {
    const person = people.find((p) => p.personId === params.personId && p.isActive)
    if (!person) {
      return HttpResponse.json({ detail: 'Person not found.' }, { status: 404 })
    }
    return HttpResponse.json<PersonResponse>(toPersonResponse(person))
  }),

  http.patch(endpoint('/people/:personId'), async ({ params, request }) => {
    const person = people.find((p) => p.personId === params.personId && p.isActive)
    if (!person) {
      return HttpResponse.json({ detail: 'Person not found.' }, { status: 404 })
    }

    const body = (await request.json()) as Record<string, unknown>

    if (typeof body.firstName === 'string') person.firstName = body.firstName
    if (typeof body.lastName === 'string') person.lastName = body.lastName
    if (typeof body.nationalId === 'string') {
      const conflict = people.find((p) => p.nationalId === body.nationalId && p.isActive && p.personId !== person.personId)
      if (conflict) {
        return HttpResponse.json({ detail: 'A person with this national ID already exists.' }, { status: 409 })
      }
      person.nationalId = body.nationalId
    }
    if (typeof body.details === 'object' && body.details !== null) person.details = body.details as Record<string, unknown>
    if (typeof body.isActive === 'boolean') person.isActive = body.isActive
    person.updatedAt = now()

    audit('person_updated', 'person', person.personId, 'success', { fields: Object.keys(body) })

    return HttpResponse.json<PersonResponse>(toPersonResponse(person))
  }),

  http.delete(endpoint('/people/:personId'), ({ params }) => {
    const person = people.find((p) => p.personId === params.personId && p.isActive)
    if (!person) {
      return HttpResponse.json({ detail: 'Person not found.' }, { status: 404 })
    }

    person.isActive = false
    person.updatedAt = now()
    photos
      .filter((p) => p.personId === person.personId)
      .forEach((photo) => {
        photo.isActive = false
        photo.samples.forEach((sample) => {
          sample.isActive = false
        })
      })

    audit('person_deleted', 'person', person.personId, 'success', { cascade: true })

    return new HttpResponse(null, { status: 204 })
  }),

  http.get(endpoint('/people/:personId/photos'), ({ params }) => {
    const person = people.find((p) => p.personId === params.personId && p.isActive)
    if (!person) {
      return HttpResponse.json({ detail: 'Person not found.' }, { status: 404 })
    }
    const personPhotos = photos.filter((p) => p.personId === person.personId && p.isActive).map(toPhotoResponse)
    return HttpResponse.json<PhotoResponse[]>(personPhotos)
  }),

  http.post(endpoint('/people/:personId/photos'), async ({ params, request }) => {
    const person = people.find((p) => p.personId === params.personId && p.isActive)
    if (!person) {
      return HttpResponse.json({ detail: 'Person not found.' }, { status: 404 })
    }

    const formData = await request.formData()
    const image = formData.get('image')
    if (!(image instanceof File)) {
      return HttpResponse.json({ detail: 'No image file provided.' }, { status: 400 })
    }

    if (image.size > 10 * 1024 * 1024) {
      return HttpResponse.json({ detail: 'File too large. Maximum 10 MiB.' }, { status: 413 })
    }

    const photo = createMockPhoto(person.personId, photos.filter((p) => p.personId === person.personId).length)
    photo.samples.forEach((sample) => {
      sample.qualityScore = qualityFromFile(image)
    })
    photos.push(photo)

    audit('photo_enrolled', 'person_photo', photo.photoId, 'success', { personId: person.personId })

    return HttpResponse.json<PhotoEnrollmentResponse>(
      toEnrollmentResponse(photo, photo.samples[0]!),
      { status: 201 }
    )
  }),

  http.delete(endpoint('/people/:personId/photos/:photoId'), ({ params }) => {
    const person = people.find((p) => p.personId === params.personId && p.isActive)
    if (!person) {
      return HttpResponse.json({ detail: 'Person not found.' }, { status: 404 })
    }
    const photo = photos.find((p) => p.photoId === params.photoId && p.personId === person.personId && p.isActive)
    if (!photo) {
      return HttpResponse.json({ detail: 'Photo not found.' }, { status: 404 })
    }
    photo.isActive = false
    photo.samples.forEach((sample) => {
      sample.isActive = false
    })

    audit('photo_deleted', 'person_photo', photo.photoId, 'success', { personId: person.personId })

    return new HttpResponse(null, { status: 204 })
  }),

  http.post(endpoint('/identify'), async ({ request }) => {
    const url = new URL(request.url)
    const topK = Number(url.searchParams.get('topK') ?? '5')
    const thresholdParam = url.searchParams.get('threshold')
    const matchedThreshold = thresholdParam ? Number(thresholdParam) : MATCHED_THRESHOLD

    const formData = await request.formData()
    const image = formData.get('image')
    if (!(image instanceof File)) {
      return HttpResponse.json({ detail: 'No image file provided.' }, { status: 400 })
    }

    const response = runIdentification(image, topK, matchedThreshold, POSSIBLE_MATCH_THRESHOLD)
    return HttpResponse.json<IdentifyResponse>(response)
  }),

  http.get(endpoint('/identification-requests'), ({ request }) => {
    const url = new URL(request.url)
    const limit = Number(url.searchParams.get('limit') ?? '20')
    const offset = Number(url.searchParams.get('offset') ?? '0')
    const summaries = [...storedRequests]
      .sort((a, b) => b.summary.createdAt.localeCompare(a.summary.createdAt))
      .map((r) => r.summary)
    return HttpResponse.json<PaginatedList<IdentificationRequestSummary>>(paginate(summaries, limit, offset))
  }),

  http.get(endpoint('/identification-requests/:requestId'), ({ params }) => {
    const stored = storedRequests.find((r) => r.requestId === params.requestId)
    if (!stored) {
      return HttpResponse.json({ detail: 'Identification request not found.' }, { status: 404 })
    }
    return HttpResponse.json<IdentifyResponse>(stored.full)
  }),

  http.get(endpoint('/audit'), ({ request }) => {
    const url = new URL(request.url)
    const entityType = url.searchParams.get('entityType')
    const entityId = url.searchParams.get('entityId')
    const action = url.searchParams.get('action')
    const limit = Number(url.searchParams.get('limit') ?? '20')
    const offset = Number(url.searchParams.get('offset') ?? '0')

    const filtered = auditLog.filter((entry) => {
      if (entityType && entry.entityType !== entityType) return false
      if (entityId && entry.entityId !== entityId) return false
      if (action && entry.action !== action) return false
      return true
    })

    return HttpResponse.json<PaginatedList<AuditLogEntry>>(paginate(filtered, limit, offset))
  }),

  http.get(endpoint('/media/:bucket/:objectKey'), () => {
    return HttpResponse.arrayBuffer(transparentGif.buffer, {
      headers: {
        'Content-Type': 'image/gif',
      },
    })
  }),
]
