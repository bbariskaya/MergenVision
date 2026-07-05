# High-Level Architecture

```mermaid
flowchart TB
    subgraph UserLayer["Kullanıcı Katmanı"]
        User[Kullanıcı]
        UI[React + Vite UI<br/>localhost:5174]
    end

    subgraph Runtime["Docker Runtime"]
        direction TB
        SingleAPI["api<br/>FastAPI<br/>localhost:8000"]
        LB["api-lb<br/>nginx load balancer<br/>localhost:8080"]
        GPU0["api-gpu-0<br/>FastAPI + ONNX/InsightFace<br/>GPU 0"]
        GPU1["api-gpu-1<br/>FastAPI + ONNX/InsightFace<br/>GPU 1"]
        GPU2["api-gpu-2<br/>FastAPI + ONNX/InsightFace<br/>GPU 2"]
        LB --> GPU0
        LB --> GPU1
        LB --> GPU2
    end

    subgraph FastAPIApp["FastAPI Uygulama Mantığı"]
        direction LR
        Routes[API Routes]
        Controllers[API Controllers]
        Services[Application Services]
    end

    subgraph InfraAdapters["Infrastructure Adaptörleri"]
        Repositories[PostgreSQL Repositories]
        VectorStore[VectorStore Adapter]
        ImageStorage[ImageStorage Adapter]
        FacePipeline[FacePipeline Adapter<br/>ONNX Runtime / InsightFace]
    end

    subgraph DataLayer["Veri / Harici Sistemler"]
        PG[(PostgreSQL<br/>kişi / fotoğraf / örnek<br/>tanımlama geçmişi<br/>denetim logları)]
        Qdrant[(Qdrant<br/>yüz embedding vektörleri<br/>sample/person/photo referansları)]
        MinIO[(MinIO<br/>orijinal fotoğraflar<br/>yüz kırpıntıları<br/>sorgu görüntüleri)]
    end

    subgraph FutureLayer["Gelecek Dış Kaynak İmportu"]
        Oracle[(Oracle DB<br/>gelecek import kaynağı)]
        Importer[Future Import Adapter / Worker]
    end

    User -->|browser| UI
    UI -->|"/api → 8080"| LB
    UI -.->|"/api → 8000 (alternatif)"| SingleAPI

    SingleAPI -->|çalıştırır| FastAPIApp
    GPU0 -->|çalıştırır| FastAPIApp
    GPU1 -->|çalıştırır| FastAPIApp
    GPU2 -->|çalıştırır| FastAPIApp

    FastAPIApp -->|iş mantığı / veri erişimi| Repositories
    FastAPIApp -->|vektör arama / upsert| VectorStore
    FastAPIApp -->|görüntü yükleme / imza URL| ImageStorage
    FastAPIApp -->|doğrula / tespit / kırp / embed| FacePipeline

    Repositories --> PG
    VectorStore --> Qdrant
    ImageStorage --> MinIO

    Oracle -.->|gelecek okuma| Importer
    Importer -.->|gelecek import orkestrasyonu| FastAPIApp

    Note1["Not: api-gpu-* container'ları aynı FastAPI kodunu çalıştırır.<br/>GPU worker'lar GPU hızlandırmalı FacePipeline kullanırken,<br/>tekil api container geliştirme / geri dönüş yoludur."]
    Note1 -.-> GPU0
    Note1 -.-> GPU1
    Note1 -.-> GPU2
```

## Kısa Açıklama

- **Kullanıcı**: Tarayıcı üzerinden React + Vite arayüzüne erişir.
- **UI**: Vite dev sunucusu `localhost:5174`'te çalışır; `/api` ve `/media` isteklerini `localhost:8080`'deki nginx yük dengeleyicisine yönlendirir.
- **api-lb**: Üç GPU worker arasında round-robin trafik dağıtır.
- **api-gpu-0/1/2**: Aynı FastAPI uygulama kodunu çalıştıran GPU işlem container'ları; yüz doğrulama, tespit, kırpma ve embedding çıkarımını ONNX Runtime + InsightFace ile GPU üzerinde yapar.
- **api**: Tek-instance FastAPI container'ı `localhost:8000`; geliştirme, test veya geri dönüş amaçlı kullanılır.
- **PostgreSQL**: Kişiler, fotoğraflar, yüz örnekleri, tanımlama istekleri/sonuçları, sorgu yüzleri ve denetim logları için ilişkisel veri saklar.
- **Qdrant**: 512 boyutlu yüz embedding vektörlerini saklar ve kosinüs benzerliğiyle komşu araması yapar.
- **MinIO**: Orijinal fotoğraflar, yüz kırpıntıları ve isteğe bağlı sorgu görüntüleri için S3-benzeri nesne depolama sağlar.
- **Oracle / future import worker**: Sadece mimari vizyon; mevcut kodda veya Docker Compose'da gerçeklenmemiştir.
