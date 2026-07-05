# Demo Kapsamı vs Gelecek Kapsamı

## Demo Kapsamı (MVP)

Bu aşamada aşağıdaki özellikler inşa edilir ve uçtan uca çalışır durumda gösterilir:

- Docker Compose ile sistemi ayağa kaldırma
- PostgreSQL üzerinde kişi, fotoğraf, sample, istek ve audit verilerini saklama
- Qdrant üzerinde yüz embedding vektörlerini saklama ve arama yapma
- MinIO üzerinde orijinal fotoğraf ve yüz crop'larını saklama
- Python 3.11 + FastAPI backend
- React + Vite tabanlı demo UI
- Manuel kişi oluşturma
- Person detail ekranı
- Manuel fotoğraf enrollment (yüz kaydetme)
- Enrolled photo / face crop preview
- Yüklenen sorgu fotoğrafından kişi identification (eşleştirme)
- Multiple face / no face / no match / matched / possible_match UI state'leri
- Qdrant vektör search ile top-K sonuç getirme
- PostgreSQL enrichment ile kişi/fotoğraf bilgilerini zenginleştirme
- `requestId` ile identification traceability
- Identification request history
- Identification request detail
- Audit log minimum düzeyde önemli operasyonlar için

## Demo Helper / Seed Data Notu

Import işi MVP'nin bir ürün özelliği değildir.

- Demo verisi gerekiyorsa basit seed script veya manuel test datası kullanılabilir.
- Bu bir ürün endpoint'i olmak zorunda değildir.
- `import_job` / `import_job_item` tabloları MVP'de yoktur.
- Demo seed işlemi future import mimarisiyle karıştırılmamalıdır.

## Gelecek Kapsamı (Şu An Yapılmayacak)

Bu özellikler mimaride genişleyebilecek şekilde bırakılır ama demo/MVP kapsamında uygulanmaz:

- Demo folder import endpoint'i
- CSV import
- Oracle DB'den veri importu (runtime bağımlılık değil, sadece dış kaynak)
- Async batch importer worker (kuyruk tabanlı toplu işleme)
- Import job tracking (`import_job` / `import_job_item` tabloları)
- Batch error reporting
- 10 milyon+ kayıt ölçeği ve sharding/stratejiler
- Büyük veri migration/import stratejileri
- GPU hızlandırma ve model optimizasyonu
- Face model değişimi/replacement (örn. farklı embedding modeli)
- İleri düzey RBAC ve güvenlik yönetimi
- Üretim seviyesinde şifreleme, KMS ve secret yönetimi
- Canlı video akışı (livefeed) desteği
- Video dosyası işleme ve izleme
- Çok kiracılık (multi-tenancy)
- Coğrafi replikasyon ve yüksek erişilebilirlik

## Senior Scope Kararı

MVP'nin amacı import sistemi yapmak değildir. MVP'nin amacı şu dört akışı uçtan uca çalışır göstermektir:

1. Person kayıt akışı
2. Face photo enrollment akışı
3. Photo-based identification akışı
4. Request traceability/history akışı

Import, Oracle, async worker, 10M ölçek ve GPU optimizasyonu bu demo scope'unu genişletir. Bunlar mimaride future-ready olarak düşünülür ama MVP'de uygulanmaz.
