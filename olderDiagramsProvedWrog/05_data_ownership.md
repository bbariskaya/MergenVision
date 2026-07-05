# Veri Sahipliği / Saklama Sorumluluğu

Bu doküman, `person-face-identification-demo` sistemindeki verilerin hangi bileşende tutulduğunu ve neden öyle tutulduğunu açıklar.

- **PostgreSQL:** source-of-truth business database’tir. Kişi, fotoğraf metadata, sample metadata, istek geçmişi, sonuç geçmişi, import durumu ve audit log burada tutulur.
- **Qdrant:** source-of-truth değildir; sadece yüz embedding vektörlerinin arandığı vector search index’tir.
- **MinIO:** database değildir; sadece orijinal fotoğraflar, yüz crop’ları ve opsiyonel sorgu görsellerinin saklandığı object storage’dır.
- Sistem bileşenleri birbirine `personId`, `photoId`, `sampleId`, `qdrantPointId`, `imageKey`, `requestId`, `queryFaceId`, `resultId` gibi referans ID’lerle bağlanır.

| Veri Tipi | Örnek | Saklandığı Yer | Neden | İlişkili ID'ler |
|---|---|---|---|---|
| Temel kişi detayları | `firstName`, `lastName`, `birthDate`, `gender`, `department`, `title`, `organization` | PostgreSQL `person` | İlişkisel iş verisi, sorgulanabilirlik, bütünlük | `personId`, `externalPersonId` |
| Esnek kişi detayları | telefon, adres, sicil no, kart no, müşteri özel alanları, notlar | PostgreSQL `person.details` JSONB | Müşteri domain'ine göre değişebilen kişi detaylarını esnek tutmak için | `personId` |
| Hassas kimlik alanları | `national_id_hash`, `national_id_encrypted`, `national_id_masked` | PostgreSQL `person` | Hash duplicate/lookup için; encrypted yetkili production erişimi için; masked UI gösterimi için | `personId` |
| Orijinal kayıtlı fotoğraf | JPEG/PNG dosyası | MinIO | Büyük binary veriler ayrı object store'da | `imageKey` → `person_photo.image_key` |
| Yüz crop'u | kırpılmış yüz görüntüsü | MinIO | Görsel gösterim ve trace için | `cropImageKey` → `face_sample.crop_image_key` |
| Yüz embedding | 512 boyutlu float vektör | Qdrant | Benzerlik araması için özel vektör DB | `qdrantPointId` ↔ `face_sample.qdrant_point_id` |
| Qdrant vektör payload | `sampleId`, `personId`, `photoId`, `sourceSystem`, `externalPersonId`, `modelName`, `modelVersion`, `isActive`, `qualityScore`, `createdAt` | Qdrant | Arama sonuçlarını PostgreSQL ile birleştirmek için minimal referans payload | `personId`, `photoId`, `sampleId` |
| Sorgu yüklenen görüntü | kullanıcının identify için yüklediği fotoğraf | MinIO, opsiyonel / kısa süreli | Query image biyometrik / hassas veri olabilir; saklama davranışı konfigüre edilebilir olmalı | `requestId`, `inputImageKey` → `identification_request.input_image_key` |
| Sorgu yüz crop'u | identify fotoğrafından kırpılmış seçili yüz | MinIO, opsiyonel / kısa süreli | Debug, UI preview veya trace için; biyometrik veri sayılır | `queryFaceId`, `cropImageKey` |
| Identification isteği | işlem metadata, durum | PostgreSQL `identification_request` | Traceability ve geçmiş | `requestId` |
| Sorguda tespit edilen yüz | bounding box, detection confidence, quality score | PostgreSQL `identification_query_face` | Hangi yüzün arandığı bilgisi | `queryFaceId` → `requestId` |
| Identification sonucu | benzerlik skoru, karar, sıralama | PostgreSQL `identification_result` | Kalıcı sonuç geçmişi | `resultId`, `requestId`, `queryFaceId`, `personId?`, `photoId?`, `sampleId?` |
| Audit log | kim, ne zaman, hangi entity üzerinde ne yaptı | PostgreSQL `audit_log` | Güvenlik ve geriye dönük izleme | `auditId`, `entityType`, `entityId`, `requestId?` |
| Import işi | demo klasörü, CSV, future Oracle import source | PostgreSQL `import_job`, `import_job_item` | Toplu iş durumu ve hata takibi; Oracle sadece future external source | `importJobId`, `itemId` |

## Hassas Veri Kuralları

- **Raw national ID**, response'ta dönmez.
- **Raw national ID**, audit log'a yazılmaz.
- **Raw / masked / encrypted national ID**, Qdrant payload'ına yazılmaz.
- **Tam `person.details` JSON'u** Qdrant payload'ına kopyalanmaz.
- **Tam `person.details` JSON'u** audit log'a yazılmaz.
- **Raw image bytes**, embedding vector veya full face crop**, audit log'a yazılmaz.
- Audit log sadece referans ID'ler, action, entity type, entity ID, request ID ve güvenli özet metadata tutar.

## Önemli Kurallar

- **PostgreSQL:** business source-of-truth; kişi, fotoğraf metadata, sample metadata, request history, result history, import status ve audit log burada tutulur.
- **Qdrant:** primary vector search engine; embedding vector + minimal reference payload tutar. Business source-of-truth değildir.
- **MinIO:** object storage; orijinal fotoğraflar, yüz crop'ları ve opsiyonel query images burada tutulur. Metadata PostgreSQL'dedir.
- **Sensitive data:** raw national ID, full `person.details`, telefon/adres gibi hassas alanlar Qdrant payload'ına veya audit log'a kopyalanmaz.
- **Traceability:** identify akışında `requestId`, query face için `queryFaceId`, result için `resultId` kullanılır.
- **Retention:** query image ve query face crop gibi hassas geçici veriler için retention policy gerekir.

## `person.details` Notu

- `person.details`, müşteri tarafından tanımlanabilecek esnek bir JSONB alanıdır.
- Backend bu alanın içeriğini önceden bilmez, sadece JSON object olmasını doğrular.
- UI demo için bu alanı JSON/key-value viewer-editor olarak gösterebilir.
- Demo ortamında gösterilebilir; production'da allowlist/masking gerekir.

## Qdrant Payload Notu

- Qdrant payload yalnızca PostgreSQL'e geri dönmek için gereken referans ID'leri taşımalıdır.
- `fullName` demo kolaylığı için eklenebilir, ama senior recommendation referans-only payload'dır; kişi detayları PostgreSQL enrichment ile alınmalıdır.
- Şunlar Qdrant payload'ında olmamalıdır: raw/masked/encrypted national ID, doğum tarihi, telefon, adres, `person.details`, diğer hassas business detaylar.
