#!/usr/bin/env bash
# MergenVision Phase 0B-GPU Docker verification orchestrator.
# -----------------------------------------------------------------------------
# This script is verification-only. It does NOT start an application server,
# does NOT modify host CUDA/cuDNN, and does NOT touch production Docker files.
# -----------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
IMAGE_NAME="mergenvision-phase0b-gpu-ort-smoke:local"
DOCKERFILE="${SCRIPT_DIR}/docker/Dockerfile.gpu-ort-smoke"
RESULTS_DIR="${REPO_ROOT}/artifacts/model_benchmarks/results"
MODELS_DIR="${REPO_ROOT}/artifacts/model_benchmarks/models"

mkdir -p "${RESULTS_DIR}"

BACKUP_DIR="$(mktemp -d)"

# GPU selection: GPU 0 is occupied by VLLM/other workloads, so verification uses
# GPU 1 as the default / primary device and GPU 2 as a replica. GPU 0 is not used.
DEFAULT_GPU="device=1"
REPLICA_GPUS=(1 2)

# Preserve pre-existing Phase 0B host-venv results so we don't overwrite them.
backup_result() {
  local name="$1"
  local src="${RESULTS_DIR}/${name}"
  if [[ -f "${src}" ]]; then
    cp -a "${src}" "${BACKUP_DIR}/${name}"
  fi
}

restore_result() {
  local name="$1"
  local backup="${BACKUP_DIR}/${name}"
  if [[ -f "${backup}" ]]; then
    mv -f "${backup}" "${RESULTS_DIR}/${name}"
  fi
}

# On script exit, restore all host results we backed up.
cleanup() {
  for f in "${BACKUP_DIR}"/*.json; do
    [[ -f "${f}" ]] || continue
    local name
    name="$(basename "${f}")"
    cp -a "${f}" "${RESULTS_DIR}/${name}" || true
  done
  rm -rf "${BACKUP_DIR}"
}
trap cleanup EXIT

backup_result "phase0b_ort_providers.json"
backup_result "phase0b_manifest_verification.json"
backup_result "phase0b_onnx_shapes.json"

echo "=== Building verification image ${IMAGE_NAME} ==="
docker build -t "${IMAGE_NAME}" -f "${DOCKERFILE}" "${SCRIPT_DIR}/docker"

echo ""
echo "=== Docker / NVIDIA environment inside container (GPU 1) ==="
docker run --rm --gpus "${DEFAULT_GPU}" "${IMAGE_NAME}" bash -c \
  'echo "docker runtime reported GPU:"; nvidia-smi --query-gpu=name,driver_version,memory.total,memory.free --format=csv; echo ""; echo "onnxruntime:"; python -c "import onnxruntime as ort; print(ort.__version__); print(ort.get_available_providers())"; echo ""; echo "python:"; python --version'

run_in_container() {
  local gpuspec="$1"
  shift
  docker run --rm --gpus "${gpuspec}" \
    -v "${REPO_ROOT}:/workspace:rw" \
    -w /workspace \
    "${IMAGE_NAME}" \
    "$@"
}

echo ""
echo "=== Provider smoke (inside container, GPU 1) ==="
run_in_container "${DEFAULT_GPU}" python tools/model_verification/ort_provider_smoke.py
cp "${RESULTS_DIR}/phase0b_ort_providers.json" "${RESULTS_DIR}/phase0b_gpu_docker_ort_providers.json"
restore_result "phase0b_ort_providers.json"

echo ""
echo "=== Manifest verification (inside container) ==="
run_in_container "${DEFAULT_GPU}" python tools/model_verification/verify_model_manifest.py
cp "${RESULTS_DIR}/phase0b_manifest_verification.json" "${RESULTS_DIR}/phase0b_gpu_docker_manifest_verification.json"
restore_result "phase0b_manifest_verification.json"

echo ""
echo "=== ONNX shape inspection (inside container) ==="
run_in_container "${DEFAULT_GPU}" python tools/model_verification/inspect_onnx_shapes.py
cp "${RESULTS_DIR}/phase0b_onnx_shapes.json" "${RESULTS_DIR}/phase0b_gpu_docker_onnx_shapes.json"
restore_result "phase0b_onnx_shapes.json"

run_dummy_for_model() {
  local gpuspec="$1"
  local model_name="$2"    # e.g. scrfd_10g_320_batch
  local width="$3"         # kept for explicit control; script can also infer
  local out_name="$4"
  local model_path="artifacts/model_benchmarks/models/${model_name}.onnx"

  run_in_container "${gpuspec}" python tools/model_verification/dummy_batch_smoke.py \
    --model_path "${model_path}" \
    --provider CUDA \
    --batch_sizes 1,4,8,16,32 \
    --size "${width}" \
    --output "artifacts/model_benchmarks/results/${out_name}" \
    || true
}

merge_dummy_models() {
  local output="$1"
  shift
  if run_in_container all python tools/model_verification/merge_dummy_results.py \
      --output "${output}" "$@"; then
    echo "Merged dummy results into ${output}"
  else
    echo "WARNING: merge failed for ${output}"
  fi
}

echo ""
echo "=== CUDA dummy batch against default GPU 1 (inside container) ==="
run_dummy_for_model "${DEFAULT_GPU}" "scrfd_10g_320_batch" 320 "phase0b_gpu_docker_dummy_batch_cuda_scrfd.json"
run_dummy_for_model "${DEFAULT_GPU}" "arcface_w600k_r50_batch" 112 "phase0b_gpu_docker_dummy_batch_cuda_arcface.json"

if [[ -f "${RESULTS_DIR}/phase0b_gpu_docker_dummy_batch_cuda_scrfd.json" && -f "${RESULTS_DIR}/phase0b_gpu_docker_dummy_batch_cuda_arcface.json" ]]; then
  merge_dummy_models "artifacts/model_benchmarks/results/phase0b_gpu_docker_dummy_batch_cuda.json" \
    "artifacts/model_benchmarks/results/phase0b_gpu_docker_dummy_batch_cuda_scrfd.json" \
    "artifacts/model_benchmarks/results/phase0b_gpu_docker_dummy_batch_cuda_arcface.json"
fi

echo ""
echo "=== Optional per-GPU replica verification (device 1, 2; device 0 skipped because occupied) ==="
for gpu_idx in "${REPLICA_GPUS[@]}"; do
  echo ""
  echo "--- GPU ${gpu_idx} ---"
  scrfd_out="phase0b_gpu_docker_dummy_batch_cuda_gpu${gpu_idx}_scrfd.json"
  arcface_out="phase0b_gpu_docker_dummy_batch_cuda_gpu${gpu_idx}_arcface.json"
  merged_out="phase0b_gpu_docker_dummy_batch_cuda_gpu${gpu_idx}.json"

  run_dummy_for_model "device=${gpu_idx}" "scrfd_10g_320_batch" 320 "${scrfd_out}"
  run_dummy_for_model "device=${gpu_idx}" "arcface_w600k_r50_batch" 112 "${arcface_out}"

  if [[ -f "${RESULTS_DIR}/${scrfd_out}" && -f "${RESULTS_DIR}/${arcface_out}" ]]; then
    merge_dummy_models "artifacts/model_benchmarks/results/${merged_out}" \
      "artifacts/model_benchmarks/results/${scrfd_out}" \
      "artifacts/model_benchmarks/results/${arcface_out}" || true
  fi
done

echo ""
echo "=== Verification outputs ==="
ls -lh "${RESULTS_DIR}"/phase0b_gpu_docker_*.json || true

echo ""
echo "=== Quick provider check inside container ==="
python3 - <<'PY'
import json, sys
from pathlib import Path
p = Path("artifacts/model_benchmarks/results/phase0b_gpu_docker_ort_providers.json")
if not p.is_file():
    print("phase0b_gpu_docker_ort_providers.json not found")
    sys.exit(1)
data = json.loads(p.read_text())
for m in data.get("models", []):
    name = m.get("file", "?")
    active = m.get("cuda_with_fallback", {}).get("active_providers", [])
    print(f"{name}: active providers = {active}")
PY

echo ""
echo "=== Done ==="
echo "Host Phase 0B CPU result JSONs have been preserved."
