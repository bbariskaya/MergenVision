"""CPU/GPU image resizing and normalization using torch."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import torch


class TorchPreprocessor:
    """Resize and normalize images/crops using torch operations."""

    def __init__(self, device_id: int = 0) -> None:
        self._device_id = device_id

    def _get_device(self) -> torch.device:
        import torch

        if torch.cuda.is_available():
            return torch.device(f"cuda:{self._device_id}")
        return torch.device("cpu")

    def resize_normalize(
        self,
        images: torch.Tensor,
        size: int,
        mean: tuple[float, float, float] = (127.5, 127.5, 127.5),
        std: tuple[float, float, float] = (128.0, 128.0, 128.0),
    ) -> torch.Tensor:
        """Resize [N,3,H,W] to [N,3,size,size], normalize (x-mean)/std."""
        import torch
        import torch.nn.functional as F

        # Move to target device first.
        images = images.to(self._get_device())

        # Handle letterbox: resize preserving aspect ratio, then pad.
        n, c, h, w = images.shape
        scale = min(size / h, size / w)
        new_h = int(round(h * scale))
        new_w = int(round(w * scale))

        resized = F.interpolate(
            images,
            size=(new_h, new_w),
            mode="bilinear",
            align_corners=False,
        )

        padded = torch.zeros((n, c, size, size), dtype=images.dtype, device=images.device)
        padded[:, :, :new_h, :new_w] = resized

        mean_t = torch.tensor(mean, dtype=padded.dtype, device=padded.device).view(1, 3, 1, 1)
        std_t = torch.tensor(std, dtype=padded.dtype, device=padded.device).view(1, 3, 1, 1)
        return (padded - mean_t) / std_t

    def resize_center_crop(
        self,
        images: torch.Tensor,
        size: int,
    ) -> torch.Tensor:
        """Resize smallest side to `size` and center crop, used for ArcFace input."""
        import torch.nn.functional as F

        images = images.to(self._get_device())
        _, _, h, w = images.shape
        scale = size / min(h, w)
        new_h = int(round(h * scale))
        new_w = int(round(w * scale))
        resized = F.interpolate(
            images,
            size=(new_h, new_w),
            mode="bilinear",
            align_corners=False,
        )
        # Center crop
        top = (new_h - size) // 2
        left = (new_w - size) // 2
        return resized[:, :, top : top + size, left : left + size]
