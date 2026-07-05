# MergenVision Phase 0 Architecture Plan

> **Mode:** Design Mode / Documentation Only.  
> **Scope:** `docs/architecture/` files only. No implementation, benchmark, inference, Docker Compose, package install, model download, or git operation in this phase.

## Executive Summary

MergenVision, fotoğraf tabanlı kişi tanıma (Phase 1) ve gelecekteki video tabanlı tanıma (Phase 2) için tek bir kimlik platformu kuracak şekilde tasarlanır. Phase 1'de manuel kişi kaydı, fotoğraf enrollment ve tek fotoğraf üzerinden sorgulama uçtan uca çalışır. Phase 2, aynı `person`, `person_photo`, `face_sample` verileri, aynı Qdrant kimlik koleksiyonlarını ve aynı MinIO nesne referanslarını yeniden kullanarak video işleme ekler.

Bu plan, Phase 0'da kabul edilen mimari kararları, referans kontrolünü, kapsam dışı kalanları, riskleri ve sıradaki kapıları (gate'leri) tanımlar.

## Governance Lock

Phase 0 mimari dokümantasyonuyla birlikte aşağıdaki yönetişim dokümanları da kabul edilmiş ve kod yazılmadan önce okunması zorunlu hale gelmiştir:

- `AGENTS.md`
- `CLAUDE.md`
- `docs/architecture/IMPLEMENTATION_GOVERNANCE.md`
- `docs/architecture/REFERENCE_FIRST_CHECKLIST.md`
- `docs/architecture/MCP_TOOL_USAGE_POLICY.md`
- `docs/architecture/PHASE_IMPLEMENTATION_GATES.md`
- `docs/architecture/DOCKER_GPU_STRATEGY_LOCK.md`
- `docs/architecture/NO_SCOPE_CREEP_RULES.md`
- `docs/architecture/SELF_REVIEW_AND_VERIFICATION_POLICY.md`

Bu dokümanlar: REFERENCE_FIRST kuralını, MCP/tool kullanımını, Phase 1 kapsam kilidini, Docker/GPU stratejisini, veri sahipliğini, model adapter sınırlarını, UUIDv7 kuralını ve tamamlama öncesi doğrulama kuralını kilitler. Gelecek uygulama fazları bu kurallara göre ilerler.

---

## REFERENCE_CHECK

### Task
Phase 0 mimari dokümantasyonunu yazmadan önce kaynak doğruluk kontrolü yapılmıştır.

### Relevant requirements checked
- `requirements/phase1recognitionrequirements.md` — Phase 1 fotoğraf tabanlı kişi tanıma gereksinimleri (source of truth).
- `requirements/phase2videorequirements.md` — Phase 2 video gereksinimleri; sadece gelecek sınır olarak ele alındı.
- `opensourceReferences/references.md` — referans-öncelikli politika.

### Relevant local docs checked
- `docs/model_research/PHASE_MINUS_1_MODEL_SELECTION_REPORT.md` — model seçimi hipotezi.
- `docs/model_research/PHASE_0A_MODEL_ACCESS_REPORT.md` — model erişim sonucu.
- `artifacts/model_benchmarks/MODEL_MANIFEST.json` — indirilmiş/engellenmiş model manifesti.

### Relevant old diagrams/reports checked
- `olderDiagramsProvedWrog/01_system_purpose.md`
- `olderDiagramsProvedWrog/02_high_level_architecture.md`
- `olderDiagramsProvedWrog/03_docker_compose_architecture.md`
- `olderDiagramsProvedWrog/04_layered_backend_architecture.md`
- `olderDiagramsProvedWrog/05_data_ownership.md`
- `olderDiagramsProvedWrog/06_database_erd.md`
- `olderDiagramsProvedWrog/07_enrollment_sequence.md`
- `olderDiagramsProvedWrog/08_identification_sequence.md`
- `olderDiagramsProvedWrog/09_ui_wireflow.md`
- `olderDiagramsProvedWrog/10_api_map.md`
- `olderDiagramsProvedWrog/11_demo_vs_future_scope.md`
- `olderDiagramsProvedWrog/12_risks_and_open_questions.md`
- `olderDiagramsProvedWrog/README.md`
- `/home/user/Demo/VideoFaceGpuLab/docs/API_CONTRACT.md`
- `/home/user/Demo/VideoFaceGpuLab/docs/DATABASE_OBJECT_VECTOR_SCHEMA.md`
- `/home/user/Demo/VideoFaceGpuLab/docs/DOCKER_GPU_WORKER_RUNBOOK.md`
- `/home/user/Demo/VideoFaceGpuLab/docs/ENGINE_ARCHITECTURE.md`
- `/home/user/Demo/VideoFaceGpuLab/docs/PHASE9A_INFERENCE_CONTRACTS_REPORT.md`
- `/home/user/Demo/VideoFaceGpuLab/docs/PHASE9C_ORT_IOBINDING_REPORT.md`
- `/home/user/Demo/VideoFaceGpuLab/docs/PHASE9D_SCRFD_ADAPTER_REPORT.md`
- `/home/user/Demo/VideoFaceGpuLab/docs/PHASE10A_GPU_ALIGNMENT_CROP_BRIDGE_REPORT.md`
- `/home/user/Demo/VideoFaceGpuLab/docs/OPEN_SOURCE_MODEL_ADAPTER_BRIDGE_PLAN.md`
- `/home/user/Demo/Demo12_VGGFace2Lab/docs/BATCHED_ONNX_CUDA_SMOKE_REPORT.md`
- `/home/user/Demo/Demo12_VGGFace2Lab/docs/BATCHED_ONNX_IMPORT_MODEL_REPORT.md`
- `/home/user/Demo/Demo12_VGGFace2Lab/docs/PRODUCTION_MULTI_GPU_RUNBOOK.md`
- `/home/user/Demo/Demo12_VGGFace2Lab/docs/DATA_DELETION_SAFETY.md`

### Relevant official docs checked (via context7)
- FastAPI: APIRouter include_router, dependency injection, bigger applications (`/fastapi/fastapi`).
- SQLAlchemy 2.0 ORM architecture (`/websites/sqlalchemy_en_20_orm`).
- Alembic migration organization (`/websites/alembic_sqlalchemy`).
- Qdrant: collection, vector dimension, payload, upsert, search (`/websites/qdrant_tech`).
- MinIO Python client: bucket, object, presigned URL (`/minio/docs`).
- ONNX Runtime: execution providers, CUDAExecutionProvider, IOBinding (`/microsoft/onnxruntime`).
- Docker Compose: deploy.resources.reservations.devices GPU mapping (`/docker/compose`).
- Nginx: upstream load balancing reverse proxy (`/websites/nginx`).
- Mermaid: flowchart / sequenceDiagram / erDiagram syntax (`/mermaid-js/mermaid`).

### Model reports checked
- `PHASE_0A_MODEL_ACCESS_REPORT.md`
- `MODEL_MANIFEST.json`
- `BATCHED_ONNX_IMPORT_MODEL_REPORT.md`
- `BATCHED_ONNX_CUDA_SMOKE_REPORT.md`
- `PHASE9D_SCRFD_ADAPTER_REPORT.md`
- `PHASE10A_GPU_ALIGNMENT_CROP_BRIDGE_REPORT.md`

### Patterns to follow
- Root-level REST endpoint'ler (Phase 1'de `/api/v1` öneki yok).
- PostgreSQL → iş verisi ve metadata source-of-truth; Qdrant → sadece vektör indeksi; MinIO → sadece nesne deposu.
- UUIDv7 anahtarlar.
- Adapter boundary: `DetectorAdapter`, `RecognizerAdapter`, `AlignerPreprocessor` ayrı ara yüzler.
- `modelName/modelVersion/embeddingDimension` her `face_sample`'da saklanır.
- Her model/dimension/version için ayrı Qdrant koleksiyonu.
- Phase 1 ve Phase 2 için tek, mantıksal paylaşımlı veri platformu (ayrı kalıcı stack yok).
- GPU demo modunda her fiziksel GPU için bir API replikası; Python kodu GPU UUID sabitlemez.
- Soft delete + `isActive` payload filtreleme.
- Hassas veri (raw national ID, `person.details`, image bytes, embedding) Qdrant payload'a ve audit log'a yazılmaz.

### Patterns rejected
- `/imports/*` endpoint'lerinin Phase 1'e sızması (kabul edilmedi, future).
- `/videos/*` ve async worker'ların Phase 1'de yapılması (kabul edilmedi, Phase 2).
- Phase 1 ve Phase 2 için ayrı kalıcı PostgreSQL/Qdrant/MinIO stack.
- Qdrant payload içinde raw/masked national ID veya `person.details` saklama.
- Python kodunda sabit GPU UUID/index kullanma.
- InsightFace runtime bağımlılığı; yerine ONNX Runtime + adapter yaklaşımı benimsendi.
- Batch inference business domain bağımlılığı yapma; batch sadece performans detayı.

### How this maps to MergenVision
- Phase 1: yukarıdaki root endpoint'ler, adapter boundary, tek data platformu.
- Phase 2: `video_job`, `video_track`, `face_video_appearance` tabloları aynı PostgreSQL'ye eklenir; Qdrant koleksiyonları yeniden kullanılır; worker GPU container'lar aynı model adaptörlerini kullanır.

### Files to create
- `PHASE_0_ARCHITECTURE_PLAN.md`
- `HIGH_LEVEL_ARCHITECTURE.md`
- `API_CONTRACT.md`
- `DATA_MODEL.md`
- `RUNTIME_TOPOLOGY.md`
- `MODEL_ADAPTER_BOUNDARY.md`
- `PHASE1_PHASE2_SHARED_DATA_PLATFORM.md`
- `OLD_DIAGRAMS_LESSONS_LEARNED.md`
- `SENSITIVE_DATA_RULES.md`
- `FUTURE_BOUNDARIES.md`
- `ARCHITECTURE_DECISION_RECORDS.md`
- `DIAGRAM_INDEX.md`

### Mermaid diagrams to create
1. Combined Phase 1 + Phase 2 high-level architecture (`flowchart TD`)
2. Backend layering diagram (`flowchart TD`)
3. Data ownership ERD (`erDiagram`)
4. Phase 1 enrollment sequence (`sequenceDiagram`)
5. Phase 1 identify sequence (`sequenceDiagram`)
6. Future Phase 2 video sequence (`sequenceDiagram`)
7. Model adapter boundary (`flowchart LR`)
8. Shared data platform separation (`flowchart TD`)
9. Runtime topology dev vs GPU demo (`flowchart LR`)
10. Future boundaries map (`flowchart TD`)

### Unverified claims
- SCRFD/ArcFace ONNX shape ve çıkış boyutları `MODEL_MANIFEST.json` içinde **unverified** olarak işaretlendi.
- ONNX Runtime `CUDAExecutionProvider` seçimi ve IOBinding davranışı Phase 0B'ye kadar MergenVision kod tabanında doğrulanmadı.
- Batch inference contamination-free davranışı Phase 0B'ye kadar doğrulanmadı.
- Model doğruluğu, threshold değerleri ve ölçeklenebilirlik iddiası Phase 0B ve sonrası testlerle kanıtlanmalı.

---

## Scope

### Phase 1 (Mevcut)
- `POST /people`, kişi oluşturma.
- `POST /people/{personId}/photos`, fotoğraf enrollment.
- `POST /identify`, sorgu fotoğrafı ile kişi arama.
- `GET /identification-requests`, geçmiş listesi.
- `GET /identification-requests/{requestId}`, tek istek detayı.
- `GET /audit`, temel audit log.
- `GET /stats`, durum özetleri.
- `GET /media/{bucket}/{objectKey}`, görsel erişim.
- PostgreSQL + Qdrant + MinIO entegrasyonu.
- FastAPI backend + isteğe bağlı React demo/admin UI.
- Model adapter boundary ve batch-ready tasarım.

### Phase 2 (Gelecek)
- Video upload API.
- `video_job` kuyruğu ve worker GPU container'ları.
- Frame sampling, batched detection, tracking, embedding extraction.
- Qdrant üzerinden kimlik arama.
- Video timeline / appearances.

### Shared platform
- Phase 1 ve Phase 2 için tek PostgreSQL, tek Qdrant, tek MinIO (tablo/koleksiyon/prefix ayrımı ile).

---

## Non-Goals

Phase 0 dokümantasyonunda ve Phase 1 uygulamasında **yapılmayacak** şeyler:

- Oracle import implementasyonu.
- `/imports/*` endpoint'leri.
- Async batch importer worker.
- Video işleme, live stream, RTSP.
- Genel nesne tespiti (object detection).
- LFW benchmark pipeline.
- Production RBAC/KMS/multitenancy.
- 10M+ kayıt için production sharding.
- TensorRT implementasyonu.
- Model inference kodu (Phase 0'da).
- `docker-compose.yml` implementasyonu (Phase 0'da).

---

## Decisions

1. **One logical shared data platform** — Phase 1 ve Phase 2 aynı PostgreSQL/Qdrant/MinIO servislerini kullanır.
2. **Phase 1 scope** — fotoğraf tabanlı kişi tanıma + history + audit; import/video dışarıda.
3. **Phase 2 future boundary** — video işleme aynı kimlik verilerini yeniden kullanır.
4. **GPU deployment** — tek kod; demo modda her fiziksel GPU için bir replika; Python sabit GPU UUID kullanmaz.
5. **API shape** — root-level endpoint'ler; `/imports/*`, `/videos/*`, `/faces/*` Phase 1'de yok.
6. **Data ownership** — PostgreSQL iş verisi; Qdrant vektör; MinIO nesne; hassas veri Qdrant/audit'a gitmez.
7. **Model/pipeline architecture** — adapter boundary, model metadata tracking, dimension-specific Qdrant koleksiyonları.

Kararların her biri `ARCHITECTURE_DECISION_RECORDS.md` içinde ADR formatında detaylandırılmıştır.

---

## Risks

| Risk | Etki | Azaltma |
|---|---|---|
| Model şekli/provider henüz doğrulanmadı | Yüksek | Phase 0B kapısında doğrula; adapter boundary ile model değişimi mümkün. |
| Batch inference davranışı bilinmiyor | Orta | Batch business bağımlılığı değil; tekli inference yedek yol. |
| False positive/yanlış eşleşme | Yüksek | `matched`/`possible_match`/`no_match` ayrımı; skor UI'da gösterilir. |
| Lisans (insightface-non-commercial) | Yüksek | Production öncesi hukuk/ürün onayı; model değiştirilebilir adapter tasarımı. |
| Hassas veri sızıntısı | Yüksek | Qdrant/audit kısıtlamaları, presigned URL/placeholder politikası. |
| Phase 2'de model kalitesi yetersizse | Orta | YuNet/SFace veya başka model çiftine geçiş mümkün; kimlik tabloları korunur. |
| PostgreSQL-Qdrant-MinIO tutarlılığı | Orta | Transaction + `is_indexed` bayrak + hata durumunda best-effort cleanup. |

---

## Next Gates

1. **Phase 0B** — model shape, ONNX Runtime provider, batch doğruluğu ve temel smoke test.
2. **Phase 0 review** — dokümanların kullanıcı tarafından onaylanması.
3. **Phase 1 implementation planning** — onay sonrası kod, migration, test planı.
4. **Phase 1 implementation** — endpoint'ler, adapter'lar, repository'ler, UI.
5. **Phase 2 planning** — video job queue, worker, tracking boundary.

---

## Model Verification Caveat

MergenVision envanterinde indirilmiş ancak **yerel olarak doğrulanmamış** modeller vardır:

- `scrfd_10g_320_batch.onnx` — beklenen input `[N,3,320,320]`, çıkış bbox + 5 landmarks + score.
- `arcface_w600k_r50_batch.onnx` — beklenen input `[N,3,112,112]`, çıkış `[N,512]`.

Bu modeller mimaride **aday** olarak ele alınır. Sabit bir final production gerçeği değildir. Phase 0B'ye kadar şekil, provider ve batch davranışı doğrulanmalıdır.

---

## Implementation Forbidden Until Phase 0B + Doc Approval

- Bu doküman seti tamamlanana ve Phase 0B model doğrulaması bitene kadar **uygulama kodu yazılmayacaktır**.
- `docker-compose.yml`, migration, frontend, inference, benchmark, model indirme bu aşamada yasaktır.
- Sadece `docs/architecture/` altındaki izin verilen dosyalar oluşturulur/güncellenir.
