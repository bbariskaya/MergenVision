"""GPU-assisted (CuPy) and CPU PIL-based image decoder."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image

if TYPE_CHECKING:
    import torch


class GpuPilDecoder:
    """Decode JPEG/PNG bytes to a CHW torch tensor.

    The class name reflects the actual implementation: CPU-side PIL decoding
    followed by an optional GPU upload via CuPy/DLPack. It does not use the
    NVIDIA nvJPEG hardware decoder.
    """

    _device: object | None = None

    def __init__(self, device_id: int = 0) -> None:
        self._device_id = device_id

    def _get_device(self) -> torch.device:
        import torch

        if torch.cuda.is_available():
            return torch.device(f"cuda:{self._device_id}")
        return torch.device("cpu")

    def decode_batch(self, image_bytes_list: list[bytes]) -> torch.Tensor:
        """Decode a list of image byte strings to a [N, 3, H, W] float32 tensor."""
        try:
            import cupyx  # noqa: F401

            return self._decode_cupy(image_bytes_list)
        except Exception:
            return self._decode_cpu(image_bytes_list)

    def decode_batch_from_paths(self, paths: list[str | Path]) -> torch.Tensor:
        """Read image bytes from disk and decode them."""
        image_bytes_list = [Path(p).read_bytes() for p in paths]
        return self.decode_batch(image_bytes_list)

    def _decode_cupy(self, image_bytes_list: list[bytes]) -> torch.Tensor:
        import cupy as cp
        import torch
        import torch.utils.dlpack as torch_dlpack

        images = []
        for data in image_bytes_list:
            img = cp.asarray(Image.open(BytesIO(data)).convert("RGB"))
            img = cp.transpose(img, (2, 0, 1))
            images.append(torch_dlpack.from_dlpack(img.astype(cp.float32).toDlpack()))
        return torch.stack(images).to(self._get_device())

    def _decode_cpu(self, image_bytes_list: list[bytes]) -> torch.Tensor:
        import numpy as np
        import torch

        images = []
        for data in image_bytes_list:
            img = Image.open(BytesIO(data)).convert("RGB")
            arr = np.array(img).astype(np.float32)
            arr = np.transpose(arr, (2, 0, 1))
            images.append(torch.from_numpy(arr))
        return torch.stack(images).to(self._get_device())
