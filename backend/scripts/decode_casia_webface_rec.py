#!/usr/bin/env python3
"""Decode the CASIA-WebFace MXNet .rec archive into identity folders.

The Kaggle CASIA-WebFace dataset ships as:
    train.rec   MXNet recordio archive
    train.idx   record offsets
    train.lst   list with original paths (used for identity names)

This script extracts the JPEG images to:
    testdatasets/casia-webface-extracted/<identity>/<basename>.jpg

Example::

    uv run python scripts/decode_casia_webface_rec.py \
        --rec-dir /home/user/MergenVision/testdatasets/casia-webface/casia-webface \
        --output-dir /home/user/MergenVision/testdatasets/casia-webface-extracted
"""

from __future__ import annotations

import argparse
import struct
import sys
import time
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Decode CASIA-WebFace .rec archive")
    parser.add_argument(
        "--rec-dir",
        type=Path,
        default=Path("/home/user/MergenVision/testdatasets/casia-webface/casia-webface"),
        help="Directory containing train.rec, train.idx and train.lst",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("/home/user/MergenVision/testdatasets/casia-webface-extracted"),
        help="Directory to extract identity folders into",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=0,
        help="Max records to decode (0 = all)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=10000,
        help="Number of records to decode between progress prints",
    )
    return parser.parse_args()


def parse_lst(lst_path: Path) -> list[tuple[str, str]]:
    """Return list of (identity_name, basename) for each train.lst line."""
    entries: list[tuple[str, str]] = []
    with open(lst_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) < 2:
                continue
            original_path = parts[1]
            p = Path(original_path)
            identity = p.parent.name
            basename = p.name
            entries.append((identity, basename))
    return entries


def parse_idx(idx_path: Path) -> list[tuple[int, int]]:
    """Return list of (key, offset)."""
    offsets: list[tuple[int, int]] = []
    with open(idx_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) < 2:
                continue
            offsets.append((int(parts[0]), int(parts[1])))
    return offsets


def decode_record(
    rec_path: Path,
    key: int,
    offset: int,
    entries: list[tuple[str, str]],
    output_dir: Path,
) -> tuple[str, str] | None:
    """Decode one record and write the JPEG to the output tree."""
    idx = key - 1
    if idx < 0 or idx >= len(entries):
        return None
    identity, basename = entries[idx]
    out_path = output_dir / identity / basename
    if out_path.exists():
        return identity

    with open(rec_path, "rb") as f:
        f.seek(offset)
        magic = struct.unpack("<I", f.read(4))[0]
        length = struct.unpack("<I", f.read(4))[0]
        data = f.read(length)

    soi = data.find(b"\xff\xd8")
    if soi == -1:
        return None

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(data[soi:])
    return identity


def main() -> int:
    args = parse_args()
    rec_dir = args.rec_dir
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    rec_path = rec_dir / "train.rec"
    idx_path = rec_dir / "train.idx"
    lst_path = rec_dir / "train.lst"

    for p in (rec_path, idx_path, lst_path):
        if not p.exists():
            print(f"Missing file: {p}", file=sys.stderr)
            return 1

    print("Parsing train.lst...")
    entries = parse_lst(lst_path)
    print(f"  {len(entries)} entries")

    print("Parsing train.idx...")
    offsets = parse_idx(idx_path)
    print(f"  {len(offsets)} records")

    if args.max_records > 0:
        offsets = offsets[: args.max_records]

    print(f"Decoding {len(offsets)} records to {output_dir} ...")
    start = time.perf_counter()

    # Sequential decoding is faster for many small files than thousands of
    # concurrent futures because it avoids scheduler overhead and keeps the
    # filesystem cache warm.
    for i, (key, offset) in enumerate(offsets):
        decode_record(rec_path, key, offset, entries, output_dir)
        if (i + 1) % args.chunk_size == 0:
            elapsed = time.perf_counter() - start
            rate = (i + 1) / elapsed
            remaining = (len(offsets) - (i + 1)) / rate if rate > 0 else 0
            print(
                f"  decoded {i + 1}/{len(offsets)} | "
                f"{elapsed:.1f}s elapsed | {rate:.0f} rec/s | "
                f"~{remaining:.0f}s remaining"
            )

    elapsed = time.perf_counter() - start
    print(f"Done in {elapsed:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
