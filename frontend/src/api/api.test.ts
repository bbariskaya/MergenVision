// @vitest-environment node
import { describe, expect, it } from 'vitest'
import { apiClient, ApiError, isApiError } from './client'
import {
  createPerson,
  deletePerson,
  getPeople,
  getPerson,
  updatePerson,
} from './people'
import { deletePhoto, getPhotos, uploadPhoto } from './photos'
import { identify } from './identify'
import { getIdentificationRequest, getIdentificationRequests } from './requests'
import { getAuditLogs } from './audit'
import { getStats } from './stats'
import { getHealth, getReady } from './health'

describe('API client', () => {
  it('exports ApiError and type guard', () => {
    const error = new ApiError(400, 'bad request')
    expect(isApiError(error)).toBe(true)
    expect(isApiError(new Error('generic'))).toBe(false)
  })

  it('normalizes axios errors into ApiError', async () => {
    try {
      await apiClient.get('/people/not-a-real-id')
      expect.fail('expected request to fail')
    } catch (error) {
      expect(isApiError(error)).toBe(true)
      if (isApiError(error)) {
        expect(error.status).toBe(404)
      }
    }
  })
})

describe('health endpoints', () => {
  it('returns ok from /health', async () => {
    const data = await getHealth()
    expect(data.status).toBe('ok')
  })

  it('returns ready from /ready', async () => {
    const data = await getReady()
    expect(data.status).toBe('ready')
    expect(data.dependencies.postgresql).toBe('ok')
    expect(data.dependencies.qdrant).toBe('ok')
    expect(data.dependencies.minio).toBe('ok')
    expect(data.dependencies.tensorrtRuntime).toBe('ok')
  })
})

describe('/people', () => {
  it('creates and retrieves a person', async () => {
    const created = await createPerson({
      firstName: 'Test',
      lastName: 'User',
      nationalId: '11111111111',
      details: { department: 'QA' },
    })
    expect(created.personId).toBeDefined()
    expect(created.firstName).toBe('Test')
    expect(created.nationalIdMasked).toBe('******1111')
    expect(created.details.department).toBe('QA')

    const fetched = await getPerson(created.personId)
    expect(fetched.personId).toBe(created.personId)
  })

  it('lists people with pagination', async () => {
    const list = await getPeople({ limit: 10, offset: 0 })
    expect(list.items.length).toBeGreaterThanOrEqual(5)
    expect(list.limit).toBe(10)
    expect(list.offset).toBe(0)
    expect(list.total).toBeGreaterThanOrEqual(5)
  })

  it('updates a person', async () => {
    const created = await createPerson({
      firstName: 'Update',
      lastName: 'Me',
      nationalId: '22222222222',
    })
    const updated = await updatePerson(created.personId, { lastName: 'Changed' })
    expect(updated.lastName).toBe('Changed')
  })

  it('soft deletes a person', async () => {
    const created = await createPerson({
      firstName: 'Delete',
      lastName: 'Me',
      nationalId: '33333333333',
    })
    await deletePerson(created.personId)
    await expect(getPerson(created.personId)).rejects.toThrow()
  })
})

describe('/people/:id/photos', () => {
  it('enrolls and lists a photo', async () => {
    const person = await createPerson({
      firstName: 'Photo',
      lastName: 'Owner',
      nationalId: '44444444444',
    })
    const file = new File(['fake-image-bytes'], 'face.jpg', { type: 'image/jpeg' })
    const enrolled = await uploadPhoto(person.personId, file)
    expect(enrolled.personId).toBe(person.personId)
    expect(enrolled.imageUrl).toMatch(/^\/media\/people-photos\//)
    expect(enrolled.cropImageUrl).toMatch(/^\/media\/face-crops\//)
    expect(enrolled.modelName).toBeDefined()
    expect(enrolled.embeddingDimension).toBe(512)

    const photos = await getPhotos(person.personId)
    expect(photos.length).toBeGreaterThanOrEqual(1)
  })

  it('deletes a photo', async () => {
    const person = await createPerson({
      firstName: 'Photo',
      lastName: 'Remover',
      nationalId: '55555555555',
    })
    const file = new File(['x'], 'face.jpg', { type: 'image/jpeg' })
    const enrolled = await uploadPhoto(person.personId, file)
    await deletePhoto(person.personId, enrolled.photoId)
    const photos = await getPhotos(person.personId)
    const deleted = photos.find((p) => p.photoId === enrolled.photoId)
    expect(deleted).toBeUndefined()
  })
})

describe('/identify', () => {
  it('returns a completed single-face result with candidates', async () => {
    const file = new File(['query-image'], 'query.jpg', { type: 'image/jpeg' })
    const result = await identify(file, { topK: 5 })
    expect(result.status).toBe('completed')
    expect(result.decision).toBe('single_face')
    expect(result.faceCount).toBe(1)
    expect(result.queryImageUrl).toMatch(/^\/media\/query-images\//)
    expect(result.faces.length).toBe(1)
    expect(result.faces[0]?.candidates.length).toBeGreaterThanOrEqual(1)
  })

  it('respects topK param', async () => {
    const file = new File(['query-image'], 'query.jpg', { type: 'image/jpeg' })
    const result = await identify(file, { topK: 2 })
    expect(result.faces[0]?.candidates.length).toBeLessThanOrEqual(2)
  })
})

describe('requests / audit / stats', () => {
  it('lists identification requests', async () => {
    const file = new File(['x'], 'q.jpg', { type: 'image/jpeg' })
    await identify(file, { topK: 5 })
    const list = await getIdentificationRequests({ limit: 10, offset: 0 })
    expect(list.items.length).toBeGreaterThanOrEqual(1)
  })

  it('gets an identification request by id', async () => {
    const file = new File(['x'], 'q.jpg', { type: 'image/jpeg' })
    const created = await identify(file, { topK: 5 })
    const fetched = await getIdentificationRequest(created.requestId)
    expect(fetched.requestId).toBe(created.requestId)
  })

  it('queries audit logs', async () => {
    const logs = await getAuditLogs({ limit: 20, offset: 0 })
    expect(logs.items.length).toBeGreaterThanOrEqual(10)
  })

  it('returns stats', async () => {
    const stats = await getStats()
    expect(stats.personCount).toBeGreaterThanOrEqual(5)
    expect(stats.photoCount).toBeGreaterThanOrEqual(5)
    expect(stats.faceSampleCount).toBeGreaterThanOrEqual(5)
  })
})
