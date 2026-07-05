"""ArcFace 5-landmark alignment using torch grid sampling."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from app.infrastructure.adapters.base import DetectionBatch

if TYPE_CHECKING:
    import torch

_ARCFACE_DST = np.array(
    [
        [38.2946, 51.6963],
        [73.5318, 51.5014],
        [56.0252, 71.7366],
        [41.5493, 92.3655],
        [70.7299, 92.2041],
    ],
    dtype=np.float32,
)


class AlignerPreprocessor:
    """Warp detected faces to [M,3,112,112] using the ArcFace landmark template."""

    _OUTPUT_SIZE = 112

    def __init__(self, device_id: int = 0) -> None:
        self._device_id = device_id

    def _get_device(self, fallback: torch.device | None = None) -> torch.device:
        import torch

        if fallback is not None:
            return fallback
        if torch.cuda.is_available():
            return torch.device(f"cuda:{self._device_id}")
        return torch.device("cpu")

    def _template(self, device: torch.device, dtype) -> torch.Tensor:
        import torch

        return torch.from_numpy(_ARCFACE_DST).to(device=device, dtype=dtype)

    def align_crops(
        self,
        image: torch.Tensor,
        detections: DetectionBatch,
        out_size: int = 112,
    ) -> torch.Tensor:
        """Return warped face crops [M,3,out_size,out_size]."""
        import torch
        import torch.nn.functional as F

        if len(detections) == 0:
            return torch.empty(
                (0, image.shape[0], out_size, out_size),
                dtype=image.dtype,
                device=image.device,
            )

        device = image.device
        dtype = image.dtype
        template = self._template(device, dtype)
        h, w = image.shape[1], image.shape[2]

        pad = 4
        padded = F.pad(image, (pad, pad, pad, pad), mode="constant", value=0)

        crops = []
        for det in detections:
            src = torch.tensor(
                [[lm[0] + pad, lm[1] + pad] for lm in det.landmarks],
                dtype=dtype,
                device=device,
            )
            affine = self._estimate_similarity(template + pad, src)
            grid = self._make_grid(affine, out_size, out_size, w + 2 * pad, h + 2 * pad)
            crop = F.grid_sample(
                padded.unsqueeze(0),
                grid,
                mode="bilinear",
                padding_mode="zeros",
                align_corners=False,
            )
            crops.append(crop.squeeze(0))

        return torch.stack(crops, dim=0)

    def _estimate_similarity(
        self,
        dst: torch.Tensor,
        src: torch.Tensor,
    ) -> torch.Tensor:
        """Solve 2D similarity matrix A (2x3) such that src = s*R*dst + t."""
        import torch

        # Similarity parametrization:
        #   x' = a*x - b*y + c
        #   y' = b*x + a*y + d
        # Rows for x' and y' are stacked into one linear system.
        x = dst[:, 0]
        y = dst[:, 1]
        xp = src[:, 0]
        yp = src[:, 1]

        top = torch.stack([x, -y, torch.ones_like(x), torch.zeros_like(x)], dim=1)
        bot = torch.stack([y, x, torch.zeros_like(x), torch.ones_like(x)], dim=1)
        matrix = torch.cat([top, bot], dim=0)
        target = torch.cat([xp, yp], dim=0)

        sol = torch.linalg.lstsq(matrix, target).solution
        a, b, c, d = sol[0], sol[1], sol[2], sol[3]
        return torch.stack(
            [
                torch.stack([a, -b, c]),
                torch.stack([b, a, d]),
            ]
        )

    def _make_grid(
        self,
        affine: torch.Tensor,
        out_h: int,
        out_w: int,
        in_w: int,
        in_h: int,
    ) -> torch.Tensor:
        """Create a grid_sample grid mapping output pixels to normalized input coordinates."""
        import torch

        y = torch.arange(out_h, dtype=affine.dtype, device=affine.device)
        x = torch.arange(out_w, dtype=affine.dtype, device=affine.device)
        yy, xx = torch.meshgrid(y, x, indexing="ij")
        ones = torch.ones_like(xx)
        flat = torch.stack([xx.reshape(-1), yy.reshape(-1), ones.reshape(-1)], dim=1)

        src_pixels = flat @ affine.T

        src_pixels[:, 0] = 2.0 * src_pixels[:, 0] / max(in_w - 1, 1) - 1.0
        src_pixels[:, 1] = 2.0 * src_pixels[:, 1] / max(in_h - 1, 1) - 1.0

        return src_pixels.view(out_h, out_w, 2).unsqueeze(0)
