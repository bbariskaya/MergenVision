# Sistem Amacı

## Demo Veri Uyarısı

> **Demo ortamında gerçek T.C. kimlik numarası, gerçek yüz görüntüsü veya gerçek kişi verisi kullanılmamalıdır. Demo için sentetik/sahte veriler ve test fotoğrafları kullanılmalıdır.**

## Sistem Ne Yapar?

Bu sistem, kayıtlı kişi fotoğraflarından bir yüz embedding arşivi oluşturan, yeni yüklenen bir fotoğraftaki yüzü bu arşivde arayan, en yakın eşleşen kişiyi ve alternatif adayları kullanıcıya gösteren, bu arama işlemini sonradan incelenebilir şekilde kaydeden **photo-based person identification** sistemidir.

Sistemin dört ana amacı vardır:

1. Kişileri business metadata ile kaydetmek.
2. Her kişiye ait yüz fotoğraflarını enroll ederek vektör temsillerini saklamak.
3. Yeni bir sorgu fotoğrafındaki yüzü, kayıtlı vektörler arasında aramak.
4. Her identification işlemini kalıcı ve traceable olarak kaydetmek.

## Temel Kavramlar

### Person Creation

Person creation, bir kişinin business/person metadata ile sisteme kaydedilmesi işlemidir. Bu işlem:

- `person` tablosuna satır ekler.
- Kişinin ad, soyad, departman, unvan, kurum gibi bilgilerini tutar.
- Fotoğraf işlemez.
- Face detection yapmaz.
- Embedding çıkarmaz.
- Qdrant’a hiçbir şey yazmaz.
- MinIO’ya fotoğraf yüklemez.

Kişi oluşturulduğunda sistemde bir `personId` sahibi olur; bu kişiye daha sonra fotoğraf enroll edilebilir. Opsiyonel olarak ileride "create person with first photo" tarzında birleşik bir endpoint yapılabilir, ama MVP mental modelinde bu iki ayrı operasyondur.

### Photo Enrollment

Photo enrollment, var olan bir `personId` için fotoğraf yükleyip o fotoğraftaki yüzü sisteme kaydetme işlemidir. Bu işlem:

- Var olan kişiye fotoğraf ekler.
- Görüntüyü doğrular (format, boyut, okunabilirlik).
- Görüntüde tam olarak bir kullanılabilir yüz arar.
- Yüzü crop eder.
- Embedding çıkarır.
- Orijinal fotoğrafı MinIO’ya kaydeder.
- Face crop’u MinIO’ya kaydeder.
- PostgreSQL’de `person_photo` satırı oluşturur.
- PostgreSQL’de `face_sample` satırı oluşturur.
- Qdrant’a embedding vector yazar.
- `face_sample.qdrant_point_id`, Qdrant point ID ile aynı olur.

Özetle:

- Person creation sırasında `person` satırı oluşur.
- Photo enrollment sırasında `person_photo` ve `face_sample` satırları oluşur.

### Face Sample

`face_sample`, bir fotoğraftan çıkarılmış tek bir yüz temsilidir. Bir sample şunları içerir:

- `sampleId`
- `personId`
- `photoId`
- `qdrantPointId`
- Model adı ve versiyonu
- Crop görüntü key'i
- Bounding box
- Detection güven skoru
- Kalite skoru
- Embedding boyutu

Her fotoğraf tek bir kullanılabilir yüz içermelidir. Çoklu yüz durumunda enrollment reddedilir.

### Identification / Search

Identification, kullanıcının yüklediği sorgu fotoğrafındaki yüzü, sistemdeki kayıtlı sample’larla karşılaştırarak en yakın kişiyi/eşleşmeyi bulma işlemidir.

Adımlar:

1. Sorgu fotoğrafı yüklenir.
2. `identification_request` satırı oluşturulur (`status=pending`).
3. Yüz(ler) tespit edilir.
4. Her tespit edilen yüz için `identification_query_face` satırları oluşturulur.
5. Seçilen yüz için embedding vektörü çıkarılır.
6. Qdrant’ta en yakın `topK` vektör aranır.
7. Qdrant sonuçlarından `personId`, `photoId`, `sampleId` değerleri alınır.
8. PostgreSQL’den kişi ve fotoğraf detayları zenginleştirilir.
9. MinIO’dan geçici indirme URL’leri üretilir.
10. Adaylar `identification_result` tablosunda saklanır.
11. `identification_request` başarılı olarak güncellenir.
12. Kullanıcıya en iyi eşleşme, benzerlik skoru, bounding box, kişi detayları ve `requestId` döner.

### Traceability

Identification traceability:

- Her identify işlemi için `identification_request` satırı oluşur.
- Tespit edilen her query face için `identification_query_face` satırı oluşur.
- Top-k adaylar için `identification_result` satırları oluşur.
- API response mutlaka `requestId` döner.
- Hata olsa bile mümkünse `requestId`, `errorCode` ve `errorMessage` saklanır.
- Eski aramalar `GET /identification-requests/{requestId}` ile tekrar incelenebilir.

Operational audit:

- Person create, photo enrollment, import, delete/update gibi operasyonlar `audit_log` ile izlenir.
- Photo enrollment response en az `personId`, `photoId`, `sampleId` döndürmelidir.
- İleride eski projedeki generic process logging mantığına benzer `operation_log` eklenebilir.
- MVP için identification history tabloları + `audit_log` yeterlidir.

## Neden Bir Kişiye Birden Fazla Fotoğraf Gerekir?

Bir kişinin farklı açılardan, ışık koşullarında, yaş gruplarından ya da pozlardan çekilmiş fotoğrafları olabilir. Her fotoğraf farklı bir yüz sample’ı üretir. Birden fazla sample:

- Tanıma doğruluğunu artırır.
- Modelin farklı koşullara karşı dayanıklılığını sağlar.
- Kişi bazında zengin bir vektör temsilinin oluşmasına yardımcı olur.

Her fotoğraf yine de **tek bir** kullanılabilir yüz içerecek şekilde kısıtlanmıştır.

## Sorgu Fotoğrafı Yüklendiğinde Ne Olur?

- API hemen bir `identification_request` kaydı oluşturur (`status=pending`).
- Görüntü doğrulanır.
- Yüz tespiti yapılır.
  - 0 yüz: `no_face`
  - Birden fazla yüz ve seçim yapılmamışsa: `multiple_faces` / yüz seçimi istenir
  - Tek yüz veya seçilmiş yüz: embedding çıkarılır, Qdrant aranır, sonuçlar zenginleştirilir.
- Tespit edilen her yüz `identification_query_face` olarak kaydedilir.
- Aday eşleşmeler `identification_result` olarak kaydedilir.
- Her adım `requestId` ile izlenebilir.
- Sonuçlar kalıcı olarak saklanır; sonradan `GET /identification-requests/{requestId}` ile sorgulanabilir.

## PostgreSQL'de Ne Saklanır?

- Kişi iş/business verileri (`person`)
- Fotoğraf metadata'sı (`person_photo`)
- Yüz sample metadata'sı (`face_sample`)
- Identification istek geçmişi (`identification_request`)
- Identification sonuçları (`identification_result`)
- Sorgu fotoğrafındaki tespit edilen yüzler (`identification_query_face`)
- Import işleri (`import_job`, `import_job_item`)
- Audit log (`audit_log`)

`person.details` alanı da PostgreSQL’de saklanır; bu alanın rolü için aşağıdaki bölüme bakın.

## Qdrant'ta Ne Saklanır?

Asıl saklanan şey:

- Yüz embedding vektörleri

Qdrant payload sadece PostgreSQL’e geri dönmek için gereken referansları taşır:

- `sampleId`
- `personId`
- `photoId`
- `sourceSystem`
- `externalPersonId`
- `modelName`
- `modelVersion`
- `isActive`
- `qualityScore`
- `createdAt`

Qdrant payload’a şunlar yazılmamalıdır:

- raw national ID
- masked national ID
- encrypted national ID
- telefon
- adres
- `person.details`
- doğum tarihi
- kişi hakkında hassas business detaylar

`fullName` hakkında not:

- Demo kolaylığı için payload’a konabilir.
- Senior recommendation: `fullName` bile PostgreSQL enrichment ile alınmalı; Qdrant payload mümkün olduğunca referans-only kalmalı.

## MinIO'da Ne Saklanır?

- Orijinal yüklenen fotoğraflar (`person_photo.image_key` ile referanslanır).
- Yüz crop’ları (`face_sample.crop_image_key` ile referanslanır).
- Query image: varsayılan olarak saklanmayabilir. Saklanacaksa `identification_request.input_image_key` üzerinden nullable olarak referanslanır.
- Query face crop’u da aynı şekilde hassas veri kabul edilmelidir.

Query image saklama davranışı konfigüre edilebilir olmalıdır. Demo için query image saklama opsiyoneldir. Production için retention policy, encryption, access control ve audit gerekir.

## `person.details` Alanının Rolü

`person.details`, müşteri tarafından tanımlanabilecek esnek bir JSONB alanıdır. Bu alan müşteri sisteminden gelen veya manuel girilen ek kişi detaylarını tutar.

Örnek içerikler (zorunlu kolon değildir):

- telefon
- adres
- sicil numarası
- kart numarası
- kurum içi özel kodlar
- notlar
- departman detayları
- müşteri domain’ine özel başka alanlar

Backend sorumlulukları:

- `person.details` alanının JSON object olmasını doğrular.
- Bu alanın içindeki özel field’lara business logic bağlamaz.
- Bu alanı Qdrant payload’a komple kopyalamaz.
- Bu alanı audit log’a komple yazmaz.
- Identification response içinde dönmesini kontrollü şekilde yönetir.

UI demo için bu alanı JSON/key-value viewer-editor olarak gösterebilir. Demo ortamında gösterilebilir; production’da allowlist/masking gerekir.

## Identification Response İçinde Hangi Kişi Bilgileri Döner?

Dönebilecek temel alanlar:

- `personId`
- `firstName`
- `lastName`
- `fullName`
- `nationalIdMasked`
- `department`
- `title`
- `organization`

Opsiyonel:

- `details`

`details` hakkında not:

- Demo ortamında `details` gösterilebilir.
- Production’da `details` içinden hangi alanların döneceği allowlist ile sınırlandırılmalıdır.
- Çünkü `details` içinde telefon, adres veya başka hassas veri olabilir.

## Sistem Henüz Ne Yapmaz?

- Video işlemez.
- Canlı akış (livefeed) desteklemez.
- RTSP/camera stream işlemez.
- Oracle’a runtime bağımlı değildir.
- Oracle sadece ileride import kaynağı olabilir.
- 10 milyon+ production scale bu demo scope’unun dışındadır; mimari buna hazırlanabilir ama MVP değildir.
- Production-grade KMS/RBAC/multi-tenancy demo scope’unda değildir.
