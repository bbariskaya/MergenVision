# API Endpoint Haritası

> **Tüm endpoint'ler root seviyededir; `/api/v1` öneki kullanılmaz.**
> **API response'larında asla raw national ID dönmez.**

## `GET /health`

- **Amaç:** Servis sağlık kontrolü.
- **Girdi:** Yok.
- **Çıktı:** `{ "status": "ok" }`
- **Hatalar:** 500 internal_error (servis kullanılamıyorsa).

## `POST /people`

- **Amaç:** Yeni kişi oluştur.
- **Girdi:** JSON `{ firstName, lastName, fullName, nationalId, birthDate?, gender?, department?, title?, organization?, details? }`
- **Çıktı:** 201 Created `{ personId, externalPersonId?, fullName, nationalIdMasked, createdAt, requestId }`
- **Hatalar:**
  - 400 validation_error (zorunlu alan eksik)
  - 409 conflict (aynı national_id_hash zaten var)

## `GET /people`

- **Amaç:** Kişi listesini döner (sayfalama + temel filtreler).
- **Girdi:** Query params: `page`, `size`, `query`, `isActive`
- **Çıktı:** `{ items[], total, page, size }`
- **Hatalar:** 400 validation_error (geçersiz query param).

## `GET /people/{personId}`

- **Amaç:** Tek kişi detayı.
- **Girdi:** path `personId`
- **Çıktı:** `{ personId, fullName, nationalIdMasked, photosCount, samplesCount, details, isActive, createdAt, updatedAt }`
- **Hatalar:** 404 not_found.

## `PATCH /people/{personId}`

- **Amaç:** Kişi bilgilerini güncelle.
- **Girdi:** JSON `{ firstName?, lastName?, fullName?, nationalId?, birthDate?, gender?, department?, title?, organization?, details?, isActive? }`
- **Çıktı:** `{ personId, updatedAt }`
- **Hatalar:** 404 not_found, 409 conflict (hash çakışması).

## `DELETE /people/{personId}`

- **Amaç:** Kişiyi soft-delete yap.
- **Girdi:** path `personId`
- **Çıktı:** `{ personId, deleted: true }`
- **Hatalar:** 404 not_found.

## `POST /people/{personId}/photos`

- **Amaç:** Kişiye fotoğraf ekle / yüz enroll et.
- **Girdi:** multipart `image`; path `personId`
- **Çıktı:** 201 Created `{ photoId, sampleId, qdrantPointId, imageKey, cropImageKey, requestId }`
- **Hatalar:**
  - 400 invalid_image
  - 400 no_face_detected
  - 400 multiple_faces_detected
  - 404 person_not_found

## `GET /people/{personId}/photos`

- **Amaç:** Kişiye ait fotoğraf ve sample listesini döner.
- **Girdi:** path `personId`; query `page`, `size`
- **Çıktı:** `{ items[{photoId, imageUrl, isPrimary, samples[]}], total }`
- **Hatalar:** 404 not_found.

## `POST /identify`

- **Amaç:** Sorgu fotoğrafından kişi eşleştirme yap.
- **Girdi:** multipart `image`; query `topK?`, `selectedFaceIndex?`
- **Çıktı:**
  - Başarı: `{ requestId, status, faceCount, topMatch, alternatives[], boundingBox, imageUrl }`
  - Çoklu yüz: `{ requestId, status: "multiple_faces", faceCount, faces[] }`
- **Hatalar:**
  - 400 invalid_image
  - 400 no_face_detected
  - 500 storage_error / internal_error

## `GET /identification-requests`

- **Amaç:** Identification istek geçmişini listele.
- **Girdi:** Query `page`, `size`, `status?`
- **Çıktı:** `{ items[{requestId, status, createdAt, topMatch?}], total }`
- **Hatalar:** 400 validation_error.

## `GET /identification-requests/{requestId}`

- **Amaç:** Tek identification isteğinin detayını ve sonuçlarını döner.
- **Girdi:** path `requestId`
- **Çıktı:** `{ requestId, status, createdAt, updatedAt, queryFaces[], results[] }`
- **Hatalar:** 404 request_not_found.

## `POST /imports/demo-folder`

- **Amaç:** Demo amaçlı bir klasörden kişi/fotoğraf import işi başlat.
- **Girdi:** JSON `{ folderPath, modelName? }`
- **Çıktı:** 202 Accepted `{ importJobId, status, requestId }`
- **Hatalar:**
  - 400 validation_error (klasör yok)
  - 501 not_implemented (demo'da sync veya async worker seçimine bağlı)

## `GET /imports/{importJobId}`

- **Amaç:** Import işinin durumunu ve özetini döner.
- **Girdi:** path `importJobId`
- **Çıktı:** `{ importJobId, status, total, processed, succeeded, failed, summary, createdAt, updatedAt }`
- **Hatalar:** 404 import_job_not_found.

## `GET /audit`

- **Amaç:** Audit log kayıtlarını listele.
- **Girdi:** Query `entityType?`, `entityId?`, `action?`, `page`, `size`
- **Çıktı:** `{ items[{auditId, entityType, entityId, action, actor, createdAt}], total }`
- **Hatalar:** 400 validation_error.
