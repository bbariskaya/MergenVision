#!/usr/bin/env python3
import json
import hashlib
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "artifacts" / "model_benchmarks" / "MODEL_MANIFEST.json"
RESULT_PATH = REPO_ROOT / "artifacts" / "model_benchmarks" / "results" / "phase0b_manifest_verification.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def verify() -> dict:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    results = []
    verified_count = 0
    verified_primary = 0
    primary = {"scrfd_10g_320_batch.onnx", "arcface_w600k_r50_batch.onnx"}

    for model in manifest.get("models", []):
        status = model.get("download_status")
        local_path = model.get("local_path")
        expected_sha = model.get("sha256")
        expected_size = model.get("size_bytes")
        name = model.get("model_name")
        role = model.get("role")

        entry = {
            "model_name": name,
            "role": role,
            "download_status": status,
            "local_path": local_path,
            "expected_sha256": expected_sha,
            "expected_size_bytes": expected_size,
        }

        if status != "downloaded":
            entry["phase0b_status"] = status if status else "unknown"
            entry["file_exists"] = False
            entry["sha_match"] = None
            entry["size_match"] = None
            results.append(entry)
            continue

        path = REPO_ROOT / local_path if local_path else None
        if not path or not path.is_file():
            entry["phase0b_status"] = "missing_file"
            entry["file_exists"] = False
            entry["sha_match"] = False
            entry["size_match"] = False
            entry["actual_sha256"] = None
            entry["actual_size_bytes"] = None
            results.append(entry)
            continue

        actual_sha = sha256_file(path)
        actual_size = path.stat().st_size
        sha_ok = (actual_sha == expected_sha) if expected_sha else None
        size_ok = (actual_size == expected_size) if expected_size is not None else None
        ok = (sha_ok is not False) and (size_ok is not False)

        entry.update({
            "file_exists": True,
            "actual_sha256": actual_sha,
            "actual_size_bytes": actual_size,
            "sha_match": sha_ok,
            "size_match": size_ok,
            "phase0b_status": "verified" if ok else "mismatch",
        })
        results.append(entry)
        if ok:
            verified_count += 1
            if name in primary:
                verified_primary += 1

    return {
        "manifest_version": manifest.get("manifest_version"),
        "manifest_phase": manifest.get("phase"),
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "verification_scope": "Phase 0B: readonly SHA-256/size check against MODEL_MANIFEST.json",
        "primary_models": sorted(primary),
        "primary_verified": verified_primary,
        "downloaded_verified": verified_count,
        "verification_results": results,
    }


def main() -> int:
    result = verify()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({
        "ok": result["primary_verified"] == len(result["primary_models"]),
        "primary_verified": result["primary_verified"],
        "result_path": str(RESULT_PATH.relative_to(REPO_ROOT)),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
