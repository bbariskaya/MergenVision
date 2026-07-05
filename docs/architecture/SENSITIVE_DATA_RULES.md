# Sensitive Data Rules

MergenVision, yüz görüntüleri ve kimlik bilgileri gibi hassas verileri korumak için aşağıdaki kurallara uyar. Bu kurallar Phase 0 mimarisinde tanımlanır; Phase 1 implementasyonunda uygulanır.

## Raw National ID Rules

- **Raw national ID** hiçbir API yanıtında yer almaz.
- PostgreSQL'de `nationalIdHash` (tek yönlü hash) ve `nationalIdMasked` (maske) saklanır.
- Hash algoritması Phase 1'de Argon2id veya SHA-256 + salt olabilir; algoritma değiştirilebilir ancak saklanan değerler güncellenmelidir.
- National ID duplicate kontrolü hash üzerinden yapılır.
- Demo/test ortamlarında bile production gerçek national ID kullanılmaz; sentetik/sahte veri uygulanır.

## Masking / Hash / Encryption Concept

| Veri | Yöntem | Konum |
|---|---|---|
| national ID | hash + mask | PostgreSQL only |
| full details (doğum yeri vb.) | encrypted-at-rest (future) veya masked | PostgreSQL only |
| image bytes | stored as objects in MinIO | MinIO |
| embeddings | vector in Qdrant | Qdrant |
| audit metadata | statistical summary only | PostgreSQL |

- **Hash:** Tek yönlü, eşleştirme için.
- **Mask:** UI/response için.
- **Encryption-at-rest:** Phase 1'de zorunlu değil; production sonrası değerlendirilir.
- **Presigned URL:** Geçici, süreli object erişimi; uzun ömürlü public URL yoktur.

## Qdrant Payload Restrictions

Qdrant payload'ına **asla** şunlar yazılmaz:

- raw national ID
- tam ad-soyad
- doğum tarihi, adres gibi detaylı PII
- görüntü byte'ları veya base64 görüntü
- embedding dışında frontend display blob'u

Qdrant payload'ında olması gerekenler:

- `sampleId`, `personId`, `photoId` (UUID referans)
- `modelName`, `modelVersion`, `embeddingDimension`
- `isActive` (soft delete filtresi)

## Audit Restrictions

`audit_log` satırları şunları **içermez**:

- raw national ID
- image bytes / base64
- embedding vektörü
- kişi detayları (`details` JSON tamamı)

`audit_log` satırları şunları içerebilir:

- `entityType`, `entityId` (UUID)
- `action` (örn. `person_created`, `photo_enrolled`, `identification_completed`)
- `actor` id
- istatistiksel metadata (örn. face_count, top_k, model_name, elapsed_ms)

## MinIO Object Access

- Object'lere doğrudan erişim olmaz.
- API, `GET /media/{bucket}/{objectKey}` ile:
  - presigned URL yönlendirmesi yapar, veya
  - binary stream proxyler.
- Presigned URL'ler kısa ömürlüdür (örn. 5 dakika).
- Bucket policy'leri default private'tır.

## Presigned URL / Proxy Idea

Tercih sırası:

1. API ve istemci aynı güven alanındaysa **API proxy stream** (satır içi image yanıtı).
2. API ve istemci ayrıysa veya yüksek verim isteniyorsa **presigned redirect** (302).

Hem proxy hem presigned URL, authorization check sonrası üretilir.

## Frontend Display Restrictions

- UI'da national ID sadece masked gösterilir.
- Enrollment sırasında sistem otomatik maskeleme üretir.
- Sorgu sonuçlarında sadece `personId`, masked id, ad soyad ve crop preview URL gösterilir.
- UI logs embeddings veya internal model sonuçlarını konsola yazmaz.

## Demo vs Production Data Rules

| Ortam | Kural |
|---|---|
| Demo | Production verisi kullanılmaz; sentetik veri, kamuya açık LFW gibi veri setleri ile sınırlı. |
| Test | Her test çalıştırması bağımsız; leftover veri temizlenir. |
| Production | National ID gerçek; encryption-at-rest ve audit zorunlu. |
| Lab | Ayrı MinIO/Qdrant/PostgreSQL ise PII kuralları yine geçerlidir. |

## Data Deletion Safety (Assignment)

- `person` soft delete yapılır; bağlı `person_photo` ve `face_sample` satırları da `isActive=false`/soft delete.
- Silinen fotoğrafla birlikte Qdrant payload `isActive=false` güncellenir veya point silinir.
- Phase 1'de hard delete admin/background job ile; önce PostgreSQL iş kaydı kapatılır, sonra MinIO object cleanup yapılır.
- Veri sahibi kurallarına (data subject rights) uygun ileride silme API eklenebilir.

## Embedding Security

- Embedding vektörü, tek başına biyometrik öznitelik olarak kabul edilir.
- Embedding'ler Qdrant dışında depolanmaz.
- API yanıtlarında raw embedding döndürülmez.
- Audit log'da embedding olmaz.

## Summary Table

| Veri | PostgreSQL | Qdrant | MinIO | API response | Audit |
|---|---|---|---|---|---|
| national ID raw | ❌ | ❌ | ❌ | ❌ | ❌ |
| national ID hash | ✅ | ❌ | ❌ | ❌ | ❌ |
| national ID masked | ✅ | ❌ | ❌ | ✅ | ❌ |
| person details | ✅ | ❌ | ❌ | kısıtlı | ❌ |
| image bytes | ❌ | ❌ | ✅ | proxy/presigned | ❌ |
| crop bytes | ❌ | ❌ | ✅ | proxy/presigned | ❌ |
| embedding vector | ❌ | ✅ | ❌ | ❌ | ❌ |
| sampleId/personId refs | ✅ | ✅ | metadata | ✅ | ✅ |
| model metadata | ✅ | ✅ | metadata | ✅ | ✅ |
| action log | ✅ | ❌ | ❌ | ❌ | ✅ |
