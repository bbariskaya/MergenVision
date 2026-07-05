# Layered Backend Architecture

```mermaid
flowchart TB
    subgraph API["app/api"]
        Routes["routes/<br/>HTTP endpoint binding"]
        Controllers["controllers/<br/>request/response adaptation"]
        Schemas["schemas/<br/>Pydantic API contracts"]
    end

    subgraph ServicesLayer["app/services"]
        PersonService["PersonService<br/>person business logic"]
        PhotoService["PersonPhotoService<br/>photo enrollment logic"]
        IdentificationService["IdentificationService<br/>query photo search logic"]
        AuditService["AuditService<br/>audit events"]
    end

    subgraph Domain["app/domain"]
        DomainEnums["enums.py<br/>statuses / decisions"]
        PersonDomain["person.py"]
        PhotoDomain["photo.py"]
        IdentificationDomain["identification.py"]
    end

    subgraph Repositories["app/repositories"]
        PersonRepo["PersonRepository"]
        PhotoRepo["PersonPhotoRepository"]
        SampleRepo["FaceSampleRepository"]
        RequestRepo["IdentificationRequestRepository"]
        QueryFaceRepo["IdentificationQueryFaceRepository"]
        ResultRepo["IdentificationResultRepository"]
        AuditRepo["AuditLogRepository"]
    end

    subgraph Infrastructure["app/infrastructure"]
        DBInfra["database/<br/>SQLAlchemy connection / models"]
        VectorInfra["vector/<br/>VectorStore protocol<br/>Qdrant adapter"]
        StorageInfra["storage/<br/>ImageStorage protocol<br/>MinIO adapter"]
        FaceInfra["face_pipeline/<br/>validation / detection / crop / embedding<br/>ONNX Runtime / InsightFace"]
    end

    subgraph Core["app/core"]
        Exceptions["exceptions.py<br/>AppError hierarchy"]
        Security["security.py<br/>hashing / masking helpers"]
    end

    Config["app/config.py<br/>environment settings"]

    Runtime["Runtime Notu:<br/>Aynı backend kodu hem api (localhost:8000)<br/>hem de api-gpu-0/1/2 container'larında çalışır.<br/>GPU container'lar GPU hızlandırmalı FacePipeline kullanır.<br/>Tekil api container geliştirme / geri dönüş yoludur."]

    Rules["Layer Rules:<br/>Routes only bind HTTP<br/>Controllers adapt request/response<br/>Services contain business logic<br/>Repositories handle PostgreSQL CRUD<br/>Infrastructure hides Qdrant, MinIO, ML libraries<br/>Services must not import FastAPI or API schemas<br/>Repositories must not import API/controllers/services"]

    Routes --> Controllers
    Routes --> Schemas
    Controllers --> Schemas
    Controllers --> ServicesLayer

    ServicesLayer --> Repositories
    ServicesLayer --> VectorInfra
    ServicesLayer --> StorageInfra
    ServicesLayer --> FaceInfra
    ServicesLayer --> Domain
    ServicesLayer --> Core
    ServicesLayer --> Config

    Repositories --> DBInfra
    Repositories --> Domain

    Infrastructure --> Core
    Infrastructure --> Config

    Rules -.-> Routes
    Rules -.-> ServicesLayer
    Rules -.-> Repositories
    Rules -.-> Infrastructure

    Runtime -.-> ServicesLayer
    Runtime -.-> FaceInfra

    style API fill:#e1f5fe
    style ServicesLayer fill:#fff3e0
    style Repositories fill:#e8f5e9
    style Infrastructure fill:#fce4ec
    style Domain fill:#f3e5f5
    style Core fill:#eeeeee
    style Config fill:#eeeeee
```

## Açıklama

- **API Layer**: FastAPI router'ları HTTP endpoint'leri bağlar, controller'lar request/response dönüşümünü yapar, Pydantic şemalar API sözleşmelerini tanımlar.
- **Services Layer**: İş mantığını barındırır. `PersonService`, `PersonPhotoService`, `IdentificationService`, `AuditService` mevcut servislerdir.
- **Domain Layer**: Temel domain modelleri ve enum'lar (`person.py`, `photo.py`, `identification.py`, `enums.py`).
- **Repositories**: PostgreSQL CRUD operasyonları. `PersonRepository`, `PersonPhotoRepository`, `FaceSampleRepository`, `IdentificationRequestRepository`, `IdentificationQueryFaceRepository`, `IdentificationResultRepository`, `AuditLogRepository` bulunur.
- **Infrastructure**: Protokol/adapter pattern. `VectorStore` → Qdrant, `ImageStorage` → MinIO, `FacePipeline` → ONNX Runtime + InsightFace, `database` → SQLAlchemy.
- **Core**: `AppError` hiyerarşisi ve güvenlik yardımcıları.
- **Runtime Notu**: Aynı backend kodu `api` (tek-instance) ve `api-gpu-0/1/2` (GPU replikaları) container'larında çalışır. GPU worker'lar `FACE_PIPELINE_BACKEND=gpu` ve `ONNXRUNTIME_PROVIDERS` ile GPU inference yapar.
- **Eksik Future Bileşenler**: `ImportService`, `ImportJobRepository`, `ImportJobItemRepository` ve `import_job.py` domain modeli mevcut kodda yoktur; sadece gelecek Oracle import vizyonunda yer alır.
