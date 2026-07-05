#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[2]


def merge(paths: list[Path], output: Path) -> dict:
    combined = {
        "merged_at": datetime.now(timezone.utc).isoformat(),
        "merged_files": [str(p.relative_to(REPO_ROOT)) for p in paths],
        "common_environment": {},
        "models": [],
    }
    for p in paths:
        data = json.loads(p.read_text(encoding="utf-8"))
        env = data.get("environment", {})
        combined["common_environment"]["onnxruntime_version"] = env.get("onnxruntime_version")
        combined["common_environment"]["available_providers"] = env.get("available_providers")
        combined["models"].append({
            "model_file": env.get("model_file"),
            "requested_provider": env.get("requested_provider"),
            "input_spatial_size": env.get("input_spatial_size"),
            "overall_status": data.get("overall_status"),
            "error": data.get("error"),
            "results": data.get("results", []),
        })
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(combined, indent=2), encoding="utf-8")
    return combined


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("inputs", nargs="+", type=Path)
    args = parser.parse_args()

    paths = [REPO_ROOT / p for p in args.inputs]
    combined = merge(paths, REPO_ROOT / args.output)
    print(json.dumps({"ok": True, "models": len(combined["models"]), "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
