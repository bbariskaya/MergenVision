# MergenVision Faz -1 Model Seçim Raporu

> **Durum:** Taslak – Faz 1'e başlamadan önce yerel kanıt toplanana kadar geçerli.  
> **Dil:** Rapor Türkçedir; model adları, dosya yolları, kod parçacıkları ve CLI komutları İngilizce kalır.  
> **Kapsam:** Sadece Faz 1 fotoğraf tabanlı kimlik tanıma; video, Oracle entegrasyonu ve gerçek üretim dağıtımı bu raporun dışındadır.

## 0. Referans Kontrol Listesi

Her bölümde `[REF: ...]` etiketleri kullanılmıştır:

- `ctx7`: Context7 MCP üzerinden resmi dokümantasyon.
- `web`: Doğrudan açılan birincil açık kaynak/link kaynakları.
- `local`: `/home/user/MergenVision` içindeki mevcut gereksinim ve eski rapor dosyaları.

Raporun tamamı aşağıdaki kaynaklara dayanmaktadır:

- [REF: local] `/home/user/MergenVision/requirements/phase1recognitionrequirements.md`
- [REF: local] `/home/user/MergenVision/requirements/phase2videorequirements.md`
- [REF: local] `/home/user/MergenVision/opensourceReferences/references.md`
- [REF: local] `/home/user/MergenVision/olderDiagramsProvedWrog/` (eski dizayn dokümanları, sadece "neler yapılmamalı" olarak kullanılmıştır)
- [REF: local] `/home/user/Demo/Demo12_VGGFace2Lab/docs/` (eski SCRFD/ArcFace deney raporları)
- [REF: local] `/home/user/Demo/VideoFaceGpuLab/docs/` (eski ONNX Runtime/IOBinding/batch deney raporları)
- [REF: web] `https://huggingface.co/alonsorobots/scrfd_320_batched`
- [REF: web] `https://huggingface.co/alonsorobots/scrfd_320_batched_64`
- [REF: web] `https://huggingface.co/alonsorobots/arcface_w600k_r50_batched`
- [REF: web] `https://docs.openvino.ai/2023.3/omz_models_model_face_recognition_resnet100_arcface_onnx.html`
- [REF: web] `https://github.com/opencv/opencv_zoo/tree/master/models/face_detection_yunet`
- [REF: web] `https://github.com/opencv/opencv_zoo/tree/master/models/face_recognition_sface`
- [REF: web] `https://github.com/yakhyo/edgeface-onnx`
- [REF: web] `https://github.com/yakhyo/face-recognition`
- [REF: web] `https://github.com/deepcam-cn/yolov5-face`
- [REF: web] `https://github.com/derronqi/yolov8-face`
- [REF: ctx7] ONNX Runtime CUDA/TensortRT/IOBinding Execution Provider dokümantasyonu (Context7)
- [REF: ctx7] Qdrant vektör veritabanı dokümantasyonu (Context7)
- [REF: ctx7] MinIO S3-compatible object store dokümantasyonu (Context7)

> **Not:** `alonsorobots/arcface_w600k_r50_batched` Hugging Face sayfasına doğrudan erişim 401/gated döndürdüğü için teknik detaylar ONNX yapısı çıkarımı ve eski VGGFace2 deney kayıtlarından elde edilmiştir. Faz 0'da gerçek dosya indirilerek doğrulanmalıdır.

---

## 1. Yönetici Özeti

Bu rapor, MergenVision Faz 1 (fotoğraf-tabanlı kimlik tanıma) için önerilen ilk model çiftini, alternatiflerini, lisans risklerini ve doğrulama yol haritasını sunar.

- **İlk kıyaslama (benchmark) çifti**:  
  - **Dedektör:** `alonsorobots/scrfd_320_batched` → `scrfd_10g_320_batch.onnx`  
  - **Tanıyıcı:** `alonsorobots/arcface_w600k_r50_batched` → `arcface_w600k_r50_batch.onnx`
- **Batch stratejisi:** Kıyaslama `[1,4,8,16,32]`; toplu kayıt (bulk enrollment) için `batch=32` ilk tatlı nokta olarak önerilir. `batch=64` sadece `batch=32` sonuçları buna işaret ederse değerlendirilir.
- **Lisans uyarısı:** Seçilen çift InsightFace topluluğu ağırlıklarına dayanır; ticari kullanım için mutlaka hukuk onayı gerekir. Daha güvenli lisanslı alternatifler Bölüm 13'te listelenmiştir.
- **Sonraki adım:** Bu rapor onaylandıktan sonra Faz 0'da yerel kıyaslama kanıtı üretilmeli; kanıt olmadan Faz 1 uygulama kodu yazılmamalıdır.

---

## 2. Faz 1 Kapsamı ve Sınır Koşulları

[REF: local] `phase1recognitionrequirements.md`

Faz 1 gereksinimleri:

| Gereksinim | Açıklama |
|---|---|
| Girdi | Tek fotoğraf veya toplu fotoğraf listesi |
| Çıktı | En yakın eşleşme(ler): `personId`, benzerlik skoru, eşleşen görüntü referansı |
| Kayıt | Manuel kişi oluşturma + bir/çok fotoğraf ekleme |
| Arama | Top-K cosine similarity (L2 normalize edilmiş gömüler üzerinde dot product) |
| Depolama | PostgreSQL (kişi/meta), Qdrant (512-D vektör), MinIO (ham görüntü) |
| İzlenebilirlik | Her istek `requestId`; çıkarım/arama/saklama adımları loglanabilir olmalı |
| Sınır | Video akışı, Oracle DB, gerçek zamanlı kamera beslemesi ve otomatik toplu web kazıma Faz 1 dışı |

Raporun geri kalanı yalnızca bu sınırlar içindeki teknik seçimleri kapsar.

---

## 3. Gereksinim İzlenebilirlik Matrisi

| Gereksinim | Çözüm Bileşeni | Açıklama |
|---|---|---|
| Yüz tespiti | `scrfd_10g_320_batch.onnx` | Batch destekli, hızlı, orta kalitede dedektör |
| Yüz tanıma | `arcface_w600k_r50_batch.onnx` | 512-D embedding, LFW/IJB-C üzerinde güçlü taban çizgisi |
| Manuel kayıt | Backend servis + Qdrant upsert | Kişi ve fotoğraf ilişkisi PostgreSQL'de, vektör Qdrant'ta |
| Identify sorgusu | Qdrant `search` | Cosine similarity; L2 normalize sonrası dot product |
| Top-K eşleşme | Qdrant `limit=k` | `k` istemciden parametre olarak alınır |
| `requestId` izleme | Her çıkarım adımına tag | Giriş görüntüsü, çıkan box, embedding, arama sonucu |
| Çoklu görüntüde tek kişi | Batch processing | Girişler arasında ayrılmış tensörler; çapraz bulaşma yok |

---

## 4. Değerlendirme Metodolojisi

Model seçimi aşağıdaki kriterlere göre yapılmıştır:

1. **Açık kaynak erişilebilirliği:** Model ve ağırlıklar indirilebilir olmalı.
2. **Batch desteği:** Faz 1'de toplu kayıt ve sorgu için `batch > 1` zorunludur.
3. **ONNX Runtime uyumluluğu:** CUDAExecutionProvider ve TensorRTExecutionProvider ile çalışabilmeli.
4. **Doğruluk/kalite taban çizgisi:** LFW/IJB-C üzerinde ArcFace tabanlı modeller tercih edilir.
5. **Çıkarım hızı:** 1 ms/ortamcı görüntü gibi hedefler Faz 0 kıyaslaması ile doğrulanacak.
6. **Ön işleme zinciri uyumu:** RGB, NCHW, `(x - 127.5) / 128` normalizasyonu, 5 noktalı hizalama şablonu.
7. **Lisans riski:** Modellerin ticari kullanım izinleri açık olmalı; şüpheli durumlarda alternatif sunulur.

> **Önemli:** Sayısal doğruluk ve hız iddiaları, Faz 0'da bu repoda çalıştırılan kıyaslama ile güncellenecektir. Bu rapordaki değerler kaynak belgelerden ve eski deneylerden alınmıştır; "kanıt" değil "varsayım" olarak değerlendirilmelidir.

---

## 5. Aday Dedektör Modelleri

### 5.1 Birincil Aday: `alonsorobots/scrfd_320_batched`

[REF: web] `https://huggingface.co/alonsorobots/scrfd_320_batched`

| Özellik | Değer |
|---|---|
| Aile | SCRFD (Sample and Computation Redistribution for Efficient Face Detection) |
| Hedef dosya | `scrfd_10g_320_batch.onnx` (önerilen)  |
| Alternatifler | `scrfd_2.5g_320_batch.onnx`, `scrfd_500m_320_batch.onnx` |
| Girdi şekli | `[B, 3, 320, 320]`, NCHW, RGB |
| Normalizasyon | `(x - 127.5) / 128` |
| Çıktı | Çok ölçekli kafalar: bbox, 5 keypoint, confidence skorları |
| Ölçekler | 80×80, 40×40, 20×20 (stride 8, 16, 32) |
| Batch desteği | Dinamik batch boyutu |

**Avantajlar:**
- ONNX Runtime CUDA/TensorRT ile iyi uyumlu.
- Eski VGGFace2/VideoFaceGPU deneylerinde stabil çalıştığı gözlemlendi.
- 5 noktalı keypoint çıkışı, ArcFace hizalama şablonu için yeterli.

**Dezavantajlar/Riskler:**
- Ağırlıklar InsightFace ekosistemine dayanır; lisans riski yüksek (Bölüm 12).
- 320×320 giriş, çok küçük yüzleri bulmak için yeterli olmayabilir; Faz 0'da NMS threshold ve min face size ile doğrulanmalı.

### 5.2 Alternatif Dedektörler

| Model | Kaynak | Notlar |
|---|---|---|---|
| OpenCV YuNet | `opencv/opencv_zoo` | Daha güvenli lisans; batch desteği sınırlı/deneysel; inference daha yavaş olabilir. |
| YOLOv5-face | `deepcam-cn/yolov5-face` | Topluluk popüler; ONNX export mevcut; ön işleme farklıdır. |
| YOLOv8-face | `derronqi/yolov8-face` | Daha yeni; Ultralytics export iş akışı; öncelik düşük kıyaslama çifti dışında. |
| EdgeFace detector bileşeni | `yakhyo/edgeface-onnx` | Deneysel; öncelik düşük. |

---

## 6. Aday Tanıyıcı Modelleri

### 6.1 Birincil Aday: `alonsorobots/arcface_w600k_r50_batched`

[REF: web] Hugging Face gösterim sayfasına doğrudan erişim 401/gated döndürdü; teknik detaylar eski VGGFace2 deney kayıtlarından ve ONNX ArcFace literatüründen elde edilmiştir.

| Özellik | Değer |
|---|---|
| Taban mimarisi | ResNet-50 |
| Eğitim verisi | WebFace600K |
| Hedef dosya | `arcface_w600k_r50_batch.onnx` |
| Girdi şekli | `[B, 3, 112, 112]`, NCHW, RGB |
| Normalizasyon | `(x - 127.5) / 128` |
| Çıktı | `[B, 512]` embedding vektörü |
| Normalize | Çıkış genellikle L2 normalize edilmiştir; Faz 0'da tekrar kontrol edilmeli |

**Avantajlar:**
- ArcFace literatüründe yüksek standart; 512-D uzay Qdrant ile doğrudan uyumlu.
- Batch boyutu dinamiktir.
- Hizalama şablonu SCRFD 5 noktası ile uyumlu.

**Dezavantajlar/Riskler:**
- Aynı lisans riski (Bölüm 12).
- ONNX dosyası indirilmeden önce doğrudan kaynak doğrulanamadı.

### 6.2 Alternatif Tanıyıcılar

| Model | Kaynak | Boyut | Notlar |
|---|---|---|---|
| OpenVINO `face-recognition-resnet100-arcface-onnx` | Intel Open Model Zoo | 512-D | Daha katı lisans denetimi; güvenli lisans alternatifi. |
| OpenCV SFace | `opencv/opencv_zoo` | 128-D | Çok daha düşük kalite beklentisi; yüksek hız, küçük boyut. |
| EdgeFace (MobileFaceNet taban) | `yakhyo/edgeface-onnx` | 512-D | Düşük güç/kenar cihaz odaklı; doğruluk performansı Faz 0'da ölçülmedi. |

---

## 7. Seçilen İlk Kıyaslama Çifti

[REF: local] eski VGGFace2/VideoFaceGPU deneyleri

### 7.1 Dedektör + Tanıyıcı

| Rol | Model | ONNX Dosyası | Girdi | Çıktı |
|---|---|---|---|---|
| Yüz tespiti | SCRFD 10g 320 | `scrfd_10g_320_batch.onnx` | `[B,3,320,320]` | bbox + 5 keypoint + score |
| Yüz tanıma | ArcFace r50 WebFace600K | `arcface_w600k_r50_batch.onnx` | `[B,3,112,112]` | `[B,512]` embedding |

### 7.2 Neden Bu Çift?

1. **Batch uyumu:** Her iki modelde de batch boyutu programatik olarak ayarlanabilir.
2. **Ön işleme uyumu:** Aynı RGB/NCHW/normalizasyon semantiği.
3. **Keypoint → hizalama → crop:** SCRFD'nin 5 noktası ArcFace 112×112 kırpma şablonuyla kullanılabilir.
4. **Ekosistem tutarlılığı:** Eski deneylerde bu kombinasyonun çalıştığı görüldü; tekrarlanabilirliği yüksek.
5. **Doğruluk potansiyeli:** ArcFace r50 + SCRFD, topluluk referanslarında güçlü performans gösterir.

### 7.3 Önerilen Runtime Sıralaması

```text
1. TensorRTExecutionProvider (GPU, hızlı)
2. CUDAExecutionProvider (GPU, evrensel)
3. CPUExecutionProvider (CPU, fallback)
```

TensorRT için FP16/INT8 kalibrasyonu Faz 0'da ayrıca değerlendirilir.

---

## 8. Batch Boyutu Stratejisi

[REF: local] eski VideoFaceGPU batch matris raporları; [REF: ctx7] ONNX Runtime IOBinding

### 8.1 İlk Kıyaslama Planı

| Senaryo | Batch Değerleri | Amaç |
|---|---|---|
| Identify (tek fotoğraf) | 1 | Gecikme taban çizgisi |
| Identify (küçük toplu) | 4, 8 | Ortalama gecikme/verim |
| Identify / Enrollment | 16, 32 | Verimlilik tatlı noktası |
| Yüksek batch | 64 | Yalnızca 32 sonuçları buna işaret ederse |

### 8.2 Bulk Enrollment İçin Öneri

- **Varsayılan `batch=32`** ile başlanır.
- Çok büyük toplu işlemler (örneğin binlerce görüntü) bu batch boyutunda parçalanır (chunking).
- GPU belleği dolarsa veya gecikme kabul edilemezse `batch=16` veya `batch=8` düşürülür.
- `batch=64` için ayrı `scrfd_320_batched_64` dosyası incelenir; ancak ilk deneme 32 ile yapılır.

---

## 9. Ön İşleme ve Hizalama Zinciri

Eski VideoFaceGPU deneylerinden çıkarılan ve **doğrulanmış** olarak kabul edilen zincir:

```text
Girdi (PIL/NumPy RGB image)
  ↓
Letterbox / resize → 320×320 (SCRFD) / 112×112 (ArcFace crop)
  ↓
RGB → NCHW transpose
  ↓
float32 (x - 127.5) / 128
  ↓
ONNX Runtime InferenceSession (IOBinding kullanarak)
```

### 9.1 Yüz Dedeksiyon Sonrası Hizalama

1. SCRFD çıkışından NMS uygulanır.
2. En yüksek skorlu yüzün 5 keypoint'i seçilir.
3. ArcFace standart 5-nokta referans şablonuna göre affine transform hesaplanır.
4. 112×112 kırpma üretilir.
5. Aynı normalize işlemi uygulanır.
6. Embedding çıkarılır ve L2 normalize edilir.

### 9.2 Çoklu Yüz Durumu

- Faz 1'de "bir görüntüdeki en büyük/tek yüz" varsayımı geçerlidir.
- Eğer bir görüntüde birden fazla yüz varsa: default olarak en yüksek skorlu yüz seçilir; opsiyonel olarak tüm yüzler ayrı `imageId` kayıtları olarak işlenebilir.

---

## 10. Runtime / Execution Provider Stratejisi

[REF: ctx7] ONNX Runtime Execution Provider dokümantasyonu

### 10.1 Provider Sıralaması

1. **TensorRTExecutionProvider** – En yüksek GPU verimliliği; engine önbellekleme gerekli.
2. **CUDAExecutionProvider** – Genel GPU desteği; FP32 güvenli.
3. **CPUExecutionProvider** – Yedek; çok yavaş.

### 10.2 IOBinding Kullanımı

- Girdi `OrtValue` olarak GPU'ya bağlanır.
- Çıktı tensörleri önceden ayrılır.
- `run_with_binding()` ile kopya maliyeti minimize edilir.
- Batch değişikliklerinde `bind_input`/`bind_output` yeniden yapılır.

### 10.3 Session Seçenekleri

```python
so = onnxruntime.SessionOptions()
so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
```

### 10.4 CPU Fallback

- GPU mevcut değilse CPU provider ile çalışır; performans hedefleri değişir.
- Üretim ortamında container GPU sürücüleri ve CUDA/TensorRT kütüphaneleri önceden yüklenmelidir.

---

## 11. Depolama ve Vektör Arama Etkileri

[REF: ctx7] Qdrant; [REF: ctx7] MinIO

| Veri | Teknoloji | Şema / Not |
|---|---|---|
| Ham görüntü | MinIO | `images/{personId}/{imageId}.jpg` |
| Kişi/Photo meta | PostgreSQL | `person`, `photo` tabloları |
| Yüz embedding | Qdrant | Collection: `face_embeddings`; vektör boyutu `512`; mesafe: Cosine |
| Arama | Qdrant `search` | `limit=k`, filtreleme için payload'ta `personId` |

- L2 normalize edilmiş embedding üzerinde cosine distance = `1 - dot(v1, v2)` eşdeğeridir.
- Bulk enrollment için Qdrant `upsert` batch'leri kullanılır.
- Her embedding kaydına `imageId`, `personId`, `requestId` gibi meta alanları eklenir.

---

## 12. Lisans ve Ticari Kullanım Risk Analizi

[REF: web] SCRFD / ArcFace GitHub ve Hugging Face sayfaları; [REF: local] `opensourceReferences/references.md`

### 12.1 Seçilen Çiftin Riski

| Bileşen | Kod Lisansı | Ağırlık/Model Lisansı | Risk |
|---|---|---|---|
| SCRFD (InsightFace) | Apache-2.0 | Topluluk ağırlıkları; açık ticari izin yok | **YÜKSEK** |
| ArcFace (InsightFace taban) | Apache-2.0 (kod) | Orjinal MS1MV3/WebFace600K ağırlıkları; non-commercial/research vurgusu yaygın | **YÜKSEK** |

**Yüksek risk nedenleri:**
- Hugging Face model kartlarında eksik veya belirsiz ticari kullanım ifadesi.
- InsightFace önceden eğitilmiş modelleri genellikle "research/non-commercial" olarak dağıtılmıştır.
- Üretimde kullanılmadan önce hukuk ekibi onayı şarttır.

### 12.2 Öneri

- Faz 0 kıyaslama ve prototip için kullanılabilir.
- Müşteri demosu / üretime geçmeden önce Bölüm 13'teki alternatiflerden biri seçilmeli veya orijinal model sahiplerinden yazılı izin alınmalıdır.

---

## 13. Fallback / Daha Güvenli Lisans Alternatifleri

| Senaryo | Dedektör | Tanıyıcı | Lisans Durumu |
|---|---|---|---|
| Güvenli lisans, düşük risk | OpenCV YuNet | OpenVINO `face-recognition-resnet100-arcface-onnx` | Intel OMZ kodu Apache-2.0; model kartı açık |
| Güvenli lisans, hız öncelikli | OpenCV YuNet | OpenCV SFace | OpenCV Zoo; çok kompakt ama 128-D ve doğruluk düşük |
| Edge cihaz | OpenCV YuNet | EdgeFace ONNX | Topluluk projesi; lisans ve doğruluk Faz 0'da teyit edilmeli |

**Öneri:** Faz 0'da hem birincil InsightFace çifti hem de OpenCV YuNet + OpenVINO ArcFace çifti kıyaslanmalı; böylece lisans kararı teknik veriye dayanır.

---

## 14. Gelecek Video / Faz 2 Değerlendirmeleri

[REF: local] `phase2videorequirements.md`

- Faz 2'de video kareleri akışı ve muhtemelen `requestId` ile kare izleme gerekir.
- Dedektör olarak aynı SCRFD/YuNet tercih edilebilir; tracker (örneğin DeepSORT/BoT-SORT) eklenir.
- Tanıyıcı aynı kalabilir; fakat kare başına tekrar çıkarım maliyetli olacağı için embedding önbelleği düşünülmelidir.
- Video elde edilene kadar bu raporda detaylandırılmaz.

---

## 15. Eski Repolardan Bilinen Anti-Patternler

[REF: local] `olderDiagramsProvedWrog/`

Aşağıdaki desenler eski VGGFace2/VideoFaceGPU kodlarında görüldü ve MergenVision'da **tekrarlanmamalıdır**:

| Anti-Pattern | Neden Kötü | Doğrusu |
|---|---|---|
| Sabit/sahte batch=1 pipeline | Toplu işlemlerde performans çöker | Dinamik batch destekli ONNX pipe |
| Tek mutable NumPy buffer'ı girişler arasında paylaşma | Çapraz bulaşma (cross-image contamination) | Her batch için ayrı contigüous tensör |
| BGR/RGB karışıklığı | Model girdisi yanlış renk kanalıyla çalışır | Her model için renk uzayı açıkça doğrulanır |
| Resize yerine stretch | Yüz orantısı bozulur | Letterbox veya aspect-ratio-aware crop |
| L2 normalizasyonu atlamak | Cosine similarity hesabı bozulur | Embedding çıkışından sonra mutlaka `v /= np.linalg.norm(v)` |
| `arcface_w600k_r50_batch.onnx` dosya adını varsaymak | Farklı dosya varsa karışıklık oluşur | `MODEL_PATH` env/config ile alınır ve dosya varlığı kontrol edilir |
| NMS threshold'u sert kodlamak | Çok fazla/çok az tespit | `DETECTION_CONFIDENCE` ve `NMS_IOU` konfigüre edilebilir olmalı |

---

## 16. Risk Register

| ID | Risk | Olasılık | Etki | Önleme / Eylem |
|---|---|---|---|---|
| R1 | Ağırlıkların ticari kullanım izni yok | Orta | Çok Yüksek | Hukuk onayı; Bölüm 13 alternatifleri hazır tut |
| R2 | ONNX dosyaları indirilemez/gated | Düşük | Yüksek | Faz 0'da doğrudan indirme testi yap |
| R3 | `batch=32` belleği aşıyor | Orta | Orta | Bellek profili çıkar; chunking ve düşük batch |
| R4 | 320×320 çok küçük yüzleri kaçırıyor | Orta | Orta | Min yüz boyutu, NMS threshold ve alternatif çözünürlük testi |
| R5 | L2 normalize doğru çalışmıyor | Düşük | Yüksek | Faz 0'da `np.linalg.norm` doğrulaması |
| R6 | Çoklu yüz senaryosu tanımsız | Yüksek | Orta | Faz 1 gereksiniminde "en iyi yüz" kararı netleştirilsin |
| R7 | TensorRT engine cache sorunu | Orta | Orta | Engine cache dizini belirle; FP16 kalibrasyon ayrı test |

---

## 17. Öneriler ve Go/No-Go

### 17.1 Öneriler

1. Faz 0'da birincil çift (`scrfd_10g_320_batch.onnx` + `arcface_w600k_r50_batch.onnx`) ile kıyaslama başlat.
2. Aynı anda güvenli lisans alternatifini (YuNet + OpenVINO ArcFace) de küçük ölçekte değerlendir.
3. Batch boyutu `[1,4,8,16,32]` üzerinden latency/throughput eğrisi çiz.
4. ONNX model dosya boyutlarını, inference latency'yi ve doğruluk taban çizgisini ölç.
5. Hukuk onayı alınmadan üretim dağıtımı yapma.

### 17.2 Go/No-Go Kriterleri

| Kriter | Geçiş Koşulu | Durum |
|---|---|---|
| Modeller indirilebilir | SCRFD ve ArcFace ONNX dosyaları başarıyla download edilir | Henüz doğrulanmadı |
| Inference pipeline çalışır | Tek ve batch çıkarım sonuç üretir | Henüz doğrulanmadı |
| Embedding kalitesi | Aynı kişiye ait fotoğraflar yüksek benzerlik, farklı kişiler düşük | Henüz doğrulanmadı |
| Lisans onayı | Hukuk tarafından "üretimde kullanılabilir" onayı | Henüz yok |

**Go kararı** yalnızca yukarıdaki kriterler sağlandığında verilebilir.

---

## 18. Doğrulama Komutları ve Kanıt Listesi

Aşağıdaki komutlar Faz 0'da çalıştırılarak bu rapordaki varsayımlar kanıtlanmalıdır.

### 18.1 Ortam ve Dosya Kontrolü

```bash
# 1. Hedef dizin kontrolü
ls -la docs/model_research/

# 2. Model dosyası varlığı (indirme sonrası)
ls -la models/scrfd_10g_320_batch.onnx
ls -la models/arcface_w600k_r50_batch.onnx
```

### 18.2 ONNX Model İnceleme

```bash
# 3. Girdi/çıktı şekilleri
python - <<'PY'
import onnx
for m in ["models/scrfd_10g_320_batch.onnx", "models/arcface_w600k_r50_batch.onnx"]:
    model = onnx.load(m)
    for i in model.graph.input:
        print(m, "INPUT", i.name, [d.dim_value or d.dim_param for d in i.type.tensor_type.shape.dim])
    for o in model.graph.output:
        print(m, "OUTPUT", o.name, [d.dim_value or d.dim_param for d in o.type.tensor_type.shape.dim])
PY
```

### 18.3 Çıkarım Duman Testi

```bash
# 4. Batch=1 ve batch=4 dummy inference
python - <<'PY'
import numpy as np
import onnxruntime as ort

def smoke(path, shape, provider="CPUExecutionProvider", batch_sizes=[1,4]):
    sess = ort.InferenceSession(path, providers=[provider])
    in_name = sess.get_inputs()[0].name
    for b in batch_sizes:
        x = np.random.rand(b, *shape[1:]).astype(np.float32)
        out = sess.run(None, {in_name: x})
        print(path, "batch", b, "output shapes", [o.shape for o in out])

smoke("models/scrfd_10g_320_batch.onnx", [1,3,320,320])
smoke("models/arcface_w600k_r50_batch.onnx", [1,3,112,112])
PY
```

### 18.4 GPU Provider Kontrolü

```bash
# 5. Kullanılabilir provider listesi
python - <<'PY'
import onnxruntime as ort
print(ort.get_available_providers())
PY
```

### 18.5 Embedding Normalize Kontrolü

```bash
# 6. Çıkış vektörlerinin L2 normu 1.0 olmalı (veya normalize sonrası)
python - <<'PY'
import numpy as np
# arcface çıkış vektörü v için
v = ... # inference sonucu
norm = np.linalg.norm(v, axis=1)
print("L2 norms:", norm)
assert np.allclose(norm, 1.0, atol=1e-5), "Normalize gerekli"
PY
```

### 18.6 Kanıt Listesi

- [ ] `scrfd_10g_320_batch.onnx` başarıyla indirildi ve SHA/MD5 ile bütünlük doğrulandı.
- [ ] `arcface_w600k_r50_batch.onnx` başarıyla indirildi ve bütünlük doğrulandı.
- [ ] Her iki modelde de batch boyutu dinamik olarak değiştirilebildi.
- [ ] `[1,4,8,16,32]` batch'leri için latency ve throughput ölçümleri kaydedildi.
- [ ] Aynı kişiye ait 5+ fotoğraf embedding'leri cosine > 0.65, farklı kişiler < 0.45 olarak gözlemlendi.
- [ ] L2 normalize sonrası tüm embedding normları 1.0 ± 1e-5.
- [ ] CUDAExecutionProvider inference CPU'dan anlamlı şekilde hızlı.
- [ ] Hukuk ekibi InsightFace tabanlı modeller için ticari kullanım onayı verdi.

---

## Ek A: Kısaltmalar

| Kısaltma | Anlamı |
|---|---|
| SCRFD | Sample and Computation Redistribution for Efficient Face Detection |
| ArcFace | Additive Angular Margin Loss for Deep Face Recognition |
| ONNX | Open Neural Network Exchange |
| NCHW | Batch × Channel × Height × Width |
| NMS | Non-Maximum Suppression |
| FP16/INT8 | 16-bit floating point / 8-bit integer quantization |
| OMZ | Open Model Zoo (Intel) |

---

## Ek B: Kaynak Referansları

1. `alonsorobots/scrfd_320_batched` – `https://huggingface.co/alonsorobots/scrfd_320_batched`
2. `alonsorobots/scrfd_320_batched_64` – `https://huggingface.co/alonsorobots/scrfd_320_batched_64`
3. Intel OpenVINO ArcFace – `https://docs.openvino.ai/2023.3/omz_models_model_face_recognition_resnet100_arcface_onnx.html`
4. OpenCV YuNet – `https://github.com/opencv/opencv_zoo/tree/master/models/face_detection_yunet`
5. OpenCV SFace – `https://github.com/opencv/opencv_zoo/tree/master/models/face_recognition_sface`
6. EdgeFace ONNX – `https://github.com/yakhyo/edgeface-onnx`
7. Eski VGGFace2 raporları – `/home/user/Demo/Demo12_VGGFace2Lab/docs/`
8. Eski VideoFaceGPU raporları – `/home/user/Demo/VideoFaceGpuLab/docs/`
9. MergenVision Faz 1 Gereksinimleri – `/home/user/MergenVision/requirements/phase1recognitionrequirements.md`
