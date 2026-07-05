#!/usr/bin/env python3
"""Download a Kaggle dataset to the local testdatasets folder.

Requires the ``kaggle`` CLI to be installed and authenticated:
    pip install kaggle
    # ~/.kaggle/kaggle.json must contain your API token.

Example::

    uv run python scripts/kaggle_download.py \
        --kaggle-handle jessicali9530/lfw-dataset \
        --output-dir /home/user/MergenVision/testdatasets/lfw_kaggle
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download a Kaggle dataset")
    parser.add_argument(
        "--kaggle-handle",
        required=True,
        help="Kaggle dataset handle, e.g. jessicali9530/lfw-dataset",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory to download and unzip into (default: testdatasets/<handle_slug>)",
    )
    parser.add_argument(
        "--unzip",
        action="store_true",
        default=True,
        help="Unzip the downloaded archive (default: True)",
    )
    parser.add_argument(
        "--no-unzip",
        dest="unzip",
        action="store_false",
        help="Do not unzip the downloaded archive",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not shutil.which("kaggle"):
        print(
            "Error: 'kaggle' CLI not found. Install it with:\n"
            "  pip install kaggle\n"
            "and place your API token at ~/.kaggle/kaggle.json",
            file=sys.stderr,
        )
        return 1

    handle = args.kaggle_handle
    output_dir = args.output_dir or Path("/home/user/MergenVision/testdatasets") / handle.replace("/", "_")
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading Kaggle dataset: {handle}")
    print(f"Output directory: {output_dir}")

    cmd = [
        "kaggle",
        "datasets",
        "download",
        "-d",
        handle,
        "-p",
        str(output_dir),
    ]
    if args.unzip:
        cmd.append("--unzip")

    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        print(f"Error: kaggle download failed with exit code {result.returncode}", file=sys.stderr)
        return result.returncode

    # Summary
    image_files = list(output_dir.rglob("*.jpg")) + list(output_dir.rglob("*.png"))
    print(f"Download complete. Found {len(image_files)} images under {output_dir}")

    subdirs = [p for p in output_dir.iterdir() if p.is_dir()]
    if len(subdirs) > 10:
        print(f"Dataset has {len(subdirs)} top-level subdirectories (likely identity folders).")
    else:
        print("Top-level subdirectories:", [p.name for p in subdirs])

    return 0


if __name__ == "__main__":
    sys.exit(main())
