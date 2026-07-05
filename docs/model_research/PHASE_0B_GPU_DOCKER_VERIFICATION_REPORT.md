# Phase 0B-GPU Docker CUDA Dogrulama Raporu

Tarih: 2026-07-04
Durum: MERGENVISION_TASK_STATUS: pass
Karar: Phase 0B-GPU icin GO - ONNX Runtime CUDAExecutionProvider, kontrollu Docker GPU runtime'inda calisiyor.

## REFERENCE_CHECK

Task: Phase 0B-GPU: ONNX Runtime CUDAExecutionProvider'in Docker GPU runtime icinde calistigini dogrula; sonuc JSON'lari ve Turkce rapor uret.
Phase: Phase 0B (model dogrulama)
Allowed scope: model verification araclari, Docker imaji (smoke-test only), sonuc JSON'lari, rapor
Files allowed to change:
  - docs/model_research/PHASE_0B_GPU_DOCKER_VERIFICATION_REPORT.md
  - artifacts/model_benchmarks/results/phase0b_gpu_docker_*.json
  - tools/model_verification/docker/Dockerfile.gpu-ort-smoke
  - tools/model_verification/docker/README.md
  - tools/model_verification/run_gpu_docker_verification.sh
  - tools/model_verification/README.md
Files forbidden to change:
  - backend/**, frontend/**, migrations/**, docker-compose.yml, production image
  - artifacts/model_benchmarks/MODEL_MANIFEST.json
  - uygulama kodu, API router, /videos/* /imports/* /faces/* /oracle/* /streams/*
Local docs checked: AGENTS.md, CLAUDE.md, DOCKER_GPU_STRATEGY_LOCK.md, MODEL_ADAPTER_BOUNDARY.md, PHASE_IMPLEMENTATION_GATES.md, NO_SCOPE_CREEP_RULES.md, RUNTIME_TOPOLOGY.md, PHASE_0B_MODEL_SHAPE_PROVIDER_BATCH_REPORT.md
Architecture docs checked: yukaridakiler + MODEL_MANIFEST.json
Requirements checked: phase1recognitionrequirements.md, phase2videorequirements.md (gelecek siniri onayi)
Official docs checked via context7: ONNX Runtime CUDA Execution Provider, Docker GPU runtime, NVIDIA CUDA base image tagleri
Open-source references checked via exa/web: PyPI onnxruntime-gpu 1.27.0 wheel bagimliliklari (nvidia-cuda-runtime-cu13, nvidia-cudnn-cu13), nvidia/cuda:13.0.0-cudnn-runtime-ubuntu24.04
Existing local code inspected: tools/model_verification/verify_model_manifest.py, inspect_onnx_shapes.py, ort_provider_smoke.py, dummy_batch_smoke.py, merge_dummy_results.py, artifacts/model_benchmarks/MODEL_MANIFEST.json
Old lessons checked: olderDiagramsProvedWrog/, Demo12_VGGFace2Lab/docs/, VideoFaceGpuLab/docs/
Patterns to follow: bu rapor formati, REFERENCE_CHECK, UUIDv7, Model Adapter Boundary, veri sahipligi kurallari
Patterns rejected: host sisteminde CUDA/cuDNN kurulumu, --break-system-packages, GPU UUID/index hardcode, GPU 0 kullanimi (VLLM dolayi), production FacePipeline, placeholder route, model dosyasi/manifest degisikligi
Architecture decisions that apply: DOCKER_GPU_STRATEGY_LOCK.md (demo modda api-gpu-* servisleri ayni kodu kosar, GPU cihaz atamasi orchestrator/compose'da), MODEL_ADAPTER_BOUNDARY.md
Docker/GPU strategy that applies: nvidia/cuda:13.0.0-cudnn-runtime-ubuntu24.04 tabanli yalnizca dogrulama imaji; Python paketlerini container icinde venv'e kur
Data ownership rules that apply: sonuc JSON'larinda ham embedding veya image byte yoktur
Security/PII rules that apply: uygulama/kimlik verisi islenmemistir; testler dummy tensörlerle yapilmistir
Tests/verification planned:
  - ort_provider_smoke.py ile active provider kontrolu
  - dummy_batch_smoke.py batch 1/4/8/16/32 SCRFD + ArcFace on CUDA
  - GPU 1 ve GPU 2 replica testleri
  - scope-safety grep
Unverified assumptions:
  - GPU 0 test edilmedi, cunku VLLM/EngineCore tarafindan kullaniliyor.
  - NVIDIA surucu 580.105.08 ve Docker 29.1.5 zaten host'ta calisiyordu.
Approval gates: yok
Out-of-scope requests detected: yok

## Ozet

Phase 0B'nin host ortamindaki kanitlar (shape, provider, dummy batch) bu sefer Docker GPU konteyneri icinde tekrarlandi. Amac, "host'ta calisan CUDA ortaminin container'a tasindiginda sessizce CPU'ya dusmedigini" gostermektir. Bu hedefe ulasildi: her iki birincil model (SCRFD ve ArcFace) icin InferenceSession.get_providers() ilk sirasinda CUDAExecutionProvider gorundu ve batch 1-32 dummy inference'lari GPU 1 ve GPU 2 uzerinde basariyla tamamlandi.

## Ortam

- Host OS / docker: Docker 29.1.5, Docker Compose v5.0.2
- Host GPU / surucu: 3x NVIDIA Quadro RTX 8000, driver 580.105.08, CUDA Version 13.0 (surucu)
- GPU 0 durumu: VLLM/EngineCore ve diger surecler tarafindan kullanimda; Phase 0B-GPU'da test disi birakildi.
- GPU 1 / GPU 2: Phase 0B-GPU dogrulamasi yapildi.
- Konteyner base image: nvidia/cuda:13.0.0-cudnn-runtime-ubuntu24.04
- Konteyner Python paketleri: onnxruntime==1.27.0, onnx==1.22.0, numpy==2.5.0 (venv icinde)
- ORT available providers: [TensorrtExecutionProvider, CUDAExecutionProvider, CPUExecutionProvider]
- Incelenen modeller: scrfd_10g_320_batch.onnx, arcface_w600k_r50_batch.onnx (birincil); ayrica YuNet, SFace, EdgeFace provider smoke'da kontrol edildi.

## Yontem

1. Gorsel olustur: tools/model_verification/docker/Dockerfile.gpu-ort-smoke
   - Python 3, venv, onnxruntime, onnx, numpy
   - Repository read-only mount noktasi /workspace
   - NVIDIA_VISIBLE_DEVICES=all disaridan --gpus ile sinirlandirilabilir.
2. Otomasyon: tools/model_verification/run_gpu_docker_verification.sh
   - Imaji derle.
   - Konteyner icinde verify_model_manifest.py, inspect_onnx_shapes.py, ort_provider_smoke.py, dummy_batch_smoke.py, merge_dummy_results.py calistir.
   - GPU 1'de ontanimli bir dongu ve ayrica GPU 1+2 icin per-device dongu yap.
   - Ciktilari artifacts/model_benchmarks/results/ altina yaz.
3. Sessiz CPU fallback'ini onlemek icin: ort_provider_smoke.py hem ort.get_available_providers() hem de session.get_providers() dokumu verir; active_provider_first == CUDAExecutionProvider sarti arandi.
4. Dummy batch testi: Rastgele float32 tensörlerle batch 1, 4, 8, 16, 32 inference; cikis sekillerinin batch boyutunu korudugu kontrol edildi.

## Sonuclar

### 1. Provider Smoke (GPU 1, konteyner ici)

Tum modellerde cuda_strict ve cuda_with_fallback modlarinda aktif provider'in ilk sirasi CUDAExecutionProvider olarak goruldu. Bu, sessiz CPU fallback olmadigini gosterir.

active_providers: [CUDAExecutionProvider, CPUExecutionProvider]
active_provider_first: CUDAExecutionProvider

### 2. Dummy Batch - GPU 1

SCRFD batch 1: 4.40 ms, [1,3200,1], ok
SCRFD batch 4: 11.79 ms, [4,3200,1], ok
SCRFD batch 8: 21.43 ms, [8,3200,1], ok
SCRFD batch 16: 49.90 ms, [16,3200,1], ok
SCRFD batch 32: 107.18 ms, [32,3200,1], ok
ArcFace batch 1: 4.29 ms, [1,512], ok
ArcFace batch 4: 8.37 ms, [4,512], ok
ArcFace batch 8: 12.14 ms, [8,512], ok
ArcFace batch 16: 18.47 ms, [16,512], ok
ArcFace batch 32: 34.81 ms, [32,512], ok

### 3. Dummy Batch - GPU 2 (Replica)

Tum batch boyutlari basarili, overall_status: ok.

SCRFD batch 1: GPU1 4.40 ms / GPU2 4.50 ms, ok
SCRFD batch 4: GPU1 11.79 ms / GPU2 12.11 ms, ok
SCRFD batch 8: GPU1 21.43 ms / GPU2 23.03 ms, ok
SCRFD batch 16: GPU1 49.90 ms / GPU2 49.42 ms, ok
SCRFD batch 32: GPU1 107.18 ms / GPU2 109.77 ms, ok
ArcFace batch 1: GPU1 4.29 ms / GPU2 5.51 ms (ilk isinma etkisi), ok
ArcFace batch 4: GPU1 8.37 ms / GPU2 8.32 ms, ok
ArcFace batch 8: GPU1 12.14 ms / GPU2 11.86 ms, ok
ArcFace batch 16: GPU1 18.47 ms / GPU2 18.45 ms, ok
ArcFace batch 32: GPU1 34.81 ms / GPU2 34.26 ms, ok

### 4. Kapsam/Dosya Guvenligi

- git diff --name-only bos: izlenen kaynak dosyalarda degisiklik yok.
- Yeni dosyalar yalnizca izin verilen kapsamda:
  - tools/model_verification/docker/Dockerfile.gpu-ort-smoke
  - tools/model_verification/docker/README.md
  - tools/model_verification/run_gpu_docker_verification.sh
  - artifacts/model_benchmarks/results/phase0b_gpu_docker_*.json
- Scope grep sonuclari:
  - /videos/, /imports/, /faces/, /oracle/, /streams/ ifadeleri yalnizca yonetisim/mimari dokumanlarda; araclarda yok.
  - FastAPI, APIRouter, uvicorn yeni araclarda yok.
  - FacePipeline / sahte runtime pipeline yok.
  - 501 Not Implemented placeholder route yeni araclarda yok.
- MODEL_MANIFEST.json ve model dosyalari salt okunmus, degistirilmemis.

## Uretilen Ciktilar

- artifacts/model_benchmarks/results/phase0b_gpu_docker_ort_providers.json
- artifacts/model_benchmarks/results/phase0b_gpu_docker_manifest_verification.json
- artifacts/model_benchmarks/results/phase0b_gpu_docker_onnx_shapes.json
- artifacts/model_benchmarks/results/phase0b_gpu_docker_dummy_batch_cuda.json (GPU 1 birlesik)
- artifacts/model_benchmarks/results/phase0b_gpu_docker_dummy_batch_cuda_gpu1.json
- artifacts/model_benchmarks/results/phase0b_gpu_docker_dummy_batch_cuda_gpu2.json
- tools/model_verification/docker/Dockerfile.gpu-ort-smoke
- tools/model_verification/docker/README.md
- tools/model_verification/run_gpu_docker_verification.sh
- docs/model_research/PHASE_0B_GPU_DOCKER_VERIFICATION_REPORT.md (bu rapor)

## Araclar / Kaynaklar

- codebase-memory-mcp: Repository yapisi, mevcut Phase 0B raporu, MODEL_MANIFEST.json ve dogrulama betiklerinin kesfi.
- context7-mcp: ONNX Runtime CUDA Execution Provider, Docker GPU runtime, NVIDIA CUDA 13.0/cuDNN 9 runtime image tag bilgileri.
- exa/web: PyPI onnxruntime-gpu 1.27.0 bagimliliklari ve resmi NVIDIA hub tag sayfalari.
- bash/filesystem: imaj derleme, konteyner calistirma, JSON ciktilari, git status, grep dogrulamalari.

## Kullanilan Yetkinlikler (Skills)

- brainstorming
- writing-plans
- executing-plans
- systematic-debugging
- verification-before-completion
- codebase-memory
- context7-mcp
- self-review / code-review

## Dogrulama (Verification)

- Git diff: git diff --name-only -> Bos: hicbir izlenen dosya degistirilmemis.
- Untracked files: git status --short -> Yeni izinli dosyalar disinda kalan sadece halihazirda var olan dokumanlar.
- ORT provider smoke: python tools/model_verification/ort_provider_smoke.py --provider CUDA ... -> active_provider_first: CUDAExecutionProvider
- Dummy batch GPU 1: python tools/model_verification/dummy_batch_smoke.py ... -> Tum batch'ler status: ok
- Dummy batch GPU 2: Per-device loop script icinde -> Tum batch'ler status: ok
- Scope grep: /videos/, /imports/, 501, FacePipeline, FastAPI -> Yeni araclarda eslesme yok
- Lint / typecheck: N/A -> Rapor ve dogrulama betikleri; proje uygulama koduna dokunulmadi.

## Dogrulanmamis Varsayımlar

1. GPU 0: Phase 0B-GPU'da GPU 0 test edilmedi; uretim oncesi tum 3 GPU'yu kapsayacak sekilde tekrar calistirilmali.
2. Host NVIDIA surucusu / Docker runtime: Test edilmedi, cunku zaten calisir durumdaydi (nvidia-smi ve docker run --gpus all nvidia/cuda ... nvidia-smi basarili).
3. Image optimizasyonu: TensorRT opsiyonel provider olarak gorunuyor, ancak TensorRT engine olusturma test edilmedi.
4. Gercek goruntu accuracy/LFW: Bu rapor sadece shape + dummy inference + provider kanitidir; tanima dogrulugu Phase 0B host raporunun kapsamindadir.

## Sonraki Onerilen Adimlar

1. GPU 0 bosaldiginda tools/model_verification/run_gpu_docker_verification.sh'i GPU 0 da dahil olacak sekilde tekrar calistir; sonuclari phase0b_gpu_docker_dummy_batch_cuda_gpu0.json olarak ekle.
2. Phase 1 API gelistirme sirasinda api-gpu-* servislerinin ayni mergenvision-phase0b-gpu-ort-smoke:local imaji degil, production Dockerfile'ini kullanacagini netlestir; bu imaj yalnizca dogrulama icindir.
3. Model adapter boundary dokumanina gore DetectorAdapter + RecognizerAdapter implementasyonuna gec; Qdrant koleksiyonunun 512-D embedding uzayina gore olusturulacagini dogrula (arcface_w600k_r50_batch.onnx cikisi [B,512]).
4. Phase 0B sonuclarini kapat ve Phase 1 implementasyon kapisindan gec.
