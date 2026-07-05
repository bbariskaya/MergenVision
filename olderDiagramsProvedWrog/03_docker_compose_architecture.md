# Docker Compose Architecture

```mermaid
flowchart TB
    subgraph DockerCompose["Docker Compose Ortamı"]
        direction TB

        UI["frontend<br/>React + Vite<br/>port 5174"]

        subgraph APILayer["API Katmanı"]
            direction TB
            SingleAPI["api<br/>FastAPI<br/>localhost:8000"]
            LB["api-lb<br/>nginx load balancer<br/>localhost:8080"]
            GPU0["api-gpu-0<br/>FastAPI + ONNX/InsightFace<br/>GPU 0 → 8001"]
            GPU1["api-gpu-1<br/>FastAPI + ONNX/InsightFace<br/>GPU 1 → 8002"]
            GPU2["api-gpu-2<br/>FastAPI + ONNX/InsightFace<br/>GPU 2 → 8003"]
            LB --> GPU0
            LB --> GPU1
            LB --> GPU2
        end

        subgraph DataLayer["Veri Katmanı"]
            direction TB
            Postgres["postgres<br/>PostgreSQL 16<br/>5433:5432"]
            QdrantSvc["qdrant<br/>Qdrant vector DB<br/>6333 / 6334"]
            MinIOSvc["minio<br/>MinIO S3-compatible<br/>9010 / 9001"]
            MinIOInit["minio-init<br/>bucket kurulumu"]
        end
    end

    subgraph FutureLayer["Gelecek Katman"]
        direction TB
        Oracle[(Oracle DB<br/>gelecek import kaynağı)]
        Importer["future import worker<br/>henüz mevcut değil"]
    end

    Browser["Kullanıcı Tarayıcısı"]

    Browser -->|"http://localhost:5174"| UI
    UI -->|"/api proxy → 8080"| LB
    UI -.->|"/api proxy → 8000 (alternatif)"| SingleAPI

    SingleAPI --> Postgres
    SingleAPI --> QdrantSvc
    SingleAPI --> MinIOSvc

    GPU0 --> Postgres
    GPU0 --> QdrantSvc
    GPU0 --> MinIOSvc
    GPU1 --> Postgres
    GPU1 --> QdrantSvc
    GPU1 --> MinIOSvc
    GPU2 --> Postgres
    GPU2 --> QdrantSvc
    GPU2 --> MinIOSvc

    MinIOInit -->|"mc mb face-demo"| MinIOSvc

    Oracle -.->|"gelecek okuma"| Importer
    Importer -.->|"gelecek import"| SingleAPI

    Note1["Not: Her api-gpu-* container'ı deploy.resources.reservations.devices ile<br/>belirli bir fiziksel GPU'ya sabitlenir.<br/>NVIDIA_VISIBLE_DEVICES ve CUDA_VISIBLE_DEVICES=0 kullanılır."]
    Note1 -.-> GPU0
    Note1 -.-> GPU1
    Note1 -.-> GPU2

    Note2["Not: frontend/vite.config.ts dev ortamında /api ve /media isteklerini 8080'e yönlendirir."]
    Note2 -.-> UI
```

## Kısa Açıklama

- **frontend**: React + Vite geliştirme sunucusu; `localhost:5174` üzerinden çalışır.
- **api**: Tekil FastAPI uygulaması; `localhost:8000` üzerinden erişilir, geliştirme veya geri dönüş amaçlı kullanılır.
- **api-lb**: nginx yük dengeleyici; `/api` isteklerini üç GPU worker arasında dağıtır.
- **api-gpu-0/1/2**: ONNX Runtime + InsightFace yüz işleme hattı içeren FastAPI replikaları; her biri fiziksel bir GPU'ya sabitlenmiştir.
- **postgres**: Kişi, fotoğraf, örnek, tanımlama geçmişi ve denetim logları için ilişkisel veritabanı.
- **qdrant**: Yüz embedding vektörlerinin saklandığı vektör veritabanı.
- **minio**: Orijinal fotoğraf, yüz kırpıntıları ve sorgu görüntülerinin saklandığı S3-benzeri nesne deposu.
- **minio-init**: Başlangıçta `face-demo` bucket'ını oluşturan tek seferlik init container'ı.
- **Oracle / future import worker**: Sadece mimari vizyon; mevcut kodda veya Docker Compose'da gerçeklenmemiştir.
