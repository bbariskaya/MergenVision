# Old Diagrams Lessons Learned

`olderDiagramsProvedWrog/` dizinindeki eski Phase 8/9 diyagramları ve raporları, MergenVision Phase 0 mimarisine girdi olarak kullanıldı. Bazı fikirler korundu, bazıları güncellendi, bazıları reddedildi.

## Keep / Update / Reject Table

| Old idea / doc | Keep | Update | Reject | Reason | MergenVision decision |
|---|---|---|---|---|---|
| FacePipeline abstraction | ✅ | — | — | detect/align/recognize ayrımı model değişimine izin verir. | `DetectorAdapter`, `RecognizerAdapter`, `AlignerPreprocessor` boundary olarak benimsendi. |
| Postgres / Qdrant / MinIO ayrımı | ✅ | — | — | Veri sahipliği netliği sağlar; hassas veriyi doğru yere koyar. | `DATA_MODEL.md` ve `SENSITIVE_DATA_RULES.md`'de güçlendirildi. |
| `requestId` / `processId` traceability | ✅ | — | — | Her isteğin izlenebilirliği gerekli. | `identification_request` her `/identify` çağrısında oluşturulur; audit log her交易'e yazılır. |
| `api-lb` + GPU replikalar | ✅ | — | — | Çoklu GPU demo modu için doğru pattern. | `RUNTIME_TOPOLOGY.md`'de nginx + api-gpu-N olarak uygulanacak. |
| Root-level API endpoint map | ✅ | — | — | Eski `10_api_map.md`'deki temel photo/identify endpoint'leri doğruydu. | `API_CONTRACT.md`'de root-level API kararı benimsendi. |
| InsightFace runtime bağımlılığı | — | ✅ | — | Ağırlıkları indirmek uygun, runtime bağımlılığı riskli. | ONNX Runtime + adapter bridge'ine dönüştürüldü. |
| YuNet/SFace fallback | ✅ | — | — | Phase 2 kalitesi düşerse geri dönüş seçeneği. | `MODEL_ADAPTER_BOUNDARY.md`'de fallback olarak eklendi. |
| Connected/known identity only | ✅ | — | — | Anonymous yüz kimlikleri Phase 1 gereksinim değil. | Kişi merkezli model; anonim identity yok. |
| Soft delete / `isActive` | ✅ | — | — | Veri kaybı riskini azaltır, silinen sample'ların Qdrant index'inden çıkarılmasını sağlar. | Tüm iş tablolarında soft delete; Qdrant payload'ında `isActive` filtresi. |
| National ID masking | ✅ | — | — | PII kısıtlaması. | `nationalIdMasked` + `nationalIdHash`; raw değer PostgreSQL dışına çıkmaz. |
| Fake default pipeline | — | — | ✅ | Sahte varsayılan pipeline test dışında kabul edilemez. | ADR-012: production/runtime pipeline test dışında sahte olamaz. |
| Hardcoded GPU UUID / device index in Python | — | — | ✅ | Kod GPU UUID bilmemeli; sabitleme sadece Compose/orchestrator'da. | `RUNTIME_TOPOLOGY.md` GPU UUID policy. |
| Import endpoint'lerinin Phase 1'e sızması | — | — | ✅ | Phase 1 manuel enrollment ile sınırlı; import future. | `/imports/*` future boundary olarak işaretlendi. |
| Video / RTSP'nin Phase 1'de yapılması | — | — | ✅ | Phase 1 fotoğraf odaklıdır. | `/videos/*`, video worker Phase 2'ye ertelendi. |
| Oracle bağlantısı runtime bağımlılığı | — | — | ✅ | Phase 1 database Oracle değil PostgreSQL; Oracle import future. | Oracle endpoint'leri future ertelendi. |
| 10M production sharding in Phase 1 | — | — | ✅ | Phase 1'de production ölçeği hedeflenmez. | 10M ölçek future boundary olarak işaretlendi. |
| Sadece ArcFace 512-D varsayımı | — | ✅ | — | Model boyutları sabitlenmemeli. | `embeddingDimension` ve model koleksiyonu ayrımı eklendi. |
| Eski `/faces/*` anonymous API | — | — | ✅ | Kişi merkezli modelle çelişir. | Reddedildi. |
| Auth/RBAC/KMS detayları in Phase 1 | — | — | ✅ | Phase 1'de uygulanmaz. | `FUTURE_BOUNDARIES.md`'de future boundary. |
| Full Docker Compose implementation in Phase 0 | — | — | ✅ | Phase 0 mimari dokümantasyonu, Docker implementasyonu değil. | Docker Compose Phase 1 implementasyonuna bırakıldı. |

## Hangi Eski Kavramlar Nasıl Evrimleşti?

### FacePipeline abstraction
Eski diyagramlarda "InsightFace pipeline" adı altında geçen akış, MergenVision'da bağımsız adapter setine dönüştü:

- `DetectorAdapter` + `RecognizerAdapter` ayrımı.
- `AlignerPreprocessor` kendi boundary'si.
- `FacePipeline` sadece orkestrasyon.

### Postgres / Qdrant / MinIO separation
Eski `05_data_ownership.md` doğruydu. MergenVision'da ek kurallar:

- Qdrant payload raw national ID içermez.
- Audit log embedding/image byte içermez.
- MinIO object access API üzerinden proxy/presigned URL ile yapılır.

### requestId / processId traceability
Eski `identification_sequence.md`'deki `processId` kavramı `requestId`'ye dönüştü. Her `/identify` çağrısı:

- Önce `identification_request` satırı oluşturur.
- Hata durumunda bile `requestId` döndürür.
- Audit log `requestId` ile ilişkilendirilir.

### api-lb + GPU replicas
Eski `03_docker_compose_architecture.md` GPU worker replica kavramı:

- Demo modda: nginx -> `api-gpu-0/1/2`.
- Python kodu GPU UUID bilmez.
- Production'da orchestrator devralır.

### Fake default pipeline problem
Eski bazı snippet'lerde "dummy backend" veya "fake default pipeline" ihtimali vardı. MergenVision'da:

- Production/runtime pipeline'ı test dışında sahte olamaz.
- Testlerde ONNX stub model'ler (random weights) kullanılabilir; ancak adapter boundary gerçektir.

### Model / migration drift
Eski `12_risks_and_open_questions.md` model sürüm uyumsuzluğu riskini vurguluyordu. Çözüm:

- Her `face_sample` kaydı `modelName/modelVersion/embeddingDimension` taşır.
- Qdrant koleksiyonları model/dimension/version bazında ayrılır.

### Docs / source mismatch
Eski diyagramlarla kod arasındaki uyumsuzluk riski MergenVision Phase 0'da şöyle yönetilir:

- Phase 0 önce mimari doküman setini oluşturur.
- Phase 1 implementasyonunda her değişiklik için ADR güncellenir.
- Kod yorumları mimari dokümanlara referans verir.

## Sonuç

Eski diyagramlardan öğrenilen en önemli dersler:

1. Adapter boundary, model değişimini mümkün kılar.
2. Veri sahipliği net olmalı; PII vektör/kaynak deposuna sızmasın.
3. Phase 1'i küçük tutmak gerekir; import/video gibi büyük kavramlar Phase 2'ye ertelenmelidir.
4. GPU atama sadece konfigürasyon katmanında olmalıdır.
5. Batch inference performans detayıdır; iş domaini buna bağlanmamalıdır.
