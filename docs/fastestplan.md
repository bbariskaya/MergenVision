# Fastest Phase 1 Stack — End-to-End Flow

> Stack: `torch` + `torchvision` + `tensorrt` + `cupy`  
> CPU boundary: only final `[N,512]` embedding + metadata go to PostgreSQL / Qdrant / MinIO.

---

## 1. Full Request-to-Response Flow

```mermaid
flowchart TB
    subgraph Client["Client"]
        REQ["POST /people/{personId}/photos\nveya\nPOST /identify"]
    end

    subgraph FastAPI["FastAPI — CPU / I/O"]
        Router["Router\npeople, photos, identify, ..."]
        Service["Business Service\nEnrollmentService / IdentificationService"]
        Repo["SQLAlchemy Repository\nPostgreSQL"]
    end

    subgraph GPU["GPU — tamamen burada kalır"]
        Decode["nvJPEG decode\ncupyx → torch.cudaTensor"]
        Preprocess["torchvision resize 320\n+ normalize"]
        DetRT["SCRFD TensorRT\n[N,3,320,320]"]
        DetPost["torch NMS\nboxes + 5 landmarks"]
        Align["affine_grid + grid_sample\n112x112 crop"]
        RecRT["ArcFace TensorRT\n[M,3,112,112]"]
        Norm["torch L2 normalize"]
    end

    subgraph Storage["CPU Depolama"]
        PSQL[("PostgreSQL\nmetadata + audit")]
        Qdrant[("Qdrant\nvector + payload")]
        MinIO[("MinIO\norijinal + crop + query")]
    end

    REQ --> Router
    Router --> Service
    Service --> Repo
    Service --> Decode

    Decode --> Preprocess
    Preprocess --> DetRT
    DetRT --> DetPost
    DetPost --> Align
    Align --> RecRT
    RecRT --> Norm

    Norm -->|".cpu().numpy()"| CPU_EMB["[N,512]\nembedding"]
    CPU_EMB --> PSQL
    CPU_EMB --> Qdrant
    Service --> MinIO

    PSQL --> Router
    Qdrant --> Router
    MinIO --> Router
    Router --> RESP["HTTP Response\n201 / 200 / 400"]
```

---

## 2. GPU-Only Detail

```mermaid
flowchart LR
    A["JPEG bytes"] --> B["nvJPEG GPU decode"]
    B --> C["torchvision resize\n320x320 normalize"]
    C --> D["TensorRT SCRFD\nbatch inference"]
    D --> E["torch decode scores/bboxes\n+ batched NMS"]
    E --> F["5 landmark → affine\naffine_grid + grid_sample"]
    F --> G["TensorFace ArcFace\nbatch inference"]
    G --> H["torch L2 normalize"]
    H --> I["[N,512] embedding\nGPU memory"]
    I --> J[".cpu().numpy()\nsadece burada CPU'ya çıkar"]
```

---

## 3. Hız Hedefleri

| Veri | Süre | Throughput |
|---|---|---|
| LFW ~13K | ~1 dk | ≥ 220 img/s |
| 100K fotoğraf | ~10 dk | ≥ 167 img/s |
| 1M fotoğraf | ~90 dk | ≥ 185 img/s |

Gerçek rakamlar GPU, batch boyutu, disk/ağ hızına bağlıdır.
