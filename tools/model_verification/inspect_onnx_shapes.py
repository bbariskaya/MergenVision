#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

import onnx

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULT_PATH = REPO_ROOT / "artifacts" / "model_benchmarks" / "results" / "phase0b_onnx_shapes.json"
MANIFEST_PATH = REPO_ROOT / "artifacts" / "model_benchmarks" / "MODEL_MANIFEST.json"


def dim_spec(dim):
    if dim.HasField("dim_value") and dim.dim_value > 0:
        return dim.dim_value
    if dim.HasField("dim_param"):
        return dim.dim_param
    return None


def shape_of(value_info):
    tensor_type = value_info.type.tensor_type
    if not tensor_type.HasField("shape"):
        return [None]
    return [dim_spec(d) for d in tensor_type.shape.dim]


def inspect_model(model_path: Path) -> dict:
    model = onnx.load(str(model_path))
    onnx.checker.check_model(model)
    graph = model.graph

    return {
        "file": str(model_path.relative_to(REPO_ROOT)),
        "onnx_ir_version": model.ir_version,
        "opset_imports": [{"domain": o.domain, "version": o.version} for o in model.opset_import],
        "producer_name": graph.doc_string if graph.doc_string else None,
        "inputs": [
            {"name": i.name, "shape": shape_of(i), "dtype": onnx.TensorProto.DataType.Name(i.type.tensor_type.elem_type)}
            for i in graph.input
        ],
        "outputs": [
            {"name": o.name, "shape": shape_of(o), "dtype": onnx.TensorProto.DataType.Name(o.type.tensor_type.elem_type)}
            for o in graph.output
        ],
        "num_initializers": len(graph.initializer),
        "num_nodes": len(graph.node),
    }


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    entries = []
    errors = []

    for model in manifest.get("models", []):
        if model.get("download_status") != "downloaded":
            continue
        local_path = model.get("local_path")
        if not local_path:
            continue
        path = REPO_ROOT / local_path
        if not path.is_file():
            errors.append({"model_name": model.get("model_name"), "error": "file not found", "path": str(path)})
            continue
        try:
            entries.append(inspect_model(path))
        except Exception as exc:
            errors.append({"model_name": model.get("model_name"), "error": str(exc)})

    result = {
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "models": entries,
        "errors": errors,
    }

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"ok": len(errors) == 0, "inspected": len(entries), "errors": len(errors), "result_path": str(RESULT_PATH.relative_to(REPO_ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
