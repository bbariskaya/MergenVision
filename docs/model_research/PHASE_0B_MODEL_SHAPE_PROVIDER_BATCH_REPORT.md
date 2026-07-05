# PHASE 0B Model Şekil, Sağlayıcı ve Batch Doğrulama Raporu

**Proje:** MergenVision  
**Tarih:** 2026-07-04  
**Yazar:** opencode (otomatik doğrulama oturumu)  
**Amaç:** Phase 1 için seçilen birincil InsightFace ONNX model çiftinin yerel ortamda şekil, ONNX Runtime sağlayıcı ve dummy batch çıktı olarak doğrulanması.  
**Kapsam Kilidi:** Phase 0B; uygulama kodu, API route, migration, Docker veya gerçek veri seti yok.

---

## REFERENCE_CHECK

```text
Task:
  Phase 0B model şekil / ONNX Runtime sağlaycı / dummy batch doğrulaması:
  scrfd_10g_320_batch.onnx (detektör) ve arcface_w600k_r50_batch.onnx (tanıyıcı).

Phase:
  0B

Allowed scope:
  - Phase 0B doğrulama betikleri (tools/model_verification/)
  - Phase 0B sonuç JSON'ları (artifacts/model_benchmarks/results/)
  - Bu rapor dosyası (docs/model_research/PHASE_0B_MODEL_SHAPE_PROVIDER_BATCH_REPORT.md)

Files allowed to change:
  - tools/model_verification/*.py
  - tools/model_verification/README.md
  - artifacts/model_benchmarks/results/phase0b_*.json
  - docs/model_research/PHASE_0B_MODEL_SHAPE_PROVIDER_BATCH_REPORT.md

Files forbidden to change:
  - artifacts/model_benchmarks/MODEL_MANIFEST.json (salt okunur)
  - artifacts/model_benchmarks/models/* (sadece okundu)
  - backend/, frontend/, app/, migrations/, docker compose, API route tanımları
  - README veya dokümantasyon dosyaları (rapor hariç)

Local docs checked:
  - AGENTS.md, CLAUDE.md
  - docs/architecture/PHASE_IMPLEMENTATION_GATES.md
  - docs/architecture/MODEL_ADAPTER_BOUNDARY.md
  - docs/architecture/DOCKER_GPU_STRATEGY_LOCK.md
  - docs/architecture/NO_SCOPE_CREEP_RULES.md
  - docs/architecture/SELF_REVIEW_AND_VERIFICATION_POLICY.md
  - docs/architecture/PHASE_0_ARCHITECTURE_PLAN.md, API_CONTRACT.md, DATA_MODEL.md, RUNTIME_TOPOLOGY.md
  - requirements/phase1recognitionrequirements.md, requirements/phase2videorequirements.md

Architecture docs checked:
  - MODEL_ADAPTER_BOUNDARY.md (detector/aligner/recognizer ayrımı, Qdrant koleksiyon boyutu kuralı)
  - DOCKER_GPU_STRATEGY_LOCK.md (api-lb + api-gpu-N, GPU UUID kodda yasak)
  - NO_SCOPE_CREEP_RULES.md (Phase 1 route ve tablo kilit listesi)
  - PHASE1_PHASE2_SHARED_DATA_PLATFORM.md

Requirements checked:
  - Phase 1 tanıma gereksinimleri (fotoğraf tabanlı kisi kaydı/tanıma)
  - Phase 2 video gereksinimleri (gelecek; Phase 1'de dokunulmadı)

Official docs checked via context7:
  - /microsoft/onnxruntime — ONNX Runtime Python InferenceSession, provider listesi, CUDAExecutionProvider, CPUExecutionProvider.
  - /websites/onnxruntime_ai_api_python — InferenceSession __init__ providers argümanı, get_available_providers, IOBinding giriş.

Open-source references checked via exa/web:
  - Hugging Face model kartı https://huggingface.co/alonsorobots/scrfd_320_batched
    - Dynamic batch 1-32, SCRFD [N,3,320,320], 9 çıkış (score/bbox/kps × 3 stride)
    - ArcFace [N,3,112,112] çıkış [N,512]

Existing local code inspected:
  - artifacts/model_benchmarks/MODEL_MANIFEST.json (salt okunur karşılaştırma)
  - docs/model_research/PHASE_0A_MODEL_ACCESS_REPORT.md
  - Demo/Demo12_VGGFace2Lab/docs/BATCHED_ONNX_CUDA_SMOKE_REPORT.md
  - Demo/VideoFaceGpuLab/docs/PHASE9C_ORT_IOBINDING_REPORT.md
  - Demo/VideoFaceGpuLab/docs/PHASE10B_ARCFACE_ONNX_EMBEDDING_SMOKE_REPORT.md

Patterns to follow:
  - Detector ve recognizer ayrı adaptör sınırında kalacak.
  - Model dosyaları ve manifest salt okunur; Phase 0B durumu ayrı JSON'larla raporlanacak.
  - Python kodu GPU UUID veya fiziksel cihaz indeksi sabitlemeyecek.
  - Docker/GPU stratejisine göre GPU kanıtı aynı backend imajının replica'larında konteyner ortamında yapılacak.

Patterns rejected:
  - MODEL_MANIFEST.json üzerinde verified_locally güncellemesi yapmak (girişimde bulunulmadı).
  - Eksik libcudnn.so.9 için sistem CUDA/cuDNN paketi kurmak veya rastgele çözüm denemek.
  - Sahte/Fake FacePipeline üretmek.
  - LFW veya gerçek görüntü benchmark çalıştırmak.

Architecture decisions that apply:
  - Phase 1 GPU demo: api-lb + api-gpu-0/1/2, aynı backend imajı, ortak PostgreSQL/Qdrant/MinIO.
  - Phase 1'de ayrı ML mikroservis yok.
  - Phase 2'de worker-gpu konteynerleri eklenecek.

Docker/GPU strategy that applies:
  - api-gpu-* aynı kodu çalıştırır ve tek fiziksel GPU'ya pinlenir (compose/orkestratör düzeyinde).
  - Python kodu cihaz indeksi varsayamaz; ORT varsayılan görünür cihazı kullanır.

Data ownership rules that apply:
  - PostgreSQL: kişi iş verisi, metadata, talep/sonuçlar.
  - Qdrant: embedding vektörleri, referans payload (PIT/etiket/fotoğraf referans; ham resim veya NTC numarası yok).
  - MinIO: orijinal görüntüler ve face crop.
  - Bu Phase 0B raporunda hiçbir gerçek resim, NTC, embedding veya PII saklanmadı.

Security/PII rules that apply:
  - Dummy batch smoke sadece rastgele float32 tensörler kullandı.
  - Gerçek yüz görüntüsü veya kişisel veri işlenmedi.

Tests/verification planned:
  1. SHA-256 ve boyut karşılaştırması (MODEL_MANIFEST.json salt okunur).
  2. ONNX graph şekil denetimi.
  3. ORT sağlayıcı smoke testi (CPU, CUDA strict, CUDA+CPU fallback).
  4. CPU üzerinde 1/4/8/16/32 batch dummy inference (sıcaklık/çıkış şekli).
  5. CUDA teşebbüsü; sağlayıcı yüklenemezse hata raporlanıp CPU verisiyle devam edilecek.
  6. Kapsam güvenliği grep kontrolü.

Unverified assumptions:
  - Modeller ön işlenmiş gerçek yüz resimleriyle doğru NMS ve landmark çıkışı üretir.
  - Dynamic batch 1-32 aralığı, modelin gerçek uygulamada da geçerlidir.
  - Konteyner tabanlı GPU ortamında (cuDNN 9 / CUDA 13) CUDAExecutionProvider yüklenecektir.

Approval gates:
  - Phase 0B çıktıları bu raporla kilitlenir.

Out-of-scope requests detected:
  - MODEL_MANIFEST.json güncellenmesi talep edilmedi; güncellenmedi.
  - Sistem CUDA/cuDNN kurulumu, Docker compose değişikliği, LFW, gerçek resim benchmark, API implementasyonu yok.
```

---

## Kullanılan Araçlar

| Araç | Görev | Çıktı |
|---|---|---|
| `tools/model_verification/verify_model_manifest.py` | İndirilen modellerin SHA-256 ve boyutunu Phase 0A manifestiyle karşılaştırma | `phase0b_manifest_verification.json` |
| `tools/model_verification/inspect_onnx_shapes.py` | ONNX graph girdi/çıkış şekillerini, opset ve düğüm sayılarını raporlama | `phase0b_onnx_shapes.json` |
| `tools/model_verification/ort_provider_smoke.py` | İndirilen her model için CPU ve CUDA InferenceSession oluşturma deneysi | `phase0b_ort_providers.json` |
| `tools/model_verification/dummy_batch_smoke.py` | Rastgele tensörlerle 1/4/8/16/32 batch inference (zaman ve çıkış şekli) | Ara dosyalar -> `phase0b_dummy_batch_cpu.json`, `phase0b_dummy_batch_cuda.json` |
| `tools/model_verification/merge_dummy_results.py` | Model başına üretilen CPU/CUDA sonuçlarını birleştirme | `phase0b_dummy_batch_cpu.json`, `phase0b_dummy_batch_cuda.json` |

Ortam:

- Python 3.12.3 (venv: `/home/user/.venv`)
- `numpy 2.2.6`
- `onnx 1.22.0`
- `onnxruntime-gpu 1.27.0`
- `ort.get_available_providers()` → `['TensorrtExecutionProvider', 'CUDAExecutionProvider', 'CPUExecutionProvider']`
- Host GPU: 3× Quadro RTX 8000, sürücü 580.105.08, CUDA Version 13.0 (heyecan)

> **Not:** `onnxruntime-gpu` kurulumu, kullanıcıdan açık onay alındıktan sonra `/home/user/.venv` içinde sadece `onnx` ve `onnxruntime-gpu` paketleri halinde yapıldı. Başka paket kurulmadı, sistem NVIDIA/CUDA paketleri değiştirilmedi.

---

## 1. Manifest Doğrulama (Salt Okunur)

`artifacts/model_benchmarks/MODEL_MANIFEST.json` üzerinde **hiçbir yazma işlemi yapılmadı**. Dosya salt okunur karşılaştırıldı.

Birincil modeller:

| Model | Rol | Durum | SHA-256 | Boyut (byte) |
|---|---|---|---|---|
| `scrfd_10g_320_batch.onnx` | detektör | **verified** | uyuşuyor | 16.926.136 |
| `arcface_w600k_r50_batch.onnx` | tanıyıcı | **verified** | uyuşuyor | 174.383.866 |

- Her iki modelin SHA-256 ve boyut değerleri manifestle birebir eşleşti.
- Diğer indirilen modeller (`face_detection_yunet_2026may`, `face_recognition_sface_2021dec`, `edgeface_xxs`) için de SHA/boyut kontrolü yapıldı; hepsi doğrulandı.
- `batch64` alternatifleri, gated standalone arcface deposu ve `yolov5-face` / `yolov8-face` gibi modeller `skipped` / `blocked` durumları nedeniyle dosyada yer almadı.

---

## 2. ONNX Şekil Denetimi

### 2.1 SCRFD (`scrfd_10g_320_batch.onnx`)

- **IR version:** 7
- **Opset:** 11
- **Girdi:** `input.1` → `[batch, 3, 320, 320]`, `FLOAT`
- **Çıkışlar (9 adet):**
  - `score_8`, `score_16`, `score_32` → `[batch, anchors_per_stride, 1]`
  - `bbox_8`, `bbox_16`, `bbox_32` → `[batch, anchors_per_stride, 4]`
  - `kps_8`, `kps_16`, `kps_32` → `[batch, anchors_per_stride, 10]` (5 keypoint × 2)
- **Düğüm sayısı:** 164
- **Initializer sayısı:** 127
- **Değerlendirme:** Beklenen `[N,3,320,320]` girdi ve stride 8/16/32 çıkışları doğrulandı; dinamik batch ekseni (`batch`) modelde tanımlı.

### 2.2 ArcFace (`arcface_w600k_r50_batch.onnx`)

- **IR version:** 6
- **Opset:** 11
- **Girdi:** `input.1` → `[batch, 3, 112, 112]`, `FLOAT`
- **Çıkış:** `683` → `[batch, 512]`, `FLOAT`
- **Düğüm sayısı:** 130
- **Initializer sayısı:** 237
- **Değerlendirme:** Beklenen `[N,3,112,112]` girdi ve 512-D embedding çıkışı doğrulandı; dinamik batch ekseni (`batch`) tanımlı.

### 2.3 Diğer Modeller (bilgi amaçlı, Phase 0B odak dışı)

- `face_detection_yunet_2026may.onnx`: girdi `[1, 3, height, width]`, statik batch 1, dinamik H/W.
- `face_recognition_sface_2021dec.onnx`: girdi `[1, 3, 112, 112]`, çıkış `[1, 128]`; öğrenilebilir parametreler graph input listesine dahil edilmiş (runtime'de uyarı üretiyor, işlevsel).
- `edgeface_xxs.onnx`: girdi `[batch_size, 3, 112, 112]`, çıkış `[batch_size, 512]`.

---

## 3. ONNX Runtime Sağlayıcı Smoke Testi

`phase0b_ort_providers.json` sonuçları:

| Model | CPU | CUDA (strict) | CUDA+CPU fallback |
|---|---|---|---|
| `scrfd_10g_320_batch.onnx` | OK | `CPUExecutionProvider` seçti (silent fallback) | `CPUExecutionProvider` seçti |
| `arcface_w600k_r50_batch.onnx` | OK | `CPUExecutionProvider` seçti (silent fallback) | `CPUExecutionProvider` seçti |
| diğer 3 model | OK | aynı silent fallback | aynı silent fallback |

Açıklama:

- `ort.get_available_providers()` `CUDAExecutionProvider` listeliyor, ancak `libcudnn.so.9` kütüphanesi sistemde bulunmadığı için CUDA runtime yüklenemiyor.
- ORT sessizce `CPUExecutionProvider`'a düşüyor; session oluşturma `Exception` fırlatmıyor.
- Bu nedenle **gerçek bir GPU çalıştırması bu host venv'de yapılamadı**; aşağıdaki dummy-batch CUDA denemesi de aynı hatayı raporlar.

Tam hata mesajı:

```text
Failed to load library /home/user/.venv/lib/python3.12/site-packages/onnxruntime/capi/libonnxruntime_providers_cuda.so with error: libcudnn.so.9: cannot open shared object file: No such file or directory
Failed to create CUDAExecutionProvider. Require cuDNN 9.* and CUDA 13.*.
```

---

## 4. CPU Dummy Batch Smoke (Birincil Modeller)

`phase0b_dummy_batch_cpu.json`.

Ortam: Intel CPU, `CPUExecutionProvider`, rastgele `float32` girdi, ısınma 2, 10 ölçüm.

### 4.1 SCRFD

| Batch | Girdi şekli | İlk çıkış şekli | Median ms |
|---|---|---|---|
| 1 | `[1,3,320,320]` | `[1,3200,1]` | 12.4 |
| 4 | `[4,3,320,320]` | `[4,3200,1]` | 31.5 |
| 8 | `[8,3,320,320]` | `[8,3200,1]` | 56.6 |
| 16 | `[16,3,320,320]` | `[16,3200,1]` | 132.1 |
| 32 | `[32,3,320,320]` | `[32,3200,1]` | 228.0 |

- Tüm batch boyutları başarılı.
- Çıkış şekilleri batch boyutuyla büyüdü; model dinamik batch kabul ediyor.

### 4.2 ArcFace

| Batch | Girdi şekli | Çıkış şekli | Median ms |
|---|---|---|---|
| 1 | `[1,3,112,112]` | `[1,512]` | 36.6 |
| 4 | `[4,3,112,112]` | `[4,512]` | 83.0 |
| 8 | `[8,3,112,112]` | `[8,512]` | 123.7 |
| 16 | `[16,3,112,112]` | `[16,512]` | 290.8 |
| 32 | `[32,3,112,112]` | `[32,512]` | 490.5 |

- Tüm batch boyutları başarılı.
- Çıkış boyutu 512-D ve batch ekseni dinamik.

> **Not:** Süreler rastgele girdiyle, ısınmadan sonra ölçülen ham inference süreleridir; ön işleme, NMS veya database I/O dahil değildir.

---

## 5. CUDA Dummy Batch Denemesi

`phase0b_dummy_batch_cuda.json`.

| Model | Durum | Açıklama |
|---|---|---|
| `scrfd_10g_320_batch.onnx` | `cuda_provider_unavailable` | ORT istenen `CUDAExecutionProvider` yerine `CPUExecutionProvider` seçti.|
| `arcface_w600k_r50_batch.onnx` | `cuda_provider_unavailable` | Aynı neden.|

Hata:

```text
Requested CUDAExecutionProvider but ORT selected ['CPUExecutionProvider'];
CUDA runtime shared library (libcudnn.so.9) could not be loaded.
```

Kullanıcı talimatına uygun olarak:

- Rastgele çözüm denenmedi.
- Sistem CUDA/cuDNN paketi kurulmadı.
- Docker/NVIDIA yapılandırması değiştirilmedi.
- CPU doğrulaması tamamlandı.
- CUDA durumu raporda "blocked/unavailable" olarak işaretlendi.

---

## 6. Kapsam Güvenliği Kontrolü

Çalıştırılan güvenlik grep'leri:

- `MODEL_MANIFEST.json` üzerinde `git diff` boş çıktı verdi; **dosya değiştirilmedi**.
- `backend/`, `frontend/`, `migrations/`, Docker compose, API route veya production `FacePipeline` dosyası oluşturulmadı.
- `/videos/`, `/imports/`, `/faces/`, `/oracle/`, `/objects/`, `/streams/` kalıpları sadece önceden var olan mimari dokümanlarda geçiyor; yeni araçlarda veya sonuç dosyalarında **yok**.
- `fake runtime pipeline` kalıpları sadece yönetişim dokümanlarında (`IMPLEMENTATION_GOVERNANCE.md`, `NO_SCOPE_CREEP_RULES.md`, v.b.) bulundu.

---

## 7. Değerlendirme ve Karar (Go / No-Go)

### Geçen Sonuçlar

1. İndirilen birincil model dosyaları SHA-256 ve boyut olarak manifestle eşleşiyor.
2. SCRFD girdi/çıkış şekilleri Phase 1 detektör kontratına uygun: `[N,3,320,320] → 9 multi-scale çıkış`.
3. ArcFace girdi/çıkış şekilleri Phase 1 tanıyıcı kontratına uygun: `[N,3,112,112] → [N,512]`.
4. CPU üzerinde `N = 1, 4, 8, 16, 32` dummy batch inference her iki modelde de başarılı ve çıkış şekilleri doğru.
5. Kod ve dosya kalıntıları Phase 1 kapsam kilidine uygundur; MODEL_MANIFEST.json değiştirilmemiştir.

### Bloklu Sonuç

- **CUDAExecutionProvider bu host venv ortamında yüklenemedi** (`libcudnn.so.9` eksik). Gerçek GPU inference ispatlanamadı.
- ORT sessiz bir CPU fallback yapıyor, bu da `session.get_providers()` kontrolü olmadan yanlış "GPU çalışıyor" yorumuna yol açabilirdi; betikler bu durumu yakalayıp raporladı.

### Phase 0B Kararı

- **CPU tarafı:** **GO** — Birincil modellerin şekil ve CPU batch davranışı doğrulandı.
- **GPU tarafı:** **BLOCKED / NO-GO** — Host'ta `onnxruntime-gpu` yüklenmiş olsa da `libcudnn.so.9` eksikliği nedeniyle gerçek CUDA çalıştırması yapılamadı.
- **Genel Phase 0B durumu:** `partial`.

### Öneri

GPU doğrulaması, DOCKER_GPU_STRATEGY_LOCK.md'de belirtilen `api-gpu-*` konteyner imajında, uyumlu `cuDNN 9` ve `CUDA 13` runtime içeren bir imajla çalıştırılmalıdır. Host sistemine sistem düzeyinde CUDA/cuDNN kurulmamalıdır; bu, kilitli stratejiye aykırıdır ve çevre tutarsızlığı riski doğurur.

---

## Ekler

- `artifacts/model_benchmarks/results/phase0b_manifest_verification.json`
- `artifacts/model_benchmarks/results/phase0b_onnx_shapes.json`
- `artifacts/model_benchmarks/results/phase0b_ort_providers.json`
- `artifacts/model_benchmarks/results/phase0b_dummy_batch_cpu.json`
- `artifacts/model_benchmarks/results/phase0b_dummy_batch_cuda.json`
