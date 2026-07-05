# Riskler ve Açık Sorular

## Senior Scope Notu

MVP’nin amacı import sistemi, Oracle entegrasyonu, 10M scale, GPU optimizasyonu veya video/livefeed yapmak değildir.

MVP’nin amacı şu akışları uçtan uca çalışır göstermektir:

- Manuel kişi oluşturma
- Kişiye fotoğraf enroll etme
- Query fotoğraf ile identification
- Top-K sonuçları gösterme
- `requestId` ile identification history/detail izlenebilirliği
- Temel audit log

Import, Oracle, async worker, GPU, 10M scale ve video/livefeed future scope’tur.

## Ana MVP Riskleri

| Risk | Açıklama | Etki | MVP Kararı / Azaltma |
|---|---|---|---|
| Model doğruluğu | Demo veri setinde çalışması production başarımı garanti etmez. Farklı ışık, yaş, kamera, poz, kalite koşulları sonucu etkiler. | Yüksek | Demo veri setiyle hızlı POC yapılır. Threshold değerleri config üzerinden yönetilir. UI’da score ve decision açık gösterilir. Production accuracy claim yapılmaz. |
| False positive / yanlış kişi eşleşmesi | Yanlış kişiyi yüksek confidence ile eşleştirmek en kritik ürün risklerinden biridir. | Yüksek | `matched`, `possible_match`, `no_match` ayrımı yapılır. Score kullanıcıya gösterilir. Eşik altındaki sonuçlar kesin eşleşme gibi sunulmaz. Demo UI’da “possible match” açık gösterilir. |
| Model lisansı | Kütüphane lisansı, model ağırlığı lisansı ve dataset lisansı ayrı olabilir. | Yüksek | Demo için kullanılabilir adapter soyutlanır. Production öncesi kullanılan model/package/weight lisansları hukuk/ürün tarafında doğrulanmalıdır. FacePipeline adapter tasarımı model değişimini kolaylaştırmalıdır. |
| Threshold ayarı | Düşük threshold false positive artırır. Yüksek threshold false negative artırır. | Yüksek | `match_threshold`, `possible_match_threshold`, `top_k` config/env ile yönetilir. Değerler hardcode edilmez. Demo datasına göre ayarlanabilir. |
| Birden fazla sample | Aynı kişiye ait çok sayıda sample Qdrant top-K sonuçlarında tekrar edebilir. | Orta | Backend Qdrant raw sample sonuçlarını PostgreSQL ile enrich eder. UI’da alternatifler person bazında anlaşılır gösterilir. Mümkünse aynı person için en iyi sample öne çıkarılır. Full advanced grouping future optimization olabilir. |
| Duplicate kişi | Aynı kişi farklı external ID veya manuel girişlerle tekrar kaydedilebilir. | Orta | `external_person_id + source_system` varsa duplicate kontrolü yapılır. `national_id_hash` varsa duplicate kontrol için kullanılabilir. Face-based duplicate person detection future scope’tur. |
| Görüntü kalitesi | Düşük çözünürlük, küçük yüz, blur, yanlış poz, düşük detection confidence sonucu etkiler. | Orta | Minimum image validation yapılır. Detection confidence ve face bounding box size kontrol edilir. Aşırı düşük kalite için `low_quality` veya validation error dönebilir. Advanced blur/pose quality future scope olabilir. |
| Veri gizliliği / biyometrik veri | Fotoğraflar, face crop’lar ve embeddings biyometrik/hassas veri kabul edilebilir. National ID ve `person.details` hassas veri içerebilir. | Yüksek | Gerçek kişi verisi kullanılmaz; synthetic/fake demo verisi kullanılır. Raw national ID response’ta, Qdrant payload’da veya audit log’da yer almaz. `person.details` Qdrant payload’a veya audit log’a komple kopyalanmaz. Query image/crop saklama opsiyonel ve retention gerektiren bir karardır. |
| Query image retention | Identify için yüklenen query image ve query crop hassas/biyometrik veri olabilir. | Yüksek | `identification_request.input_image_key` nullable olur. Varsayılan olarak query image saklama kapalı veya kısa süreli olabilir. Saklanırsa MinIO’da retention policy ile tutulur. Production’da encryption/access control/audit gerekir. |
| PostgreSQL-Qdrant-MinIO consistency | MinIO upload başarılı olup DB veya Qdrant işlemi hata verebilir. Qdrant upsert başarılı olup DB update hata verebilir. Orphan object veya orphan vector oluşabilir. | Orta | DB transaction kullanılır. `face_sample.is_indexed=false` olarak oluşturulur, Qdrant upsert sonrası true yapılır. Hata durumunda best-effort MinIO cleanup denenir. Reconciliation/repair job future scope olabilir. |
| Soft delete / vector lifecycle | Person/photo silindiğinde Qdrant point’lerinin nasıl yönetileceği net olmalı. | Orta | PostgreSQL’de soft delete / inactive state tutulur. Qdrant payload’da `isActive=false` güncellenir veya point silinir. MVP için güvenli yaklaşım: search filter `isActive=true` kullanmak. Hard delete / GDPR-style purge future production policy olarak ele alınır. |
| Qdrant ölçeklendirme | Sample sayısı arttıkça vector collection büyür. | Orta | Tek collection: `face_embeddings`. Vector size: 512. Distance: Cosine. Sharding/replication/quantization future scope. |
| UI demo karmaşıklığı | Create person, enroll photo, identify photo, multiple face states, no match states ve history/detail ekranları aynı demo UI’da yönetilecek. | Orta | Önce happy path UI yapılır. Sonra no_face / multiple_faces / no_match / low_quality state’leri eklenir. Import UI core MVP değildir. |
| Docker kaynak gereksinimleri | Face model loading, API, Qdrant, MinIO, PostgreSQL aynı makinede RAM/CPU kullanır. Model cold start gecikmesi olabilir. | Orta | CPU-only demo varsayılır. Model warmup yapılabilir. Docker Compose servisleri sade tutulur. GPU future scope’tur. |
| Model cold start / dependency download | İlk inference sırasında model indirme/yükleme gecikmesi demo akışını bozabilir. | Orta | Model cache path belirlenir. API startup veya first request sırasında warmup stratejisi düşünülür. Demo öncesi model dosyaları hazır hale getirilir. |

## Future Scope Riskleri

Aşağıdakiler MVP’nin ana riskleri değil, gelecekte ele alınacak risklerdir:

- Oracle import riski
- CSV/demo-folder bulk import riski
- Async importer worker riski
- Import job tracking riski
- 10M+ kayıt ölçeği ve Qdrant sharding/replication riski
- GPU acceleration ve model optimizasyon riski
- Model replacement / ONNX / TensorRT geçiş riski
- Production RBAC ve yetkilendirme riski
- KMS/secret management riski
- Multi-tenancy riski
- Video/livefeed/RTSP riskleri
- Büyük veri migration/import stratejisi riskleri

## Kodlamadan Önce Kapatılan Kararlar

### National ID stratejisi

- `national_id_hash`
- `national_id_encrypted` optional/future production
- `national_id_masked`
- Demo’da gerçek national ID kullanılmaz.
- Raw national ID response, Qdrant payload veya audit log içinde dönmez.

### topK

- Default `topK=5`
- Config veya request ile değiştirilebilir.
- Maksimum limit backend tarafından sınırlandırılır.

### Threshold

- `match_threshold` ve `possible_match_threshold` config/env üzerinden yönetilir.
- Demo datasına göre ayarlanır.
- Hardcode edilmez.

### Enrollment crop saklama

- Enrollment face crop MinIO’da saklanır.
- Çünkü Person Detail ve audit/debug için faydalıdır.
- Metadata PostgreSQL’de `face_sample.crop_image_key` ile tutulur.

### Query image saklama

- Query image saklama opsiyoneldir.
- `input_image_key` nullable olur.
- Demo’da kapalı veya kısa retention ile açık olabilir.
- Production’da retention/access/encryption policy gerekir.

### Import demo

- MVP core feature değildir.
- `POST /imports/demo-folder`, async worker, import job tracking MVP dışında kalır.
- Demo data gerekiyorsa seed script veya manuel giriş kullanılabilir.

### Model seçimi

- MVP’de mevcut çalışan FacePipeline adapter yaklaşımı kullanılır.
- Model detayları adapter arkasına saklanır.
- Production’da model/lisans/accuracy tekrar değerlendirilir.

### Çoklu yüz davranışı

- Identify akışında multiple face varsa UI kullanıcıya yüz seçtirir.
- Varsayılan olarak otomatik en güvenilir yüzü seçme MVP’de riskli olabilir.
- `selectedFaceIndex` ile tekrar identify çalışabilir.

### Soft delete politikası

- PostgreSQL soft delete/inactive state kullanılır.
- Qdrant search payload filter `isActive=true` kullanılır.
- Gerekiyorsa Qdrant point payload update edilir.
- Hard delete/purge future production policy’dir.

### Audit log detayı

- MVP’de write operations audit edilir:
  - person created
  - person updated/deleted
  - photo enrolled
  - photo deleted/deactivated
  - identification completed summary
- Read audit future scope olabilir.
- Audit log raw national ID, image bytes, embedding vector veya full `person.details` içermez.

## Hâlâ İnsan Onayı Gerektiren Sorular

1. Demo için query image retention açık mı kapalı mı olacak?
2. Demo için kullanılacak synthetic dataset nasıl hazırlanacak?
3. UI’da `person.details` tamamen mi gösterilecek, yoksa sadece allowlist örnek alanlar mı gösterilecek?
4. Demo öncesi kabul edilebilir minimum accuracy/success kriteri nedir?
5. Demo makinesinin RAM/CPU limitleri nedir?

## Final Senior Recommendation

MVP için riskleri azaltmanın en iyi yolu scope’u küçük tutmaktır.

Önerilen uygulama sırası:

1. Docker Compose + healthcheck
2. PostgreSQL schema
3. MinIO storage adapter
4. Qdrant vector adapter
5. FacePipeline adapter
6. Person create/list/detail
7. Photo enrollment
8. Identify photo
9. Request history/detail
10. Minimal audit log
11. UI polish and demo states

Import, Oracle, GPU, video/livefeed ve 10M scale bu sıraya dahil edilmemelidir.
