# PHASE 0A-Lite Model Access Report — MergenVision

> **Durum:** Tamamlandı  
> **Dil:** Rapor Türkçedir; model adları, dosya yolları, URL'ler ve CLI komutları İngilizce kalır.  
> **Kapsam:** Sadece model erişimi, indirme ve kaynak/lisans doğrulama. Mimari, benchmark, çıkarım veya uygulama kodu içermez.

---

## 1. Executive Summary

Bu fazda Faz -1 raporunda önerilen birincil ve yedek model dosyalarının resmi kaynaklardan gerçekten erişilebilir olup olmadığı test edilmiştir.

- **Birincil dedektör** `scrfd_10g_320_batch.onnx` **başarıyla indirildi** (alonsorobots/scrfd_320_batched, halka açık).
- **Birincil tanıyıcı** `arcface_w600k_r50_batch.onnx` **başarıyla indirildi**; aynı model, ayrı `alonsorobots/arcface_w600k_r50_batched` reposunda **401 / gated** olduğu için halka açık `scrfd_320_batched` reposundan alındı.
- **Batch-64 teknoloji önizleme çifti** kaydedildi ancak **indirilmedi**; Faz 0A kapsamı dışı.
- **Yedek dedektör** OpenCV YuNet (`face_detection_yunet_2026may.onnx`) **indirildi** (MIT).
- **Yedek tanıyıcı** OpenCV SFace (`face_recognition_sface_2021dec.onnx`) **indirildi** (Apache-2.0).
- **Araştırma tanıyıcı** EdgeFace-XXS (`edgeface_xxs.onnx`) **indirildi** (MIT).
- **OpenVINO ArcFace** doğrudan indirilmedi; resmi `omz_downloader` aracı gerekiyor. Gelecek yedek olarak kaydedildi.
- **YOLOv5-face / YOLOv8-face** kaynak kodu açık ancak önceden eğitilmiş ağırlıklar yalnızca Google Drive/Baidu bağlantılarıyla dağıtılıyor; güvenilir doğrudan indirme URL'si bulunamadı.

**Önerilen sonraki gate:** Model şekil / execution-provider doğrulaması (Phase 0B). Birincil çift erişilebilir ve diskte; mimari tasarım bundan sonra başlayabilir.

---

## 2. Scope and Non-Goals

Bu fazın kapsamı:

- Aday model dosyalarının resmi kaynaklardan erişilebilirliğini doğrulamak.
- Erişilebilir dosyaları `artifacts/model_benchmarks/models/` altına indirmek.
- SHA-256 hash ve dosya boyutu ile indirim kanıtı oluşturmak.
- Her model için lisans, giriş/çıkış şekli ve batch iddiasını kaydetmek.
- `MODEL_MANIFEST.json` ve bu raporu yazmak.

Bu fazın kapsamı **değildir**:

- **Benchmark** yapmak.
- **LFW** veya herhangi bir veri seti indirmek.
- **Inference / çıkarım** çalıştırmak.
- Uygulama **implementasyonu** yazmak.
- **Mimari tasarım** oluşturmak.
- Benchmark scriptleri, Python modülleri, backend/frontend dosyaları veya migration dosyaları oluşturmak.
- Docker Compose değiştirmek.
- `git add`, `git commit` veya `git push` yapmak.
- Gated/login gerektiren kaynakları atlatmak veya güvenilmeyir ayna siteler kullanmak.

---

## 3. REFERENCE_CHECK

```text
REFERENCE_CHECK

Task:
  MergenVision Phase 0A-Lite model access and source verification.
  Verify that the candidate model files are legitimately accessible,
  downloadable, and usable as source candidates before architecture
  and implementation.

Requirements checked:
  - /home/user/MergenVision/requirements/phase1recognitionrequirements.md
    (Oracle, 10M kişi ölçek, fotoğraf tabanlı tanıma, kişi-fotoğraf eşleştirme,
    gizlilik, ölçeklenebilirlik)
  - /home/user/MergenVision/requirements/phase2videorequirements.md
    (video Faz 2 genişlemesi; bu fazda sadece gelecekteki etki notu olarak kullanıldı)
  - /home/user/MergenVision/opensourceReferences/references.md
    (reference-first politika, ONNX Runtime, InsightFace, OpenCV Zoo, vb. bağlantılar)

Local reports checked:
  - /home/user/MergenVision/docs/model_research/PHASE_MINUS_1_MODEL_SELECTION_REPORT.md
    (Faz -1 varsayım raporu: aday model çifti, batch stratejisi, lisans riskleri)
  - /home/user/MergenVision/olderDiagramsProvedWrog/01_system_purpose.md
  - /home/user/MergenVision/olderDiagramsProvedWrog/02_high_level_architecture.md
  - /home/user/MergenVision/olderDiagramsProvedWrog/03_docker_compose_architecture.md
  - /home/user/MergenVision/olderDiagramsProvedWrog/README.md

Older diagrams/reports checked:
  - /home/user/Demo/Demo12_VGGFace2Lab/docs/ (eski SCRFD/ArcFace batch deney raporları)
  - /home/user/Demo/VideoFaceGpuLab/docs/ (eski ONNX Runtime/IOBinding/batch raporları)
  - codebase-memory-mcp arama sonuçları: VideoFaceGpuLab içinde ScrfdDetectorAdapter,
    model_registry.py, source_refs.py; Demo12_VGGFace2Lab içinde batched_onnx_provider.py,
    run_lfw_batched_worker.py, compare_batched_onnx_vs_buffalo_l.py

Official docs checked:
  - Context7 /microsoft/onnxruntime: CUDAExecutionProvider, TensorRTExecutionProvider,
    IOBinding, InferenceSession provider sıralaması
  - ONNX Runtime Python API summary (Context7) - sadece bağlam için

Model sources checked:
  - https://huggingface.co/alonsorobots/scrfd_320_batched
    (primary detector + primary recognizer fallback)
  - https://huggingface.co/alonsorobots/scrfd_320_batched_64
    (batch-64 future candidate)
  - https://huggingface.co/alonsorobots/arcface_w600k_r50_batched
    (standalone recognizer repo; gated)
  - https://docs.openvino.ai/2023.3/omz_models_model_face_recognition_resnet100_arcface_onnx.html
    (OpenVINO ArcFace)
  - https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet
    (OpenCV YuNet)
  - https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface
    (OpenCV SFace)
  - https://github.com/yakhyo/edgeface-onnx
    (EdgeFace ONNX)
  - https://github.com/deepcam-cn/yolov5-face
    (YOLOv5-face source)
  - https://github.com/derronqi/yolov8-face
    (YOLOv8-face source)

Implementation details found:
  - alonsorobots/scrfd_320_batched reposundaki dosyalar:
    - scrfd_10g_320_batch.onnx  -> 16,926,136 bytes, SHA 875763ba...
    - arcface_w600k_r50_batch.onnx -> 174,383,866 bytes, SHA 6afbf406...
  - alonsorobots/scrfd_320_batched_64 reposundaki dosyalar:
    - scrfd_10g_320_batch64.onnx -> 16,926,136 bytes
    - arcface_w600k_r50_batch64.onnx -> 174,383,866 bytes
  - SCRFD girdi: [N, 3, 320, 320], NCHW, RGB, normalizasyon (x-127.5)/128, 5 keypoint.
  - ArcFace girdi: [N, 3, 112, 112], NCHW, RGB; çıktı: [N, 512] L2 normalize vektör.
  - YuNet 2026may: dinamik H/W, MIT lisans.
  - SFace: MobileFaceNet tabanlı, Apache-2.0, 5-landmark warping, çıktı 128-D bekleniyor.
  - EdgeFace: MIT, GitHub release'dan indiriliyor.

Patterns to follow:
  - Resmi kaynaklardan indir; aynalara ve bypass'e gitme.
  - İndirilen dosyaları manifeste SHA-256 ile kaydet.
  - Gated modelleri raporla ve alternatif yasal kaynak ara.
  - Büyük dosya (>1GB) indirmeden önce onay al.

Patterns rejected:
  - Standalone ArcFace reposunun 401'ini bypass etmeye çalışmak.
  - Google Drive / Baidu ağırlık bağlantıları olan YOLO modellerini indirmek
    (doğrudan resmi olmayan dağıtım).
  - ONNX şekil incelemesi için bu fazda paket kurmak veya script yazmak.

How this maps to MergenVision:
  - Faz 1 için birincil model çifti (SCRFD + ArcFace) erişilebilir ve diskte var.
  - InsightFace lisansı ticari kullanım için uygun değil; yedek MIT/Apache-2.0
    çift (YuNet + SFace) hazır.
  - Model config dosya adlarını varsaymayacak; modelName/modelVersion saklanacak.
  - Qdrant koleksiyon boyutu hangi tanıyıcı seçilirse ona göre ayarlanacak.

Allowed outputs:
  - docs/model_research/PHASE_0A_MODEL_ACCESS_REPORT.md
  - artifacts/model_benchmarks/models/
  - artifacts/model_benchmarks/MODEL_MANIFEST.json

Not allowed:
  - benchmark scripts
  - LFW
  - inference
  - app implementation
```

---

## 4. Local Context Read

| Source | Found? | Path | Notes |
|---|---|---|---|
| Phase -1 model selection report | yes | `docs/model_research/PHASE_MINUS_1_MODEL_SELECTION_REPORT.md` | Birincil çift ve yedeklerin varsayım raporu. |
| Phase 1 requirements | yes | `requirements/phase1recognitionrequirements.md` | Oracle, fotoğraf tabanlı tanıma, 10M ölçek. |
| Phase 2 video requirements | yes | `requirements/phase2videorequirements.md` | Gelecek video genişlemesi; bu fazda sınır notu. |
| Reference-first policy | yes | `opensourceReferences/references.md` | Zorunlu REFERENCE_CHECK formatı ve resmi linkler. |
| Older diagrams / reports | yes | `olderDiagramsProvedWrog/` | Eski dizaynlar; sadece ders çıkarılan dokümanlar. |
| Old VGGFace2 lab reports | yes | `/home/user/Demo/Demo12_VGGFace2Lab/docs/` | Eski batch ArcFace deneyleri. |
| Old VideoFace GPU lab reports | yes | `/home/user/Demo/VideoFaceGpuLab/docs/` | Eski SCRFD adaptörü / ONNX Runtime deneyleri. |

---

## 5. Model Source Verification

| Candidate | Role | Source | Maintainer | License | Access Status | Expected Files | Notes |
|---|---|---|---|---|---|---|---|
| `alonsorobots/scrfd_320_batched` | detector + recognizer | https://huggingface.co/alonsorobots/scrfd_320_batched | alonsorobots | insightface-non-commercial | public | `scrfd_10g_320_batch.onnx`, `arcface_w600k_r50_batch.onnx` | Birincil dedektör ve tanıyıcı aynı repoda; dosyalar indirildi. |
| `alonsorobots/scrfd_320_batched_64` | detector + recognizer | https://huggingface.co/alonsorobots/scrfd_320_batched_64 | alonsorobots | insightface-non-commercial | public | `scrfd_10g_320_batch64.onnx`, `arcface_w600k_r50_batch64.onnx` | Batch 1-64 gelecek adayı; indirilmedi. |
| `alonsorobots/arcface_w600k_r50_batched` | recognizer | https://huggingface.co/alonsorobots/arcface_w600k_r50_batched | alonsorobots | insightface-non-commercial (beklenen) | gated / HTTP 401 | `arcface_w600k_r50_batch.onnx` | Standalone repo 401 döndürdü; aynı dosya diğer repoda public. |
| OpenCV YuNet | detector | https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet | opencv | MIT | public | `face_detection_yunet_2026may.onnx` | Dinamik H/W, hafif dedektör; indirildi. |
| OpenCV SFace | recognizer | https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface | opencv | Apache-2.0 | public | `face_recognition_sface_2021dec.onnx` | MobileFaceNet tabanlı; indirildi. |
| OpenVINO face-recognition-resnet100-arcface-onnx | recognizer | https://docs.openvino.ai/2023.3/omz_models_model_face_recognition_resnet100_arcface_onnx.html | Intel / OpenVINO | Apache-2.0 (orijinal) | official downloader | `face-recognition-resnet100-arcface-onnx` IR/ONNX | `omz_downloader --name face-recognition-resnet100-arcface-onnx` gerekli. |
| EdgeFace ONNX | recognizer | https://github.com/yakhyo/edgeface-onnx | yakhyo | MIT | public | `edgeface_xxs.onnx` | GitHub release'dan indirildi. |
| YOLOv5-face | detector | https://github.com/deepcam-cn/yolov5-face | deepcam-cn | GPL-3.0 | source-only | `.pt` weights | Ağırlıklar Google Drive/Baidu; doğrudan resmi link yok. |
| YOLOv8-face | detector | https://github.com/derronqi/yolov8-face | derronqi | GPL-3.0 | source-only | `.pt` weights | Ağırlılar Google Drive; doğrudan resmi link yok. |
| MobileFaceNet ONNX | recognizer | OpenCV SFace / EdgeFace ile kapsandı | - | - | - | - | Ayrı bir güvenilir bağımsız ONNX modeli bulunmadı. |

---

## 6. Download Results

| Model | Status | Local Path | Size | SHA256 | Notes |
|---|---|---|---|---|---|
| `scrfd_10g_320_batch.onnx` | downloaded | `artifacts/model_benchmarks/models/scrfd_10g_320_batch.onnx` | 16,926,136 bytes | `875763ba0b0725de5097f2bf2900fb3690667f53ab0f642a0ad31f94581483f8` | Birincil dedektör. |
| `arcface_w600k_r50_batch.onnx` | downloaded | `artifacts/model_benchmarks/models/arcface_w600k_r50_batch.onnx` | 174,383,866 bytes | `6afbf406aa229a439abbca7436cc42be254d4e3af6200d8b7ae4c1fec0c18f2f` | Birincil tanıyıcı; public SCRFD reposundan alındı. |
| `face_detection_yunet_2026may.onnx` | downloaded | `artifacts/model_benchmarks/models/face_detection_yunet_2026may.onnx` | 229,738 bytes | `ebafce4e3c118d6554634be5c27ab333b4c047a9a8c3faf1d7cf93101c22f0f0` | Yedek dedektör. |
| `face_recognition_sface_2021dec.onnx` | downloaded | `artifacts/model_benchmarks/models/face_recognition_sface_2021dec.onnx` | 38,696,353 bytes | `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79` | Yedek tanıyıcı. |
| `edgeface_xxs.onnx` | downloaded | `artifacts/model_benchmarks/models/edgeface_xxs.onnx` | 5,133,128 bytes | `dc674de4cbc77fa0bf9a82d5149558ab8581d82a2cd3bb60f28fd1a5d3ff8a2f` | Araştırma / kenar cihaz tanıyıcı. |

---

## 7. Blocked / Gated Models

**`alonsorobots/arcface_w600k_r50_batched` standalone repository**

- **HTTP durumu:** `401 Unauthorized`
- **Hata mesajı:** `Invalid username or password.` ; `www-authenticate: Bearer realm="Authentication required"`
- **Sebep:** Hugging Face bu repoyu gated veya en azından kimlik doğrulaması gerektiren şekilde ayarlamış.
- **Neden bypass edilmedi:** Kullanıcı talimatı açık: login/token/gated erişim gerektiren modellerde dur, atlatma, ayna arama.
- **Çözüm:** Aynı `arcface_w600k_r50_batch.onnx` dosyası `alonsorobots/scrfd_320_batched` reposunda halka açık olarak bulunduğu için dosya oradan indirildi.
- **Kullanıcı aksiyonu:** Eğer ileride standalone repoya özel erişim gerekirse Hugging Face token / lisans kabulü sağlanmalı; şu an için gerek yok.

**`yolov5-face` / `yolov8-face` önceden eğitilmiş ağırlıkları**

- Resmi GitHub release'i yok; ağırlıklar Google Drive ve Baidu linklerinde.
- Güvenilir, doğrudan ve sürdürülebilir bir indirme URL'si bulunamadığı için indirilmedi.
- Faz 1'de SCRFD ve YuNet dedektörleri yeterli olduğundan bu bir engel değil.

**OpenVINO ArcFace**

- Doğrudan `.onnx` URL'si bu fazda bulunamadı.
- Resmi `omz_downloader --name face-recognition-resnet100-arcface-onnx` aracı mevcut.
- İndirilmedi çünkü `omz_downloader` çalıştırmak paket kurulumu / araç çalıştırma anlamına gelir; Phase 0A kapsamı dışı. Faz 0B'de denenebilir.

---

## 8. License Notes

### Demo / prototip için kabul edilebilir aday
- `scrfd_10g_320_batch.onnx` + `arcface_w600k_r50_batch.onnx`
- Lisans: **insightface-non-commercial** (InsightFace non-commercial research only).
- Hız ve doğruluk beklenen en iyi çift. Ticari kullanım için kesinlikle hukuk onayı gerekir.

### Üretim / hukuk onayı gerektiren
- Yukarıdaki InsightFace çifti ticari MergenVision dağıtımında kullanılmadan önce `recognition-oss-pack@insightface.ai` ile iletişime geçilmeli.

### Daha güvenli lisans yedeği
- **Dedektör:** OpenCV YuNet (`face_detection_yunet_2026may.onnx`) — **MIT**
- **Tanıyıcı:** OpenCV SFace (`face_recognition_sface_2021dec.onnx`) — **Apache-2.0**
- Bu çift üretimde daha az lisans riski taşır ancak doğruluk/hız birincil çifte göre daha düşük olabilir; Phase 0B kıyaslama ile karşılaştırılmalı.

### Araştırma / kenar cihaz yedeği
- EdgeFace-XXS (`edgeface_xxs.onnx`) — **MIT**
- Çok küçük (4.9 MB). Doğruluk ve uyumluluk test edilmemiş; araştırma adayı.

---

## 9. Architecture Impact Notes

Henüz mimari tasarım yapılmıyor; sadece erişim doğrulamasından çıkan etkiler:

- **Birincil model çifti erişilebilir:** `scrfd_10g_320_batch.onnx` ve `arcface_w600k_r50_batch.onnx` diskte, Faz 0B model şekil/provider doğrulamasına hazır.
- **Yedek çift de indirildi:** YuNet + SFace; lisans riski düşük ve canlı alternatif.
- **Model config dosya adlarını varsaymamalı:** `modelName`, `modelVersion` ve `modelPath` gibi alanlar runtime config'den alınmalı.
- **Detector / recognizer adaptör sınırı korunmalı:** Farklı lisanslı modeller arasında geçiş, iyi tanımlanmış adaptör yüzeyi ile mümkün olmalı.
- **Qdrant vektör boyutu:** ArcFace 512-D; SFace 128-D bekleniyor. Koleksiyon boyutu seçilen tanıyıcıya bağlı olmalı.
- **Batch iddiası doğrulanmadı:** Dinamik batch `N` iddia ediliyor ama şekil / uyumluluk Phase 0B'de test edilmeli.

---

## 10. Next Recommended Step

**Önerilen sonraki gate:** Phase 0B — model şekil / execution provider doğrulaması.

Sebep:
- Birincil model çifti diskte ve public.
- Lisans riski biliniyor; üretim kararı daha sonra.
- ONNX graph giriş/çıkş isimleri, `dynamic_axes`, `CUDAExecutionProvider` / `CPUExecutionProvider` yüklenmesi ve batch=1..32 davranışı henüz doğrulanmadı.
- Mimari tasarım, model kanıtı olduktan sonra daha güvenli yapılır.

---

## 11. MCP / Tool Accountability

| Tool/MCP | Used/Skipped | What checked | Result | Limitation |
|---|---|---|---|---|
| `codebase-memory-mcp` | used | MergenVision structure, Phase -1 report, olderDiagramsProvedWrog, old VideoFaceGpuLab/Demo12_VGGFace2Lab SCRFD/ArcFace references | MergenVision indexed (151 nodes); old reports show SCRFD adapter, batched_onnx_provider, model_registry | Docs excluded from index by design; old projects are external reference only |
| `context7` | used | ONNX Runtime CUDAExecutionProvider, TensorRTExecutionProvider, IOBinding docs | Confirmed `providers=['CUDAExecutionProvider', 'CPUExecutionProvider']`, IOBinding Python API usage | Docker/NVIDIA docs not queried because Phase 0A scope is download/license only |
| `exa` / webfetch | used | HF model cards, GitHub OpenCV Zoo, EdgeFace, YOLOv5/8, OpenVINO model card | All primary and fallback pages opened; sizes/shapes extracted | Some pages are JS-heavy; webfetch got full markdown |
| `postman` | skipped | No API runtime in this phase | - | - |
| `playwright` | skipped | No UI runtime in this phase | - | - |
| `ruflo` | skipped | Forbidden by task | - | - |
| `21st` | skipped | Forbidden by task | - | - |

---

## 12. Skills Used

| Skill | Used/Skipped | Purpose |
|---|---|---|
| brainstorming | used | Initial approach selection before downloads (which sources to try first, fallback plan). |
| writing-plans | used | Structured the gate-by-gate Phase 0A plan in this session. |
| executing-plans | used | Followed Gate 0-5 in order, created artifacts, verified. |
| systematic-debugging | used | When standalone ArcFace returned 401, root-caused as gated access rather than guessing broken URL; chose alternate official source. |
| verification-before-completion | used | Re-hashed downloads, listed files, and ran gate 5 verification commands before claiming completion. |
| codebase-memory | used | Indexed MergenVision and searched old VideoFace/VGGFace2 labs for SCRFD/ArcFace prior art. |
| context7-mcp | used | Fetched current ONNX Runtime provider/IOBinding documentation for context. |
| requesting-code-review | skipped | No code merge or PR in this phase; self-review applied to Markdown report and JSON manifest. |

---

## 13. Verification Before Completion

Run and paste summarized result:

```bash
test -f docs/model_research/PHASE_0A_MODEL_ACCESS_REPORT.md && echo "report exists"
test -f artifacts/model_benchmarks/MODEL_MANIFEST.json && echo "manifest exists"
find artifacts/model_benchmarks/models -maxdepth 1 -type f -printf "%f %s bytes\n" | sort || true
sha256sum artifacts/model_benchmarks/models/* || true
grep -n "REFERENCE_CHECK" docs/model_research/PHASE_0A_MODEL_ACCESS_REPORT.md
grep -n "benchmark\|LFW\|inference\|implementation" docs/model_research/PHASE_0A_MODEL_ACCESS_REPORT.md || true
git status --short || true
git diff --stat || true
git diff --name-only || true
```

**Outcome (actual verification output):**

- `report exists`
- `manifest exists`
- Disk sizes:
  - `arcface_w600k_r50_batch.onnx` 174,383,866 bytes
  - `edgeface_xxs.onnx` 5,133,128 bytes
  - `face_detection_yunet_2026may.onnx` 229,738 bytes
  - `face_recognition_sface_2021dec.onnx` 38,696,353 bytes
  - `scrfd_10g_320_batch.onnx` 16,926,136 bytes
- SHA-256 hashes:
  - `6afbf406aa229a439abbca7436cc42be254d4e3af6200d8b7ae4c1fec0c18f2f  arcface_w600k_r50_batch.onnx`
  - `dc674de4cbc77fa0bf9a82d5149558ab8581d82a2cd3bb60f28fd1a5d3ff8a2f  edgeface_xxs.onnx`
  - `ebafce4e3c118d6554634be5c27ab333b4c047a9a8c3faf1d7cf93101c22f0f0  face_detection_yunet_2026may.onnx`
  - `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79  face_recognition_sface_2021dec.onnx`
  - `875763ba0b0725de5097f2bf2900fb3690667f53ab0f642a0ad31f94581483f8  scrfd_10g_320_batch.onnx`
- SHA-256 hashes match `MODEL_MANIFEST.json`.
- `git status` and `git diff` fail with `fatal: not a git repository` because `/home/user/MergenVision` is not a git repository.
