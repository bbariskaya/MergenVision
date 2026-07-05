# Kaggle Face Datasets for MergenVision

This folder contains helpers to download public face datasets from Kaggle and
enroll them into the local MergenVision stack (PostgreSQL + MinIO + Qdrant).

## Prerequisites

1. The `kaggle` CLI must be installed and authenticated:
   ```bash
   pip install kaggle
   # Place your API token at ~/.kaggle/kaggle.json
   kaggle datasets list
   ```
2. MergenVision Docker Compose services (PostgreSQL, Qdrant, MinIO) must be
   running and exposed on the host ports used by the enrollment scripts.
3. TensorRT engines must be built and available under
   `/home/user/MergenVision/artifacts/trt_engines`.

## Dataset catalog

| Dataset | Kaggle handle | Size | Layout | Enrollment script |
|---------|---------------|------|--------|-------------------|
| CelebA | `jessicali9530/celeba-dataset` | ~1.4 GB | Flat JPGs | `scripts/bulk_enroll_celeba.py` |
| LFW | `jessicali9530/lfw-dataset` | ~112 MB | One folder per identity | `scripts/load_lfw_to_system.py` or `scripts/bulk_enroll_identity_folders.py` |
| VGGFace2 (full) | `dimarodionov/vggface2` | ~40 GB | One folder per identity | `scripts/bulk_enroll_identity_folders.py` |
| VGGFace2 (112×112 aligned) | `yakhyokhuja/vggface2-112x112` | ~19 GB | One folder per identity | `scripts/bulk_enroll_identity_folders.py` |
| CASIA-WebFace | `debarghamitraroy/casia-webface` | ~2.9 GB | One folder per identity | `scripts/bulk_enroll_identity_folders.py` |
| UTKFace | `akashkruttiventi/utkface` | ~200 MB | Flat JPGs | `scripts/bulk_enroll_celeba.py` |
| FFHQ | `arnaud58/flickr-faces-hq-dataset-nvidia` | ~90 GB | Flat 1024×1024 PNGs | `scripts/bulk_enroll_celeba.py` |

## Usage

### Download a dataset

```bash
cd /home/user/MergenVision/backend
uv run python scripts/kaggle_download.py \
    --kaggle-handle jessicali9530/lfw-dataset \
    --output-dir /home/user/MergenVision/testdatasets/lfw_kaggle
```

### Enroll a flat dataset (CelebA, UTKFace, FFHQ)

```bash
CUDA_VISIBLE_DEVICES=1 uv run python scripts/bulk_enroll_celeba.py \
    --dataset /home/user/MergenVision/testdatasets/lfw_kaggle \
    --batch-size 1024 \
    --gpu-device-id 0
```

### Enroll an identity-folder dataset (LFW, VGGFace2, CASIA-WebFace)

```bash
CUDA_VISIBLE_DEVICES=1 uv run python scripts/bulk_enroll_identity_folders.py \
    --dataset /home/user/MergenVision/testdatasets/lfw_kaggle \
    --batch-size 1024 \
    --gpu-device-id 0
```

## Notes

- Datasets are downloaded as-is. Review each dataset's license and terms of use
  before using them in production.
- The scripts create one MergenVision `Person` per image for flat datasets and
  one `Person` per identity folder for folder datasets.
- Large downloads can take a long time and consume significant disk space.
  Monitor `/home/user/MergenVision/testdatasets/` usage.
