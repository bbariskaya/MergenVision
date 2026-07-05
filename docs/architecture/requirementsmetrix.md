# Requirements Matrix: MergenVision Mimarisi vs Gereksinimler

> Phase 0 tasarım incelemesi sırasında oluşturulmuştur.  
> Kaynaklar: `requirements/phase1recognitionrequirements.md`, `requirements/phase2videorequirements.md` ve `docs/architecture/` altındaki Phase 0 mimari doküman seti.

## Phase 1 Gereksinimleri (`phase1recognitionrequirements.md`)

| ID | Gereksinim | Mimarideki Karşılığı | Durum | Not / Risk |
|---|---|---|---|---|
| REQ-001 | Oracle Veritabanı Entegrasyonu | Oracle Phase 2/gelecek import kaynağı olarak işaretlendi; runtime source-of-truth PostgreSQL. | ⚠️ Kısmen / Netleştirme gerekli | Gereksinim açıkça Oracle entegrasyonu istiyor. Mevcut mimaride Oracle ertelenmiş. Eğer proje "Oracle'dan canlı okuyacağız" diyorsa ciddi uyumsuzluk var. |
| REQ-002 | 10.000.000 kişilik kayıt kapasitesi | 10M ölçek future boundary; tek mantıksal PostgreSQL/Qdrant/MinIO platformu. | ⚠️ Kısmen | Mimari büyümeye izin verir ama 10M için sharding/partitioning planı henüz yok. |
| REQ-003 | Fotoğraf bazlı yüz tanıma | `/identify`, enrollment akışı ve Qdrant vector search tamamen tasarlandı. | ✅ Karşılanıyor | Diyagramlar ve API contract bu akışı uçtan uca kapsıyor. |
| REQ-004 | Kişi bilgileri (ad, soyad, TC, detay) | `PERSON` tablosunda `firstName`, `lastName`, `nationalIdHash`, `nationalIdMasked`, `details` JSON mevcut. | ✅ Karşılanıyor | `details` JSON ile ek alanlar esnek şekilde eklenebilir. |
| REQ-005 | Kişi-fotoğraf eşleştirme | `identification_result` Qdrant adaylarını `person`, `person_photo`, `face_sample` ile zenginleştirir. | ✅ Karşılanıyor | |
| REQ-006 | Gizlilik ve veri güvenliği | `SENSITIVE_DATA_RULES.md` maskeleme, hash, Qdrant/audit kısıtlamaları ve MinIO erişim politikasını tanımlar. | ✅ Karşılanıyor | Güçlü PII kontrolleri var. |
| REQ-007 | Ölçeklenebilirlik | Stateless API replikaları, GPU demo topolojisi, batch-ready tasarım, adapter boundary. | ⚠️ Kısmen | Orta ölçek için uygun; 10M+ ve yüksek concurrency için ek önlem gerekir. |

## Phase 2 Video Gereksinimleri (`phase2videorequirements.md`)

| Bölüm | Gereksinim | Mimarideki Karşılığı | Durum | Not / Risk |
|---|---|---|---|---|
| 1 | Video upload (`POST /videos/recognize`) | `/videos/*` future boundary; `video_job` tablosu planlandı. | ✅ Kavram olarak karşılanıyor | Endpoint isimleri tam uyuşmuyor ama kavram mevcut. |
| 1 | Video format/boyut doğrulama | Mimariye detaylı olarak işlenmemiş. | ⚠️ Eksik detay | Format, boyut, süre limitleri ve env-driven doğrulama eklenmeli. |
| 1 | Video retention / yapılandırılabilir saklama | MinIO prefix'ler belirtildi; lifecycle policy detaylanmadı. | ⚠️ Kısmen | Retention env var'ları ve temizlik politikası eklenmeli. |
| 1 | Job/process ID erişimi | Identify için `requestId` izlenebilirliği var; video için `video_job` planlandı. | ✅ Karşılanıyor | |
| 2 | Frame sampling / timestamp | Belirtilmiş ama detaylı değil. | ⚠️ Kısmen | `processedFrames`, `samplingRate`, `timestamp`, `frameNumber` alanları eklenmeli. |
| 3 | Face tracking + trackId | `video_track` tablosu var; ayrı `Tracker` abstraction yok. | ⚠️ Kısmen | `Tracker` boundary ve `trackId` semantiği veri modeline eklenmeli. |
| 4 | known / anonymous / new_anonymous | **Modelde yok.** `person` sadece known kişileri kapsar. | ❌ Eksik | Phase 2 kalıcı anonim kimlikler istiyor. `face_identity` veya `anonymous_face` tablosu gerekir. |
| 4 | Sonuç toplama (firstSeen, lastSeen, totalDuration, appearances) | `video_track` ve `face_video_appearance` planlandı; alanlar detaylanmadı. | ⚠️ Kısmen | appearances ve duration alanları şemaya eklenmeli. |
| 5 | Orijinal çözünürlüğe göre bounding box | Detaylandırılmamış. | ❌ Eksik | Video pipeline'ına koordinat dönüşüm katmanı eklenmeli. |
| 6 | Async job / durum / iptal | Async job kuyruğu planlandı; iptal mekanizması belirtilmedi. | ⚠️ Kısmen | `DELETE /videos/jobs/{jobId}` ve cancellation state machine eklenmeli. |
| 7 | Process logging / metadata | Audit log var; video özel metadata detaylanmadı. | ⚠️ Kısmen | `video_job`'a video metadata alanları eklenmeli. |
| 8 | Yüz görünüm sorgusu (`GET /faces/{faceId}/appearances`) | `/faces/*` Phase 1'de reddedildi; Phase 2 için yeniden açılmadı. | ❌ Eksik | Phase 2'de anonim/tanınmış yüz geçmişi için `/faces` endpoint'leri gerekir. |
| 9 | Sadece API, UI yok | Mimari isteğe bağlı React demo/admin UI içeriyor. | ⚠️ Çelişki | Gereksinim "herhangi bir kullanıcı arayüzü olmayacak" diyor. UI sadece demo/adminTool olarak kalmalı. |
| 10 | Örnek endpoint'ler | `/videos/*` genel endpoint'ler planlandı; tam path'ler farklı. | ⚠️ Kısmen | Gereksinimler bağlayıcı hale gelirse endpoint isimleri hizalanmalı. |
| 11 | Sonuç içeriği (faceId, trackId, status, name, appearances, detections) | Sonuç şekli detaylanmadı. | ⚠️ Kısmen | Örnek response'a uygun result şeması eklenmeli. |
| 13 | Paralel/batch frame işleme | Batch-ready tasarım ve worker kuyruğu planlandı. | ✅ Karşılanıyor | |
| 13 | Yapılandırılabilir concurrency / timeout / limitler | Detaylanmadı. | ⚠️ Eksik | Env-driven worker limitleri eklenmeli. |
| 14 | Docker deployment / ayrı worker servisi | Docker Compose ertelendi; worker servis kavramı var. | ⚠️ Kısmen | Phase 2'de worker image API image'ından ayrılmalı. |

## Kapsam Büyüdükçe Sorun Çıkarabilecek Yerler

| Risk | Mevcut Durum | Önerilen Çözüm |
|---|---|---|
| Anonim yüz modeli eksik | `person` sadece known kişileri modelleyebilir | `face_identity` tablosu ekle: `identityType` enum `known`, `anonymous`, `new_anonymous` |
| `/faces/*` API eksik | Phase 1'de reddedildi | Phase 2 için `/faces/{faceId}` ve `/faces/{faceId}/appearances` ekle |
| 10M ölçek ele alınmamış | Tek node mantıksal platform | PostgreSQL partition, Qdrant sharding, read replica, object storage scaling planı ekle |
| Audit log yazma yükü | Audit aynı PostgreSQL'de | `audit_log` tablosunu erken partition'la veya async log stream'e (Kafka vb.) taşı |
| Qdrant koleksiyon patlaması | Her model/dimension/version için ayrı koleksiyon | Aynı dimension içinde versiyonlar payload farkıyla tek koleksiyonda kalsın; yeni koleksiyon sadece dimension değişince açılsın |
| Video işleme API ile aynı container'da | `api-gpu-N` demo topolojisinde HTTP ve inference beraber | Phase 2'de `worker-gpu` ayrı container/image olsun; API sadece submit/sorgu yapsın |
| Medya proxy I/O darboğazı | API image stream proxyleyebilir | Production'da presigned redirect (302) kullan; proxy sadece yetki kontrolü için |
| Oracle kapsamı belirsiz | Oracle ertelendi | Oracle one-time import mu yoksa canlı okuma bağımlılığı mı? netleştir |
| UI/API çelişkisi | İsteğe bağlı React UI var | UI kesinlikle demo/adminTool sınırlı kalmalı; nihai ürün API-only olmalı |
| Video bbox koordinat dönüşümü | Modelde yok | `video_processing_scale` metadata ile orijinal çözünürlüğe geri dönüşüm yap |
| Job iptali | Modelde yok | `cancelling`/`cancelled` durumları ve worker iptal mekanizması ekle |

## Bloklayıcı Maddeler (Implementasyon Öncesi Çözülmeli)

Aşağıdaki konular Phase 1 implementasyonuna başlamadan çözülmeli; aksi halde geriye dönük düzeltmesi pahalı olur:

1. **REQ-001 Oracle kapsamı** — Oracle one-time import kaynağı mı, yoksa canlı okuma bağımlılığı mı?
2. **REQ-002 10M ölçek beklentisi** — Phase 1 hedefi mi, yoksa gelecek production hedefi mi?
3. **REQ-009 UI/API çelişkisi** — Demo/admin UI izinli mi, yoksa ürün tamamen API-only mı?
4. **Phase 2 anonim yüz modeli** — Ertelense bile `person` tablosu anonim kimlikler eklendiğinde kırılmadan evrilebilmeli.

## Öneri

Phase 0B model doğrulamasına ve Phase 1 planlamaya geçmeden önce:

- Oracle, 10M ölçek ve UI konularını paydaşlarla netleştir.
- `DATA_MODEL.md`, `API_CONTRACT.md` ve `FUTURE_BOUNDARIES.md` dokümanlarını anonim yüz ve `/faces/*` endpoint'lerini kapsayacak şekilde güncelle.
- `PHASE_0_ARCHITECTURE_PLAN.md` içine single-node'dan sharded deployment'a geçiş yol haritası ekle.
