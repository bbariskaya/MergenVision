#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

import onnxruntime as ort

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULT_PATH = REPO_ROOT / "artifacts" / "model_benchmarks" / "results" / "phase0b_ort_providers.json"
MANIFEST_PATH = REPO_ROOT / "artifacts" / "model_benchmarks" / "MODEL_MANIFEST.json"


def test_session(model_path: Path, provider_name: str, providers: list) -> dict:
    result = {
        "requested_provider": provider_name,
        "providers_argument": providers,
    }
    try:
        session = ort.InferenceSession(str(model_path), providers=providers)
        result["session_created"] = True
        result["active_providers"] = session.get_providers()
        result["active_provider_first"] = session.get_providers()[0] if session.get_providers() else None
        result["input_metadata"] = [{"name": i.name, "shape": i.shape, "type": i.type} for i in session.get_inputs()]
        result["output_metadata"] = [{"name": o.name, "shape": o.shape, "type": o.type} for o in session.get_outputs()]
        result["error"] = None
    except Exception as exc:
        result["session_created"] = False
        result["active_providers"] = []
        result["active_provider_first"] = None
        result["input_metadata"] = []
        result["output_metadata"] = []
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def test_model(model_path: Path) -> dict:
    cpu = test_session(model_path, "CPUExecutionProvider", ["CPUExecutionProvider"])
    cuda_strict = test_session(model_path, "CUDAExecutionProvider", ["CUDAExecutionProvider"])
    cuda_with_fallback = test_session(model_path, "CUDAExecutionProvider_with_CPU_fallback", ["CUDAExecutionProvider", "CPUExecutionProvider"])
    return {
        "file": str(model_path.relative_to(REPO_ROOT)),
        "cpu": cpu,
        "cuda_strict": cuda_strict,
        "cuda_with_fallback": cuda_with_fallback,
    }


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    models = []
    errors = []
    environment = {
        "onnxruntime_version": ort.__version__,
        "available_providers": ort.get_available_providers(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    for model in manifest.get("models", []):
        if model.get("download_status") != "downloaded":
            continue
        local_path = model.get("local_path")
        if not local_path:
            continue
        path = REPO_ROOT / local_path
        if not path.is_file():
            errors.append({"model_name": model.get("model_name"), "error": "file not found"})
            continue
        try:
            models.append(test_model(path))
        except Exception as exc:
            errors.append({"model_name": model.get("model_name"), "error": str(exc)})

    result = {
        "environment": environment,
        "models": models,
        "errors": errors,
    }

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"ok": len(errors) == 0, "tested": len(models), "errors": len(errors), "result_path": str(RESULT_PATH.relative_to(REPO_ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
